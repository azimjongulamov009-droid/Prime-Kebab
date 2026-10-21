import hashlib
import hmac
import json
import os
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory

from main import PRODUCTS, DB_PATH, DELIVERY_ZONES, DELIVERY_FEE, ADMIN_ID, money, price_to_int

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, 'webapp')
app = Flask(__name__, static_folder=WEB_DIR)
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()


def verify_init_data(init_data: str):
    """Telegram Mini App initData tekshiruvi; soxta user_id qabul qilinmaydi."""
    if not BOT_TOKEN or not init_data:
        return None
    try:
        pairs = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received_hash = pairs.pop('hash', '')
        auth_date = int(pairs.get('auth_date', '0'))
        if not received_hash or time.time() - auth_date > 86400 or auth_date > time.time() + 60:
            return None
        data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(pairs.items()))
        secret_key = hmac.new(b'WebAppData', BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calculated, received_hash):
            return None
        user = json.loads(pairs.get('user', '{}'))
        uid = int(user.get('id', 0))
        return {'id': uid, 'name': (user.get('first_name', '') + ' ' + user.get('last_name', '')).strip(), 'username': user.get('username', '')} if uid else None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def send_admin_notice(text):
    if not BOT_TOKEN or not ADMIN_ID:
        return
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    body = json.dumps({'chat_id': ADMIN_ID, 'text': text, 'parse_mode': 'HTML'}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            response.read()
    except Exception:
        app.logger.exception('Admin xabari yuborilmadi')


@app.get('/')
def index():
    return send_from_directory(WEB_DIR, 'index.html')


@app.get('/api/products')
def get_products():
    items = []
    for name, (photo, description, price) in PRODUCTS.items():
        items.append({'name': name, 'photo': photo, 'description': description, 'price': price_to_int(price), 'price_text': price})
    return jsonify({'products': items, 'zones': [{'name': z, 'fee': fee, 'eta': eta} for z, (fee, eta) in DELIVERY_ZONES.items()]})


@app.post('/api/orders')
def create_order():
    payload = request.get_json(silent=True) or {}
    user = verify_init_data(payload.get('initData', ''))
    if not user:
        return jsonify({'error': 'Telegram foydalanuvchisi tasdiqlanmadi. Bot ichidan oching.'}), 401
    items = payload.get('items')
    name = str(payload.get('name') or user['name'] or '').strip()[:100]
    phone = str(payload.get('phone') or '').strip()[:40]
    address = str(payload.get('address') or '').strip()[:500]
    latitude = payload.get('latitude')
    longitude = payload.get('longitude')
    try:
        latitude = float(latitude) if latitude is not None else None
        longitude = float(longitude) if longitude is not None else None
    except (ValueError, TypeError):
        return jsonify({'error': 'Lokatsiya koordinatalari noto‘g‘ri.'}), 400
    if (latitude is None) != (longitude is None):
        return jsonify({'error': 'Lokatsiya to‘liq yuborilmadi. Qayta urinib ko‘ring.'}), 400
    if latitude is not None and not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return jsonify({'error': 'Lokatsiya koordinatalari chegaradan tashqarida.'}), 400
    if latitude is not None and len(address) < 4:
        address = '📍 Mijoz lokatsiya yubordi'
    zone = str(payload.get('zone') or '').strip()
    if not isinstance(items, list) or not items or len(items) > 50:
        return jsonify({'error': 'Savat bo‘sh yoki mahsulotlar soni noto‘g‘ri.'}), 400
    if len(name) < 2 or len(''.join(c for c in phone if c.isdigit())) < 9 or (len(address) < 4 and latitude is None):
        return jsonify({'error': 'Ism, telefon va manzilni to‘liq kiriting.'}), 400
    if zone not in DELIVERY_ZONES:
        return jsonify({'error': 'Yetkazib berish hududini tanlang.'}), 400
    clean_items = {}
    subtotal = 0
    for item in items:
        product = str(item.get('name', ''))
        try:
            qty = int(item.get('qty', 0))
        except (ValueError, TypeError):
            qty = 0
        if product not in PRODUCTS or qty < 1 or qty > 20:
            return jsonify({'error': 'Mahsulot yoki miqdor noto‘g‘ri.'}), 400
        clean_items[product] = clean_items.get(product, 0) + qty
        subtotal += price_to_int(PRODUCTS[product][2]) * qty
    fee, eta = DELIVERY_ZONES[zone]
    total = subtotal + fee
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    product_text = '; '.join(f'{p} x{q}' for p, q in clean_items.items())
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute('''INSERT INTO orders(user_id,product,price,customer_name,phone,created_at,total,address,status,discount,delivery_fee,items_json,eta_minutes,zone,latitude,longitude)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (user['id'], product_text, money(total), name, phone, now, total, f'{zone}: {address}', 'Qabul qilindi', 0, fee, json.dumps(clean_items, ensure_ascii=False), eta, zone, latitude, longitude))
        order_id = cur.lastrowid
        conn.execute('INSERT INTO profiles(user_id,phone) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET phone=excluded.phone', (user['id'], phone))
        conn.commit()
    map_line = f'🗺 Xarita: https://www.google.com/maps?q={latitude},{longitude}' if latitude is not None else '🗺 Lokatsiya yuborilmagan'
    lines = [f'🔴 <b>YANGI MINI APP BUYURTMA #{order_id}</b>', f'👤 {name}', f'📞 {phone}', f'📍 {zone}: {address}', map_line, '']
    lines += [f'• {p} × {q} — {money(price_to_int(PRODUCTS[p][2]) * q)} so‘m' for p, q in clean_items.items()]
    lines += ['', f'🧾 Mahsulotlar: {money(subtotal)} so‘m', f'🛵 Yetkazish: {money(fee)} so‘m', f'💰 JAMI: {money(total)} so‘m', f'⏱ Taxminiy vaqt: {eta} daqiqa', f'🕒 {now}']
    send_admin_notice('\n'.join(lines))
    return jsonify({'ok': True, 'order_id': order_id, 'total': total, 'eta': eta})


if __name__ == '__main__':
    port = int(os.getenv('PORT', '8080'))
    app.run(host='0.0.0.0', port=port, debug=False)
