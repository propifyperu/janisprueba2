# 📱 Guía: Obtener Credenciales de Meta Developers

## ¿Qué datos necesitas?

Tu `.env` está casi listo, pero te faltan 2 datos críticos:

```
WHATSAPP_PHONE_NUMBER_ID=???????       ← NECESITAS ESTO
WHATSAPP_BUSINESS_ACCOUNT_ID=???????   ← NECESITAS ESTO
```

## Paso a Paso: Obtener los datos

### 1️⃣ Ir a Meta Developers
- Ve a: https://developers.facebook.com/
- Selecciona tu aplicación (ej: "JanisPropify CRM")

### 2️⃣ Obtener WHATSAPP_BUSINESS_ACCOUNT_ID
1. En el menú izquierdo, busca **"WhatsApp"**
2. Click en **"WhatsApp Business"**
3. Click en **"Settings"** o **"Configuración"**
4. Busca **"Business Account ID"** (es un número largo como `123456789012345`)
5. **Cópialo** y pégalo en `.env`

### 3️⃣ Obtener WHATSAPP_PHONE_NUMBER_ID
1. En el menú izquierdo de WhatsApp, click en **"Phone Numbers"**
2. Verás tu número registrado (ej: `+1 555 626 4749`)
3. Busca el campo **"Phone Number ID"** (es un número como `104850145989456`)
4. **Cópialo** y pégalo en `.env`

### 4️⃣ Configurar WHATSAPP_VERIFY_TOKEN (Opcional, pero recomendado)
- Este es un token que TÚ creas para verificar que los webhooks vienen de Meta
- Ejemplo: `webhook_token_super_seguro_12345`
- Lo usarás cuando configures los webhooks en Meta Developers

## Resultado final del `.env`

```dotenv
WHATSAPP_PHONE_NUMBER_ID=104850145989456
WHATSAPP_BUSINESS_ACCOUNT_ID=102334012345678
WHATSAPP_ACCESS_TOKEN=EAAMNc88VC1gBQE4gDv3joPZBccZAs...
WHATSAPP_VERIFY_TOKEN=webhook_token_super_seguro_12345
WHATSAPP_API_VERSION=v18.0
```

## Después de rellenar el `.env`

Ejecuta el script de prueba:

```bash
python send_test_message.py
```

Esto enviará un mensaje a: **+51 921 055 407** ✅

## ¿Qué pasa si algo falla?

### Error 401 (Unauthorized)
- ❌ El token expiró
- ✅ Solución: Genera un nuevo token en Meta Developers

### Error 400 (Bad Request)
- ❌ El número de teléfono está mal formateado
- ✅ Solución: Usa el formato: `+51921055407` (sin espacios)

### Error 403 (Forbidden)
- ❌ El System User no tiene los permisos correctos
- ✅ Solución: Revisa que tenga los permisos: `whatsapp_business_messaging`, `whatsapp_business_management`

## Configurar Webhooks (Para recibir mensajes)

Una vez que envíes mensajes exitosamente, configura los webhooks para recibir respuestas:

1. Ve a Meta Developers → Configuración → Webhooks
2. Click en "Editar Suscripciones"
3. Configura:
   - **URL de Callback**: `https://tunombre.com/whatsapp/webhook/` (o ngrok para local)
   - **Verify Token**: El mismo que pusiste en `.env`
   - **Eventos**: Selecciona `messages`

Tu aplicación Django está listo para recibir mensajes en `/whatsapp/webhook/`

---

## Próximos Pasos

✅ Rellenar el `.env` con los datos
✅ Ejecutar `python send_test_message.py`
✅ Verificar que el mensaje llega a `+51 921 055 407`
✅ Configurar webhooks en Meta Developers
✅ Probar recibir mensajes entrantes
