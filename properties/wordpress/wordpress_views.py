from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.conf import settings
from properties.models import Property
from .service import WordPressSyncService


def _check_internal_key(request):
    # ✅ Si viene desde el dashboard (usuario logueado), permitir.
    user = getattr(request, "user", None)
    if user and user.is_authenticated and (user.is_staff or user.is_superuser):
        return True

    # ✅ Si viene desde afuera, exigir INTERNAL_SYNC_KEY
    expected = getattr(settings, "INTERNAL_SYNC_KEY", None)
    if not expected:
        return True
    return request.headers.get("X-INTERNAL-KEY") == expected


class WPAuthTestView(APIView):
    def get(self, request):
        if not _check_internal_key(request):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        svc = WordPressSyncService()
        return Response(svc.test_auth())


class WPSyncOneView(APIView):
    def post(self, request, property_id: int):
        if not _check_internal_key(request):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        prop = Property.objects.get(id=property_id)
        svc = WordPressSyncService()
        try:
            wp_obj = svc.sync_one(prop)
            return Response({"ok": True, "wp": wp_obj})
        except ValidationError as e:
            return Response({"ok": False, **e.detail}, status=status.HTTP_400_BAD_REQUEST)


class WPGetOneView(APIView):
    def get(self, request, property_id: int):
        if not _check_internal_key(request):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        prop = Property.objects.get(id=property_id)
        svc = WordPressSyncService()
        wp_obj = svc.get_wp_property_for(prop)
        return Response({"property_id": prop.id, "wp_post_id": prop.wp_post_id, "wp": wp_obj})


class WPDeleteOneView(APIView):
    def delete(self, request, property_id: int):
        if not _check_internal_key(request):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        force = str(request.query_params.get("force", "true")).lower() == "true"
        prop = Property.objects.get(id=property_id)
        svc = WordPressSyncService()
        result = svc.delete_one(prop, force=force)
        return Response(result)


class WPSyncManyView(APIView):
    def post(self, request):
        if not _check_internal_key(request):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        only_active = request.data.get("only_active", True)
        limit = request.data.get("limit")

        qs = Property.objects.all().order_by("id")
        if only_active:
            qs = qs.filter(is_active=True)

        if limit:
            qs = qs[: int(limit)]

        svc = WordPressSyncService()
        result = svc.sync_many(qs)
        return Response(result)