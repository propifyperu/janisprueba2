# Sistema CRM WhatsApp - JanisPropify

Guía completa para configurar y usar el sistema de CRM integrado con WhatsApp Business API.

## 📋 Tabla de Contenidos

1. [Configuración Inicial](#configuración-inicial)
2. [Credenciales de WhatsApp](#credenciales-de-whatsapp)
3. [Usar las Vistas](#usar-las-vistas)
4. [Webhook Setup](#webhook-setup)
5. [Solución de Problemas](#solución-de-problemas)

---

## 🚀 Configuración Inicial

### 1. Activar el Entorno Virtual

```powershell
cd e:\janisprueba2
.\venv\Scripts\Activate.ps1
```

### 2. Instalar Dependencias

Las dependencias ya están instaladas, pero si necesitas reinstalar:

```powershell
pip install -r requirements.txt
pip install python-dotenv requests
```

### 3. Configurar Variables de Entorno

Edita el archivo `.env` en la raíz del proyecto:

```
WHATSAPP_PHONE_NUMBER_ID=tu_numero_aqui
WHATSAPP_BUSINESS_ACCOUNT_ID=tu_id_aqui
WHATSAPP_ACCESS_TOKEN=tu_token_aqui
WHATSAPP_VERIFY_TOKEN=tu_verify_token_aqui
```

---

## 🔑 Credenciales de WhatsApp

### Dónde obtenerlas

1. **WHATSAPP_PHONE_NUMBER_ID**
   - Meta Developers → Tu App → WhatsApp → Phone Numbers
   - Copia el número largo (ej: `104850145989456`)

2. **WHATSAPP_BUSINESS_ACCOUNT_ID**
   - Meta Developers → Tu App → WhatsApp → Getting Started
   - Copia el Business Account ID

3. **WHATSAPP_ACCESS_TOKEN**
   - Settings → Users and Permissions → System Users
   - Click en tu usuario → Tokens → Generate Token
   - Copia el token completo (empieza con `EAAx...`)

4. **WHATSAPP_VERIFY_TOKEN**
   - Lo creas tú (cualquier string seguro)
   - Ej: `my_whatsapp_verify_token_abc123xyz789`

---

## 🖥️ Usar las Vistas

### Gestionar Enlaces de WhatsApp

```
URL: http://localhost:8000/dashboard/whatsapp/enlaces/<property_id>/
```

**Funcionalidades:**
- ✅ Listar enlaces de WhatsApp por propiedad
- ✅ Crear nuevo enlace con tracking automático
- ✅ Copiar enlace WhatsApp completo
- ✅ Eliminar enlaces

### Crear Nuevo Enlace

```
URL: http://localhost:8000/dashboard/whatsapp/enlaces/<property_id>/crear/
```

**Campos:**
- **Nombre del Enlace**: Nombre identificable (ej: "Facebook Ads - Villa Marina")
- **Red Social**: Selecciona (Facebook, Instagram, Google, Website, Otro)
- **Número WhatsApp**: El número de tu Business Account
- **Parámetros UTM** (opcional): Para rastreo en Google Analytics

**Resultado:**
- Se genera automáticamente un ID único para rastrear
- Se crea el enlace de WhatsApp con parámetros UTM
- Se guarda en la base de datos

### Gestionar Leads

```
URL: http://localhost:8000/dashboard/whatsapp/leads/
```

**Funcionalidades:**
- ✅ Ver todos los leads de WhatsApp
- ✅ Filtrar por estado, red social y propiedad
- ✅ Ver detalles del lead
- ✅ Ver conversación completa
- ✅ Cambiar estado del lead
- ✅ Asignar a un agente

### Ver Detalle del Lead

```
URL: http://localhost:8000/dashboard/whatsapp/leads/detalle/<lead_id>/
```

**Información disponible:**
- Teléfono, nombre, email
- Red social de origen
- Propiedad asociada
- Conversación completa (mensajes entrantes y salientes)
- Estado actual
- Fecha de creación

---

## 🔗 Webhook Setup

### Cómo funciona

1. **Meta envía mensajes a tu webhook**
   ```
   POST http://tudominio.com/whatsapp/webhook/
   ```

2. **Tu servidor responde**
   - Verifica el token
   - Procesa el mensaje
   - Crea un Lead si no existe
   - Guarda la conversación

### Configurar en Meta Developers

1. Ve a **Settings → Webhooks**
2. Selecciona **WhatsApp Business Account**
3. Configura:
   - **URL de Callback**: `https://tudominio.com/whatsapp/webhook/`
   - **Verify Token**: El que pusiste en `.env`
   - **Eventos**: `messages`, `message_template_status_update`

### Estructura del Webhook

El webhook recibe JSON como:

```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "changes": [
        {
          "field": "messages",
          "value": {
            "messages": [
              {
                "from": "51987654321",
                "id": "message_id_123",
                "timestamp": "1234567890",
                "type": "text",
                "text": {
                  "body": "Hola, estoy interesado en la propiedad"
                },
                "context": {
                  "referred_product": "tracking_id_xyz"
                }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

---

## 📊 Modelos de Base de Datos

### PropertyWhatsAppLink

Guarda los enlaces únicos por propiedad:

```python
- property (FK)
- social_network (char: facebook, instagram, google, website, other)
- whatsapp_phone_id (string)
- link_name (string)
- unique_identifier (string, único)
- utm_source, utm_medium, utm_campaign, utm_content
- is_active (boolean)
- created_by (FK User)
- created_at, updated_at
```

### Lead

Guarda los leads generados:

```python
- property (FK)
- whatsapp_link (FK, nullable)
- phone_number (string)
- name, email (nullable)
- social_network (char)
- status (new, contacted, qualified, negotiating, won, lost)
- assigned_to (FK User, nullable)
- first_message_at, last_message_at
- created_at, updated_at
```

### WhatsAppConversation

Guarda los mensajes:

```python
- lead (FK)
- property (FK)
- message_type (incoming, outgoing)
- sender_name (string)
- message_body (text)
- message_id (string, nullable)
- sent_by_user (FK User, nullable)
- media_url, media_type (nullable)
- created_at
```

---

## 🧪 Pruebas Manuales

### Con Postman

1. **Test del Webhook Verification**
   ```
   GET http://localhost:8000/whatsapp/webhook/?hub.verify_token=TU_TOKEN&hub.challenge=123456789
   ```
   Debe responder con el challenge

2. **Simular Mensaje Entrante**
   ```
   POST http://localhost:8000/whatsapp/webhook/
   Content-Type: application/json
   
   {
     "object": "whatsapp_business_account",
     "entry": [{
       "changes": [{
         "field": "messages",
         "value": {
           "messages": [{
             "from": "51987654321",
             "id": "test_123",
             "timestamp": "1234567890",
             "type": "text",
             "text": {"body": "Test message"},
             "context": {"referred_product": "tu_tracking_id"}
           }]
         }
       }]
     }]
   }
   ```

---

## 🐛 Solución de Problemas

### El webhook no recibe mensajes

1. Verifica que el `WHATSAPP_VERIFY_TOKEN` en `.env` es igual al de Meta
2. Asegúrate que la URL es accesible desde internet (no localhost)
3. Revisa los logs: `python manage.py shell`

### Los leads no se crean

1. Verifica que el `unique_identifier` en el mensaje coincida con el guardado
2. Revisa que la propiedad exista en la BD
3. Mira el archivo de logs para errores

### Los mensajes no se guardan

1. Verifica que el Lead existe
2. Revisa que `message_type` sea "incoming" o "outgoing"
3. Comprueba la estructura JSON del webhook

---

## 📱 Flujo Completo

```
1. Creas un enlace de WhatsApp en una propiedad
   ↓
2. Obtienes un ID único (ej: "abc12345")
   ↓
3. Lo pones en Facebook/Instagram/Google
   ↓
4. Un usuario hace click en el enlace
   ↓
5. Se abre WhatsApp con un mensaje preescrito
   ↓
6. El usuario envía el mensaje
   ↓
7. Meta te envía un webhook con el mensaje
   ↓
8. Tu servidor crea un Lead en la BD
   ↓
9. Se guarda la conversación
   ↓
10. Ves el lead en tu dashboard
    ↓
11. Lo asignas a un agente
    ↓
12. El agente responde desde WhatsApp Business
```

---

## 🔒 Seguridad

- Nunca commits el archivo `.env` a git
- Guarda los tokens en secretas de tu servidor
- Usa HTTPS en producción
- Verifica siempre el token del webhook

---

## 📝 Próximos Pasos

- [ ] Crear interfaz para responder mensajes desde el sistema
- [ ] Agregar sistema de notas y etiquetas en leads
- [ ] Integrar con CRM dashboard
- [ ] Agregar reportes y estadísticas
- [ ] Implementar auto-respuestas

---

## 📞 Soporte

Para más información sobre WhatsApp Business API:
https://developers.facebook.com/docs/whatsapp/cloud-api/

