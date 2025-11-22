# 🏪 Agente de Despensa - MVP

Un agente conversacional inteligente construido con **LangGraph** que gestiona el inventario de una despensa. El agente puede recibir inputs (simulando mensajes de WhatsApp) y decidir automáticamente si debe consultar o actualizar el estado de los ítems en la despensa.

## 🎯 Características

- **Agente Inteligente**: Usa LLM (OpenAI) para entender la intención del usuario
- **Dos Herramientas Simuladas**:
  - `consultar_despensa`: Consulta el estado actual de un ítem
  - `actualizar_despensa`: Actualiza el estado de un ítem en la base de datos simulada
- **Enrutamiento Automático**: El agente decide automáticamente qué herramienta usar basándose en el contexto
- **Arquitectura Modular**: Código preparado para expandirse con funcionalidades multimodales (audio/imagen)

## 📋 Requisitos

- Python 3.10 o 3.11 (recomendado) o 3.12
  - ⚠️ **Nota**: Python 3.13 puede tener problemas de compatibilidad con algunas dependencias. Si usas Python 3.13, considera usar Python 3.12 o 3.11.
- API Key de OpenAI

## 🚀 Instalación

1. **Clonar o navegar al proyecto**:
```bash
cd Platanus
```

2. **Crear y activar un entorno virtual**:
```bash
# Si tienes Python 3.13, usa Python 3.12 o 3.11:
python3.12 -m venv .venv  # O python3.11
# O si tienes Python 3.10-3.12:
python3 -m venv .venv

source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

3. **Actualizar pip**:
```bash
pip install --upgrade pip setuptools wheel
```

4. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

> ⚠️ **Problemas con la instalación?** Consulta [SETUP.md](SETUP.md) para soluciones detalladas, especialmente si usas Python 3.13.

4. **Configurar variables de entorno**:
```bash
cp .env.example .env
# Editar .env y agregar tu OPENAI_API_KEY
```

## 💻 Uso

### Ejecutar el agente interactivo:

```bash
python despensa_agent.py
```

### Ejemplos de uso:

**Consultas:**
- "¿Qué me falta?"
- "¿Tengo leche?"
- "¿Cuál es el estado del pan?"

**Actualizaciones:**
- "Compré huevos"
- "Se me acabó el pan"
- "Agregué azúcar"
- "Ya no tengo leche"

## 🏗️ Arquitectura

El agente está construido con **LangGraph** y sigue este flujo:

```
Usuario → Agente (Razonamiento) → Router → Herramienta → Respuesta Final
```

### Componentes principales:

1. **Estado del Grafo (`AgentState`)**: Mantiene `messages` (historial) y `user_input`
2. **Nodo del Agente (`agent_node`)**: Usa el LLM para razonar sobre la intención
3. **Enrutador (`should_continue`)**: Decide si ejecutar herramientas o terminar
4. **Herramientas**: `consultar_despensa` y `actualizar_despensa`
5. **Nodo de Respuesta Final**: Genera la respuesta natural después de ejecutar herramientas

## 📊 Base de Datos Simulada

Por ahora, la despensa usa un diccionario global en Python (`DESPENSA_DB`). Los estados posibles son:
- `BAJO`: El ítem está escaso
- `MEDIO`: El ítem tiene cantidad moderada
- `ALTO`: El ítem está bien abastecido

## 🔮 Próximos Pasos (Extensibilidad)

El código está diseñado para ser fácilmente expandible:

- **Integración con WhatsApp**: Reemplazar el input simulado con webhooks reales
- **Base de Datos Real**: Reemplazar el diccionario con SQLite/PostgreSQL
- **Funcionalidades Multimodales**: Agregar procesamiento de imágenes (fotos de la despensa) o audio (mensajes de voz)
- **Notificaciones**: Alertas cuando un ítem está bajo
- **Historial Persistente**: Guardar conversaciones en base de datos

## 📝 Notas

- Este es un MVP (Minimum Viable Product) para demostrar la lógica central
- La base de datos es volátil (se reinicia al cerrar el programa)
- El agente usa `gpt-4o-mini` por defecto (económico y rápido)

## 🐛 Troubleshooting

**Error: OPENAI_API_KEY no encontrada**
- Asegúrate de haber creado el archivo `.env` con tu API key
- Verifica que el archivo esté en la raíz del proyecto

**Error al instalar dependencias**
- Asegúrate de tener Python 3.9 o superior
- Verifica que el entorno virtual esté activado

