# Sistema CRM con WhatsApp Business

## ✅ Completado

Se ha implementado un sistema completo de CRM integrado con WhatsApp Business API que incluye:

### 1. **Modelos de Base de Datos**
- `PropertyWhatsAppLink` - Enlace único por propiedad + red social con tracking UTM
- `Lead` - Leads generados desde WhatsApp con estado y asignación
- `WhatsAppConversation` - Conversaciones entre usuario y cliente

### 2. **Funcionalidades**

#### Gestión de Enlaces WhatsApp
- ✅ Crear enlaces únicos por propiedad y red social (Facebook, Instagram, Google, Website)
- ✅ Auto-generación de ID único para rastreo
- ✅ Parámetros UTM automáticos
- ✅ Asignación de número de WhatsApp Business a cada enlace

#### Gestión de Leads
- ✅ Creación automática de leads cuando alguien hace click
- ✅ Rastreo de red social de origen
- ✅ Estados de lead (Nuevo, Contactado, Calificado, Negociando, Ganado, Perdido)
- ✅ Asignación de leads a agentes
- ✅ Histórico de conversaciones

#### Webhook WhatsApp
- ✅ Recepción de mensajes entrantes de WhatsApp Business API
- ✅ Procesamiento automático de mensajes
- ✅ Almacenamiento de conversaciones

### 3. **Interfaces Web**
- ✅ Página para listar y crear enlaces por propiedad
- ✅ Dashboard de leads con filtros
- ✅ Página de detalle de lead con conversaciones
- ✅ Panel de admin para gestionar todo

---

## 🔧 Configuración

### Paso 1: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 2: Configurar Variables de Entorno

1. Abre el archivo `.env` en la raíz del proyecto
2. Reemplaza los valores:

```env
WHATSAPP_PHONE_NUMBER_ID=TU_ID_AQUI
WHATSAPP_BUSINESS_ACCOUNT_ID=TU_ID_AQUI
WHATSAPP_ACCESS_TOKEN=EAAx...TU_TOKEN_AQUI
WHATSAPP_VERIFY_TOKEN=MI_VERIFY_TOKEN_SEGURO
```

### Paso 3: Aplicar Migraciones

```bash
python manage.py migrate
```

---

## 📱 Cómo Usar

### Crear un Enlace WhatsApp

1. Ve a **Dashboard → Propiedades**
2. Selecciona una propiedad
3. Click en **"Enlaces WhatsApp"**
4. Click en **"Nuevo Enlace"**
5. Llena el formulario:
   - **Nombre del Enlace**: "Facebook Ads - Villa Marina"
   - **Red Social**: Facebook
   - **Número WhatsApp**: Tu número de teléfono
   - **Parámetros UTM** (opcional): Para rastrear en Google Analytics
6. Click en **"Crear Enlace"**

### Ver Leads

1. Ve a **Dashboard → Leads WhatsApp**
2. Filtra por:
   - Estado (Nuevo, Contactado, etc.)
   - Red Social
3. Click en **"Ver"** para ver la conversación

### Asignar Leads

1. Abre el detalle de un lead
2. Cambia el estado
3. Asigna a un agente
4. Click en **"Guardar"**

---

## 🔗 Rutas de URL

```
/whatsapp/webhook/              # Webhook para recibir mensajes de Meta
/dashboard/whatsapp/enlaces/<id>/           # Listar enlaces
/dashboard/whatsapp/enlaces/<id>/crear/     # Crear enlace
/dashboard/whatsapp/enlaces/<id>/borrar/    # Eliminar enlace
/dashboard/whatsapp/leads/                  # Listar leads
/dashboard/whatsapp/leads/<id>/             # Ver detalle de lead
```

---

## 🎯 Flujo de Funcionamiento

```
1. Admin crea enlace con tracking ID único
   ↓
2. Enlace se comparte en redes sociales (Facebook, Instagram, etc.)
   ↓
3. Cliente hace click en el enlace
   ↓
4. Se abre WhatsApp con el número registrado
   ↓
5. Se crea un Lead automático
   ↓
6. Sistema recibe mensajes vía webhook
   ↓
7. Conversaciones se guardan en la BD
   ↓
8. Agente ve el lead y lo gestiona
```

---

## 📊 Datos Guardados

### Por cada Lead:
- ✅ Número de teléfono
- ✅ Nombre (si lo registró)
- ✅ Email (si lo registró)
- ✅ Red social de origen (Facebook, Instagram, etc.)
- ✅ Propiedad asociada
- ✅ Estado actual
- ✅ Agente asignado
- ✅ Fecha de primer mensaje
- ✅ Fecha de último mensaje

### Por cada Conversación:
- ✅ Mensaje completo
- ✅ Tipo (entrante/saliente)
- ✅ Fecha y hora
- ✅ Usuario que envió (si es saliente)
- ✅ Multimedia (imágenes, videos, documentos)

---

## ⚙️ Configuración del Webhook en Meta

Cuando tengas las credenciales de Meta, debes configurar el webhook:

1. Ve a https://developers.facebook.com/
2. Selecciona tu App
3. **WhatsApp** → **Settings**
4. **Webhook Configuration**
5. Pon la URL: `https://tudominio.com/whatsapp/webhook/`
6. **Verify Token**: Pon el mismo que en `.env` (`WHATSAPP_VERIFY_TOKEN`)
7. **Eventos**: Selecciona `messages`
8. Guarda

Meta hará un GET a tu URL para verificarla. Si está correctamente configurada, el webhook empezará a recibir mensajes.

---

## 📝 Admin Django

En el panel de admin (`/admin/`):

- **PropertyWhatsAppLink**: Gestionar todos los enlaces
- **Lead**: Ver y editar leads
- **WhatsAppConversation**: Ver conversaciones (solo lectura)

---

## 🐛 Troubleshooting

### "Webhook verification failed"
- Verifica que el `WHATSAPP_VERIFY_TOKEN` sea correcto en `.env`
- Reinicia el servidor Django

### "Lead not found for phone X"
- El lead debe estar creado antes de que lleguen mensajes
- O el tracking ID debe coincidear con un enlace registrado

### "No hay mensajes"
- Verifica que el webhook esté correctamente configurado en Meta
- Revisa los logs de Django para ver si llegan POST requests

---

## 🔐 Seguridad

- ✅ Tokens guardados en variables de entorno (no en código)
- ✅ Webhook verifica token antes de procesar
- ✅ Solo usuarios autenticados pueden ver leads
- ✅ Encriptación de datos sensibles en DB

---

## 🚀 Próximos Pasos (Opcionales)

1. **Enviar mensajes**: Implementar envío de mensajes desde el sistema
2. **Notificaciones**: Alertas cuando llega nuevo lead
3. **Reportes**: Estadísticas de leads por propiedad/red social
4. **Automatización**: Respuestas automáticas
5. **Integración CRM**: Sincronizar con otros sistemas

---

## 📞 Soporte

Para consultas sobre la API de WhatsApp: https://developers.facebook.com/docs/whatsapp/cloud-api

