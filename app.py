import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g, session
from database import init_db, get_db_connection
from models import (
    get_categorias, get_gastos, get_gasto, add_gasto, update_gasto, delete_gasto,
    get_ingresos, get_ingreso, add_ingreso, update_ingreso, delete_ingreso,
    get_inversiones, get_inversion, add_inversion, add_retorno, cerrar_inversion, delete_inversion,
    get_diezmo_data, get_dashboard_summary, get_gastos_por_categoria, get_monthly_totals,
)
from auth import login_required, admin_required, verificar_login, crear_usuario, get_usuario, init_admin

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'conthome-personal-key-2026')


def get_db():
    if 'db' not in g:
        g.db = get_db_connection()
    return g.db


def uid():
    return session['user_id']


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = get_usuario(session['user_id'])
    return dict(current_user=user)


# --- Auth ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user = verificar_login(username, password)
        if user:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['es_admin'] = bool(user['es_admin'])
            next_url = request.form.get('next') or url_for('dashboard')
            return redirect(next_url)
        flash('Usuario o contraseña incorrectos.', 'danger')
    next_url = request.args.get('next', '')
    return render_template('login.html', next=next_url)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- Admin: gestión de usuarios ---

@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    conn = get_db_connection()
    usuarios = conn.execute("SELECT id, username, es_admin, activo, created_at FROM usuarios ORDER BY id").fetchall()
    conn.close()
    return render_template('admin_usuarios.html', usuarios=usuarios)


@app.route('/admin/usuarios/crear', methods=['POST'])
@admin_required
def admin_crear_usuario():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    es_admin = request.form.get('es_admin') == '1'
    if not username or not password:
        flash('Usuario y contraseña son requeridos.', 'danger')
        return redirect(url_for('admin_usuarios'))
    ok, err = crear_usuario(username, password, es_admin=es_admin)
    if ok:
        flash(f'Usuario "{username}" creado correctamente.', 'success')
    else:
        flash(f'Error: {err}', 'danger')
    return redirect(url_for('admin_usuarios'))


@app.route('/admin/usuarios/<int:uid_param>/toggle', methods=['POST'])
@admin_required
def admin_toggle_usuario(uid_param):
    if uid_param == session['user_id']:
        flash('No puedes desactivar tu propia cuenta.', 'warning')
        return redirect(url_for('admin_usuarios'))
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM usuarios WHERE id = ?", (uid_param,)).fetchone()
    if user:
        nuevo = 0 if user['activo'] else 1
        conn.execute("UPDATE usuarios SET activo = ? WHERE id = ?", (nuevo, uid_param))
        conn.commit()
        estado = 'activado' if nuevo else 'desactivado'
        flash(f'Usuario "{user["username"]}" {estado}.', 'info')
    conn.close()
    return redirect(url_for('admin_usuarios'))


@app.route('/admin/usuarios/<int:uid_param>/eliminar', methods=['POST'])
@admin_required
def admin_eliminar_usuario(uid_param):
    if uid_param == session['user_id']:
        flash('No puedes eliminar tu propia cuenta.', 'warning')
        return redirect(url_for('admin_usuarios'))
    conn = get_db_connection()
    conn.execute("DELETE FROM usuarios WHERE id = ?", (uid_param,))
    conn.commit()
    conn.close()
    flash('Usuario eliminado.', 'warning')
    return redirect(url_for('admin_usuarios'))


# --- Dashboard ---

@app.route('/')
@login_required
def dashboard():
    mes = request.args.get('mes', '')
    data = get_dashboard_summary(get_db(), uid(), mes=mes)
    return render_template('dashboard.html', data=data)


@app.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    mes = request.args.get('mes', '')
    db = get_db()
    categorias = get_gastos_por_categoria(db, uid(), mes=mes)
    monthly = get_monthly_totals(db, uid())
    return jsonify({
        'categorias': [{'nombre': c['nombre'] or 'Sin categoria', 'total': c['total']} for c in categorias],
        'monthly': monthly,
    })


# --- Gastos ---

@app.route('/gastos')
@login_required
def gastos():
    tipo = request.args.get('tipo', 'todos')
    mes = request.args.get('mes', '')
    db = get_db()
    items = get_gastos(db, uid(), tipo=tipo, mes=mes)
    categorias_list = get_categorias(db)
    total = sum(item['monto'] for item in items)
    return render_template('gastos.html', gastos=items, categorias=categorias_list,
                           filtro_tipo=tipo, filtro_mes=mes, total=total)


@app.route('/gastos/agregar', methods=['POST'])
@login_required
def agregar_gasto():
    form = request.form
    add_gasto(get_db(), uid(), form['descripcion'], form['monto'], form['tipo_gasto'],
              form.get('categoria_id'), form['fecha'], form.get('nota', ''))
    flash('Gasto agregado correctamente', 'success')
    return redirect(url_for('gastos'))


