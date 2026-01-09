from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """Conversación entre usuarios. Puede ser 1:1 o grupal."""
    title = models.CharField(max_length=255, blank=True, null=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_conversations'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or f'Conversation {self.id}'


class Message(models.Model):
    """Mensaje dentro de una conversación.

    Guardamos un snapshot del nombre y rol del remitente para preservar historial.
    """
    MESSAGE_TYPE_CHOICES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System'),
    )

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    sender_name = models.CharField(max_length=255, blank=True, null=True)
    sender_role = models.CharField(max_length=100, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']

    def __str__(self):
        return f'Message {self.id} by {self.sender_name or self.sender_id}'


class Attachment(models.Model):
    """Archivos adjuntos vinculados a un mensaje."""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='chat/attachments/%Y/%m/%d')
    content_type = models.CharField(max_length=200, blank=True, null=True)
    size = models.PositiveIntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_attachments'

    def __str__(self):
        return getattr(self.file, 'name', '') or f'Attachment {self.id}'
