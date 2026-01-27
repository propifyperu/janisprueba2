from django.db import models
from django.conf import settings

class Task(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('in_progress', 'En curso'),
        ('done', 'Hecho'),
    )

    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(blank=True, verbose_name="Descripción")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_tasks',
        verbose_name="Asignado a"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Estado"
    )
    color = models.CharField(max_length=7, default='#047D7D', verbose_name="Color de fondo")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        verbose_name="Creado por"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"

    def __str__(self):
        return self.title

class TaskComment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Tarea"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Usuario"
    )
    content = models.TextField(verbose_name="Comentario")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Comentario de Tarea"
        verbose_name_plural = "Comentarios de Tareas"

    def __str__(self):
        return f"Comentario de {self.user} en {self.task}"
