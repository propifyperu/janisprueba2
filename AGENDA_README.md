# Sistema de Agenda - Propify

## 📅 Descripción

Sistema de gestión de eventos y visitas con interfaz estilo Google Calendar, que permite a los usuarios programar y gestionar visitas, reuniones y otros eventos relacionados con propiedades inmobiliarias.

## ✨ Características Principales

### 🎨 Interfaz de Usuario
- **Diseño profesional** inspirado en Google Calendar
- **Mini calendario** en barra lateral para navegación rápida
- **Vistas múltiples**: Día, Semana y Mes
- **Día actual destacado** en color verde
- **Modal de detalles** con información completa del evento
- **Botón flotante** para crear eventos rápidamente

### 📊 Funcionalidades

#### Gestión de Eventos
- **Crear eventos** con información completa:
  - Código único generado automáticamente (formato: EVT2026XXXXXX)
  - Tipo de evento (Visita, Reunión, Llamada, etc.)
  - Título
  - Fecha y horario (inicio y fin)
  - Detalle de la visita
  - Interesado
  - Inmueble relacionado (opcional)

- **Editar eventos** existentes
- **Eliminar eventos**
- **Visualizar eventos** en calendario interactivo

#### Tipos de Eventos Predefinidos
1. **Visita** - Color turquesa (#047D7D)
2. **Reunión** - Color azul (#2196F3)
3. **Llamada** - Color naranja (#FF9800)
4. **Firma de Contrato** - Color verde (#4CAF50)
5. **Entrega de Llaves** - Color púrpura (#9C27B0)
6. **Seguimiento** - Color gris (#607D8B)
7. **Otro** - Color gris oscuro (#757575)

### 🔐 Sistema de Permisos

#### Usuario Regular
- Ve **únicamente sus propios eventos**
- Puede crear, editar y eliminar solo sus eventos
- No puede ver eventos de otros usuarios

#### Superusuario
- Ve **todos los eventos de todos los usuarios**
- Puede editar y eliminar cualquier evento
- Vista completa del calendario de toda la organización

## 🗂️ Estructura de Archivos

### Modelos
```python
# properties/models.py
- EventType: Tipos de eventos con colores
- Event: Eventos/visitas agendadas
```

### Vistas
```python
# properties/views.py
- agenda_calendar_view: Dashboard principal del calendario
- event_create_view: Crear nuevo evento
- event_edit_view: Editar evento existente
- event_delete_view: Eliminar evento
- api_events_json: API JSON para FullCalendar
```

### Templates
```
properties/templates/properties/
├── agenda_calendar.html  # Dashboard principal con calendario
├── event_create.html     # Formulario crear evento
└── event_edit.html       # Formulario editar evento
```

### URLs
```
/dashboard/propiedades/agenda/                      # Calendario principal
/dashboard/propiedades/agenda/eventos/crear/        # Crear evento
/dashboard/propiedades/agenda/eventos/<id>/editar/  # Editar evento
/dashboard/propiedades/agenda/eventos/<id>/borrar/  # Eliminar evento
/dashboard/propiedades/api/events/                  # API JSON eventos
```

## 🚀 Tecnologías Utilizadas

- **Backend**: Django 5.x
- **Frontend**: FullCalendar 6.1.10
- **Estilos**: CSS personalizado con diseño Material
- **Base de datos**: SQL Server

## 📝 Uso

### Acceder al Calendario
1. Navegar a `/dashboard/propiedades/agenda/`
2. Ver eventos en el calendario con diferentes vistas (día/semana/mes)
3. Hacer clic en un evento para ver detalles
4. Usar el mini calendario para navegación rápida

### Crear un Evento
1. Hacer clic en el botón **"Crear evento"**
2. Completar el formulario:
   - Seleccionar tipo de evento
   - Ingresar título
   - Seleccionar fecha
   - Definir horario de inicio y fin
   - (Opcional) Agregar interesado, inmueble y detalles
3. Guardar

### Editar un Evento
1. Hacer clic en el evento en el calendario
2. En el modal, hacer clic en **"Editar"**
3. Modificar los campos necesarios
4. Guardar cambios

### Eliminar un Evento
1. Hacer clic en el evento en el calendario
2. En el modal, hacer clic en **"Eliminar"**
3. Confirmar la eliminación

## 🎯 Campos del Modelo Event

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `code` | CharField | Código único autogenerado (EVT2026XXXXXX) |
| `event_type` | ForeignKey | Tipo de evento |
| `titulo` | CharField | Título del evento |
| `fecha_evento` | DateField | Fecha del evento |
| `hora_inicio` | TimeField | Hora de inicio |
| `hora_fin` | TimeField | Hora de término |
| `detalle` | TextField | Detalle de la visita |
| `interesado` | CharField | Nombre del interesado |
| `property` | ForeignKey | Inmueble relacionado (opcional) |
| `created_by` | ForeignKey | Usuario creador |
| `created_at` | DateTimeField | Fecha de creación |
| `updated_at` | DateTimeField | Última actualización |
| `is_active` | BooleanField | Estado activo/inactivo |

## 🔧 Validaciones

- La hora de término debe ser posterior a la hora de inicio
- Los campos obligatorios: tipo de evento, título, fecha, hora inicio, hora fin
- El código se genera automáticamente y es único
- Los campos de texto aplican TitleCase automáticamente

## 📱 Responsive

El diseño está optimizado para diferentes tamaños de pantalla:
- **Desktop**: Vista completa con sidebar y calendario
- **Tablet**: Diseño adaptado
- **Mobile**: Vista optimizada para dispositivos móviles

## 🎨 Personalización

### Agregar Nuevos Tipos de Evento
```python
from properties.models import EventType

EventType.objects.create(
    name='Nuevo Tipo',
    color='#FF5733',  # Color en formato hexadecimal
    is_active=True
)
```

### Modificar Colores de Eventos Existentes
Desde el admin de Django:
1. Ir a `/admin/properties/eventtype/`
2. Seleccionar el tipo de evento
3. Modificar el campo `color`
4. Guardar

## 🔒 Seguridad

- Requiere autenticación (`@login_required`)
- Control de permisos por usuario
- Solo el creador y superusuarios pueden editar/eliminar eventos
- API filtra eventos según permisos del usuario

## 📊 Integración con Propiedades

Los eventos pueden asociarse a propiedades específicas mediante el campo `property`:
- Permite vincular visitas a inmuebles
- Muestra la dirección exacta del inmueble en el evento
- Facilita el seguimiento de actividades por propiedad

## 🎓 Casos de Uso

1. **Agendar visitas** de clientes a propiedades
2. **Programar reuniones** con propietarios o interesados
3. **Registrar llamadas** de seguimiento
4. **Coordinar firmas** de contratos
5. **Planificar entregas** de llaves
6. **Gestionar seguimientos** de clientes

## 📞 Soporte

Para más información sobre el sistema de agenda, consultar la documentación general del proyecto o contactar al equipo de desarrollo.

---

**Versión**: 1.0.0  
**Fecha**: 6 de enero de 2026  
**Desarrollado para**: Propify
