from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Task, TaskComment
from django.contrib.auth import get_user_model
from django.contrib import messages
import json

User = get_user_model()

@login_required
def kanban_board(request):
    if request.user.is_superuser:
        tasks = Task.objects.all().select_related('assigned_to', 'assigned_to__profile').prefetch_related('comments', 'comments__user')
        users_list = User.objects.filter(is_active=True).exclude(is_superuser=True)
    else:
        tasks = Task.objects.filter(assigned_to=request.user).select_related('assigned_to', 'assigned_to__profile').prefetch_related('comments', 'comments__user')
        users_list = None
    
    context = {
        'tasks': tasks,
        'tasks_pending': tasks.filter(status='pending'),
        'tasks_in_progress': tasks.filter(status='in_progress'),
        'tasks_done': tasks.filter(status='done'),
        'users_list': users_list,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'tasks/kanban.html', context)

@login_required
@require_POST
def task_create(request):
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para crear tareas.")
        return redirect('tasks:kanban_board')
    
    title = request.POST.get('title')
    description = request.POST.get('description', '')
    assigned_to_id = request.POST.get('assigned_to')
    color = request.POST.get('color', '#047d7d')
    
    if title:
        assigned_user = None
        if assigned_to_id:
            assigned_user = User.objects.filter(id=assigned_to_id).first()
            
        Task.objects.create(
            title=title,
            description=description,
            assigned_to=assigned_user,
            color=color,
            created_by=request.user
        )
        messages.success(request, "Tarea creada exitosamente.")
    else:
        messages.error(request, "El título es obligatorio.")
        
    return redirect('tasks:kanban_board')

@login_required
@require_POST
def task_update_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    # El superusuario puede mover cualquiera, el usuario solo la suya
    if not request.user.is_superuser and task.assigned_to != request.user:
        return JsonResponse({'status': 'error', 'message': 'No autorizado'}, status=403)
        
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        if new_status in ['pending', 'in_progress', 'done']:
            task.status = new_status
            task.save()
            return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Estado inválido'}, status=400)

@login_required
@require_POST
def task_edit(request):
    if not request.user.is_superuser:
        messages.error(request, "No autorizado.")
        return redirect('tasks:kanban_board')
    
    task_id = request.POST.get('task_id')
    task = get_object_or_404(Task, id=task_id)
    
    task.title = request.POST.get('title', task.title)
    task.description = request.POST.get('description', task.description)
    task.color = request.POST.get('color', task.color)
    assigned_to_id = request.POST.get('assigned_to')
    
    if assigned_to_id:
        task.assigned_to = User.objects.filter(id=assigned_to_id).first()
    else:
        task.assigned_to = None
        
    task.save()
    messages.success(request, "Tarea actualizada.")
    return redirect('tasks:kanban_board')

@login_required
@require_POST
def task_delete(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'No autorizado'}, status=403)
    
    task = get_object_or_404(Task, pk=pk)
    task.delete()
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def task_add_comment(request):
    task_id = request.POST.get('task_id')
    task = get_object_or_404(Task, id=task_id)
    
    if not request.user.is_superuser and task.assigned_to != request.user:
        messages.error(request, "No autorizado.")
        return redirect('tasks:kanban_board')
        
    content = request.POST.get('content')
    if content:
        TaskComment.objects.create(
            task=task,
            user=request.user,
            content=content
        )
        messages.success(request, "Comentario añadido.")
    
    return redirect('tasks:kanban_board')
