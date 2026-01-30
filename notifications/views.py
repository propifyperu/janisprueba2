import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.utils.timezone import localtime

from .models import Notification


def _serialize_notification(n: Notification) -> dict:
    dt = localtime(n.created_at) if n.created_at else None
    return {
        "id": n.id,
        "event_type": n.event_type,
        "title": n.title,
        "message": n.message,
        "is_read": n.is_read,
        "created_at": dt.isoformat() if dt else None,
        "data": n.data or {},
        "source": {
            "content_type_id": n.content_type_id,
            "object_id": n.object_id,
        },
    }


@login_required
@require_GET
def notifications_list(request):
    """
    GET /notifications/api/list/?limit=20&offset=0
    Devuelve array + unread_count
    """
    try:
        limit = int(request.GET.get("limit", 20))
        offset = int(request.GET.get("offset", 0))
    except ValueError:
        return HttpResponseBadRequest("limit/offset inválidos")

    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    qs = (
        Notification.objects
        .filter(user=request.user)
        .select_related("content_type")
        .order_by("-created_at")
    )

    total = qs.count()
    unread_count = qs.filter(is_read=False).count()

    items = list(qs[offset: offset + limit])
    results = [_serialize_notification(n) for n in items]

    return JsonResponse({
        "results": results,
        "total": total,
        "unread_count": unread_count,
        "limit": limit,
        "offset": offset,
    })


@login_required
@require_GET
def notifications_unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({"unread_count": count})


@login_required
@require_POST
def notification_mark_read(request, pk: int):
    """
    POST /notifications/api/<id>/mark-read/
    Marca como leída una notificación del usuario
    """
    updated = Notification.objects.filter(id=pk, user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"ok": True, "updated": int(updated)})


@login_required
@require_POST
def notifications_mark_read_bulk(request):
    """
    POST /notifications/api/mark-read-bulk/
    Body JSON: {"ids":[1,2,3]}
    """
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        ids = payload.get("ids", [])
        if not isinstance(ids, list):
            return HttpResponseBadRequest("ids debe ser lista")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")

    updated = (
        Notification.objects
        .filter(user=request.user, id__in=ids)
        .update(is_read=True)
    )

    return JsonResponse({"ok": True, "updated": int(updated)})
