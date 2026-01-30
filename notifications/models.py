from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    # Tipo de evento (para filtrar / traducir / agrupar)
    event_type = models.CharField(max_length=50)  # ej: "PROPERTY_MATCHED"

    title = models.CharField(max_length=120, blank=True, default="")
    message = models.TextField()

    # Fuente polimórfica (el “objeto que originó” la notificación)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    source_object = GenericForeignKey("content_type", "object_id")

    # Metadata flexible (score, urls, ids extra, etc.)
    data = models.JSONField(default=dict, blank=True)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event_type", "content_type", "object_id"],
                name="uniq_notification_source"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.event_type}"