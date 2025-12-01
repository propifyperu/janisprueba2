from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    # Mostrar contenido de prueba para verificar funcionamiento
    return render(request, 'properties/dashboard.html', {
        'test_message': '¡Dashboard cargado correctamente! Si ves este mensaje, la vista funciona.'
    })
