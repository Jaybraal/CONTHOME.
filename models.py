import calendar
from datetime import datetime, date


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

def get_gastos(db, usuario_id, tipo='todos', mes='', fecha_desde='', fecha_hasta=''):
    query = """
        SELECT g.*, c.nombre as categoria_nombre
        FROM gastos g
        LEFT JOIN categorias c ON g.categoria_id = c.id
        WHERE g.usuario_id = ?
    """
    params = [usuario_id]
    if tipo != 'todos':
        query += " AND g.tipo_gasto = ?"
        params.append(tipo)
    if fecha_desde and fecha_hasta:
        query += " AND g.fecha BETWEEN ? AND ?"
        params.extend([fecha_desde, fecha_hasta])
    elif mes:
        query += " AND strftime('%Y-%m', g.fecha) = ?"
        params.append(mes)
    query += " ORDER BY g.fecha DESC"
    return db.execute(query, params).fetchall()


def get_gasto(db, usuario_id, gasto_id):
    return db.execute(
        "SELECT * FROM gastos WHERE id = ? AND usuario_id = ?",
        (gasto_id, usuario_id)
    ).fetchone()


def add_gasto(db, usuario_id, descripcion, monto, tipo_gasto, categoria_id, fecha, nota=''):
    db.execute(
        "INSERT INTO gastos (usuario_id, descripcion, monto, tipo_gasto, categoria_id, fecha, nota) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (usuario_id, descripcion, float(monto), tipo_gasto, int(categoria_id) if categoria_id else None, fecha, nota)
    )
    db.commit()


def update_gasto(db, usuario_id, gasto_id, descripcion, monto, tipo_gasto, categoria_id, fecha, nota=''):
    db.execute(
        "UPDATE gastos SET descripcion=?, monto=?, tipo_gasto=?, categoria_id=?, fecha=?, nota=? WHERE id=? AND usuario_id=?",
        (descripcion, float(monto), tipo_gasto, int(categoria_id) if categoria_id else None, fecha, nota, gasto_id, usuario_id)
    )
    db.commit()


def delete_gasto(db, usuario_id, gasto_id):
    db.execute("DELETE FROM gastos WHERE id = ? AND usuario_id = ?", (gasto_id, usuario_id))
    db.commit()


def get_total_gastos(db, usuario_id, mes=''):
    query = "SELECT COALESCE(SUM(monto), 0) as total FROM gastos WHERE usuario_id = ?"
    params = [usuario_id]
    if mes:
        query += " AND strftime('%Y-%m', fecha) = ?"
        params.append(mes)
    return db.execute(query, params).fetchone()['total']


# --- Ingresos ---

def get_ingresos(db, usuario_id, mes='', fecha_desde='', fecha_hasta=''):
    query = "SELECT * FROM ingresos WHERE usuario_id = ?"
    params = [usuario_id]
    if fecha_desde and fecha_hasta:
        query += " AND fecha BETWEEN ? AND ?"
        params.extend([fecha_desde, fecha_hasta])
    elif mes:
        query += " AND strftime('%Y-%m', fecha) = ?"
        params.append(mes)
    query += " ORDER BY fecha DESC"
    return db.execute(query, params).fetchall()


def get_ingreso(db, usuario_id, ingreso_id):
    return db.execute(
        "SELECT * FROM ingresos WHERE id = ? AND usuario_id = ?",
        (ingreso_id, usuario_id)
    ).fetchone()


def add_ingreso(db, usuario_id, descripcion, monto, fecha, nota=''):
    db.execute(
        "INSERT INTO ingresos (usuario_id, descripcion, monto, fecha, nota) VALUES (?, ?, ?, ?, ?)",
        (usuario_id, descripcion, float(monto), fecha, nota)
    )
    db.commit()


def update_ingreso(db, usuario_id, ingreso_id, descripcion, monto, fecha, nota=''):
    db.execute(
        "UPDATE ingresos SET descripcion=?, monto=?, fecha=?, nota=? WHERE id=? AND usuario_id=?",
        (descripcion, float(monto), fecha, nota, ingreso_id, usuario_id)
    )
    db.commit()


def delete_ingreso(db, usuario_id, ingreso_id):
    db.execute("DELETE FROM ingresos WHERE id = ? AND usuario_id = ?", (ingreso_id, usuario_id))
    db.commit()


def get_total_ingresos(db, usuario_id, mes=''):
    query = "SELECT COALESCE(SUM(monto), 0) as total FROM ingresos WHERE usuario_id = ?"
    params = [usuario_id]
    if mes:
        query += " AND strftime('%Y-%m', fecha) = ?"
        params.append(mes)
    return db.execute(query, params).fetchone()['total']


