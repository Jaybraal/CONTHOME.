import os

# Asegurar que el directorio de la DB existe (necesario para el volumen en Railway)
db_path = os.environ.get('DATABASE_PATH', '')
if db_path:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

from database import init_db
from auth import init_admin
from app import app

init_db()
init_admin()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5002)))
