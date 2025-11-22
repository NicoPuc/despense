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
from prompts import SYSTEM_PROMPT

# Cargar variables de entorno
load_dotenv()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

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
def consultar_despensa(item_name: str = None) -> str:
    """
    Consulta el estado actual de items en la despensa.
    Si item_name es None, lista todo.
    """
    if item_name:
        item_name_lower = item_name.lower().strip()
        found = {k: v for k, v in DESPENSA_DB.items() if item_name_lower in k}
        if not found:
            return f"No encontré '{item_name}' en la despensa."
        return "\n".join([f"- {k.capitalize()}: {v}" for k, v in found.items()])
    else:
        if not DESPENSA_DB:
            return "La despensa está vacía."
        return "\n".join([f"- {k.capitalize()}: {v}" for k, v in DESPENSA_DB.items()])


@tool
def actualizar_despensa(description: str, operation_type: Literal["in", "out", "update"]) -> str:
    """
    Actualiza el inventario.
    Args:
        description: Descripción de productos (ej: "2 leches").
        operation_type: "in" (compra), "out" (consumo), "update" (corrección).
    """
    # Simulación básica compatible con el nuevo prompt
    affected_items = [item for item in DESPENSA_DB.keys() if item in description.lower()]
    
    for item in affected_items:
        if operation_type == "in":
            DESPENSA_DB[item] = "ALTO"
        elif operation_type == "out":
            DESPENSA_DB[item] = "BAJO"
        elif operation_type == "update":
            DESPENSA_DB[item] = "MEDIO"
            
    if not affected_items:
        return f"[API] Operación '{operation_type}' registrada para: {description}"
    
    return f"Actualizado ({operation_type}): {', '.join(affected_items)}"


@tool
def consultar_reposicion_de_productos() -> str:
    """
    Calcula y devuelve una lista de compras sugerida.
    """
    print("\n[TEST] - Consulta sobre reposicion de productos")
    shopping_list = [k for k, v in DESPENSA_DB.items() if v == "BAJO"]
    
    if not shopping_list:
        return "No hay nada urgente que comprar."
    return "Lista de compras sugerida:\n" + "\n".join([f"- {i.capitalize()}" for i in shopping_list])


# ============================================================================
# HERRAMIENTAS MULTIMODALES (TOOLS) - Lógica Original Restaurada
# ============================================================================
@tool
def transcribir_audio(audio_file_path: str) -> str:
    """
    Transcribe un archivo de audio a texto usando OpenAI Whisper API.
    
    Args:
        audio_file_path: Ruta al archivo de audio (ej: "audio.wav", "mensaje.mp3")
    
    Returns:
        Texto transcrito que indica lo que el usuario dijo
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
# NODO DEL AGENTE
# ============================================================================
def agent_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    messages = state["messages"]
    media_file_path = state.get("media_file_path")
    
    # Herramientas disponibles
    all_tools = [consultar_despensa, actualizar_despensa, consultar_reposicion_de_productos]
    
    # Agregar herramientas multimodales si hay archivo
    if media_file_path:
        file_ext = os.path.splitext(media_file_path)[1].lower()
        if file_ext in ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.aac']:
            all_tools.append(transcribir_audio)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            all_tools.append(procesar_imagen)
    
    # Inyectar contexto si hay media y no se ha procesado
    if media_file_path and not any("transcribir_audio" in str(msg) or "procesar_imagen" in str(msg) for msg in messages):
        file_ext = os.path.splitext(media_file_path)[1].lower()
        if file_ext in ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.aac']:
            context = f"El usuario ha enviado un archivo de audio: {media_file_path}. Debes transcribirlo primero usando 'transcribir_audio'."
            messages = [HumanMessage(content=context)] + list(messages)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            context = f"El usuario ha enviado una imagen: {media_file_path}. Debes procesarla primero usando 'procesar_imagen'."
            messages = [HumanMessage(content=context)] + list(messages)

    # Inyectar System Prompt
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = llm.bind_tools(all_tools).invoke(messages)
    
    return {
        "messages": list(state["messages"]) + [response], # Mantener historial original + respuesta
        "user_input": state["user_input"],
        "media_file_path": state.get("media_file_path")
    }


# ============================================================================
# ENRUTADOR
# ============================================================================
def should_continue(state: AgentState) -> Literal["tools", "end"]:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


# ============================================================================
# GRAFO
# ============================================================================
def create_despensa_graph():
    workflow = StateGraph(AgentState)
    
    all_tools = [
        consultar_despensa,
        actualizar_despensa,
        consultar_reposicion_de_productos,
        transcribir_audio,
        procesar_imagen
    ]
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(all_tools))
    
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()


# ============================================================================
# EJECUCIÓN
# ============================================================================
def run_agent(user_input: str = "", chat_history: list[BaseMessage] = None, media_file_path: Optional[str] = None):
    app = create_despensa_graph()
    
    initial_messages = list(chat_history) if chat_history else []
    
    if user_input:
        initial_messages.append(HumanMessage(content=user_input))
    elif media_file_path:
        file_type = "audio" if os.path.splitext(media_file_path)[1].lower() in ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.aac'] else "imagen"
        initial_messages.append(HumanMessage(content=f"El usuario ha enviado un archivo {file_type}: {media_file_path}"))
    
    initial_state = {
        "messages": initial_messages,
        "user_input": user_input or "",
        "media_file_path": media_file_path
    }
    
    result = app.invoke(initial_state)
    last_message = result["messages"][-1]
    
    return last_message.content if hasattr(last_message, "content") else str(last_message)


if __name__ == "__main__":
    print("🏪 Agente de Despensa (Modo Pruebas)")
    # ... lógica de prueba básica ...
    while True:
        user_input = input("\n👤 Tú: ").strip()
        if user_input.lower() in ["salir", "exit"]: break
        print(f"🤖 Agente: {run_agent(user_input=user_input)}")
