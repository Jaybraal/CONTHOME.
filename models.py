from datetime import datetime


# --- Categorias ---

def get_categorias(db, tipo_gasto=None):
    query = "SELECT * FROM categorias WHERE 1=1"
    params = []
    if tipo_gasto:
        query += " AND tipo_gasto = ?"
        params.append(tipo_gasto)
    query += " ORDER BY nombre"
    return db.execute(query, params).fetchall()


# --- Gastos ---

def get_gastos(db, tipo='todos', mes=''):
    query = """
        SELECT g.*, c.nombre as categoria_nombre
        FROM gastos g
        LEFT JOIN categorias c ON g.categoria_id = c.id
        WHERE 1=1
    """
    params = []
    if tipo != 'todos':
        query += " AND g.tipo_gasto = ?"
        params.append(tipo)
    if mes:
        query += " AND strftime('%Y-%m', g.fecha) = ?"
        params.append(mes)
    query += " ORDER BY g.fecha DESC"
    return db.execute(query, params).fetchall()


def get_gasto(db, gasto_id):
    return db.execute("SELECT * FROM gastos WHERE id = ?", (gasto_id,)).fetchone()


def add_gasto(db, descripcion, monto, tipo_gasto, categoria_id, fecha, nota=''):
    db.execute(
        "INSERT INTO gastos (descripcion, monto, tipo_gasto, categoria_id, fecha, nota) VALUES (?, ?, ?, ?, ?, ?)",
        (descripcion, float(monto), tipo_gasto, int(categoria_id) if categoria_id else None, fecha, nota)
    )
    db.commit()


def update_gasto(db, gasto_id, descripcion, monto, tipo_gasto, categoria_id, fecha, nota=''):
    db.execute(
        "UPDATE gastos SET descripcion=?, monto=?, tipo_gasto=?, categoria_id=?, fecha=?, nota=? WHERE id=?",
        (descripcion, float(monto), tipo_gasto, int(categoria_id) if categoria_id else None, fecha, nota, gasto_id)
    )
    db.commit()


def delete_gasto(db, gasto_id):
    db.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
    db.commit()


def get_total_gastos(db, mes=''):
    query = "SELECT COALESCE(SUM(monto), 0) as total FROM gastos WHERE 1=1"
    params = []
    if mes:
        query += " AND strftime('%Y-%m', fecha) = ?"
        params.append(mes)
    return db.execute(query, params).fetchone()['total']


# --- Ingresos ---

def get_ingresos(db, mes=''):
    query = "SELECT * FROM ingresos WHERE 1=1"
    params = []
    if mes:
        query += " AND strftime('%Y-%m', fecha) = ?"
        params.append(mes)
    query += " ORDER BY fecha DESC"
    return db.execute(query, params).fetchall()


def get_ingreso(db, ingreso_id):
    return db.execute("SELECT * FROM ingresos WHERE id = ?", (ingreso_id,)).fetchone()


def add_ingreso(db, descripcion, monto, fecha, nota=''):
    db.execute(
        "INSERT INTO ingresos (descripcion, monto, fecha, nota) VALUES (?, ?, ?, ?)",
        (descripcion, float(monto), fecha, nota)
    )
    db.commit()


def update_ingreso(db, ingreso_id, descripcion, monto, fecha, nota=''):
    db.execute(
        "UPDATE ingresos SET descripcion=?, monto=?, fecha=?, nota=? WHERE id=?",
        (descripcion, float(monto), fecha, nota, ingreso_id)
    )
    db.commit()


def delete_ingreso(db, ingreso_id):
    db.execute("DELETE FROM ingresos WHERE id = ?", (ingreso_id,))
    db.commit()


def get_total_ingresos(db, mes=''):
    query = "SELECT COALESCE(SUM(monto), 0) as total FROM ingresos WHERE 1=1"
    params = []
    if mes:
        query += " AND strftime('%Y-%m', fecha) = ?"
        params.append(mes)
    return db.execute(query, params).fetchone()['total']


# --- Inversiones ---

def get_inversiones(db):
    query = """
        SELECT i.*,
               COALESCE(SUM(r.monto), 0) as total_retornos,
               COALESCE(SUM(r.monto), 0) - i.monto_invertido as beneficio_neto,
               CASE WHEN i.monto_invertido > 0
                    THEN ROUND((COALESCE(SUM(r.monto), 0) - i.monto_invertido) / i.monto_invertido * 100, 2)
                    ELSE 0 END as roi
        FROM inversiones i
        LEFT JOIN retornos_inversion r ON i.id = r.inversion_id
        GROUP BY i.id ORDER BY i.fecha_inicio DESC
    """
    return db.execute(query).fetchall()


