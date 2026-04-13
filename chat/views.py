from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db.models import Q

from .models import MailThread, Message, Attachment

User = get_user_model()


@login_required
def search_users(request):
    q = (request.GET.get("q") or "").strip()
    out = []

    if not q:
        return JsonResponse({"results": out})

    qs = User.objects.exclude(pk=request.user.pk)
    qs = qs.filter(
        Q(username__icontains=q) |
        Q(first_name__icontains=q) |
        Q(last_name__icontains=q) |
        Q(email__icontains=q)
    )[:30]

    for u in qs:
        label = u.get_full_name() or u.username
        out.append({
            "id": u.pk,
            "label": label,
            "email": u.email,
        })

    return JsonResponse({"results": out})


@login_required
def conversation_list(request):
    return redirect("chat:inbox")


@login_required
def sent(request):
    return redirect(f"{reverse('chat:inbox')}?folder=sent")


@login_required
def inbox(request):
    folder = (request.GET.get("folder") or "all").strip().lower()
    selected = request.GET.get("selected")

    threads_qs = (
        MailThread.objects
        .filter(participants=request.user)
        .prefetch_related("participants", "messages__attachments")
        .order_by("-updated_at")
    )

    threads = []

    for thread in threads_qs:
        last = thread.messages.order_by("-created_at").first()
        if not last:
            continue

        has_unread = thread.messages.exclude(sender=request.user).filter(is_read=False).exists()
        is_received = last.sender_id != request.user.id
        is_sent = last.sender_id == request.user.id

        if folder == "unread" and not has_unread:
            continue
        if folder == "received" and not is_received:
            continue
        if folder == "sent" and not is_sent:
            continue

        threads.append({
            "thread": thread,
            "last": last,
            "has_unread": has_unread,
            "is_received": is_received,
            "is_sent": is_sent,
        })

    selected_thread = None
    messages = []

    if selected:
        try:
            sid = int(selected)
            selected_thread = MailThread.objects.filter(participants=request.user, pk=sid).first()
            if selected_thread:
                messages = selected_thread.messages.select_related("sender").prefetch_related("attachments").order_by("created_at")

                Message.objects.filter(
                    conversation=selected_thread
                ).exclude(
                    sender=request.user
                ).filter(
                    is_read=False
                ).update(is_read=True)
        except Exception:
            selected_thread = None
            messages = []

    context = {
        "threads": threads,
        "selected_thread": selected_thread,
        "messages": messages,
        "active_folder": folder if folder in ["all", "unread", "received", "sent"] else "all",
    }
    return render(request, "chat/inbox.html", context)


@login_required
def conversation_detail(request, pk: int):
    conv = get_object_or_404(MailThread, pk=pk)

    if request.user not in conv.participants.all():
        return HttpResponseBadRequest("No autorizado")

    Message.objects.filter(
        conversation=conv
    ).exclude(
        sender=request.user
    ).filter(
        is_read=False
    ).update(is_read=True)

    messages = conv.messages.select_related("sender").prefetch_related("attachments").order_by("created_at")

    return render(request, "chat/conversation_detail.html", {
        "conversation": conv,
        "messages": messages,
    })


