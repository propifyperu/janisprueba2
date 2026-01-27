# Guía de Configuración WhatsApp Business API

## Paso 1: Crear una Aplicación en Meta Developers

### 1.1 Ir a Meta Developers
1. Ve a https://developers.facebook.com/
2. Inicia sesión con tu cuenta de Facebook

### 1.2 Crear una nueva App
1. Click en "Crear aplicación" (Create App)
2. Elige **"Empresas"** como tipo de aplicación
3. Llena los datos:
   - **Nombre de la aplicación**: Tu CRM (ej: "JanisPropify CRM")
   - **Email de contacto**: Tu email
   - **Propósito**: Selecciona "Otros"

### 1.3 Agregar WhatsApp Business API
1. En el Dashboard, busca "WhatsApp"
2. Click en "Configurar"
3. Selecciona **"WhatsApp Business API"**

## Paso 2: Obtener Credenciales

### 2.1 Phone Number ID
1. Ve a WhatsApp Business → Phone Numbers
2. Registra un número de teléfono (puede ser el tuyo)
3. Copia el **Phone Number ID** (ej: `104850145989456`)

### 2.2 Business Account ID
1. Ve a WhatsApp Business → Settings
2. Copia el **Business Account ID** (ej: `102334012345678`)

### 2.3 Access Token
1. Ve a Settings → Users and Permissions → System Users
2. Crea un nuevo System User:
   - Nombre: "JanisPropify API"
   - Rol: Admin
3. Click en el usuario creado → Tokens → Generate Token
4. Selecciona tu aplicación
5. Permisos necesarios:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
6. Copia el **Access Token** (largo string que empieza con `EAAx...`)

## Paso 3: Configurar Webhook (Para recibir mensajes)

### 3.1 En Meta Developers
1. Ve a Configuración → Webhooks
2. Selecciona "WhatsApp Business Account"
3. Configura:
   - **URL de Callback**: `https://tudominio.com/api/whatsapp/webhook/`
   - **Verify Token**: Crea uno (ej: `my_secure_webhook_token_12345`)
   - **Eventos suscritos**: Selecciona `messages`, `message_template_status_update`

### 3.2 En tu Django
Tu endpoint debe responder a:
- **GET**: Verificar el token
- **POST**: Recibir mensajes entrantes

## Credenciales para guardaar en Django settings.py

```python
# WhatsApp Business API
WHATSAPP_PHONE_NUMBER_ID = "104850145989456"  # Copia del step 2.1
WHATSAPP_BUSINESS_ACCOUNT_ID = "102334012345678"  # Copia del step 2.2
WHATSAPP_ACCESS_TOKEN = "EAAx..."  # Copia del step 2.3 - GUARDA ESTO EN VARIABLES DE ENTORNO
WHATSAPP_VERIFY_TOKEN = "my_secure_webhook_token_12345"  # Step 3.1
WHATSAPP_API_VERSION = "v18.0"  # Versión actual de la API
```

## Cómo obtener números alternativos (hasta 2 teléfonos)

1. Ve a WhatsApp Business → Phone Numbers
2. Click en "Agregar número"
3. Selecciona tu Business Account
4. Sigue los pasos para registrar otro número
5. Ambos números tendrán IDs diferentes

Cada número puede ser usado para diferentes propiedades o redes sociales.

## Prueba la API (con Postman o curl)

### Enviar mensaje de prueba:
```bash
curl -X POST "https://graph.instagram.com/v18.0/PHONE_NUMBER_ID/messages" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": "1234567890",
    "type": "text",
    "text": {
      "preview_url": false,
      "body": "Hola! Este es un mensaje de prueba"
    }
  }'
```

## Variables de Entorno en Django (.env)

```
WHATSAPP_PHONE_NUMBER_ID=104850145989456
WHATSAPP_BUSINESS_ACCOUNT_ID=102334012345678
WHATSAPP_ACCESS_TOKEN=EAAx...
WHATSAPP_VERIFY_TOKEN=my_secure_webhook_token_12345
WHATSAPP_API_VERSION=v18.0
```

## Siguiente paso
Una vez tengas las credenciales, vamos a:
1. Crear modelos para enlaccs y leads
2. Implementar el webhook para recibir mensajes
3. Crear la interfaz para administrar enlaces por propiedad
