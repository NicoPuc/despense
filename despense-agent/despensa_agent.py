"""
Agente de Despensa usando LangGraph
Simula la gestión de inventario de una despensa mediante un agente conversacional.
Soporta entradas multimodales: texto, audio e imágenes.
"""

import os
import base64
from typing import TypedDict, Annotated, Literal, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from openai import OpenAI

# Cargar variables de entorno
# Buscar .env en el directorio actual y en el directorio padre
load_dotenv()  # Busca en el directorio actual (despense-agent/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))  # Busca en el directorio padre

# Inicializar cliente de OpenAI para APIs multimodales
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================================================
# BASE DE DATOS SIMULADA (Diccionario global)
# ============================================================================
DESPENSA_DB = {
    "leche": "BAJO",
    "huevos": "ALTO",
    "pan": "MEDIO",
    "azúcar": "ALTO",
    "aceite": "MEDIO",
    "arroz": "BAJO",
    "fideos": "ALTO",
}


# ============================================================================
# ESTADO DEL GRAFO
# ============================================================================
class AgentState(TypedDict):
    """Estado del agente que mantiene el historial de conversación, input del usuario y archivos multimedia."""
    messages: Annotated[list[BaseMessage], add_messages]
    user_input: str
    media_file_path: Optional[str]  # Ruta del archivo multimedia (audio o imagen)


# ============================================================================
# HERRAMIENTAS (TOOLS)
# ============================================================================
@tool
def consultar_despensa(item_name: str) -> str:
    """
    Consulta el estado actual de un ítem en la despensa.
    
    Args:
        item_name: Nombre del ítem a consultar (ej: "leche", "huevos")
    
    Returns:
        Estado del ítem: "BAJO", "MEDIO", "ALTO" o "NO_ENCONTRADO"
    """
    item_name_lower = item_name.lower().strip()
    estado = DESPENSA_DB.get(item_name_lower, "NO_ENCONTRADO")
    
    if estado == "NO_ENCONTRADO":
        return f"El ítem '{item_name}' no está registrado en la despensa."
    
    return f"El estado de '{item_name}' es: {estado}"


@tool
def actualizar_despensa(item_name: str, new_status: str) -> str:
    """
    Actualiza el estado de un ítem en la despensa.
    
    Args:
        item_name: Nombre del ítem a actualizar
        new_status: Nuevo estado ("BAJO", "MEDIO", "ALTO")
    
    Returns:
        Mensaje de confirmación de la actualización
    """
    item_name_lower = item_name.lower().strip()
    new_status_upper = new_status.upper().strip()
    
    # Validar que el estado sea válido
    estados_validos = ["BAJO", "MEDIO", "ALTO"]
    if new_status_upper not in estados_validos:
        return f"Error: El estado '{new_status}' no es válido. Use: BAJO, MEDIO o ALTO"
    
    # Actualizar o crear el ítem
    DESPENSA_DB[item_name_lower] = new_status_upper
    
    return f"✅ Actualizado: '{item_name}' ahora tiene estado '{new_status_upper}'"


# ============================================================================
# HERRAMIENTAS MULTIMODALES (TOOLS)
# ============================================================================
@tool
def transcribir_audio(audio_file_path: str) -> str:
    """
    Transcribe un archivo de audio a texto usando OpenAI Whisper API.
    
    Args:
        audio_file_path: Ruta al archivo de audio (ej: "audio.wav", "mensaje.mp3")
    
    Returns:
        Texto transcrito que indica lo que el usuario dijo
    
    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el formato de archivo no es soportado
    """
    # Validar que el archivo existe
    if not os.path.exists(audio_file_path):
        return f"Error: El archivo de audio '{audio_file_path}' no existe."
    
    if not os.path.isfile(audio_file_path):
        return f"Error: '{audio_file_path}' no es un archivo válido."
    
    # Validar formato de archivo
    valid_extensions = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
    file_ext = os.path.splitext(audio_file_path)[1].lower()
    
    if file_ext not in valid_extensions:
        return f"Error: Formato de archivo '{file_ext}' no soportado. Formatos válidos: {', '.join(valid_extensions)}"
    
    # Validar tamaño del archivo (máximo 25 MB para Whisper)
    file_size = os.path.getsize(audio_file_path) / (1024 * 1024)  # MB
    if file_size > 25:
        return f"Error: El archivo es demasiado grande ({file_size:.2f} MB). El máximo es 25 MB."
    
    try:
        # Transcribir usando OpenAI Whisper API
        with open(audio_file_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="es"  # Especificar español para mejor precisión
            )
        
        # Retornar el texto transcrito en un formato estructurado
        texto_transcrito = transcript.text.strip()
        return f"El usuario dijo: '{texto_transcrito}'"
    
    except Exception as e:
        # Manejo de errores de la API
        error_msg = str(e)
        if "rate_limit" in error_msg.lower():
            return "Error: Límite de tasa excedido. Por favor, intenta de nuevo en unos momentos."
        elif "invalid_file" in error_msg.lower():
            return f"Error: El archivo '{audio_file_path}' no es un archivo de audio válido."
        else:
            return f"Error al transcribir audio: {error_msg}"


