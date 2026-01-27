from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from .models import MailThread, Message, Attachment
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def search_users(request):
    """API simple para buscar usuarios por nombre, apellido o username.

    Query param: `q` (string). Devuelve hasta 30 coincidencias (id, label, email).
    """
    q = (request.GET.get('q') or '').strip()
    out = []
    if not q:
        return JsonResponse({'results': out})
    qs = User.objects.exclude(pk=request.user.pk)
    # buscar en username, first_name, last_name y email
    from django.db.models import Q
    qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))[:30]
    for u in qs:
        label = (u.get_full_name() or u.username)
        out.append({'id': u.pk, 'label': label, 'email': u.email})
    return JsonResponse({'results': out})

from django.urls import reverse
from django.shortcuts import redirect
from django.db.models import Max
from django.db.models import Q


@login_required
def conversation_list(request):
    qs = MailThread.objects.filter(participants=request.user).order_by('-updated_at')
    return render(request, 'chat/conversation_list.html', {'conversations': qs})


@login_required
def conversation_detail(request, pk: int):
    conv = get_object_or_404(MailThread, pk=pk)
    if request.user not in conv.participants.all():
        return HttpResponseBadRequest('No autorizado')
    messages = conv.messages.select_related('sender').order_by('created_at')
    return render(request, 'chat/conversation_detail.html', {'conversation': conv, 'messages': messages})


