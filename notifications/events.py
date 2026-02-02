from django.contrib.contenttypes.models import ContentType

from notifications.models import Notification


class EventTypes:
    PROPERTY_MATCHED = "PROPERTY_MATCHED"

    TITLES = {
        PROPERTY_MATCHED: "MATCH CON TU PROPIEDAD",
    }

EVENT_CONFIG = {
    EventTypes.PROPERTY_MATCHED: {
        "pk_field": "id",
        "conditions": [
            lambda match: float(getattr(match, "score", 0) or 0) >= 50.0
        ],
        "recipients": [
            {
                "type": "related_object",
                "field_paths": ["property.created_by", "property.user", "property.owner"],
                "title": "MATCH CON TU PROPIEDAD",
                "text": lambda match: (
                    f'Hicieron match con tu propiedad en {float(match.score):.2f} %. '
                    f'¡Se pondrán en contacto contigo!'
                ),
                "recipient_key": "property_owner",
            },
            {
                "type": "related_object",
                "field_paths": ["requirement.created_by", "requirement.user", "requirement.owner"],
                "title": "¡ENCONTRAMOS UN MATCH!",
                "text": lambda match: (
                    f'Hiciste match en un {float(match.score):.2f}%. '
                    f'Revisa los detalles y contacta al agente.'
                ),
                "recipient_key": "requirement_owner",
            },
        ],
    }
}

class EventHandler:
    def __init__(self, event_type, instance, context=None):
        self.event_type = event_type
        self.instance = instance
        self.context = context or {}
        self.config = EVENT_CONFIG.get(event_type)

        if not self.config:
            raise ValueError(f"Unknown event_type: {event_type}")

        pk_field = self.config.get("pk_field", "id")
        self.source_id = getattr(instance, pk_field, None)
        if self.source_id is None:
            raise ValueError(f"Missing primary key '{pk_field}' for {event_type}")

    # -------------------------
    # Recipient resolution utils
    # -------------------------
    def _get_related_object(self, obj, field_path: str):
        """Navigate through object relations to get the specified object"""
        current = obj
        for field in field_path.split("."):
            if current is None:
                return None
            current = getattr(current, field, None)
        return current

    def _resolve_recipient(self, recipient_config: dict):
        """
        Resolve recipient from recipient_config.
        Supports:
          - field_path: single path
          - field_paths: list of fallback paths (first truthy wins)
        """
        field_paths = recipient_config.get("field_paths")
        if field_paths and isinstance(field_paths, list):
            for path in field_paths:
                recipient = self._get_related_object(self.instance, path)
                if recipient:
                    return recipient
            return None

        field_path = recipient_config.get("field_path")
        if field_path:
            return self._get_related_object(self.instance, field_path)

        return None

    def _resolve_text_for_recipient(self, recipient_config: dict):
        """
        Resolve message text for this recipient.
        Priority:
          1) recipient_config["text"] if callable/str
          2) config["text"] if callable/str
        """
        # 1) text per recipient
        text_cfg = recipient_config.get("text")
        if callable(text_cfg):
            return text_cfg(self.instance)
        if isinstance(text_cfg, str) and text_cfg.strip():
            return text_cfg

        # 2) fallback to event-level text (if you ever want it)
        text_cfg = self.config.get("text")
        if callable(text_cfg):
            return text_cfg(self.instance)
        if isinstance(text_cfg, str) and text_cfg.strip():
            return text_cfg

        return ""

    def _resolve_title_for_recipient(self, recipient_config: dict):
        return (
            recipient_config.get("title")
            or EventTypes.TITLES.get(self.event_type, "Notificación")
        )

    # -------------------------
    # Main
    # -------------------------
    def perform(self):
        # 1) validar condiciones del evento (si existen)
        conditions = self.config.get("conditions", [])
        for cond in conditions:
            try:
                if callable(cond) and not cond(self.instance):
                    return
            except Exception:
                return
            
        ct = ContentType.objects.get_for_model(self.instance.__class__)

        recipients_cfg = self.config.get("recipients", [])
        if not isinstance(recipients_cfg, list):
            return

        seen_user_ids = set()

        for rcfg in recipients_cfg:
            if rcfg.get("type") != "related_object":
                continue

            recipient = self._resolve_recipient(rcfg)
            if not recipient:
                continue

            rid = getattr(recipient, "id", None)
            if rid in seen_user_ids:
                continue
            seen_user_ids.add(rid)

            title = self._resolve_title_for_recipient(rcfg)
            message = self._resolve_text_for_recipient(rcfg)

            Notification.objects.get_or_create(
                user=recipient,
                event_type=self.event_type,
                content_type=ct,
                object_id=self.source_id,
                defaults={
                    "title": title,
                    "message": message,
                    "data": {
                        "property_id": getattr(self.instance, "property_id", None),
                        "requirement_id": getattr(self.instance, "requirement_id", None),
                        "recipient_key": rcfg.get("recipient_key"),
                        "score": getattr(self.instance, "score", None),
                    },
                },
            )

def on_property_matched(requirement_match):
    EventHandler(EventTypes.PROPERTY_MATCHED, requirement_match).perform()