@tool
def procesar_imagen(image_file_path: str) -> str:
    """
    Procesa una imagen de la despensa usando OpenAI Vision API y extrae información sobre los productos.
    
    Args:
        image_file_path: Ruta al archivo de imagen (ej: "despensa.jpg", "compra.png")
    
    Returns:
        Texto estructurado con la información extraída de la imagen para actualizar el inventario
    
    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el formato de archivo no es soportado
    """
    # Validar que el archivo existe
    if not os.path.exists(image_file_path):
        return f"Error: El archivo de imagen '{image_file_path}' no existe."
    
    if not os.path.isfile(image_file_path):
        return f"Error: '{image_file_path}' no es un archivo válido."
    
    # Validar formato de archivo
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_ext = os.path.splitext(image_file_path)[1].lower()
    
    if file_ext not in valid_extensions:
        return f"Error: Formato de archivo '{file_ext}' no soportado. Formatos válidos: {', '.join(valid_extensions)}"
    
    # Validar tamaño del archivo (máximo 20 MB para Vision API)
    file_size = os.path.getsize(image_file_path) / (1024 * 1024)  # MB
    if file_size > 20:
        return f"Error: El archivo es demasiado grande ({file_size:.2f} MB). El máximo es 20 MB."
    
    try:
        # Leer y codificar la imagen en base64
        with open(image_file_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Determinar el tipo MIME
        mime_type = f"image/{file_ext[1:]}"  # jpg -> image/jpeg
        if file_ext == '.jpg':
            mime_type = 'image/jpeg'
        
        # Usar OpenAI Vision API para analizar la imagen
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Usar gpt-4o-mini para costos más bajos
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analiza esta imagen de una despensa, compra de supermercado, o productos alimenticios.

Identifica los productos visibles en la imagen y genera un mensaje estructurado para actualizar el inventario.

Formato de respuesta:
- Si hay un solo producto: "Compra de [producto] [cantidad si es visible], establecer a ALTO"
- Si hay múltiples productos: Lista cada uno en una línea separada con el mismo formato

Ejemplos:
- "Compra de 1kg de arroz, establecer a ALTO"
- "Compra de pan, establecer a ALTO"
- "Compra de leche, establecer a ALTO"
- "Compra de huevos, establecer a ALTO"

Si no puedes identificar productos claramente, indica: "No se pudieron identificar productos claramente en la imagen"."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        # Extraer el resultado del análisis
        analisis = response.choices[0].message.content.strip()
        return analisis
    
    except Exception as e:
        # Manejo de errores de la API
        error_msg = str(e)
        if "rate_limit" in error_msg.lower():
            return "Error: Límite de tasa excedido. Por favor, intenta de nuevo en unos momentos."
        elif "invalid_image" in error_msg.lower() or "invalid_file" in error_msg.lower():
            return f"Error: El archivo '{image_file_path}' no es una imagen válida."
        else:
            return f"Error al procesar imagen: {error_msg}"


# ============================================================================
# NODO DEL AGENTE (Razonamiento)
# ============================================================================
def agent_node(state: AgentState) -> AgentState:
    """
    Nodo del agente que usa el LLM para razonar sobre la intención del usuario
    y decidir qué herramienta usar. Maneja entradas de texto, audio e imágenes.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Obtener los mensajes del estado y el archivo multimedia
    messages = state["messages"]
    media_file_path = state.get("media_file_path")
    
    # Determinar qué herramientas están disponibles según el contexto
    all_tools = [consultar_despensa, actualizar_despensa]
    
    # Si hay un archivo multimedia, agregar las herramientas multimodales
    if media_file_path:
        # Determinar el tipo de archivo por extensión
        file_ext = os.path.splitext(media_file_path)[1].lower()
        if file_ext in ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.aac']:
            # Es un archivo de audio
            all_tools = [transcribir_audio, consultar_despensa, actualizar_despensa]
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            # Es una imagen
            all_tools = [procesar_imagen, consultar_despensa, actualizar_despensa]
    
    # Preparar el prompt del sistema
    system_prompt = """Eres un asistente de despensa inteligente. Tu trabajo es entender la intención del usuario.

FLUJO DE TRABAJO:
1. Si el usuario envía un archivo multimedia (audio o imagen):
   - PRIMERO debes usar 'transcribir_audio' para archivos de audio (.wav, .mp3, etc.)
   - O 'procesar_imagen' para archivos de imagen (.jpg, .png, etc.)
   - Luego, usa el resultado de estas herramientas para decidir la siguiente acción

2. Si el usuario está CONSULTANDO el inventario (ej: "¿Qué me falta?", "¿Tengo leche?", "¿Qué tengo?"), 
   debes usar la herramienta 'consultar_despensa'.

3. Si el usuario está ACTUALIZANDO el inventario (ej: "Compré leche", "Agregué huevos", "Ya no tengo pan"),
   debes usar la herramienta 'actualizar_despensa' con el estado apropiado:
   - "Compré/Agregué" → estado "ALTO"
   - "Se acabó/No tengo" → estado "BAJO"
   - "Tengo poco" → estado "MEDIO"

IMPORTANTE: 
- Si hay un media_file_path en el estado, SIEMPRE procesa primero el archivo multimedia
- Usa el texto resultante de la transcripción/procesamiento como input para decidir la acción
- Responde de manera natural y amigable. Si no estás seguro de la intención, pregunta al usuario."""
    
    # Crear mensajes para el LLM con las herramientas disponibles
    llm_with_tools = llm.bind_tools(all_tools)
    
    # Si hay un archivo multimedia y aún no se ha procesado, agregar contexto
    if media_file_path and not any("transcribir_audio" in str(msg) or "procesar_imagen" in str(msg) for msg in messages):
        file_ext = os.path.splitext(media_file_path)[1].lower()
        if file_ext in ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.aac']:
            # Agregar contexto sobre el archivo de audio
            audio_context = f"El usuario ha enviado un archivo de audio: {media_file_path}. Debes transcribirlo primero usando 'transcribir_audio'."
            if messages:
                messages = [HumanMessage(content=audio_context)] + list(messages)
            else:
                messages = [HumanMessage(content=audio_context)]
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            # Agregar contexto sobre la imagen
            image_context = f"El usuario ha enviado una imagen: {media_file_path}. Debes procesarla primero usando 'procesar_imagen'."
            if messages:
                messages = [HumanMessage(content=image_context)] + list(messages)
            else:
                messages = [HumanMessage(content=image_context)]
    
    # Preparar mensajes con el prompt del sistema
    # Verificar si ya hay un SystemMessage en los mensajes
    has_system_message = any(isinstance(msg, SystemMessage) for msg in messages)
    
    if not has_system_message:
        # Agregar el prompt del sistema al inicio
        messages_with_system = [SystemMessage(content=system_prompt)] + list(messages)
    else:
        messages_with_system = list(messages)
    
    # Obtener respuesta del LLM
    response = llm_with_tools.invoke(messages_with_system)
    
    # Actualizar el estado con la respuesta del agente
    return {
        "messages": messages + [response],
        "user_input": state["user_input"],
        "media_file_path": state.get("media_file_path")
    }


# ============================================================================
# ENRUTADOR (Router/Decisor)
# ============================================================================
def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """
    Decide si continuar ejecutando herramientas o terminar.
    
    Returns:
        "tools" si hay tool calls en el último mensaje
        "end" si no hay tool calls y el agente ha respondido
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # Si el último mensaje tiene tool calls, ejecutar herramientas
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # Si no hay tool calls, terminar
    return "end"


# ============================================================================
# CONSTRUCCIÓN DEL GRAFO
# ============================================================================
def create_despensa_graph():
    """
    Crea y retorna el grafo de LangGraph para el agente de despensa.
    """
    # Crear el grafo
    workflow = StateGraph(AgentState)
    
    # Agregar nodos
    # Incluir todas las herramientas en el ToolNode
    all_tools = [
        consultar_despensa,
        actualizar_despensa,
        transcribir_audio,
        procesar_imagen
    ]
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(all_tools))
    
    # Definir el punto de entrada
    workflow.set_entry_point("agent")
    
    # Agregar aristas condicionales desde el agente
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # Después de ejecutar herramientas, volver al agente para generar respuesta final
    workflow.add_edge("tools", "agent")
    
    # Compilar el grafo
    app = workflow.compile()
    
    return app


