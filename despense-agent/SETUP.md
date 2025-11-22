# 🔧 Guía de Instalación - Solución de Problemas

## Problema con Python 3.13

Si estás usando **Python 3.13** y encuentras errores al instalar dependencias (especialmente `pydantic-core` o `tiktoken`), esto se debe a que algunas dependencias aún no tienen soporte completo para Python 3.13.

## Soluciones

### Opción 1: Usar Python 3.12 o 3.11 (Recomendado)

1. **Instalar Python 3.12** (si no lo tienes):
```bash
# En macOS con Homebrew:
brew install python@3.12

# O descargar desde python.org
```

2. **Crear un nuevo entorno virtual con Python 3.12**:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Opción 2: Actualizar pip y usar versiones más recientes

Si prefieres seguir con Python 3.13:

```bash
# Actualizar pip, setuptools y wheel
pip install --upgrade pip setuptools wheel

# Instalar sin restricciones de versión (usará las más recientes)
pip install langchain langchain-openai langgraph python-dotenv

# O instalar con versiones específicas más recientes
pip install "langchain>=0.3.0" "langchain-openai>=0.2.0" "langgraph>=0.2.0" python-dotenv
```

### Opción 3: Usar pre-compilados (wheels)

```bash
pip install --upgrade pip
pip install --only-binary :all: langchain langchain-openai langgraph python-dotenv
```

## Verificar la instalación

Después de instalar, verifica que todo funciona:

```bash
python -c "import langchain; import langgraph; import langchain_openai; print('✅ Todas las dependencias instaladas correctamente')"
```

## Si persisten los problemas

1. **Verifica tu versión de Python**:
```bash
python --version
```

2. **Limpia el caché de pip**:
```bash
pip cache purge
```

3. **Reinstala en un entorno limpio**:
```bash
deactivate  # Si tienes un venv activo
rm -rf .venv
python3.12 -m venv .venv  # O python3.11
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