@login_required
@csrf_exempt
def send_message(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')
    try:
        conv_id = int(request.POST.get('conversation'))
        body = request.POST.get('body', '').strip()
    except Exception:
        return HttpResponseBadRequest('Invalid data')
    # allow messages that include attachments even without body text
    if not body and not request.FILES:
        return HttpResponseBadRequest('Empty message')
    conv = get_object_or_404(MailThread, pk=conv_id)
    if request.user not in conv.participants.all():
        return HttpResponseBadRequest('No autorizado')
    msg = Message.objects.create(
        conversation=conv,
        sender=request.user,
        sender_name=str(request.user.get_full_name() or request.user.username),
        sender_role=getattr(request.user, 'role', None) and str(request.user.role) or '',
        body=body,
        message_type='text',
        created_at=timezone.now()
    )
    # save attachments if present
    try:
        files = request.FILES.getlist('attachments')
    except Exception:
        files = []
    for f in files:
        try:
            Attachment.objects.create(message=msg, file=f, content_type=getattr(f, 'content_type', ''), size=getattr(f, 'size', None))
        except Exception:
            pass
    # update conversation timestamp
    conv.updated_at = timezone.now()
    conv.save()
    return JsonResponse({'ok': True, 'message_id': msg.id, 'created_at': msg.created_at.isoformat(), 'sender_name': msg.sender_name})


@login_required
def unread_count(request):
    qs = Message.objects.filter(conversation__participants=request.user).exclude(sender=request.user).filter(is_read=False)
    count = qs.count()
    preview = []
    for m in qs.select_related('conversation', 'sender').order_by('-created_at')[:5]:
        preview.append({
            'id': m.id,
            'conversation_id': m.conversation.id,
            'title': m.conversation.title or f'Conv {m.conversation.id}',
            'sender': m.sender_name or (m.sender.get_full_name() if m.sender else ''),
            'snippet': (m.body or '')[:120],
            'created_at': m.created_at.isoformat(),
        })
    return JsonResponse({'count': count, 'preview': preview})


@login_required
@csrf_exempt
def mark_read(request):
    """Marcar mensajes de una conversación como leídos por el usuario actual.

    POST: conversation (int)
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')
    try:
        conv_id = int(request.POST.get('conversation'))
    except Exception:
        return HttpResponseBadRequest('Invalid conversation id')
    conv = get_object_or_404(MailThread, pk=conv_id)
    if request.user not in conv.participants.all():
        return HttpResponseBadRequest('No autorizado')
    # marcar solo mensajes no enviados por el usuario
    msgs = Message.objects.filter(conversation=conv).exclude(sender=request.user).filter(is_read=False)
    updated = msgs.update(is_read=True)
    return JsonResponse({'ok': True, 'updated': updated})


@login_required
def fetch_messages(request):
    try:
        conv_id = int(request.GET.get('conversation'))
        since = request.GET.get('since')
    except Exception:
        return HttpResponseBadRequest('Invalid params')
    conv = get_object_or_404(MailThread, pk=conv_id)
    if request.user not in conv.participants.all():
        return HttpResponseBadRequest('No autorizado')
    qs = conv.messages.select_related('sender').order_by('created_at')
    if since:
        try:
            from django.utils.dateparse import parse_datetime
            dt = parse_datetime(since)
            if dt:
                qs = qs.filter(created_at__gt=dt)
        except Exception:
            pass
    out = []
    for m in qs:
        out.append({'id': m.id, 'sender_name': m.sender_name or (m.sender.get_full_name() if m.sender else ''), 'body': m.body, 'created_at': m.created_at.isoformat(), 'message_type': m.message_type})
    return JsonResponse({'messages': out})


@login_required
def compose(request):
    """Compose an internal message: create (or reuse) a conversation and send message with attachments."""
    if request.method == 'POST':
        # recipients: comma separated user ids (from form select)
        recipient_ids = request.POST.getlist('recipients')
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()

        if not recipient_ids:
            return HttpResponseBadRequest('Seleccione al menos un destinatario')

        # create conversation including sender + recipients
        participants = [request.user]
        for rid in recipient_ids:
            try:
                u = User.objects.get(pk=int(rid))
                participants.append(u)
            except Exception:
                continue

        conv = MailThread.objects.create(title=subject or None)
        conv.participants.add(*participants)
        conv.save()

        # create message
        msg = Message.objects.create(
            conversation=conv,
            sender=request.user,
            sender_name=str(request.user.get_full_name() or request.user.username),
            sender_role=getattr(request.user, 'role', None) and str(request.user.role) or '',
            body=body,
            message_type='text',
            created_at=timezone.now()
        )

        # attachments
        try:
            files = request.FILES.getlist('attachments')
        except Exception:
            files = []
        for f in files:
            try:
                Attachment.objects.create(message=msg, file=f, content_type=getattr(f, 'content_type', ''), size=getattr(f, 'size', None))
            except Exception:
                pass

        conv.updated_at = timezone.now()
        conv.save()

        return redirect(reverse('chat:sent'))

    # GET: render form
    users = User.objects.exclude(pk=request.user.pk).order_by('username')[:200]
    return render(request, 'chat/compose.html', {'users': users})


@login_required
def inbox(request):
    """Muestra hilos donde el usuario es participante y el último mensaje NO fue enviado por él (entradas)."""
    threads = MailThread.objects.filter(participants=request.user).order_by('-updated_at')
    inbox_threads = []
    for t in threads:
        last = t.messages.order_by('-created_at').first()
        if last and last.sender_id != request.user.id:
            inbox_threads.append({'thread': t, 'last': last})
    # soportar hilo seleccionado via ?selected=<id>
    selected = request.GET.get('selected')
    selected_thread = None
    messages = []
    if selected:
        try:
            sid = int(selected)
            st = MailThread.objects.filter(participants=request.user, pk=sid).first()
            if st:
                selected_thread = st
                messages = st.messages.select_related('sender').order_by('created_at')
        except Exception:
            selected_thread = None

    return render(request, 'chat/inbox.html', {'threads': inbox_threads, 'selected_thread': selected_thread, 'messages': messages})


@login_required
def sent(request):
    """Muestra hilos con mensajes enviados por el usuario (bandeja de salida)."""
    threads = MailThread.objects.filter(participants=request.user).order_by('-updated_at')
    sent_threads = []
    for t in threads:
        last = t.messages.order_by('-created_at').first()
        if last and last.sender_id == request.user.id:
            sent_threads.append({'thread': t, 'last': last})
    return render(request, 'chat/sent.html', {'threads': sent_threads})
