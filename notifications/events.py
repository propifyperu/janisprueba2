from django.contrib.contenttypes.models import ContentType

from notifications.models import Notification


class EventTypes:
    PROPERTY_MATCHED = "PROPERTY_MATCHED"

    TITLES = {
        PROPERTY_MATCHED: "MATCH CON TU PROPIEDAD",
    }


EVENT_CONFIG = {
    EventTypes.PROPERTY_MATCHED: {
        "min_score": 50.0,
        "text": lambda match: (
            f'Hicieron match con tu propiedad en {float(match.score):.2f} %. '
            f'¡Se pondrán en contacto contigo!'
        ),
        # cómo obtener destinatario (owner) desde el match
        "recipient": lambda match: getattr(match.property, "created_by", None)
                                 or getattr(match.property, "user", None)
                                 or getattr(match.property, "owner", None),
    }
}


class EventHandler:
    def __init__(self, event_type, instance):
        self.event_type = event_type
        self.instance = instance
        self.config = EVENT_CONFIG.get(event_type)

        if not self.config:
            raise ValueError(f"Unknown event_type: {event_type}")

    def perform(self):
        # 1) validar score mínimo
        min_score = float(self.config.get("min_score", 0))
        score = float(getattr(self.instance, "score", 0) or 0)
        if score < min_score:
            return

        # 2) obtener recipient
        recipient = self.config["recipient"](self.instance)
        if recipient is None:
            return

        # 3) construir texto
        message = self.config["text"](self.instance)
        title = EventTypes.TITLES.get(self.event_type, "Notificación")

        # 4) crear notificación deduplicada por source_object
        ct = ContentType.objects.get_for_model(self.instance.__class__)

        Notification.objects.get_or_create(
            user=recipient,
            event_type=self.event_type,
            content_type=ct,
            object_id=self.instance.id,
            defaults={
                "title": title,
                "message": message,
                "data": {
                    "score": score,
                    "property_id": getattr(self.instance, "property_id", None),
                    "requirement_id": getattr(self.instance, "requirement_id", None),
                }
            }
        )


def on_property_matched(requirement_match):
    EventHandler(EventTypes.PROPERTY_MATCHED, requirement_match).perform()