@login_required
@csrf_exempt
def send_message(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    try:
        conv_id = int(request.POST.get("conversation"))
        body = (request.POST.get("body") or "").strip()
    except Exception:
        return HttpResponseBadRequest("Invalid data")

    if not body and not request.FILES:
        return HttpResponseBadRequest("Empty message")

    conv = get_object_or_404(MailThread, pk=conv_id)

    if request.user not in conv.participants.all():
        return HttpResponseBadRequest("No autorizado")

    msg = Message.objects.create(
        conversation=conv,
        sender=request.user,
        sender_name=str(request.user.get_full_name() or request.user.username),
        sender_role=getattr(request.user, "role", None) and str(request.user.role) or "",
        body=body,
        message_type="text",
        created_at=timezone.now(),
    )

    try:
        files = request.FILES.getlist("attachments")
    except Exception:
        files = []

    for f in files:
        try:
            Attachment.objects.create(
                message=msg,
                file=f,
                content_type=getattr(f, "content_type", ""),
                size=getattr(f, "size", None),
            )
        except Exception:
            pass

    conv.updated_at = timezone.now()
    conv.save(update_fields=["updated_at"])

    return JsonResponse({
        "ok": True,
        "message_id": msg.id,
        "created_at": msg.created_at.isoformat(),
        "sender_name": msg.sender_name,
    })


@login_required
def unread_count(request):
    qs = (
        Message.objects
        .filter(conversation__participants=request.user)
        .exclude(sender=request.user)
        .filter(is_read=False)
    )

    count = qs.count()
    preview = []

    for m in qs.select_related("conversation", "sender").order_by("-created_at")[:5]:
        preview.append({
            "id": m.id,
            "conversation_id": m.conversation.id,
            "title": m.conversation.title or f"Conv {m.conversation.id}",
            "sender": m.sender_name or (m.sender.get_full_name() if m.sender else ""),
            "snippet": (m.body or "")[:120],
            "created_at": m.created_at.isoformat(),
        })

    return JsonResponse({
        "count": count,
        "preview": preview,
    })


@login_required
@csrf_exempt
def mark_read(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    try:
        conv_id = int(request.POST.get("conversation"))
    except Exception:
        return HttpResponseBadRequest("Invalid conversation id")

    conv = get_object_or_404(MailThread, pk=conv_id)

    if request.user not in conv.participants.all():
        return HttpResponseBadRequest("No autorizado")

    updated = Message.objects.filter(
        conversation=conv
    ).exclude(
        sender=request.user
    ).filter(
        is_read=False
    ).update(is_read=True)

    return JsonResponse({"ok": True, "updated": updated})


@login_required
def fetch_messages(request):
    try:
        conv_id = int(request.GET.get("conversation"))
        since = request.GET.get("since")
    except Exception:
        return HttpResponseBadRequest("Invalid params")

    conv = get_object_or_404(MailThread, pk=conv_id)

    if request.user not in conv.participants.all():
        return HttpResponseBadRequest("No autorizado")

    qs = conv.messages.select_related("sender").order_by("created_at")

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
        out.append({
            "id": m.id,
            "sender_name": m.sender_name or (m.sender.get_full_name() if m.sender else ""),
            "body": m.body,
            "created_at": m.created_at.isoformat(),
            "message_type": m.message_type,
        })

    return JsonResponse({"messages": out})


@login_required
def compose(request):
    """Compose an internal message: create (or reuse) a conversation and send message with attachments."""
    preselected_recipient = None
    initial_subject = (request.GET.get('subject') or '').strip()

    recipient_id = request.GET.get('recipient')
    if recipient_id:
        try:
            preselected_recipient = User.objects.exclude(pk=request.user.pk).get(
                pk=int(recipient_id),
                is_active=True,
            )
        except (User.DoesNotExist, ValueError, TypeError):
            preselected_recipient = None

    if request.method == 'POST':
        recipient_ids = request.POST.getlist('recipients')
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()

        if not recipient_ids:
            return HttpResponseBadRequest('Seleccione al menos un destinatario')

        participants = [request.user]
        for rid in recipient_ids:
            try:
                u = User.objects.get(pk=int(rid))
                if u.pk != request.user.pk:
                    participants.append(u)
            except Exception:
                continue

        unique_participants = []
        seen_ids = set()
        for user in participants:
            if user.pk not in seen_ids:
                unique_participants.append(user)
                seen_ids.add(user.pk)

        conv = MailThread.objects.create(title=subject or None)
        conv.participants.add(*unique_participants)
        conv.save()

        msg = Message.objects.create(
            conversation=conv,
            sender=request.user,
            sender_name=str(request.user.get_full_name() or request.user.username),
            sender_role=getattr(request.user, 'role', None) and str(request.user.role) or '',
            body=body,
            message_type='text',
            created_at=timezone.now()
        )

        try:
            files = request.FILES.getlist('attachments')
        except Exception:
            files = []

        for f in files:
            try:
                Attachment.objects.create(
                    message=msg,
                    file=f,
                    content_type=getattr(f, 'content_type', ''),
                    size=getattr(f, 'size', None),
                )
            except Exception:
                pass

        conv.updated_at = timezone.now()
        conv.save()

        return redirect(reverse('chat:inbox'))

    users = User.objects.exclude(pk=request.user.pk).order_by('username')[:200]
    return render(request, 'chat/compose.html', {
        'users': users,
        'preselected_recipient': preselected_recipient,
        'initial_subject': initial_subject,
    })