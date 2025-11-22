# 🏗️ Arquitectura Multimodal del Agente de Despensa

## 📋 Resumen Ejecutivo

Este documento explica cómo el LLM decide la ruta de ejecución en el Agente de Despensa cuando recibe diferentes tipos de entrada: texto puro o archivos multimedia (audio/imagen).

## 🔄 Flujo de Decisiones del LLM

### Caso A: Entrada Solo de Texto

**Ejemplo:** `"¿Qué me falta?"`

```
1. Usuario envía: "¿Qué me falta?"
   ↓
2. agent_node recibe el estado:
   - messages: [HumanMessage("¿Qué me falta?")]
   - user_input: "¿Qué me falta?"
   - media_file_path: None
   ↓
3. El LLM analiza el mensaje con el system_prompt:
   - Detecta que es una CONSULTA
   - No hay archivo multimedia, así que salta el paso de procesamiento
   ↓
4. El LLM decide usar: consultar_despensa
   - Genera un tool_call con item_name apropiado
   ↓
5. should_continue() detecta tool_calls → retorna "tools"
   ↓
6. ToolNode ejecuta: consultar_despensa
   ↓
7. Vuelve a agent_node con el resultado
   ↓
8. El LLM genera respuesta final usando el resultado de la herramienta
   ↓
9. should_continue() no detecta más tool_calls → retorna "end"
   ↓
10. FIN: Respuesta al usuario
```

**Flujo Visual:**
```
Usuario → agent_node → [LLM decide: consultar_despensa] → tools → agent_node → [LLM genera respuesta] → END
```

---

### Caso B: Entrada con Archivo Multimedia

**Ejemplo:** `media_file_path = "audio_compre_pan.wav"`

```
1. Usuario envía archivo: "audio_compre_pan.wav"
   ↓
2. agent_node recibe el estado:
   - messages: [HumanMessage("El usuario ha enviado un archivo audio: audio_compre_pan.wav")]
   - user_input: ""
   - media_file_path: "audio_compre_pan.wav"
   ↓
3. El LLM analiza el estado:
   - Detecta que media_file_path NO es None
   - Detecta que la extensión es .wav (audio)
   - El system_prompt indica: "Si hay media_file_path, PRIMERO procesa el archivo"
   ↓
4. El LLM decide usar: transcribir_audio(audio_file_path="audio_compre_pan.wav")
   - Genera un tool_call para transcribir_audio
   ↓
5. should_continue() detecta tool_calls → retorna "tools"
   ↓
6. ToolNode ejecuta: transcribir_audio
   - Retorna: "El usuario dijo: 'Compré pan'"
   ↓
7. Vuelve a agent_node con el resultado de la transcripción
   ↓
8. El LLM analiza el texto transcrito: "El usuario dijo: 'Compré pan'"
   - Detecta que es una ACTUALIZACIÓN
   - Identifica: item="pan", acción="Compré" → estado="ALTO"
   ↓
9. El LLM decide usar: actualizar_despensa(item_name="pan", new_status="ALTO")
   - Genera un nuevo tool_call
   ↓
10. should_continue() detecta tool_calls → retorna "tools"
   ↓
11. ToolNode ejecuta: actualizar_despensa
    - Actualiza DESPENSA_DB["pan"] = "ALTO"
    - Retorna: "✅ Actualizado: 'pan' ahora tiene estado 'ALTO'"
   ↓
12. Vuelve a agent_node con el resultado de la actualización
   ↓
13. El LLM genera respuesta final confirmando la actualización
   ↓
14. should_continue() no detecta más tool_calls → retorna "end"
   ↓
15. FIN: Respuesta al usuario confirmando la actualización
```

**Flujo Visual:**
```
Usuario (audio) → agent_node → [LLM decide: transcribir_audio] 
    → tools → agent_node → [LLM analiza transcripción] 
    → [LLM decide: actualizar_despensa] 
    → tools → agent_node → [LLM genera respuesta] → END
```

---

## 🧠 Lógica de Decisión del LLM

### 1. **Detección de Tipo de Entrada**

El `agent_node` determina qué herramientas están disponibles:

```python
if media_file_path:
    file_ext = os.path.splitext(media_file_path)[1].lower()
    if file_ext in ['.wav', '.mp3', ...]:  # Audio
        all_tools = [transcribir_audio, consultar_despensa, actualizar_despensa]
    elif file_ext in ['.jpg', '.png', ...]:  # Imagen
        all_tools = [procesar_imagen, consultar_despensa, actualizar_despensa]
else:
    all_tools = [consultar_despensa, actualizar_despensa]  # Solo texto
```

### 2. **System Prompt Guía la Decisión**

El `system_prompt` instruye al LLM:

```
"Si el usuario envía un archivo multimedia:
   - PRIMERO debes usar 'transcribir_audio' o 'procesar_imagen'
   - Luego, usa el resultado para decidir la siguiente acción"
```

### 3. **Procesamiento en Cascada**

El LLM procesa en múltiples pasos:

1. **Paso 1 (si hay multimedia):** Procesar archivo → obtener texto
2. **Paso 2:** Analizar texto → decidir acción (consultar/actualizar)
3. **Paso 3:** Ejecutar acción → obtener resultado
4. **Paso 4:** Generar respuesta final

### 4. **Enrutamiento Condicional**

El `should_continue()` decide el flujo:

- Si hay `tool_calls` → ir a `tools`
- Si no hay `tool_calls` → ir a `END`

## 📊 Comparación de Flujos

| Aspecto | Solo Texto | Con Multimedia |
|---------|-----------|----------------|
| **Pasos iniciales** | 1 (análisis directo) | 2 (procesar archivo + análisis) |
| **Herramientas disponibles** | 2 (consultar, actualizar) | 3-4 (multimodal + consultar + actualizar) |
| **Tool calls típicos** | 1 | 2 (procesar + acción) |
| **Tiempo de procesamiento** | Más rápido | Más lento (múltiples iteraciones) |

## 🔑 Puntos Clave

1. **El LLM decide dinámicamente** qué herramientas usar basándose en:
   - Presencia de `media_file_path`
   - Tipo de archivo (extensión)
   - Contenido del mensaje/texto procesado

2. **El flujo es iterativo**: El agente puede hacer múltiples llamadas a herramientas en secuencia:
   - Primero: procesar multimedia
   - Segundo: ejecutar acción (consultar/actualizar)
   - Tercero: generar respuesta

3. **El estado se mantiene entre iteraciones**: 
   - `messages` acumula todo el historial
   - `media_file_path` se mantiene hasta que se procesa
   - Cada iteración del `agent_node` tiene contexto completo

4. **El enrutador (`should_continue`) es simple pero efectivo**:
   - Solo verifica si hay `tool_calls`
   - No necesita lógica compleja porque el LLM ya decidió qué hacer

## 🚀 Extensibilidad

Para agregar más tipos de multimedia:

1. Agregar nueva herramienta (ej: `procesar_video`)
2. Actualizar detección de tipo de archivo en `agent_node`
3. Agregar al `ToolNode` en `create_despensa_graph()`
4. Actualizar `system_prompt` con instrucciones

El sistema es modular y fácil de extender.

