# 🧪 Guía de Prueba de APIs Multimodales

## ✅ Estado de Implementación

Las APIs reales están **completamente implementadas** y listas para usar.

## 🎤 Probar Transcripción de Audio

### Requisitos:
- Archivo de audio en formato: `.mp3`, `.mp4`, `.mpeg`, `.mpga`, `.m4a`, `.wav`, `.webm`
- Tamaño máximo: 25 MB
- Idioma: Español (configurado automáticamente)

### Ejemplo de uso:

```python
from despensa_agent import transcribir_audio

# Probar con un archivo de audio real
resultado = transcribir_audio.invoke({"audio_file_path": "tu_audio.wav"})
print(resultado)
```

### Desde la línea de comandos:

```bash
python despensa_agent.py
# Luego escribe: audio:tu_audio.wav
```

### Ejemplo de respuesta esperada:
```
El usuario dijo: 'Compré pan y leche en el supermercado'
```

---

## 🖼️ Probar Procesamiento de Imágenes

### Requisitos:
- Archivo de imagen en formato: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- Tamaño máximo: 20 MB

### Ejemplo de uso:

```python
from despensa_agent import procesar_imagen

# Probar con una imagen real
resultado = procesar_imagen.invoke({"image_file_path": "despensa.jpg"})
print(resultado)
```

### Desde la línea de comandos:

```bash
python despensa_agent.py
# Luego escribe: imagen:despensa.jpg
```

### Ejemplo de respuesta esperada:
```
Compra de 1kg de arroz, establecer a ALTO
Compra de pan, establecer a ALTO
Compra de leche, establecer a ALTO
```

---

## 🔄 Flujo Completo de Prueba

### 1. Probar con Audio:

```bash
# Ejecutar el agente
python despensa_agent.py

# Enviar un archivo de audio
👤 Tú: audio:mensaje_compra.wav

# El agente:
# 1. Transcribe el audio usando Whisper
# 2. Analiza la transcripción
# 3. Actualiza la despensa si es necesario
# 4. Responde al usuario
```

### 2. Probar con Imagen:

```bash
# Ejecutar el agente
python despensa_agent.py

# Enviar una imagen
👤 Tú: imagen:compra_supermercado.jpg

# El agente:
# 1. Procesa la imagen usando Vision API
# 2. Identifica los productos
# 3. Actualiza la despensa
# 4. Responde al usuario
```

---

## ⚠️ Manejo de Errores

El sistema maneja automáticamente:

1. **Archivo no encontrado:**
   ```
   Error: El archivo de audio 'archivo.wav' no existe.
   ```

2. **Formato no soportado:**
   ```
   Error: Formato de archivo '.avi' no soportado. Formatos válidos: .mp3, .wav, ...
   ```

3. **Archivo demasiado grande:**
   ```
   Error: El archivo es demasiado grande (30.50 MB). El máximo es 25 MB.
   ```

4. **Límite de tasa excedido:**
   ```
   Error: Límite de tasa excedido. Por favor, intenta de nuevo en unos momentos.
   ```

---

## 💰 Costos Estimados

### Transcripción de Audio (Whisper):
- $0.006 por minuto
- 100 transcripciones de 1 minuto = ~$0.60

### Procesamiento de Imágenes (GPT-4o-mini Vision):
- ~$0.15 por 1M tokens de entrada
- Una imagen típica: ~85 tokens
- 100 imágenes = ~$0.01-0.02

**Total muy económico para uso personal/desarrollo.**

---

## 🎯 Casos de Prueba Recomendados

### Audio:
1. ✅ Grabación en español diciendo "Compré pan"
2. ✅ Grabación diciendo "¿Qué me falta?"
3. ✅ Archivo de audio largo (2-3 minutos)
4. ❌ Probar con archivo inexistente (debe dar error)
5. ❌ Probar con formato no soportado (debe dar error)

### Imágenes:
1. ✅ Foto de productos en el supermercado
2. ✅ Foto de la despensa con varios productos
3. ✅ Imagen con texto visible (etiquetas de productos)
4. ❌ Probar con archivo inexistente (debe dar error)
5. ❌ Probar con formato no soportado (debe dar error)

---

## 🔍 Verificación de Implementación

Para verificar que las APIs están implementadas:

```python
import despensa_agent

# Verificar que el cliente OpenAI está inicializado
print(hasattr(despensa_agent, 'openai_client'))  # Debe ser True

# Verificar que las herramientas existen
print(hasattr(despensa_agent, 'transcribir_audio'))  # Debe ser True
print(hasattr(despensa_agent, 'procesar_imagen'))  # Debe ser True
```

---

## 📝 Notas Importantes

1. **API Key**: Asegúrate de tener `OPENAI_API_KEY` configurada en `.env`
2. **Conexión a Internet**: Las APIs requieren conexión a internet
3. **Tiempo de respuesta**: 
   - Audio: 2-10 segundos dependiendo de la duración
   - Imagen: 1-3 segundos
4. **Idioma**: El audio se transcribe en español por defecto

---

## 🚀 Próximos Pasos

Una vez probado, puedes:
1. Integrar con WhatsApp real
2. Agregar más tipos de procesamiento
3. Implementar cache para archivos ya procesados
4. Agregar soporte para más idiomas