# --- Inversiones ---

def get_inversiones(db, usuario_id):
    query = """
        SELECT i.*,
               COALESCE(SUM(r.monto), 0) as total_retornos,
               COALESCE(SUM(r.monto), 0) - i.monto_invertido as beneficio_neto,
               CASE WHEN i.monto_invertido > 0
                    THEN ROUND((COALESCE(SUM(r.monto), 0) - i.monto_invertido) / i.monto_invertido * 100, 2)
                    ELSE 0 END as roi
        FROM inversiones i
        LEFT JOIN retornos_inversion r ON i.id = r.inversion_id
        WHERE i.usuario_id = ?
        GROUP BY i.id ORDER BY i.fecha_inicio DESC
    """
    return db.execute(query, (usuario_id,)).fetchall()


def get_inversion(db, usuario_id, inversion_id):
    inversion = db.execute("""
        SELECT i.*,
               COALESCE(SUM(r.monto), 0) as total_retornos,
               COALESCE(SUM(r.monto), 0) - i.monto_invertido as beneficio_neto,
               CASE WHEN i.monto_invertido > 0
                    THEN ROUND((COALESCE(SUM(r.monto), 0) - i.monto_invertido) / i.monto_invertido * 100, 2)
                    ELSE 0 END as roi
        FROM inversiones i
        LEFT JOIN retornos_inversion r ON i.id = r.inversion_id
        WHERE i.id = ? AND i.usuario_id = ?
        GROUP BY i.id
    """, (inversion_id, usuario_id)).fetchone()
    retornos = db.execute("""
        SELECT r.* FROM retornos_inversion r
        JOIN inversiones i ON r.inversion_id = i.id
        WHERE r.inversion_id = ? AND i.usuario_id = ?
        ORDER BY r.fecha DESC
    """, (inversion_id, usuario_id)).fetchall()
    return inversion, retornos


def add_inversion(db, usuario_id, descripcion, monto_invertido, fecha_inicio, nota=''):
    db.execute(
        "INSERT INTO inversiones (usuario_id, descripcion, monto_invertido, fecha_inicio, nota) VALUES (?, ?, ?, ?, ?)",
        (usuario_id, descripcion, float(monto_invertido), fecha_inicio, nota)
    )
    db.commit()


def add_retorno(db, usuario_id, inversion_id, monto, fecha, nota=''):
    inv = db.execute("SELECT id FROM inversiones WHERE id = ? AND usuario_id = ?", (inversion_id, usuario_id)).fetchone()
    if not inv:
        return
    db.execute(
        "INSERT INTO retornos_inversion (inversion_id, monto, fecha, nota) VALUES (?, ?, ?, ?)",
        (inversion_id, float(monto), fecha, nota)
    )
    db.commit()


def cerrar_inversion(db, usuario_id, inversion_id):
    db.execute(
        "UPDATE inversiones SET estado = 'cerrada' WHERE id = ? AND usuario_id = ?",
        (inversion_id, usuario_id)
    )
    db.commit()


def delete_inversion(db, usuario_id, inversion_id):
    db.execute("DELETE FROM inversiones WHERE id = ? AND usuario_id = ?", (inversion_id, usuario_id))
    db.commit()


# --- Diezmo / Ofrenda ---

