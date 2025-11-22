"""
Servidor Flask para integrar el Agente de Despensa con WhatsApp usando Meta WhatsApp Cloud API
"""

import os
import requests
import tempfile
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from despensa_agent import run_agent
from langchain_core.messages import HumanMessage, AIMessage

# Cargar variables de entorno
load_dotenv()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)

# Configuración de WhatsApp Cloud API
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "mi_token_secreto")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v21.0")
WHATSAPP_API_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

# Almacenar historial de conversación por número de teléfono
chat_histories = {}


def send_whatsapp_message(to: str, message: str):
    """
    Envía un mensaje de texto a través de WhatsApp Cloud API.
    
    Args:
        to: Número de teléfono del destinatario (formato: 1234567890)
        message: Mensaje de texto a enviar
    """
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        print("⚠️  Error: WHATSAPP_TOKEN o WHATSAPP_PHONE_NUMBER_ID no configurados")
        return False
    
    # Formatear número de teléfono (debe incluir código de país sin +)
    phone_number = to.replace("+", "").replace(" ", "").replace("-", "")
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }
    
    try:
        print(f"\n📤 Enviando mensaje a WhatsApp:")
        print(f"   Para: {phone_number}")
        print(f"   URL: {WHATSAPP_API_URL}")
        print(f"   Mensaje: {message[:50]}..." if len(message) > 50 else f"   Mensaje: {message}")
        
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Mensaje enviado correctamente")
            print(f"   Respuesta: {response.json()}")
            return True
        else:
            print(f"❌ Error en respuesta: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            response.raise_for_status()
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error enviando mensaje a WhatsApp: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status Code: {e.response.status_code}")
            print(f"   Respuesta: {e.response.text}")
        return False


def download_media(media_id: str, mime_type: str) -> str:
    """
    Descarga un archivo multimedia desde WhatsApp Cloud API.
    
    Args:
        media_id: ID del archivo multimedia en WhatsApp
        mime_type: Tipo MIME del archivo (ej: "audio/ogg", "image/jpeg")
    
    Returns:
        Ruta al archivo descargado temporalmente
    """
    if not WHATSAPP_TOKEN:
        return None
    
    # Obtener URL del archivo
    media_url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    
    try:
        # Obtener URL de descarga
        response = requests.get(media_url, headers=headers)
        response.raise_for_status()
        media_data = response.json()
        download_url = media_data.get("url")
        
        if not download_url:
            return None
        
        # Descargar el archivo
        download_response = requests.get(download_url, headers=headers)
        download_response.raise_for_status()
        
        # Determinar extensión del archivo
        extension_map = {
            "audio/ogg": ".ogg",
            "audio/mpeg": ".mp3",
            "audio/mp4": ".m4a",
            "audio/wav": ".wav",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp"
        }
        extension = extension_map.get(mime_type, ".tmp")
        
        # Guardar en archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
            tmp_file.write(download_response.content)
            return tmp_file.name
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error descargando archivo multimedia: {e}")
        return None


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Verifica el webhook de WhatsApp (requerido por Meta).
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        print("✅ Webhook verificado correctamente")
        return challenge, 200
    else:
        print("❌ Verificación de webhook fallida")
        return "Forbidden", 403


@app.route("/debug", methods=["GET", "POST"])
def debug_endpoint():
    """
    Endpoint de debug para ver los datos recibidos (similar a n8n).
    """
    if request.method == "GET":
        return jsonify({
            "status": "debug_endpoint_active",
            "message": "Envía un POST con datos para verlos aquí",
            "webhook_url": "/webhook"
        })
    
    # Mostrar datos recibidos de forma legible
    data = request.get_json() if request.is_json else request.form.to_dict()
    headers = dict(request.headers)
    
    debug_info = {
        "method": request.method,
        "headers": headers,
        "data": data,
        "raw_data": request.get_data(as_text=True) if not request.is_json else None
    }
    
    print("\n" + "="*70)
    print("🔍 DEBUG ENDPOINT - Datos recibidos")
    print("="*70)
    print(json.dumps(debug_info, indent=2, ensure_ascii=False))
    print("="*70 + "\n")
    
    return jsonify(debug_info)


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """
    Maneja los mensajes entrantes de WhatsApp.
    """
    try:
        data = request.get_json()
        
        # Log detallado para debugging (similar a n8n)
        print("\n" + "="*70)
        print("📥 WEBHOOK RECIBIDO")
        print("="*70)
        print("📦 Datos completos recibidos:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("="*70 + "\n")
        
        if not data:
            print("⚠️  No se recibieron datos")
            return jsonify({"status": "error", "message": "No data received"}), 400
        
        # WhatsApp envía notificaciones en 'entry'
        if "object" not in data:
            print(f"⚠️  Objeto no encontrado en datos. Keys: {data.keys()}")
            return jsonify({"status": "ok"}), 200
        
        if data["object"] != "whatsapp_business_account":
            print(f"⚠️  Objeto no es whatsapp_business_account: {data.get('object')}")
            return jsonify({"status": "ok"}), 200
        
        entries = data.get("entry", [])
        print(f"📋 Entradas encontradas: {len(entries)}")
        
        if not entries:
            print("⚠️  No hay entradas en el webhook")
            print("💡 Esto puede ser normal si es solo una notificación de estado")
            return jsonify({"status": "ok"}), 200
        
        for entry in entries:
            changes = entry.get("changes", [])
            print(f"🔄 Cambios encontrados: {len(changes)}")
            
            for change in changes:
                value = change.get("value", {})
                print(f"\n📊 Estructura del cambio:")
                print(f"   Keys disponibles: {list(value.keys())}")
                print(f"   Cambio completo: {json.dumps(change, indent=2, ensure_ascii=False)}")
                
                # Verificar si hay mensajes
                messages = value.get("messages", [])
                print(f"\n💬 Mensajes encontrados: {len(messages)}")
                
                if not messages:
                    # Puede ser una notificación de estado, no un mensaje nuevo
                    statuses = value.get("statuses", [])
                    if statuses:
                        print(f"📊 Notificación de estado recibida: {statuses}")
                    continue
                
                for message in messages:
                    # Obtener información del mensaje
                    from_number = message.get("from")
                    message_id = message.get("id")
                    message_type = message.get("type")
                    
                    print(f"\n📨 Procesando mensaje:")
                    print(f"   De: {from_number}")
                    print(f"   ID: {message_id}")
                    print(f"   Tipo: {message_type}")
                    
                    if not from_number:
                        print("⚠️  No se encontró número de teléfono en el mensaje")
                        continue
                    
                    # Obtener o crear historial de conversación
                    if from_number not in chat_histories:
                        chat_histories[from_number] = []
                        print(f"✅ Nuevo historial creado para {from_number}")
                    
                    chat_history = chat_histories[from_number]
                    
                    # Procesar según el tipo de mensaje
                    if message_type == "text":
                        # Mensaje de texto
                        text_body = message.get("text", {}).get("body", "")
                        print(f"📝 Texto recibido: {text_body}")
                        process_text_message(from_number, text_body, chat_history)
                    
                    elif message_type == "audio" or message_type == "voice":
                        # Mensaje de audio
                        print("🎤 Procesando mensaje de audio...")
                        audio_data = message.get("audio") or message.get("voice")
                        if audio_data:
                            media_id = audio_data.get("id")
                            mime_type = audio_data.get("mime_type", "audio/ogg")
                            process_audio_message(from_number, media_id, mime_type, chat_history)
                        else:
                            print("⚠️  No se encontraron datos de audio")
                    
                    elif message_type == "image":
                        # Mensaje de imagen
                        print("🖼️  Procesando mensaje de imagen...")
                        image_data = message.get("image", {})
                        if image_data:
                            media_id = image_data.get("id")
                            mime_type = image_data.get("mime_type", "image/jpeg")
                            process_image_message(from_number, media_id, mime_type, chat_history)
                        else:
                            print("⚠️  No se encontraron datos de imagen")
                    
                    else:
                        # Tipo de mensaje no soportado
                        print(f"⚠️  Tipo de mensaje no soportado: {message_type}")
                        send_whatsapp_message(
                            from_number,
                            "Lo siento, solo puedo procesar mensajes de texto, audio e imágenes."
                        )
        
        print("\n✅ Webhook procesado correctamente\n")
        return jsonify({"status": "ok"}), 200
    
    except Exception as e:
        print(f"\n❌ Error procesando webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


def process_text_message(from_number: str, text: str, chat_history: list):
    """
    Procesa un mensaje de texto.
    """
    try:
        print(f"📨 Mensaje de texto recibido de {from_number}: {text}")
        
        # Ejecutar el agente
        response = run_agent(text, chat_history, None)
        
        # Enviar respuesta
        send_whatsapp_message(from_number, response)
        
        # Actualizar historial
        chat_history.append(HumanMessage(content=text))
        chat_history.append(AIMessage(content=response))
        
    except Exception as e:
        print(f"❌ Error procesando mensaje de texto: {e}")
        send_whatsapp_message(
            from_number,
            "Lo siento, hubo un error procesando tu mensaje. Por favor, intenta de nuevo."
        )


def process_audio_message(from_number: str, media_id: str, mime_type: str, chat_history: list):
    """
    Procesa un mensaje de audio.
    """
    try:
        print(f"🎤 Mensaje de audio recibido de {from_number}")
        
        # Descargar archivo de audio
        audio_path = download_media(media_id, mime_type)
        
        if not audio_path:
            send_whatsapp_message(
                from_number,
                "Lo siento, no pude descargar el archivo de audio. Por favor, intenta de nuevo."
            )
            return
        
        # Ejecutar el agente con el archivo de audio
        response = run_agent("", chat_history, audio_path)
        
        # Enviar respuesta
        send_whatsapp_message(from_number, response)
        
        # Actualizar historial
        chat_history.append(HumanMessage(content=f"Archivo audio: {audio_path}"))
        chat_history.append(AIMessage(content=response))
        
        # Limpiar archivo temporal
        try:
            os.remove(audio_path)
        except:
            pass
    
    except Exception as e:
        print(f"❌ Error procesando mensaje de audio: {e}")
        import traceback
        traceback.print_exc()
        send_whatsapp_message(
            from_number,
            "Lo siento, hubo un error procesando tu audio. Por favor, intenta de nuevo."
        )


def process_image_message(from_number: str, media_id: str, mime_type: str, chat_history: list):
    """
    Procesa un mensaje de imagen.
    """
    try:
        print(f"🖼️  Mensaje de imagen recibido de {from_number}")
        
        # Descargar archivo de imagen
        image_path = download_media(media_id, mime_type)
        
        if not image_path:
            send_whatsapp_message(
                from_number,
                "Lo siento, no pude descargar la imagen. Por favor, intenta de nuevo."
            )
            return
        
        # Ejecutar el agente con la imagen
        response = run_agent("", chat_history, image_path)
        
        # Enviar respuesta
        send_whatsapp_message(from_number, response)
        
        # Actualizar historial
        chat_history.append(HumanMessage(content=f"Archivo imagen: {image_path}"))
        chat_history.append(AIMessage(content=response))
        
        # Limpiar archivo temporal
        try:
            os.remove(image_path)
        except:
            pass
    
    except Exception as e:
        print(f"❌ Error procesando mensaje de imagen: {e}")
        import traceback
        traceback.print_exc()
        send_whatsapp_message(
            from_number,
            "Lo siento, hubo un error procesando tu imagen. Por favor, intenta de nuevo."
        )


if __name__ == "__main__":
    # Verificar configuración
    if not WHATSAPP_TOKEN:
        print("⚠️  Advertencia: WHATSAPP_TOKEN no configurado")
    if not WHATSAPP_PHONE_NUMBER_ID:
        print("⚠️  Advertencia: WHATSAPP_PHONE_NUMBER_ID no configurado")
    
    # Puerto configurable (por defecto 5001 para evitar conflicto con AirPlay en macOS)
    PORT = int(os.getenv("FLASK_PORT", 5001))
    
    print("🚀 Iniciando servidor de WhatsApp...")
    print(f"📡 Webhook URL: https://tu-dominio.com/webhook")
    print(f"🔐 Verify Token: {WHATSAPP_VERIFY_TOKEN}")
    print(f"🌐 Puerto: {PORT}")
    print(f"\n🔍 Endpoints disponibles:")
    print(f"   - POST /webhook (webhook principal de WhatsApp)")
    print(f"   - GET/POST /debug (endpoint de debug para ver datos)")
    print(f"\n💡 Para desarrollo local, usa ngrok:")
    print(f"   ngrok http {PORT}")
    print("   Luego configura el webhook en Meta con: https://tu-url-ngrok.ngrok.io/webhook")
    print("\n⚠️  Si el puerto está en uso, cambia FLASK_PORT en .env o desactiva AirPlay Receiver")
    
    # Verificar credenciales
    print(f"\n🔑 Verificación de credenciales:")
    print(f"   ✅ WHATSAPP_VERIFY_TOKEN: {'Configurado' if WHATSAPP_VERIFY_TOKEN else '❌ NO CONFIGURADO'}")
    print(f"   {'✅' if WHATSAPP_TOKEN else '❌'} WHATSAPP_TOKEN: {'Configurado' if WHATSAPP_TOKEN else 'NO CONFIGURADO (necesario para enviar mensajes)'}")
    print(f"   {'✅' if WHATSAPP_PHONE_NUMBER_ID else '❌'} WHATSAPP_PHONE_NUMBER_ID: {'Configurado' if WHATSAPP_PHONE_NUMBER_ID else 'NO CONFIGURADO (necesario para enviar mensajes)'}")
    print(f"   {'✅' if os.getenv('OPENAI_API_KEY') else '❌'} OPENAI_API_KEY: {'Configurado' if os.getenv('OPENAI_API_KEY') else 'NO CONFIGURADO (necesario para el agente)'}")
    
    # Ejecutar servidor
    app.run(host="0.0.0.0", port=PORT, debug=True)

