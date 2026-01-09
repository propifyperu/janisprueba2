from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from .models import Conversation, Message, Attachment
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

from django.urls import reverse
from django.shortcuts import redirect


@login_required
def conversation_list(request):
    qs = Conversation.objects.filter(participants=request.user).order_by('-updated_at')
    return render(request, 'chat/conversation_list.html', {'conversations': qs})


@login_required
def conversation_detail(request, pk: int):
    conv = get_object_or_404(Conversation, pk=pk)
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
    conv = get_object_or_404(Conversation, pk=conv_id)
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
def fetch_messages(request):
    try:
        conv_id = int(request.GET.get('conversation'))
        since = request.GET.get('since')
    except Exception:
        return HttpResponseBadRequest('Invalid params')
    conv = get_object_or_404(Conversation, pk=conv_id)
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

        conv = Conversation.objects.create(title=subject or None)
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

        return redirect(reverse('chat:conversation_detail', args=[conv.pk]))

    # GET: render form
    users = User.objects.exclude(pk=request.user.pk).order_by('username')[:200]
    return render(request, 'chat/compose.html', {'users': users})
