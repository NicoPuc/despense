"""
Servidor Flask para integrar el Agente de Despensa con WhatsApp usando Meta WhatsApp Cloud API
"""

import os
import requests
import tempfile
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
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error enviando mensaje a WhatsApp: {e}")
        if hasattr(e, 'response') and e.response is not None:
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


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """
    Maneja los mensajes entrantes de WhatsApp.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400
        
        # WhatsApp envía notificaciones en 'entry'
        if "object" not in data or data["object"] != "whatsapp_business_account":
            return jsonify({"status": "ok"}), 200
        
        entries = data.get("entry", [])
        
        for entry in entries:
            changes = entry.get("changes", [])
            
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                
                for message in messages:
                    # Obtener información del mensaje
                    from_number = message.get("from")
                    message_id = message.get("id")
                    message_type = message.get("type")
                    
                    # Obtener o crear historial de conversación
                    if from_number not in chat_histories:
                        chat_histories[from_number] = []
                    
                    chat_history = chat_histories[from_number]
                    
                    # Procesar según el tipo de mensaje
                    if message_type == "text":
                        # Mensaje de texto
                        text_body = message.get("text", {}).get("body", "")
                        process_text_message(from_number, text_body, chat_history)
                    
                    elif message_type == "audio" or message_type == "voice":
                        # Mensaje de audio
                        audio_data = message.get("audio") or message.get("voice")
                        if audio_data:
                            media_id = audio_data.get("id")
                            mime_type = audio_data.get("mime_type", "audio/ogg")
                            process_audio_message(from_number, media_id, mime_type, chat_history)
                    
                    elif message_type == "image":
                        # Mensaje de imagen
                        image_data = message.get("image", {})
                        if image_data:
                            media_id = image_data.get("id")
                            mime_type = image_data.get("mime_type", "image/jpeg")
                            process_image_message(from_number, media_id, mime_type, chat_history)
                    
                    else:
                        # Tipo de mensaje no soportado
                        send_whatsapp_message(
                            from_number,
                            "Lo siento, solo puedo procesar mensajes de texto, audio e imágenes."
                        )
        
        return jsonify({"status": "ok"}), 200
    
    except Exception as e:
        print(f"❌ Error procesando webhook: {e}")
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
    print("\n💡 Para desarrollo local, usa ngrok:")
    print(f"   ngrok http {PORT}")
    print("   Luego configura el webhook en Meta con: https://tu-url-ngrok.ngrok.io/webhook")
    print("\n⚠️  Si el puerto está en uso, cambia FLASK_PORT en .env o desactiva AirPlay Receiver")
    
    # Ejecutar servidor
    app.run(host="0.0.0.0", port=PORT, debug=True)

