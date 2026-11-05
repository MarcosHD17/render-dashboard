# Dashboard con login y SQLite (Render)

Aplicación Flask mínima: autenticación por sesión, base de datos SQLite y panel con datos de ejemplo.

## Estructura
- `app.py`: rutas, acceso a SQLite, siembra inicial (`init_db`).
- `templates/`: `base.html`, `login.html`, `dashboard.html`.
- `static/style.css`: estilos.
- `render.yaml`: Blueprint de Render.

## Ejecución local
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py   # http://127.0.0.1:5000
```
Credenciales por defecto: `admin` / `admin123`.

## Variables de entorno
| Variable | Descripción | Por defecto |
|---|---|---|
| `SECRET_KEY` | Clave de firma de sesión | `dev-only-change-me` |
| `ADMIN_USER` | Usuario inicial | `admin` |
| `ADMIN_PASSWORD` | Contraseña inicial | `admin123` |
| `DATABASE_PATH` | Ruta del archivo SQLite | `data/app.db` |

## Despliegue en Render
1. Subir el repositorio a GitHub.
2. Render → **New** → **Blueprint** → seleccionar el repositorio (usa `render.yaml`).
3. Consultar la contraseña generada en **Environment** → `ADMIN_PASSWORD`.
4. Abrir la URL del servicio e iniciar sesión.

## Persistencia
El plan `free` de Render tiene sistema de archivos efímero: SQLite se recrea y resiembra en cada reinicio o despliegue.
Para persistir datos: plan de pago + disco (`disk` con `mountPath: /var/data`) y `DATABASE_PATH=/var/data/app.db`.
