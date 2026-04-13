from database import init_db
from auth import init_admin
from app import app

init_db()
init_admin()

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5002)))