# ============================================================================
# FUNCIÓN PRINCIPAL PARA PROBAR EL AGENTE
# ============================================================================
def run_agent(user_input: str = "", chat_history: list[BaseMessage] = None, media_file_path: Optional[str] = None):
    """
    Ejecuta el agente con un input del usuario (texto, audio o imagen).
    
    Args:
        user_input: Mensaje del usuario en texto (simulado desde WhatsApp)
        chat_history: Historial previo de la conversación (opcional)
        media_file_path: Ruta al archivo multimedia (audio o imagen) (opcional)
    
    Returns:
        Respuesta del agente
    """
    # Crear el grafo
    app = create_despensa_graph()
    
    # Preparar el estado inicial
    initial_messages = chat_history if chat_history else []
    
    # Si hay un archivo multimedia, no necesariamente necesitamos texto
    if user_input:
        initial_messages.append(HumanMessage(content=user_input))
    elif media_file_path:
        # Si solo hay archivo multimedia, agregar un mensaje indicando que hay un archivo
        file_type = "audio" if os.path.splitext(media_file_path)[1].lower() in ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.aac'] else "imagen"
        initial_messages.append(HumanMessage(content=f"El usuario ha enviado un archivo {file_type}: {media_file_path}"))
    
    initial_state = {
        "messages": initial_messages,
        "user_input": user_input or "",
        "media_file_path": media_file_path
    }
    
    # Ejecutar el grafo
    result = app.invoke(initial_state)
    
    # Obtener la última respuesta del agente
    last_message = result["messages"][-1]
    
    return last_message.content if hasattr(last_message, "content") else str(last_message)