@app.route('/gastos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_gasto(id):
    db = get_db()
    if request.method == 'POST':
        form = request.form
        update_gasto(db, uid(), id, form['descripcion'], form['monto'], form['tipo_gasto'],
                     form.get('categoria_id'), form['fecha'], form.get('nota', ''))
        flash('Gasto actualizado', 'success')
        return redirect(url_for('gastos'))
    gasto = get_gasto(db, uid(), id)
    if not gasto:
        flash('Gasto no encontrado.', 'danger')
        return redirect(url_for('gastos'))
    categorias_list = get_categorias(db)
    return render_template('editar_gasto.html', gasto=gasto, categorias=categorias_list)


@app.route('/gastos/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_gasto(id):
    delete_gasto(get_db(), uid(), id)
    flash('Gasto eliminado', 'warning')
    return redirect(url_for('gastos'))


# --- Ingresos ---

@app.route('/ingresos')
@login_required
def ingresos():
    mes = request.args.get('mes', '')
    db = get_db()
    items = get_ingresos(db, uid(), mes=mes)
    total = sum(item['monto'] for item in items)
    return render_template('ingresos.html', ingresos=items, filtro_mes=mes, total=total)


@app.route('/ingresos/agregar', methods=['POST'])
@login_required
def agregar_ingreso():
    form = request.form
    add_ingreso(get_db(), uid(), form['descripcion'], form['monto'],
                form['fecha'], form.get('nota', ''))
    flash('Ingreso agregado correctamente', 'success')
    return redirect(url_for('ingresos'))


@app.route('/ingresos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_ingreso(id):
    db = get_db()
    if request.method == 'POST':
        form = request.form
        update_ingreso(db, uid(), id, form['descripcion'], form['monto'],
                       form['fecha'], form.get('nota', ''))
        flash('Ingreso actualizado', 'success')
        return redirect(url_for('ingresos'))
    ingreso = get_ingreso(db, uid(), id)
    if not ingreso:
        flash('Ingreso no encontrado.', 'danger')
        return redirect(url_for('ingresos'))
    return render_template('editar_ingreso.html', ingreso=ingreso)


@app.route('/ingresos/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_ingreso(id):
    delete_ingreso(get_db(), uid(), id)
    flash('Ingreso eliminado', 'warning')
    return redirect(url_for('ingresos'))


# --- Inversiones ---

@app.route('/inversiones')
@login_required
def inversiones():
    items = get_inversiones(get_db(), uid())
    return render_template('inversiones.html', inversiones=items)


@app.route('/inversiones/agregar', methods=['POST'])
@login_required
def agregar_inversion():
    form = request.form
    add_inversion(get_db(), uid(), form['descripcion'], form['monto_invertido'],
                  form['fecha_inicio'], form.get('nota', ''))
    flash('Inversion agregada correctamente', 'success')
    return redirect(url_for('inversiones'))


@app.route('/inversiones/<int:id>')
@login_required
def detalle_inversion(id):
    inversion, retornos = get_inversion(get_db(), uid(), id)
    if not inversion:
        flash('Inversion no encontrada', 'danger')
        return redirect(url_for('inversiones'))
    return render_template('detalle_inversion.html', inversion=inversion, retornos=retornos)


@app.route('/inversiones/<int:id>/retorno', methods=['POST'])
@login_required
def agregar_retorno(id):
    form = request.form
    add_retorno(get_db(), uid(), id, form['monto'], form['fecha'], form.get('nota', ''))
    flash('Retorno agregado', 'success')
    return redirect(url_for('detalle_inversion', id=id))


@app.route('/inversiones/<int:id>/cerrar', methods=['POST'])
@login_required
def cerrar_inv(id):
    cerrar_inversion(get_db(), uid(), id)
    flash('Inversion cerrada', 'info')
    return redirect(url_for('detalle_inversion', id=id))


@app.route('/inversiones/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_inversion(id):
    delete_inversion(get_db(), uid(), id)
    flash('Inversion eliminada', 'warning')
    return redirect(url_for('inversiones'))


# --- Diezmo ---

@app.route('/diezmo')
@login_required
def diezmo():
    mes = request.args.get('mes', '')
    ofrenda = request.args.get('ofrenda', '500')
    try:
        ofrenda_monto = float(ofrenda)
    except (ValueError, TypeError):
        ofrenda_monto = 500.0
    data = get_diezmo_data(get_db(), uid(), mes=mes, ofrenda_monto=ofrenda_monto)
    return render_template('diezmo.html', data=data, ofrenda_input=ofrenda_monto)


# --- Offline fallback ---

@app.route('/offline')
def offline():
    return render_template('offline.html')


# --- Filtro Jinja2 para moneda ---

@app.template_filter('moneda')
def moneda_filter(value):
    try:
        val = float(value)
        return f"${val:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


if __name__ == '__main__':
    init_db()
    init_admin()
    # Asegurar que existe el usuario admin con id=1
    from init_admin import ensure_admin_exists
    ensure_admin_exists()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5002)), debug=False)
