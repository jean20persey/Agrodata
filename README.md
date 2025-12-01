# AgroData

Aplicación Flask para gestión agrícola con estadísticas, proyecciones y análisis.

## Requisitos
- Python 3.10+
- MySQL Server (con usuario y contraseña válidos)
- Windows PowerShell recomendado

## Instalación
```powershell
# Clonar
git clone https://github.com/jean20persey/Agrodata.git
cd Agrodata

# Crear y activar entorno
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r AgroData\requirements.txt
```

## Configuración
Crea `AgroData/config.py` basado en `AgroData/config.example.py`:
```python
from config_example import Config as Base
class Config(Base):
    MYSQL_HOST = 'localhost'
    MYSQL_USER = '<tu_usuario>'
    MYSQL_PASSWORD = '<tu_password>'
    MYSQL_DB = 'agrodata'
```

## Base de datos
Importa el esquema y los datos de demostración con el script incluido:
```powershell
python AgroData\scripts\seed_demo.py
```
Este script:
- Crea la base `agrodata` si no existe
- Importa `AgroData/database/agrodata.sql`
- Importa `AgroData/database/seed_demo.sql` y `seed_more.sql` (si existe)

Si prefieres usar MySQL Workbench, abre y ejecuta los archivos SQL manualmente en la BD `agrodata`.

## Ejecutar la aplicación
```powershell
python AgroData\app.py
```
Abrir en el navegador: http://127.0.0.1:5000

## Estructura del proyecto
```
AgroData/
  app.py
  config.py (no versionado) / config.example.py
  requirements.txt
  database/
    agrodata.sql
    seed_demo.sql
    seed_more.sql
  scripts/
    seed_demo.py
  templates/
  static/
```

## Notas
- No se sube `AgroData/config.py` al repo (contiene credenciales). Usa `config.example.py` como plantilla.
- Si el puerto 5000 está ocupado, cambia `app.run(..., port=5000)` en `AgroData/app.py`.
- Para actualizar datos de demo, edita los archivos en `AgroData/database/` y vuelve a ejecutar `seed_demo.py`.