# ============================================================================
# EJECUCIÓN PRINCIPAL (Para pruebas)
# ============================================================================
if __name__ == "__main__":
    # Verificar que existe la API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Error: OPENAI_API_KEY no encontrada en las variables de entorno.")
        print("   Por favor, crea un archivo .env con tu API key de OpenAI.")
        exit(1)
    
    print("🏪 Agente de Despensa - MVP Multimodal")
    print("=" * 50)
    print("\nEstado inicial de la despensa:")
    for item, estado in DESPENSA_DB.items():
        print(f"  - {item}: {estado}")
    print("\n" + "=" * 50)
    print("\n💬 Puedes hacer consultas o actualizaciones de tres formas:")
    print("\n1️⃣  TEXTO:")
    print("   - '¿Qué me falta?'")
    print("   - '¿Tengo leche?'")
    print("   - 'Compré huevos'")
    print("   - 'Se me acabó el pan'")
    print("\n2️⃣  AUDIO (simulado):")
    print("   - 'audio:compre_pan.wav'")
    print("   - 'audio:que_falta.mp3'")
    print("\n3️⃣  IMAGEN (simulado):")
    print("   - 'imagen:despensa.jpg'")
    print("   - 'imagen:compra_arroz.png'")
    print("\nEscribe 'salir' para terminar.\n")
    
    chat_history = []
    
    while True:
        user_input = input("\n👤 Tú: ").strip()
        
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("\n👋 ¡Hasta luego!")
            break
        
        if not user_input:
            continue
        
        try:
            # Detectar si el input es un archivo multimedia
            media_file_path = None
            text_input = user_input
            
            # Detectar formato: "audio:archivo.wav" o "imagen:archivo.jpg"
            if user_input.startswith("audio:"):
                media_file_path = user_input.replace("audio:", "").strip()
                text_input = ""
            elif user_input.startswith("imagen:"):
                media_file_path = user_input.replace("imagen:", "").strip()
                text_input = ""
            elif os.path.exists(user_input) and os.path.isfile(user_input):
                # Si es una ruta de archivo válida
                media_file_path = user_input
                text_input = ""
            
            print("\n🤖 Agente: ", end="", flush=True)
            response = run_agent(text_input, chat_history, media_file_path)
            print(response)
            
            # Actualizar historial
            if text_input:
                chat_history.append(HumanMessage(content=text_input))
            elif media_file_path:
                file_type = "audio" if os.path.splitext(media_file_path)[1].lower() in ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.aac'] else "imagen"
                chat_history.append(HumanMessage(content=f"Archivo {file_type}: {media_file_path}"))
            chat_history.append(AIMessage(content=response))
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

