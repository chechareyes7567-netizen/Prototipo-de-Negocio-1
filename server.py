"""API de pedidos de Entre Bocados. WSGI: gunicorn server:app.

DATABASE_URL = PostgreSQL in production. Locally, sqlite stores data in ./data/orders.sqlite3.
A submission is pending confirmation until the business checks the WhatsApp message.
"""
import hmac
import json
import os
import re
import sqlite3
import threading
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import parse_qs, unquote
from zoneinfo import ZoneInfo

SQLITE_PATH = Path(__file__).resolve().parent / 'data' / 'orders.sqlite3'
GUATEMALA = ZoneInfo('America/Guatemala')
ALLOWED_STATUSES = {'pendiente_confirmacion', 'confirmado', 'cancelado'}
SCHEMA_LOCK = threading.Lock()
SCHEMA_READY = False
RATE_LOCK = threading.Lock()
RECENT_IPS = defaultdict(deque)

BASE_PRODUCTS = {
    'rec-barbacoa': ('Tortrix Barbacoa', 250),
    'rec-chicharrones': ('Chicharrones', 500),
    'rec-limon': ('Tortrix Limón', 250),
    'rec-picante': ('Tortrix Picante', 250),
    'post-sponch': ('Sponch', 1000),
    'post-pinguinos': ('Pingüinos', 1000),
    'post-gansitos': ('Gansitos', 800),
    'post-donitas': ('Donitas', 1000),
    'post-submarinos': ('Submarinos', 800),
    'carte-clasica': ('La Hamburguesa Clásica', 3000),
    'carte-torito': ('Torito burger', 3200),
    'carte-burrito': ('Burrito de la Casa', 3000),
    'carte-favorita': ('La favorita', 3000),
    'carte-brunch': ('La Brunch', 3200),
    'carte-italiana': ('La italiana', 3300),
    'carte-dieta': ('Dieta pechuga de pollo', 3500),
}
BREAKFAST = {
    'des-especiales': ('Panqueques especiales', 2500),
    'des-omelets': ('Omelets', 2500),
    'des-burritos': ('Burritos', 2000),
    'des-chilaquiles': ('Chilaquiles', 2500),
    'des-panqueques': ('Panqueques', 2500),
    'des-longaniza': ('Chapín con longaniza', 2800),
    'des-dobladas': ('Dobladas Francesas', 2700),
    'des-pupuseno': ('Pupuseño', 2800),
    'des-waffles': ('Waffles', 2700),
    'des-caldo-huevo': ('Caldo de Huevo', 2500),
    'des-huevos-arroz': ('Huevos con arroz revueltos', 2500),
}
SMOOTHIES = {
    'smoothie-fresa': ('Licuado de fresa', {'agua': 800, 'leche': 1200}),
    'smoothie-banano': ('Licuado de banano', {'leche': 1200}),
    'smoothie-papaya': ('Licuado de papaya', {'agua': 1200, 'leche': 1500}),
    'smoothie-mango': ('Licuado de mango', {'agua': 1200}),
    'smoothie-pina': ('Licuado de piña', {'agua': 1000}),
}
SUGAR = {'sin': 'Sin azúcar', 'poca': 'Poca azúcar', 'media': 'Azúcar media', 'mucha': 'Mucha azúcar'}
SIDES = {'Arroz', 'Papas salteadas', 'Frijol'}
EGGS = {'revueltos': 'Huevos revueltos simples', 'estrellados': 'Huevos estrellados', 'torta': 'Huevos en torta'}


class ValidationError(Exception):
    pass