def get_diezmo_data(db, usuario_id, mes='', ofrenda_monto=500.0):
    if not mes:
        mes = datetime.now().strftime('%Y-%m')

    total_ingresos = db.execute(
        "SELECT COALESCE(SUM(monto), 0) as total FROM ingresos WHERE usuario_id = ? AND strftime('%Y-%m', fecha) = ?",
        (usuario_id, mes)
    ).fetchone()['total']

    total_retornos = db.execute(
        """SELECT COALESCE(SUM(r.monto), 0) as total
           FROM retornos_inversion r
           JOIN inversiones i ON r.inversion_id = i.id
           WHERE i.usuario_id = ? AND strftime('%Y-%m', r.fecha) = ?""",
        (usuario_id, mes)
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

def get_dashboard_summary(db, usuario_id, mes='', ofrenda_monto=500.0):
    if not mes:
        mes = datetime.now().strftime('%Y-%m')

    total_ingresos = get_total_ingresos(db, usuario_id, mes=mes)
    total_gastos = get_total_gastos(db, usuario_id, mes=mes)
    balance = total_ingresos - total_gastos

    diezmo_data = get_diezmo_data(db, usuario_id, mes=mes, ofrenda_monto=ofrenda_monto)

    inversiones_activas = db.execute(
        "SELECT COUNT(*) as count, COALESCE(SUM(monto_invertido), 0) as total FROM inversiones WHERE usuario_id = ? AND estado = 'activa'",
        (usuario_id,)
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


def get_gastos_por_categoria(db, usuario_id, mes=''):
    if not mes:
        mes = datetime.now().strftime('%Y-%m')
    query = """
        SELECT c.nombre, SUM(g.monto) as total
        FROM gastos g
        LEFT JOIN categorias c ON g.categoria_id = c.id
        WHERE g.usuario_id = ? AND strftime('%Y-%m', g.fecha) = ?
        GROUP BY c.nombre
        ORDER BY total DESC
    """
    return db.execute(query, (usuario_id, mes)).fetchall()


def get_monthly_totals(db, usuario_id, months=6):
    results = []
    now = datetime.now()
    for i in range(months - 1, -1, -1):
        month = now.month - i
        year = now.year
        while month <= 0:
            month += 12
            year -= 1
        mes = f"{year:04d}-{month:02d}"
        ingresos = get_total_ingresos(db, usuario_id, mes=mes)
        gastos = get_total_gastos(db, usuario_id, mes=mes)
        results.append({'mes': mes, 'ingresos': ingresos, 'gastos': gastos})
    return results


# --- Recordatorios ---

def get_recordatorios(db, usuario_id):
    return db.execute(
        "SELECT * FROM recordatorios WHERE usuario_id = ? ORDER BY dia_mes",
        (usuario_id,)
    ).fetchall()


def get_recordatorios_proximos(db, usuario_id, dias=3):
    today = date.today()
    all_recs = get_recordatorios(db, usuario_id)
    proximos = []
    for r in all_recs:
        if not r['activo']:
            continue
        recurrencia = r['recurrencia'] if r['recurrencia'] else 'mensual'

        if recurrencia == 'unico':
            fe = r['fecha_especifica']
            if not fe:
                continue
            try:
                target = date.fromisoformat(fe)
            except ValueError:
                continue
            diff = (target - today).days
            if 0 <= diff <= dias:
                proximos.append({
                    'id': r['id'],
                    'descripcion': r['descripcion'],
                    'monto': r['monto'],
                    'tipo': r['tipo'],
                    'dia_mes': r['dia_mes'],
                    'recurrencia': recurrencia,
                    'fecha_especifica': fe,
                    'dias_restantes': diff,
                    'fecha': target.isoformat(),
                })
        else:
            dia = r['dia_mes']
            for delta_months in [0, 1]:
                month = today.month + delta_months
                year = today.year
                if month > 12:
                    month -= 12
                    year += 1
                max_day = calendar.monthrange(year, month)[1]
                actual_day = min(dia, max_day)
                try:
                    target = date(year, month, actual_day)
                except ValueError:
                    continue
                diff = (target - today).days
                if 0 <= diff <= dias:
                    proximos.append({
                        'id': r['id'],
                        'descripcion': r['descripcion'],
                        'monto': r['monto'],
                        'tipo': r['tipo'],
                        'dia_mes': r['dia_mes'],
                        'recurrencia': recurrencia,
                        'fecha_especifica': None,
                        'dias_restantes': diff,
                        'fecha': target.isoformat(),
                    })
                    break
    return proximos


def add_recordatorio(db, usuario_id, descripcion, monto, dia_mes, tipo='gasto',
                     recurrencia='mensual', fecha_especifica=None):
    db.execute(
        """INSERT INTO recordatorios
           (usuario_id, descripcion, monto, dia_mes, tipo, recurrencia, fecha_especifica)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (usuario_id, descripcion, float(monto) if monto else 0.0,
         int(dia_mes) if dia_mes else 1, tipo, recurrencia, fecha_especifica or None)
    )
    db.commit()


def toggle_recordatorio(db, usuario_id, rec_id):
    rec = db.execute(
        "SELECT activo FROM recordatorios WHERE id = ? AND usuario_id = ?",
        (rec_id, usuario_id)
    ).fetchone()
    if rec:
        db.execute(
            "UPDATE recordatorios SET activo = ? WHERE id = ? AND usuario_id = ?",
            (0 if rec['activo'] else 1, rec_id, usuario_id)
        )
        db.commit()


def delete_recordatorio(db, usuario_id, rec_id):
    db.execute("DELETE FROM recordatorios WHERE id = ? AND usuario_id = ?", (rec_id, usuario_id))
    db.commit()
