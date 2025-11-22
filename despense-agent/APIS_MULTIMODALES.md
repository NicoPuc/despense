# 🔌 APIs para Funcionalidades Multimodales

## 📋 Estado Actual

✅ **IMPLEMENTADO**: Las herramientas `transcribir_audio` y `procesar_imagen` están **completamente implementadas** usando APIs reales de OpenAI:

- `transcribir_audio`: Usa OpenAI Whisper API
- `procesar_imagen`: Usa OpenAI Vision API (GPT-4o-mini)

Ambas herramientas incluyen:

- ✅ Validación de archivos (existencia, formato, tamaño)
- ✅ Manejo de errores robusto
- ✅ Mensajes de error descriptivos
- ✅ Límites de tamaño de archivo

## 🎤 Transcripción de Audio

### Opción 1: OpenAI Whisper API (Recomendado)

**Ventajas:**

- Alta precisión
- Soporta múltiples idiomas
- Mismo proveedor que el LLM (OpenAI)
- Fácil integración

**Configuración necesaria:**

```python
# Ya tienes OPENAI_API_KEY configurada ✅
# No necesitas API key adicional
```

**Implementación:**

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribir_audio(audio_file_path: str) -> str:
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="es"  # Opcional: especificar idioma
        )
    return f"El usuario dijo: '{transcript.text}'"
```

**Costos:**

- $0.006 por minuto de audio
- Muy económico para uso personal

**Dependencias adicionales:**

```bash
# Ya está incluido en openai>=1.109.1 (que ya tienes instalado)
# No necesitas instalar nada adicional
```

---

### Opción 2: Google Cloud Speech-to-Text

**Ventajas:**

- Muy preciso
- Soporte para múltiples idiomas
- Buena para producción a escala

**Configuración necesaria:**

```bash
# Instalar SDK
pip install google-cloud-speech

# Configurar credenciales
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

**Implementación:**

```python
from google.cloud import speech

def transcribir_audio(audio_file_path: str) -> str:
    client = speech.SpeechClient()
  
    with open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()
  
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="es-ES",
    )
  
    response = client.recognize(config=config, audio=audio)
  
    transcript = " ".join([result.alternatives[0].transcript 
                          for result in response.results])
    return f"El usuario dijo: '{transcript}'"
```

**Costos:**

- Primeros 60 minutos/mes: GRATIS
- Después: $0.006 por minuto

---

## 🖼️ Procesamiento de Imágenes

### Opción 1: OpenAI Vision API (GPT-4 Vision) (Recomendado)

**Ventajas:**

- Integración perfecta con el LLM actual
- Entiende contexto complejo
- Puede extraer información estructurada
- Mismo proveedor (OpenAI)

**Configuración necesaria:**

```python
# Ya tienes OPENAI_API_KEY configurada ✅
# No necesitas API key adicional
```

**Implementación:**

```python
from openai import OpenAI
import base64

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def procesar_imagen(image_file_path: str) -> str:
    # Leer y codificar la imagen
    with open(image_file_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
  
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # o "gpt-4o" para mejor precisión
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Analiza esta imagen de una despensa o compra. 
                        Identifica los productos y genera un mensaje estructurado 
                        para actualizar el inventario. Formato: 
                        "Compra de [producto] [cantidad], establecer a ALTO"
                        Si hay múltiples productos, lista cada uno."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300
    )
  
    return response.choices[0].message.content
```

**Costos:**

- GPT-4o-mini: $0.15 por 1M tokens de entrada, $0.60 por 1M tokens de salida
- GPT-4o: $2.50 por 1M tokens de entrada, $10.00 por 1M tokens de salida
- Una imagen típica: ~85 tokens

**Dependencias adicionales:**

```bash
# Ya está incluido en openai>=1.109.1
# No necesitas instalar nada adicional
```

---

### Opción 2: Google Cloud Vision API

**Ventajas:**

- Muy preciso para detección de objetos
- Buena para reconocimiento de productos
- Escalable

**Configuración necesaria:**

```bash
# Instalar SDK
pip install google-cloud-vision

# Configurar credenciales
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

**Implementación:**

```python
from google.cloud import vision

def procesar_imagen(image_file_path: str) -> str:
    client = vision.ImageAnnotatorClient()
  
    with open(image_file_path, "rb") as image_file:
        content = image_file.read()
  
    image = vision.Image(content=content)
  
    # Detectar objetos y texto
    response = client.label_detection(image=image)
    labels = [label.description for label in response.label_annotations]
  
    # Usar el LLM para estructurar la información
    # (combinar con OpenAI para mejor resultado)
    productos_detectados = ", ".join(labels[:5])  # Top 5
  
    return f"Productos detectados en imagen: {productos_detectados}. Actualizar inventario según necesidad."
```

**Costos:**

- Primeras 1,000 unidades/mes: GRATIS
- Después: $1.50 por 1,000 unidades

---

## 🚀 Recomendación para Implementación

### Para MVP/Producción Inicial:

**Usar OpenAI para ambas funcionalidades:**

- ✅ Ya tienes la API key configurada
- ✅ No necesitas credenciales adicionales
- ✅ Integración simple
- ✅ Costos razonables
- ✅ Alta calidad

### Pasos para Implementar:

1. **Actualizar `transcribir_audio`:**

   ```python
   # Reemplazar la simulación con llamada real a OpenAI Whisper
   ```
2. **Actualizar `procesar_imagen`:**

   ```python
   # Reemplazar la simulación con llamada real a OpenAI Vision
   ```
3. **Manejo de errores:**

   ```python
   # Agregar try/except para manejar errores de API
   # Validar que el archivo existe y es válido
   ```
4. **Optimización:**

   ```python
   # Cachear resultados si el mismo archivo se procesa múltiples veces
   # Validar tipos de archivo antes de procesar
   ```

## 📝 Checklist de Configuración

- [X] OPENAI_API_KEY configurada (ya tienes esto)
- [ ] Implementar `transcribir_audio` con OpenAI Whisper
- [ ] Implementar `procesar_imagen` con OpenAI Vision
- [ ] Agregar validación de tipos de archivo
- [ ] Agregar manejo de errores
- [ ] Probar con archivos reales
- [ ] Documentar límites de tamaño de archivo

## ⚠️ Notas Importantes

1. **Límites de tamaño:**

   - OpenAI Whisper: máximo 25 MB por archivo
   - OpenAI Vision: imágenes deben ser < 20 MB
2. **Formatos soportados:**

   - Audio: mp3, mp4, mpeg, mpga, m4a, wav, webm
   - Imagen: jpg, jpeg, png, gif, webp
3. **Costos estimados:**

   - 100 transcripciones de 1 minuto: ~$0.60
   - 100 análisis de imágenes: ~$0.01-0.02

## 🔄 Migración desde Simulación

Para migrar de la simulación actual a implementación real:

1. Mantener la misma firma de función
2. Reemplazar la lógica de simulación con llamadas API reales
3. Mantener el mismo formato de retorno
4. El resto del código no necesita cambios

El código está diseñado para que esta migración sea transparente.