def money_cents(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
            raise ValueError
        return int(amount * 100)
    except (ValueError, InvalidOperation, TypeError):
        raise ValidationError('El monto en efectivo debe tener como máximo dos decimales.')


def product_for(item_id, local_now):
    if item_id in BASE_PRODUCTS:
        name, cents = BASE_PRODUCTS[item_id]
        return {'id': item_id, 'name': name, 'unit_cents': cents}
    if local_now.hour < 11 and item_id in BREAKFAST:
        name, cents = BREAKFAST[item_id]
        return {'id': item_id, 'name': name, 'unit_cents': cents}
    bits = item_id.split('::')
    if len(bits) == 3 and bits[0] in SMOOTHIES:
        base, liquid, sugar = bits
        name, prices = SMOOTHIES[base]
        if liquid in prices and sugar in SUGAR:
            return {'id': item_id, 'name': name, 'unit_cents': prices[liquid],
                    'options': ('Con leche' if liquid == 'leche' else 'Con agua') + ' · ' + SUGAR[sugar]}
    if local_now.hour < 11 and len(bits) == 3 and bits[0] == 'des-chapin':
        _, egg, term = bits
        if egg in EGGS and (term in ('bien', 'medio') if egg == 'estrellados' else term == ''):
            chosen = EGGS[egg]
            if egg == 'estrellados':
                chosen += ' (' + ('bien cocidos' if term == 'bien' else 'término medio') + ')'
            return {'id': item_id, 'name': 'Chapín', 'unit_cents': 2200, 'options': chosen}
    today = local_now.strftime('%Y-%m-%d')
    if local_now.hour >= 11 and len(bits) == 3 and bits[0] == 'daily-' + today + '-lunch':
        sides = [unquote(part) for part in bits[1:]]
        if len(set(sides)) == 2 and set(sides).issubset(SIDES):
            return {'id': item_id, 'name': 'Arroz con pollo', 'unit_cents': 3000,
                    'options': 'Guarniciones: ' + ' y '.join(sides)}
    raise ValidationError('Hay un producto o una variante que no está disponible. Actualiza el menú y revisa el pedido.')


def required_str(data, key, limit):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValidationError('Completa el campo: ' + key)
    return value.strip()


def validate_order(data, at=None):
    if not isinstance(data, dict):
        raise ValidationError('El pedido debe ser un objeto JSON.')
    at = (at or datetime.now(timezone.utc)).astimezone(GUATEMALA)
    raw_id = required_str(data, 'request_id', 36)
    try:
        request_id = str(uuid.UUID(raw_id, version=4))
    except (ValueError, AttributeError):
        raise ValidationError('El identificador del pedido no es válido.')
    if raw_id != request_id:
        raise ValidationError('El identificador del pedido no es válido.')
    site_id = required_str(data, 'site_id', 40)
    allowed_sites = {s.strip() for s in os.getenv('ALLOWED_SITE_IDS', 'entre-bocados').split(',') if s.strip()}
    if site_id not in allowed_sites:
        raise ValidationError('El sitio no está configurado para registrar pedidos.')
    customer = required_str(data, 'customer_name', 80)
    phone = required_str(data, 'phone', 25)
    if not re.fullmatch(r'[+() 0-9-]{7,25}', phone):
        raise ValidationError('El teléfono no es válido.')
    order_name = required_str(data, 'order_name', 80)
    fulfillment = required_str(data, 'fulfillment', 12)
    if fulfillment not in ('pickup', 'delivery'):
        raise ValidationError('Selecciona una modalidad de entrega.')
    address, delivery_time = None, None
    if fulfillment == 'delivery':
        address = required_str(data, 'address', 180)
        delivery_time = required_str(data, 'delivery_time', 5)
        if not re.fullmatch(r'\d{2}:\d{2}', delivery_time) or not '11:00' <= delivery_time <= '17:00':
            raise ValidationError('La hora de entrega debe estar entre 11:00 y 17:00.')
    payment = required_str(data, 'payment_method', 8)
    if payment not in ('cash', 'transfer'):
        raise ValidationError('Selecciona una forma de pago.')
    notes = data.get('notes', '')
    if not isinstance(notes, str) or len(notes) > 300:
        raise ValidationError('Las indicaciones deben tener hasta 300 caracteres.')
    raw_items = data.get('items')
    if not isinstance(raw_items, list) or not 1 <= len(raw_items) <= 40:
        raise ValidationError('El pedido debe incluir entre 1 y 40 productos diferentes.')
    seen, items, total = set(), [], 0
    for entry in raw_items:
        if not isinstance(entry, dict) or not isinstance(entry.get('id'), str):
            raise ValidationError('Un producto no es válido.')
        item_id = entry['id']
        quantity = entry.get('quantity')
        if item_id in seen or len(item_id) > 150 or not isinstance(quantity, int) or isinstance(quantity, bool) or not 1 <= quantity <= 99:
            raise ValidationError('Hay una cantidad o un producto repetido que no es válido.')
        seen.add(item_id)
        product = product_for(item_id, at)
        product['quantity'] = quantity
        product['line_cents'] = product['unit_cents'] * quantity
        items.append(product)
        total += product['line_cents']
    if total > 500000:
        raise ValidationError('El pedido supera el límite; comunícate directamente por WhatsApp.')
    cash_cents = None
    if payment == 'cash':
        cash_cents = money_cents(data.get('cash_amount'))
        if cash_cents < total or cash_cents > 1000000:
            raise ValidationError('El efectivo indicado debe cubrir el subtotal y ser menor a Q 10,000.')
    return {'id': request_id, 'source_site': site_id, 'customer_name': customer, 'phone': phone,
            'order_name': order_name, 'fulfillment': fulfillment, 'address': address,
            'delivery_time': delivery_time, 'payment_method': payment, 'cash_cents': cash_cents,
            'notes': notes.strip(), 'items_json': json.dumps(items, ensure_ascii=False), 'subtotal_cents': total,
            'created_at': datetime.now(timezone.utc).isoformat(), 'status': 'pendiente_confirmacion'}


FIELDS = ('id', 'source_site', 'customer_name', 'phone', 'order_name', 'fulfillment', 'address',
          'delivery_time', 'payment_method', 'cash_cents', 'notes', 'items_json', 'subtotal_cents',
          'created_at', 'status')


def connect():
    url = os.getenv('DATABASE_URL', '').strip()
    if url:
        import psycopg
        return psycopg.connect(url, connect_timeout=10)
    if os.getenv('RENDER'):
        raise RuntimeError('Configura DATABASE_URL: el disco del servicio gratuito no conserva pedidos.')
    SQLITE_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(SQLITE_PATH, timeout=15)


def execute(conn, sql, params=()):
    return conn.execute(sql.replace('?', '%s') if os.getenv('DATABASE_URL') else sql, params)


def ensure_schema(conn):
    global SCHEMA_READY
    if SCHEMA_READY:
        return
    with SCHEMA_LOCK:
        if SCHEMA_READY:
            return
        execute(conn, '''CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY, source_site TEXT NOT NULL, customer_name TEXT NOT NULL,
            phone TEXT NOT NULL, order_name TEXT NOT NULL, fulfillment TEXT NOT NULL,
            address TEXT, delivery_time TEXT, payment_method TEXT NOT NULL, cash_cents INTEGER,
            notes TEXT NOT NULL, items_json TEXT NOT NULL, subtotal_cents INTEGER NOT NULL,
            created_at TEXT NOT NULL, status TEXT NOT NULL)''')
        execute(conn, 'CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at)')
        conn.commit()
        SCHEMA_READY = True


def as_dict(row):
    order = dict(zip(FIELDS, row))
    order['items'] = json.loads(order.pop('items_json'))
    return order


def response(start, status, body, headers=()):
    data = json.dumps(body, ensure_ascii=False).encode('utf-8')
    start(status, [('Content-Type', 'application/json; charset=utf-8'), ('Content-Length', str(len(data))),
                   ('Cache-Control', 'no-store'), ('X-Content-Type-Options', 'nosniff'), *headers])
    return [data]


def request_json(environ):
    if not environ.get('CONTENT_TYPE', '').startswith('application/json'):
        raise ValidationError('Envía el pedido como JSON.')
    size = int(environ.get('CONTENT_LENGTH') or 0)
    if size < 2 or size > 32768:
        raise ValidationError('El pedido tiene un tamaño inválido.')
    try:
        return json.loads(environ['wsgi.input'].read(size))
    except (ValueError, UnicodeDecodeError):
        raise ValidationError('El contenido del pedido no es JSON válido.')


def is_admin(environ):
    secret = os.getenv('ADMIN_TOKEN', '')
    value = environ.get('HTTP_AUTHORIZATION', '')
    return len(secret) >= 32 and value.startswith('Bearer ') and hmac.compare_digest(secret, value[7:])


def rate_ok(environ):
    client = environ.get('REMOTE_ADDR', 'unknown')
    now = time.monotonic()
    with RATE_LOCK:
        entries = RECENT_IPS[client]
        while entries and entries[0] < now - 300:
            entries.popleft()
        if len(entries) >= 100:
            return False
        entries.append(now)
    return True


def app(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET').upper()
    origin = environ.get('HTTP_ORIGIN', '')
    allowlist = {o.strip().rstrip('/') for o in os.getenv('ALLOWED_ORIGINS', '').split(',') if o.strip()}
    headers = [('Access-Control-Allow-Origin', origin), ('Vary', 'Origin')] if origin in allowlist else []
    if path == '/health' and method == 'GET':
        try:
            conn = connect()
            try:
                ensure_schema(conn)
                execute(conn, 'SELECT 1')
            finally:
                conn.close()
        except Exception:
            return response(start_response, '503 Service Unavailable', {'ok': False})
        return response(start_response, '200 OK', {'ok': True})
    if path == '/admin' and method == 'GET':
        page = (Path(__file__).resolve().parent / 'admin.html').read_bytes()
        start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8'),
                     ('Content-Length', str(len(page))), ('Cache-Control', 'no-store'),
                     ('X-Content-Type-Options', 'nosniff')])
        return [page]
    if not path.startswith('/api/'):
        return response(start_response, '404 Not Found', {'error': 'Ruta no encontrada.'})
    if origin and origin not in allowlist:
        return response(start_response, '403 Forbidden', {'error': 'Origen no autorizado.'})
    if method == 'OPTIONS' and origin in allowlist:
        start_response('204 No Content', [*headers, ('Access-Control-Allow-Methods', 'POST, GET, PATCH, DELETE, OPTIONS'),
                       ('Access-Control-Allow-Headers', 'Content-Type, Authorization'), ('Access-Control-Max-Age', '600')])
        return [b'']
    try:
        if path.startswith('/api/admin/') and not is_admin(environ):
            return response(start_response, '401 Unauthorized', {'error': 'Acceso privado no autorizado.'}, headers)
        if path == '/api/orders' and method == 'POST':
            if not rate_ok(environ):
                return response(start_response, '429 Too Many Requests', {'error': 'Demasiados intentos; prueba más tarde.'}, headers)
            data = validate_order(request_json(environ))
            conn = connect()
            try:
                ensure_schema(conn)
                existing = execute(conn, 'SELECT ' + ','.join(FIELDS) + ' FROM orders WHERE id = ?', (data['id'],)).fetchone()
                if existing:
                    row = as_dict(existing)
                    compare_keys = ('source_site', 'customer_name', 'phone', 'order_name', 'fulfillment',
                                    'address', 'delivery_time', 'payment_method', 'cash_cents',
                                    'notes', 'subtotal_cents')
                    if any(row[key] != data[key] for key in compare_keys) or row['items'] != json.loads(data['items_json']):
                        return response(start_response, '409 Conflict', {'error': 'El identificador ya corresponde a otro pedido.'}, headers)
                    return response(start_response, '200 OK', {'order_id': data['id'], 'subtotal_cents': row['subtotal_cents'], 'status': row['status']}, headers)
                execute(conn, 'INSERT INTO orders (' + ','.join(FIELDS) + ') VALUES (' + ','.join('?' for _ in FIELDS) + ')', tuple(data[k] for k in FIELDS))
                conn.commit()
            finally:
                conn.close()
            return response(start_response, '201 Created', {'order_id': data['id'], 'subtotal_cents': data['subtotal_cents'], 'status': data['status']}, headers)
        if path == '/api/admin/orders' and method == 'GET':
            qs = parse_qs(environ.get('QUERY_STRING', ''))
            limit = min(max(int(qs.get('limit', ['50'])[0]), 1), 100)
            offset = max(int(qs.get('offset', ['0'])[0]), 0)
            conn = connect()
            try:
                ensure_schema(conn)
                rows = execute(conn, 'SELECT ' + ','.join(FIELDS) + ' FROM orders ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, offset)).fetchall()
            finally:
                conn.close()
            return response(start_response, '200 OK', {'orders': [as_dict(row) for row in rows]}, headers)
        if path == '/api/admin/orders' and method == 'DELETE':
            incoming = request_json(environ)
            if not isinstance(incoming, dict) or incoming.get('confirmation') != 'BORRAR TODOS LOS PEDIDOS':
                raise ValidationError('Escribe BORRAR TODOS LOS PEDIDOS para confirmar el borrado.')
            conn = connect()
            try:
                ensure_schema(conn)
                deleted = execute(conn, 'DELETE FROM orders').rowcount
                conn.commit()
            finally:
                conn.close()
            return response(start_response, '200 OK', {'deleted': deleted}, headers)
        if path == '/api/admin/summary' and method == 'GET':
            conn = connect()
            try:
                ensure_schema(conn)
                rows = execute(conn, 'SELECT status, source_site, COUNT(*), SUM(subtotal_cents) FROM orders GROUP BY status, source_site').fetchall()
                confirmed = execute(conn, 'SELECT items_json FROM orders WHERE status = ?', ('confirmado',)).fetchall()
            finally:
                conn.close()
            popular = {}
            for (items_json,) in confirmed:
                for item in json.loads(items_json):
                    entry = popular.setdefault(item['name'], {'quantity': 0, 'total_cents': 0})
                    entry['quantity'] += item['quantity']
                    entry['total_cents'] += item['line_cents']
            return response(start_response, '200 OK', {
                'by_status_and_site': [{'status': status, 'site': site, 'count': n, 'subtotal_cents': cents} for status, site, n, cents in rows],
                'confirmed_products': popular,
            }, headers)
        if path.startswith('/api/admin/orders/') and method == 'PATCH':
            order_id = path.removeprefix('/api/admin/orders/')
            try:
                uuid.UUID(order_id, version=4)
            except ValueError:
                raise ValidationError('El identificador del pedido no es válido.')
            incoming = request_json(environ)
            status = incoming.get('status') if isinstance(incoming, dict) else None
            if status not in ALLOWED_STATUSES:
                raise ValidationError('El estado del pedido no es válido.')
            conn = connect()
            try:
                ensure_schema(conn)
                row = execute(conn, 'SELECT id FROM orders WHERE id = ?', (order_id,)).fetchone()
                if not row:
                    return response(start_response, '404 Not Found', {'error': 'Pedido no encontrado.'}, headers)
                execute(conn, 'UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
                conn.commit()
            finally:
                conn.close()
            return response(start_response, '200 OK', {'order_id': order_id, 'status': status}, headers)
        return response(start_response, '404 Not Found', {'error': 'Ruta no encontrada.'}, headers)
    except ValidationError as error:
        return response(start_response, '400 Bad Request', {'error': str(error)}, headers)
    except (ValueError, TypeError):
        return response(start_response, '400 Bad Request', {'error': 'Parámetro incorrecto.'}, headers)
    except Exception:
        return response(start_response, '503 Service Unavailable', {'error': 'La base de datos no está disponible. Inténtalo de nuevo.'}, headers)
