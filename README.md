# ContHome

Aplicación de control de finanzas del hogar: gastos, recordatorios de pagos y un
panel con la situación del mes.

## Funcionalidad

- **Gastos** — registro, edición y categorización.
- **Dashboard** — resumen del periodo vía `/api/dashboard-data`.
- **Recordatorios** — avisos de pagos próximos.
- **Diezmo** — cálculo opcional, activable por usuario.
- **Administración** — alta y baja de usuarios, activación/desactivación y
  **caducidad de cuenta** por usuario.

## Stack

Python · Flask · SQLite · Jinja2 · autenticación con sesiones

## Arquitectura

```
app.py        rutas y vistas
auth.py       autenticacion y control de acceso
models.py     entidades
database.py   conexion y esquema
templates/    vistas Jinja2
static/       CSS y JS
```

## Ejecutar

```bash
pip install -r requirements.txt
python init_admin.py   # crea el usuario administrador
python app.py
```

## Licencia

Propietario — todos los derechos reservados. Visible para evaluación técnica;
no se autoriza su uso, copia ni distribución. Ver [LICENSE](LICENSE).