def get_inversion(db, inversion_id):
    inversion = db.execute("""
        SELECT i.*,
               COALESCE(SUM(r.monto), 0) as total_retornos,
               COALESCE(SUM(r.monto), 0) - i.monto_invertido as beneficio_neto,
               CASE WHEN i.monto_invertido > 0
                    THEN ROUND((COALESCE(SUM(r.monto), 0) - i.monto_invertido) / i.monto_invertido * 100, 2)
                    ELSE 0 END as roi
        FROM inversiones i
        LEFT JOIN retornos_inversion r ON i.id = r.inversion_id
        WHERE i.id = ?
        GROUP BY i.id
    """, (inversion_id,)).fetchone()
    retornos = db.execute(
        "SELECT * FROM retornos_inversion WHERE inversion_id = ? ORDER BY fecha DESC",
        (inversion_id,)
    ).fetchall()
    return inversion, retornos


def add_inversion(db, descripcion, monto_invertido, fecha_inicio, nota=''):
    db.execute(
        "INSERT INTO inversiones (descripcion, monto_invertido, fecha_inicio, nota) VALUES (?, ?, ?, ?)",
        (descripcion, float(monto_invertido), fecha_inicio, nota)
    )
    db.commit()


def add_retorno(db, inversion_id, monto, fecha, nota=''):
    db.execute(
        "INSERT INTO retornos_inversion (inversion_id, monto, fecha, nota) VALUES (?, ?, ?, ?)",
        (inversion_id, float(monto), fecha, nota)
    )
    db.commit()


def cerrar_inversion(db, inversion_id):
    db.execute("UPDATE inversiones SET estado = 'cerrada' WHERE id = ?", (inversion_id,))
    db.commit()


def delete_inversion(db, inversion_id):
    db.execute("DELETE FROM inversiones WHERE id = ?", (inversion_id,))
    db.commit()


# --- Diezmo / Ofrenda ---

def get_diezmo_data(db, mes='', ofrenda_monto=500.0):
    if not mes:
        mes = datetime.now().strftime('%Y-%m')

    total_ingresos = db.execute(
        "SELECT COALESCE(SUM(monto), 0) as total FROM ingresos WHERE strftime('%Y-%m', fecha) = ?",
        (mes,)
    ).fetchone()['total']

    total_retornos = db.execute(
        "SELECT COALESCE(SUM(r.monto), 0) as total FROM retornos_inversion r WHERE strftime('%Y-%m', r.fecha) = ?",
        (mes,)
    ).fetchone()['total']

    base_calculo = total_ingresos + total_retornos
    diezmo = round(base_calculo * 0.10, 2)
    ofrenda = round(float(ofrenda_monto), 2)
    total_dar = round(diezmo + ofrenda, 2)
    restante = round(base_calculo - total_dar, 2)

    return {
        'mes': mes,
        'total_ingresos': total_ingresos,
        'total_retornos': total_retornos,
        'base_calculo': base_calculo,
        'diezmo': diezmo,
        'ofrenda': ofrenda,
        'total_dar': total_dar,
        'restante': restante,
    }


# --- Dashboard ---

def get_dashboard_summary(db, mes=''):
    if not mes:
        mes = datetime.now().strftime('%Y-%m')

    total_ingresos = get_total_ingresos(db, mes=mes)
    total_gastos = get_total_gastos(db, mes=mes)
    balance = total_ingresos - total_gastos

    diezmo_data = get_diezmo_data(db, mes=mes)

    inversiones_activas = db.execute(
        "SELECT COUNT(*) as count, COALESCE(SUM(monto_invertido), 0) as total FROM inversiones WHERE estado = 'activa'"
    ).fetchone()

    return {
        'mes': mes,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'balance': balance,
        'diezmo': diezmo_data,
        'inversiones_activas': inversiones_activas['count'],
        'total_invertido': inversiones_activas['total'],
    }


def get_gastos_por_categoria(db, mes=''):
    if not mes:
        mes = datetime.now().strftime('%Y-%m')
    query = """
        SELECT c.nombre, SUM(g.monto) as total
        FROM gastos g
        LEFT JOIN categorias c ON g.categoria_id = c.id
        WHERE strftime('%Y-%m', g.fecha) = ?
        GROUP BY c.nombre
        ORDER BY total DESC
    """
    return db.execute(query, (mes,)).fetchall()


def get_monthly_totals(db, months=6):
    results = []
    now = datetime.now()
    for i in range(months - 1, -1, -1):
        month = now.month - i
        year = now.year
        while month <= 0:
            month += 12
            year -= 1
        mes = f"{year:04d}-{month:02d}"
        ingresos = get_total_ingresos(db, mes=mes)
        gastos = get_total_gastos(db, mes=mes)
        results.append({'mes': mes, 'ingresos': ingresos, 'gastos': gastos})
    return results
