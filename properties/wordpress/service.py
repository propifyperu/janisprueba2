# properties/wordpress/service.py
from django.utils import timezone
from django.db import transaction
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from rest_framework.exceptions import ValidationError

from .client import WordPressClient
from .taxonomies import resolve_term_id, PROPERTY_COUNTRY_CANONICAL_ID
from .mapper import property_to_wp_payload

class WordPressSyncService:
    def __init__(self):
        self.client = WordPressClient()

    def test_auth(self):
        return self.client.me()

    def _resolve_term_id_local(self, taxonomy: str, name: str) -> int | None:
        return resolve_term_id(taxonomy, name)

    def _resolve_taxonomies(self, prop) -> tuple[dict[str, list[int]], list[dict]]:
        """
        Retorna:
        - taxonomy_ids: dict para payload
        - warnings: lista de faltantes
        """
        out: dict[str, list[int]] = {}
        warnings: list[dict] = []

        def add_one(taxonomy: str, label: str, name: str | None):
            if not name:
                return
            tid = self._resolve_term_id_local(taxonomy, name)
            if tid:
                out[taxonomy] = [tid]
            else:
                warnings.append({"taxonomy": taxonomy, "value": name, "reason": f"No existe en taxonomies.py ({label})"})

        # property_type
        if prop.property_type and getattr(prop.property_type, "name", None):
            add_one("property_type", "property_type.name", prop.property_type.name)

        # property_status
        if prop.status and getattr(prop.status, "name", None):
            add_one("property_status", "status.name", prop.status.name)

        # country: canonical fijo (evita PERU vs Perú)
        out["property_country"] = [PROPERTY_COUNTRY_CANONICAL_ID]

        # state/city/area usando tus properties calculadas
        add_one("property_state", "department_name", getattr(prop, "department_name", None))
        add_one("property_city", "province_name", getattr(prop, "province_name", None))
        add_one("property_area", "district_name", getattr(prop, "district_name", None))

        # features desde tags (si los tags no existen en tu taxonomies.py, saldrá warning)
        try:
            feature_ids = []
            for tag in prop.tags.all():
                fid = self._resolve_term_id_local("property_feature", tag.name)
                if fid:
                    feature_ids.append(fid)
                else:
                    warnings.append({"taxonomy": "property_feature", "value": tag.name, "reason": "No existe en taxonomies.py (tag)"})

            if feature_ids:
                # Houzez acepta lista (luego lo convertimos a CSV en mapper)
                out["property_feature"] = feature_ids
        except Exception:
            pass

        return out, warnings

    def _upload_images(self, prop) -> tuple[int | None, list[int]]:
        imgs = list(prop.images.all().order_by("-is_primary", "order", "id"))
        media_ids: list[int] = []
        featured_id: int | None = None

        def resolve_or_import(img):
            if not img.image:
                return None

            url = img.image.url  # Azure public URL

            # ✅ 2B: si ya tiene wp_media_id y la URL no cambió => reusar
            if img.wp_media_id and img.wp_source_url == url:
                return {
                    "media_id": img.wp_media_id,
                    "is_primary": img.is_primary,
                    "reused": True,
                    "img_id": img.id,
                }

            # ✅ si es nueva o cambió la URL => importar en WP
            media = self.client.import_media_from_url(url)
            mid = media.get("id")
            if not mid:
                return None

            # guardamos cache en BD (esta parte es rápida)
            img.__class__.objects.filter(id=img.id).update(
                wp_media_id=int(mid),
                wp_source_url=url,
                wp_last_sync=timezone.now(),
            )

            return {
                "media_id": int(mid),
                "is_primary": img.is_primary,
                "reused": False,
                "img_id": img.id,
            }

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(resolve_or_import, img) for img in imgs]

            for future in as_completed(futures):
                result = future.result()
                if not result:
                    continue

                mid = result["media_id"]
                if mid:
                    media_ids.append(mid)
                    if featured_id is None or result["is_primary"]:
                        featured_id = mid

        return featured_id, media_ids

    def _validate_min_wp_fields(self, prop):
        missing = []

        title = (prop.title or "").strip()
        desc = (prop.description or "").strip()

        if not title:
            missing.append("título")
        if not desc:
            missing.append("descripción")

        if missing:
            # mensaje listo para UI
            raise ValidationError({
                "detail": "No se puede publicar en WordPress.",
                "message": f"Te falta registrar {', '.join(missing)} antes de subir a WP.",
                "missing_fields": missing,
            })
        
    def sync_one(self, prop):
        self._validate_min_wp_fields(prop)

        slug = f"propify-{prop.id}"

        if not prop.wp_post_id:
            found = self.client.find_property_by_slug(slug)
            if found:
                wp_existing = found[0]
                wp_id = wp_existing.get("id")
                wp_slug = wp_existing.get("slug")

                # backfill local inmediato (sin depender de prop.save)
                prop.__class__.objects.filter(id=prop.id).update(
                    wp_post_id=wp_id,
                    wp_slug=wp_slug,
                    wp_last_sync=timezone.now(),
                )

                # refrescar objeto en memoria
                prop.wp_post_id = wp_id
                prop.wp_slug = wp_slug

        taxonomy_ids, warnings = self._resolve_taxonomies(prop)
        featured_id, gallery_ids = self._upload_images(prop)

        payload = property_to_wp_payload(
            prop,
            taxonomy_ids=taxonomy_ids,
            featured_media_id=featured_id,
            gallery_media_ids=gallery_ids,
        )
        payload["slug"] = slug

        if prop.wp_post_id:
            wp_obj = self.client.update_property(prop.wp_post_id, payload)
        else:
            wp_obj = self.client.create_property(payload)

            prop.__class__.objects.filter(id=prop.id).update(
                wp_post_id=wp_obj.get("id"),
                wp_slug=wp_obj.get("slug"),
                wp_last_sync=timezone.now(),
            )
            prop.wp_post_id = wp_obj.get("id")
            prop.wp_slug = wp_obj.get("slug")

        prop.__class__.objects.filter(id=prop.id).update(
            wp_post_id=wp_obj.get("id"),
            wp_slug=wp_obj.get("slug"),
            wp_last_sync=timezone.now(),
        )

        return {"wp": wp_obj, "warnings": warnings, "payload": payload}

    def delete_one(self, prop, force=True, delete_media=True):
        if not prop.wp_post_id:
            return {"deleted": False, "reason": "Property no tiene wp_post_id"}

        wp_post_id = prop.wp_post_id
        media_deleted = []
        media_errors = []

        # 1) (opcional) borrar medias en WP
        if delete_media:
            try:
                wp_obj = self.client.get_property(wp_post_id)
                featured_id = wp_obj.get("featured_media") or 0

                meta = wp_obj.get("property_meta") or {}
                gallery = meta.get("fave_property_images") or []

                media_ids = set()
                if featured_id:
                    media_ids.add(int(featured_id))

                for x in gallery:
                    for part in str(x).split(","):
                        part = part.strip()
                        if part.isdigit():
                            media_ids.add(int(part))

                for mid in sorted(media_ids):
                    try:
                        self.client.delete_media(mid, force=True)
                        media_deleted.append(mid)
                    except Exception as e:
                        media_errors.append({"media_id": mid, "error": str(e)})

            except Exception as e:
                media_errors.append({"step": "get_property", "error": str(e)})

        # 2) borrar el post en WP
        resp = self.client.delete_property(wp_post_id, force=force)

        # ✅ 3) LIMPIAR CACHE LOCAL de imágenes (la clave del bug)
        # Esto evita reusar wp_media_id que ya no existe en WP
        prop.images.all().update(
            wp_media_id=None,
            wp_source_url=None,
            wp_last_sync=None,
        )

        # 4) limpiar tracking del post en Django
        with transaction.atomic():
            prop.wp_post_id = None
            prop.wp_slug = None
            prop.wp_last_sync = None
            prop.save(update_fields=["wp_post_id", "wp_slug", "wp_last_sync"])

        return {
            "deleted": True,
            "wp_post_id": wp_post_id,
            "wp_response": resp,
            "media_deleted": media_deleted,
            "media_errors": media_errors,
        }