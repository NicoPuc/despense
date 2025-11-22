# 📱 Guía de Configuración de WhatsApp

Esta guía te ayudará a conectar el Agente de Despensa con WhatsApp usando la API de Meta (WhatsApp Cloud API).

## 📋 Requisitos Previos

1. **Cuenta de Meta for Developers**
   - Regístrate en [Meta for Developers](https://developers.facebook.com/)
   - Verifica tu cuenta

2. **Aplicación de Meta creada**
   - Crea una aplicación en [Meta App Dashboard](https://developers.facebook.com/apps/)
   - Tipo: **Negocios**

3. **WhatsApp Business API configurada**
   - Agrega el producto "WhatsApp" a tu aplicación
   - Configura el número de teléfono de prueba o producción

## 🔧 Paso 1: Obtener Credenciales de WhatsApp

### 1.1. Token de Acceso

1. Ve a tu aplicación en [Meta App Dashboard](https://developers.facebook.com/apps/)
2. Selecciona tu aplicación
3. Ve a **WhatsApp** → **Configuración de API**
4. En la sección **Token de acceso temporal**, copia el token
   - ⚠️ **Nota**: Este token es temporal (24 horas). Para producción, necesitarás un token permanente.

### 1.2. ID del Número de Teléfono

1. En la misma página de configuración
2. Busca **ID del número de teléfono** (Phone Number ID)
3. Copia este ID

### 1.3. Token de Verificación

1. Crea un token de verificación personalizado (puede ser cualquier string)
2. Este token se usará para verificar el webhook

## 🔐 Paso 2: Configurar Variables de Entorno

Agrega las siguientes variables a tu archivo `.env`:

```bash
# WhatsApp Cloud API
WHATSAPP_TOKEN=tu_token_de_acceso_aqui
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id_aqui
WHATSAPP_VERIFY_TOKEN=tu_token_de_verificacion_personalizado
WHATSAPP_API_VERSION=v21.0

# OpenAI (ya deberías tener esto)
OPENAI_API_KEY=tu_openai_api_key_aqui
```

**Ejemplo:**
```bash
WHATSAPP_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_VERIFY_TOKEN=mi_token_secreto_123
WHATSAPP_API_VERSION=v21.0
```

## 🌐 Paso 3: Configurar Webhook

### 3.1. Para Desarrollo Local (usando ngrok)

1. **Instalar ngrok:**
   ```bash
   # macOS
   brew install ngrok
   
   # O descarga desde https://ngrok.com/download
   ```

2. **Iniciar el servidor Flask:**
   ```bash
   cd despense-agent
   source ../.venv/bin/activate  # O la ruta a tu venv
   python whatsapp_server.py
   ```
   
   ⚠️ **Nota**: Si el puerto 5000 está ocupado (común en macOS por AirPlay), el servidor usará el puerto 5001 por defecto.
   Puedes configurar un puerto personalizado agregando `FLASK_PORT=8080` en tu `.env`.

3. **En otra terminal, iniciar ngrok:**
   ```bash
   # Si el servidor está en puerto 5001 (por defecto si 5000 está ocupado)
   ngrok http 5001
   
   # O si configuraste otro puerto en .env
   ngrok http 8080  # ejemplo
   ```
   
   💡 **Tip**: Verifica en qué puerto está corriendo el servidor Flask mirando el mensaje al iniciarlo.

4. **Copiar la URL de ngrok:**
   - Deberías ver algo como: `https://abc123.ngrok.io`
   - Copia esta URL completa

### 3.2. Configurar Webhook en Meta

1. Ve a tu aplicación en [Meta App Dashboard](https://developers.facebook.com/apps/)
2. Ve a **WhatsApp** → **Configuración**
3. En la sección **Webhook**, haz clic en **Configurar webhooks**
4. Ingresa:
   - **URL de devolución de llamada**: `https://tu-url-ngrok.ngrok.io/webhook`
   - **Token de verificación**: El mismo que configuraste en `.env` (`WHATSAPP_VERIFY_TOKEN`)
5. Haz clic en **Verificar y guardar**
6. Suscríbete a los campos:
   - ✅ `messages`
   - ✅ `message_status`

## 🚀 Paso 4: Probar la Integración

### 4.1. Enviar Mensaje de Prueba

1. Abre WhatsApp en tu teléfono
2. Envía un mensaje al número de teléfono configurado en Meta
3. Deberías ver en la consola del servidor:
   ```
   📨 Mensaje de texto recibido de 1234567890: ¿Qué me falta?
   ```
4. El bot debería responder automáticamente

### 4.2. Probar con Audio

1. Envía un mensaje de voz a través de WhatsApp
2. El bot debería transcribirlo y procesarlo

### 4.3. Probar con Imagen

1. Envía una imagen de productos/despensa
2. El bot debería analizarla y actualizar el inventario

## 📦 Paso 5: Instalar Dependencias

Si aún no has instalado las dependencias:

```bash
cd despense-agent
source ../.venv/bin/activate
pip install -r requirements.txt
```

## 🔍 Solución de Problemas

### Error: "WHATSAPP_TOKEN no configurado"

- Verifica que el archivo `.env` esté en el directorio correcto
- Verifica que las variables estén escritas correctamente (sin espacios)
- Reinicia el servidor después de cambiar `.env`

### Error: "Webhook verification failed"

- Verifica que el `WHATSAPP_VERIFY_TOKEN` en `.env` coincida con el configurado en Meta
- Asegúrate de que ngrok esté corriendo y la URL sea accesible
- Verifica que el servidor Flask esté escuchando en el puerto 5000

### Error: "No puedo enviar mensajes"

- Verifica que el token de acceso no haya expirado (tokens temporales duran 24 horas)
- Para producción, necesitarás un token permanente
- Verifica que el `WHATSAPP_PHONE_NUMBER_ID` sea correcto

### El bot no responde

- Verifica los logs del servidor para ver errores
- Asegúrate de que `OPENAI_API_KEY` esté configurada
- Verifica que el webhook esté correctamente suscrito a los eventos

## 🌍 Paso 6: Desplegar a Producción

### Opciones de Despliegue:

1. **Heroku:**
   ```bash
   heroku create tu-app
   git push heroku main
   heroku config:set WHATSAPP_TOKEN=tu_token
   # ... otras variables
   ```

2. **Railway:**
   - Conecta tu repositorio
   - Configura las variables de entorno
   - Deploy automático

3. **AWS/GCP/Azure:**
   - Usa servicios como EC2, Cloud Run, o App Service
   - Configura las variables de entorno
   - Usa un dominio propio para el webhook

### Para Producción:

1. **Obtener Token Permanente:**
   - Necesitarás un token de acceso permanente
   - Esto requiere aprobación de Meta para producción
   - Consulta la [documentación oficial](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)

2. **Configurar Dominio:**
   - Usa un dominio propio (no ngrok)
   - Configura SSL/HTTPS (requerido por Meta)
   - Actualiza la URL del webhook en Meta

3. **Monitoreo:**
   - Configura logs y monitoreo
   - Implementa manejo de errores robusto
   - Considera usar una base de datos para persistir el historial

## 📚 Recursos Adicionales

- [Documentación oficial de WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Guía de webhooks de Meta](https://developers.facebook.com/docs/graph-api/webhooks)
- [Ejemplos de código](https://github.com/facebook/WhatsApp-Business-API-Setup-Scripts)

## ✅ Checklist de Configuración

- [ ] Cuenta de Meta for Developers creada
- [ ] Aplicación de Meta creada
- [ ] WhatsApp Business API agregada a la aplicación
- [ ] Token de acceso obtenido
- [ ] Phone Number ID obtenido
- [ ] Variables de entorno configuradas en `.env`
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Servidor Flask iniciado
- [ ] ngrok configurado (para desarrollo)
- [ ] Webhook configurado en Meta
- [ ] Webhook verificado correctamente
- [ ] Mensaje de prueba enviado y recibido
- [ ] Bot responde correctamente

## 🎉 ¡Listo!

Una vez completados todos los pasos, tu bot de WhatsApp debería estar funcionando. Puedes enviar mensajes de texto, audio e imágenes, y el agente los procesará automáticamente.

