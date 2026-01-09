from django.contrib import admin
from .models import Conversation, Message, Attachment


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'updated_at')
    search_fields = ('title',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender_name', 'sender_role', 'message_type', 'created_at')
    search_fields = ('sender_name', 'body')
    list_filter = ('message_type',)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'file', 'content_type', 'size', 'uploaded_at')
    search_fields = ('file',)
