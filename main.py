import asyncio
import logging
import os
import sys
import sqlite3
from datetime import datetime
from html import escape

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup

import buttons as btn

logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format="%(asctime)s | %(levelname)s | %(message)s")
dp = Dispatcher()

class OrderState(StatesGroup):
    name = State()
    phone = State()
    address = State()
    promo = State()
    feedback = State()
    search = State()
    review = State()
    review_comment = State()

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fastfood.db")

def init_db():
    """Eski baza ma'lumotlarini saqlagan holda jadvallarni yangilaydi."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            product TEXT NOT NULL, price TEXT NOT NULL, customer_name TEXT NOT NULL,
            phone TEXT NOT NULL, created_at TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            username TEXT, message TEXT NOT NULL, created_at TEXT NOT NULL)""")
        conn.execute("CREATE TABLE IF NOT EXISTS profiles (user_id INTEGER PRIMARY KEY, phone TEXT DEFAULT '')")
        conn.execute("CREATE TABLE IF NOT EXISTS cart (user_id INTEGER NOT NULL, product TEXT NOT NULL, quantity INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(user_id, product))")
        conn.execute("CREATE TABLE IF NOT EXISTS favorites (user_id INTEGER NOT NULL, product TEXT NOT NULL, PRIMARY KEY(user_id, product))")
        conn.execute("CREATE TABLE IF NOT EXISTS promo_codes (code TEXT PRIMARY KEY, percent INTEGER NOT NULL, active INTEGER NOT NULL DEFAULT 1)")
        conn.execute("CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, order_id INTEGER, rating INTEGER NOT NULL, comment TEXT, created_at TEXT NOT NULL)")
        conn.execute("INSERT OR IGNORE INTO promo_codes(code, percent, active) VALUES ('WELCOME10', 10, 1)")
        existing = {row[1] for row in conn.execute('PRAGMA table_info(orders)').fetchall()}
        additions = {
            'total': 'INTEGER NOT NULL DEFAULT 0', 'address': "TEXT NOT NULL DEFAULT ''",
            'status': "TEXT NOT NULL DEFAULT 'Qabul qilindi'", 'discount': 'INTEGER NOT NULL DEFAULT 0',
            'delivery_fee': 'INTEGER NOT NULL DEFAULT 0', 'items_json': "TEXT NOT NULL DEFAULT '{}'",
            'courier_id': 'INTEGER NOT NULL DEFAULT 0', 'eta_minutes': 'INTEGER NOT NULL DEFAULT 0', 'zone': "TEXT NOT NULL DEFAULT ''", 'latitude': 'REAL', 'longitude': 'REAL'
        }
        for col, definition in additions.items():
            if col not in existing:
                conn.execute(f'ALTER TABLE orders ADD COLUMN {col} {definition}')
        conn.commit()

init_db()

# Mahsulot nomi: (rasm URL, tavsif, narx)
PRODUCTS = {'Gamburger': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_83_22413e7d.png', "Gamburger\n\nMol go'shti kotleti, bulochka, pomidor, tuzlangan bodring,", '37 000'), 'Yovvoyi burger': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_207_98138d14.jpg', "Yovvoyi burger\n\nYangi burgerning o'ziga xos ta'mini tatib ko'ring!", '43 000'), 'Miks burger': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_208_ca68eb91.jpg', "Miks burger\n\nTurli ta'mlar uyg'unligiga ega taom", '53 000'), 'Tandir lavash': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_65_c8f27ea4.jpg', "Tandir lavash\n\nMazali mol go'shti, tovuq, pomidor, bodring, oq va qizil sous", '47 000'), 'Tandir lavash pishloqli': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_62_436c9302.jpg', "Tandir lavash pishloqli\n\nMazali mol go'shti, tovuq, pishloq, pomidor, bodring, oq va qizil sous", '49 000'), 'Lavash': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_64_2fb5e066.png', "Lavash\n\nMazali mol go'shti, tovuq, pomidor, bodring, oq va qizil sous", '39 000'), 'Lavash pishloqli': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_63_ace954ba.png', "Lavash pishloqli\n\nMazali mol go'shti, tovuq, pishloq, pomidor, bodring, oq va qizil sous", '48 000'), 'Hot-dog (oddiy)': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_126_6bd2f428.png', 'Hot-dog (oddiy)\n\nBulochka, sosiska, kartoshka fri, karam salat, sabzi salat, pomidor', '20 000'), 'Hot-dog (amerikancha)': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_60_2b8770d3.png', 'Hot-dog (amerikancha)\n\nSosiska, aysberg karam, tuzlangan bodring, mayin kartoshka fri,', '33 000'), 'Hot-dog (korolevskiy)': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_61_beaec25a.png', 'Hot-dog (korolevskiy)\n\nBulochka, sosiska x2, kartoshka fri, karam salat, chimchi salati', '25 000'), 'Hot-dog (fransuzcha)': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_59_ed33b292.png', "Hot-dog (fransuzcha)\n\nMol go'shti, pomidor, bodring, salat bargi, oq sous va barbekyu", '35 000'), 'Tovuq baytslari': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_254_7a6ad0c3.png', 'Tovuq baytslari\n\nQarsildoq panirada qovurilgan mayda va shirali tovuq bo‘laklari.', '18 000'), 'Qanotchalar': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_255_6c6bdf59.png', 'Qanotchalar\n\nTashqi tomoni qarsildoq, ichi esa shirali va yumshoq. Maxsus', '27 000'), 'Naggetslar (6 dona)': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_105_c2b605ec.png', "Naggetslar (6 dona)\n\nQarsildoq panirovkali mazali tovuq bo'lakchalari, 6 dona", '22 000'), 'Kotlet': ('https://storage.servisoft.uz/masterkebabmedia/products/2025-01-08_01.52.52.jpg', "Kotlet\n\nMazali va halol mol go'shtidan tayyorlangan kotlet", '16 000'), 'Kartoshka fri': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_107_d9b958a9.png', 'Kartoshka fri\n\nВкусные палочки картофеля, обжаренные в растительном', '18 000'), 'Guruch': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_108_c2a968b6.png', "Guruch\n\nOq guruch va makkajo'xoridan tayyorlangan garnir", '10 000'), 'Kebab taom (mol)': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_80_cd3c674d.jpg', "Kebab taom (mol go'shtli)\n\nMol go'shti, guruch, makkajo'xori, kartoshka, koleslaw, sous", '63 000'), 'Kebab taom (tovuqli)': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_81_e168313d.jpg', "Kebab taom (tovuqli)\n\nTovuq go'shti, guruch, makkajo'xori, kartoshka, karam", '58 000'), 'Pepperoni': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_72_e6d2dc7b.jpg', 'Pepperoni\n\nKolbasa, pomidor, pishloq, pitsa sousi', '94 000'), 'Lesnaya Pitsa': ('https://storage.servisoft.uz/masterkebabmedia/products/product_160_dcff11a1.jpeg', "Lesnaya Pitsa\n\nDudlangan go'sht, qo'ziqorin, qizil piyoz, marinadlangan bodring va", '86 000'), 'Yopiq pitsa': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_251_e1c0f83b.jpg', 'Yopiq pitsa\n\nOltinrang, qarsildoq xamir ichida mazali va shirali nachinka. To‘yimli,', '102 000'), 'Tovuqli pitsa': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_252_22db69b4.jpg', 'Tovuqli pitsa\n\nYumshoq xamir ustida mayin tovuq go‘shti, eritilgan pishloq va', '79 000'), "Go'shtli miks": ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_159_8e5fcaff.jpg', "Go'shtli miks\n\nDudlangan mol go'shti, dudlangan tovuq go'shti, kolbasa va pitsa", '86 000'), 'Master Kebab': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_73_6850a2f9.jpg', "Master Kebab\n\nTovuq go'shti, mol go'shti, ov kolbasa, gamburger sousi, pishloq", '94 000'), 'Pitsa 4 pishloq': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_209_0fc8e01a.jpg', "Pitsa 4 pishloq\n\nPitsa xamiri, pitsa sousi, pitsa pishlog'i, chizbuger pishlog'i,", '77 000'), 'Pitsa 4 mavsum': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_74_21195b01.jpg', "Pitsa 4 mavsum\n\nOxota kolbasasi, kurka, makkajo'xori, zaytun, bolgar", '86 000'), "Go'shtli pitsa": ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_76_c84cf3de.jpg', "Go'shtli pitsa\n\nMol go'shti, bolgar qalampiri, makkajo'xori, zaytun, pomidor,", '94 000'), 'Margarita': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_75_3f15d56f.jpg', 'Margarita\n\nPomidor, pishloq, sous', '64 000'), 'Assorti pitsa': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_71_b1b9a3bd.jpg', "Assorti pitsa\n\nOxota kolbasasi, kurka, zaytun, makkajo'xori, bolgar qalampiri,", '91 000'), 'Klab sendvich (tovuqli)': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_86_a2243715.png', "Klab sendvich (tovuqli)\n\nTovuq ko'kragi, tuzlangan bodring, pomidor, salat, pishloq, mayonez,", '41 000'), 'Starter tovuqli': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_152_47247cfa.png', "Starter tovuqli\n\nMazali tovuq go'shti, pishloq, qo'ziqorin, pomidor, oq va qizil", '27 000'), "Starter mol go'shtli": ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_151_b5cb129b.png', "Starter mol go'shtli\n\nMazali mol go'shti, pitsa pishlog'i, Hochland pishloq, pomidor,", '31 000'), 'Grekcha salati': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_256_9ea169b8.png', "Grekcha salati\n\nYangi pomidor va bodring, tort zaytun, achchiq yog'li sousli nozik", '35 000'), 'Sezar salati': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_257_01de0ebb.jpg', "Sezar salati\n\nXamirda qovurilgan tovuq bo'laklari, yangi pomidor, pishloq,", '42 000'), 'Snikers': ('https://storage.servisoft.uz/masterkebabmedia/products/snikers.png', 'Snikers', '25 000'), 'Asalcha': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_187_c614e81d.png', 'Asalcha\n\nMedoviy shirinligi', '25 000'), 'Chizkeyk': ('https://storage.servisoft.uz/masterkebabmedia/products/Untitled_design_14.png', 'Chizkeyk', '25 000'), 'IceTea karkade': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_283_b021ce75.jpg', 'IceTea karkade', '10 000'), 'Pepsi': ('https://storage.servisoft.uz/masterkebabmedia/products/product_97_83b50cfb.jpg', 'Pepsi\n\nQadoqlangan Pepsi', '10 000'), 'Moxito (klassik)': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_92_b25e3d11.png', "Moxito (klassik)\n\nIssiq kunda chanqog'ingizni qondiradigan alkogolsiz ichimlik", '15 000'), 'Pepsi (quyma)': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_94_98ec7e1c.png', 'Pepsi (quyma)\n\nSpilled Pepsi in a branded paper cup', '10 000'), 'Coca-cola': ('https://storage.servisoft.uz/masterkebabmedia/products/coca-cola.jpeg', 'Coca-cola\n\nCoca-cola', '15 000'), "Fuse tea (ko'k choy)": ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_179_5a3b4d77.jpg', "Fuse tea (ko'k choy)\n\nKo'k choy", '10 000'), 'Moxito assorti': ('https://storage.servisoft.uz/masterkebabmedia/products/IMGL2649_1.jpg', "Moxito assorti\n\nTurli mevalarning ta'mini o'zida jam etgan salqin ichimlik", '15 000'), 'Sharbat 1L': ('https://storage.servisoft.uz/masterkebabmedia/products/sok.png', 'Sharbat 1L\n\nQadoqlangan sharbat "Сочная долина" 1L', '20 000'), 'Bonaqua': ('https://storage.servisoft.uz/masterkebabmedia/products/IMGL2601_1.jpg', 'Bonaqua\n\nGazlangan Bonaqua ichimlik suvi', '5 000'), 'Fanta': ('https://storage.servisoft.uz/masterkebabmedia/products/photo_2025-05-03_00.46.25.jpeg', 'Fanta', '20 000'), 'Flash': ('https://storage.servisoft.uz/masterkebabmedia/products/product_154_436c0769.jpg', 'Flash\n\nEnergetik ichimlik', '9 000'), 'Chikenburger': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_277_f480c65e.png', 'Chikenburger\n\nQarsildoq tovuq go‘shti, yumshoq bulochka va sous.', '33 000'), 'Chizburger': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_82_5cdc0a36.png', 'Chizburger\n\nMol go‘shti kotleti, bulochka, pishloq, pomidor, bodring va marul.', '40 000'), 'Chikencha': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_157_5196a0ca.png', 'Chikencha\n\nMazali tovuq go‘shti, Aysberg bargi, pomidor va oq sous.', '25 000'), 'Klab sendvich (mol': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_87_de5ad8e9.png', 'Klab sendvich (mol go‘shtli)\n\nMol go‘shti, tuzlangan bodring, pomidor, salat, pishloq va mayonez.', '48 000'), 'Kebab Pita': ('https://storage.servisoft.uz/masterkebabmedia/test/products/product_64_2fb5e066.png', 'Kebab Pita\n\nMazali kebab go‘shti, yangi sabzavotlar va sous bilan pita noni.', '45 000')}

CATEGORY_BUTTONS = {
    "🍔Burger": (btn.burgerList, "Burgerlar"),
    "🌯Lavash": (btn.LavashList, "Lavashlar"),
    "🌭Hot-Dog": (btn.Hot_DogList, "Hot-doglar"),
    "🍟Gazaklar": (btn.gazaklarList, "Gazaklar"),
    "🍗KFC": (btn.kfcList, "KFC — tovuqli taomlar"),
    "🍲Taomlar": (btn.taomlarrList, "Taomlar"),
    "🍕Pizza": (btn.pizzaList, "Pitsalar"),
    "🥪Sendvich": (btn.sendvichList, "Sendvichlar"),
    "🥗Salatlar": (btn.salatList, "Salatlar"),
    "🍰Shirinliklar": (btn.shirinlikList, "Shirinliklar"),
    "🥤Ichimliklar": (btn.ichimlikList, "Ichimliklar"),
}

CATEGORY_PHOTOS = {
    "🍔Burger": "https://i.pinimg.com/736x/c9/c5/01/c9c5013a47c78dde12d22a8659cdb945.jpg",
    "🌯Lavash": "https://i.pinimg.com/736x/af/b5/2b/afb52b5815f999d6a215764ddf05d331.jpg",
    "🌭Hot-Dog": "https://i.pinimg.com/1200x/0f/3e/a0/0f3ea072e022a863940b9e56ad43e372.jpg",
    "🍟Gazaklar": "https://i.pinimg.com/1200x/c4/36/21/c43621ffcab0ccf0861db9789fb10f05.jpg",
    "🍗KFC": "https://storage.servisoft.uz/masterkebabmedia/test/products/product_254_7a6ad0c3.png",
    "🍲Taomlar": "https://i.pinimg.com/1200x/70/2d/e6/702de6afe94266e6fd4da0d1dc7caf24.jpg",
    "🍕Pizza": "https://i.pinimg.com/736x/dc/5d/ba/dc5dba445aea4ddfa37e05e12b2bb3f2.jpg",
    "🥪Sendvich": "https://i.pinimg.com/736x/7e/24/70/7e2470ba0ef567547ad934138f5e396e.jpg",
    "🥗Salatlar": "https://i.pinimg.com/736x/eb/3d/dd/eb3dddb9ec15de31d38c2d68313fd858.jpg",
    "🍰Shirinliklar": "https://i.pinimg.com/736x/c9/3d/04/c93d04be8286e5bdff6f61273c49a22a.jpg",
    "🥤Ichimliklar": "https://i.pinimg.com/736x/86/d8/9a/86d89aececbf4358d73d828be06bf5b5.jpg",
}

# Dark Premium: qora fon Telegram chatiga mos matnlar, qizil aksentli inline tugmalar.
DELIVERY_FEE = int(os.getenv("DELIVERY_FEE", "10000"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip().rstrip("/")
# Hudud narxlari: .env orqali o'zgartirish mumkin.
DELIVERY_ZONES = {
    "Markaz": (10000, 25),
    "Yaqin hudud": (7000, 20),
    "Uzoq hudud": (15000, 45),
}
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
PROMO_DEFAULT = "WELCOME10"
STATUS_OPTIONS = ["Qabul qilindi", "Tayyorlanmoqda", "Yo‘lda", "Yetkazildi", "Bekor qilindi"]

def money(value: int) -> str:
    return f"{int(value):,}".replace(",", " ")

def price_to_int(value: str) -> int:
    digits = ''.join(ch for ch in str(value) if ch.isdigit())
    return int(digits or 0)

def product_price(name: str) -> int:
    return price_to_int(PRODUCTS[name][2])

def cart_rows(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT product, quantity FROM cart WHERE user_id=? ORDER BY product", (user_id,)).fetchall()

def cart_total(user_id: int) -> int:
    return sum(product_price(name) * qty for name, qty in cart_rows(user_id))

def cart_keyboard(user_id: int):
    rows = cart_rows(user_id)
    buttons = []
    for name, qty in rows:
        buttons.append([
            InlineKeyboardButton(text=f"➖ {name}", callback_data=f"qtyminus:{name}"),
            InlineKeyboardButton(text=f"{qty} dona", callback_data="cart:refresh"),
            InlineKeyboardButton(text="➕", callback_data=f"qtyplus:{name}"),
        ])
    if rows:
        buttons.append([InlineKeyboardButton(text="🧹 Savatni tozalash", callback_data="cart:clear")])
        buttons.append([InlineKeyboardButton(text="✅ Buyurtmani rasmiylashtirish", callback_data="checkout:start")])
    return InlineKeyboardMarkup(inline_keyboard=buttons or [[InlineKeyboardButton(text="🍔 Menyuni ochish", callback_data="cart:menu")]])

def product_keyboard(name: str, user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        fav = conn.execute("SELECT 1 FROM favorites WHERE user_id=? AND product=?", (user_id, name)).fetchone()
    fav_text = "💔 Sevimlidan olish" if fav else "❤️ Sevimliga qo‘shish"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🛒 Savatga qo‘shish · {PRODUCTS[name][2]} so‘m", callback_data=f"cartadd:{name}")],
        [InlineKeyboardButton(text=fav_text, callback_data=f"fav:{name}")],
    ])

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    text = (f"🖤 <b>FASTFOOD PREMIUM</b> 🔴\nAssalomu alaykum, <b>{escape(message.from_user.full_name or 'mehmon')}</b>!\n\n"
            "🍔 Mazali taomlar — tez va qulay buyurtma.\n🛵 Yetkazib berish va buyurtma holatini kuzatish mavjud.")
    if WEBAPP_URL:
        web_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🍔 Vizual menyuni ochish", web_app=WebAppInfo(url=WEBAPP_URL))]])
        await message.answer(text, reply_markup=web_kb)
    await message.answer("Pastdagi menyudan foydalaning yoki yuqoridagi vizual menyuni oching.", reply_markup=btn.menuBtn)

@dp.message(F.text == "Menyu 🍽")
async def show_menu(message: Message):
    await message.answer("🔴 <b>MENYU</b>\nKerakli bo‘limni tanlang:", reply_markup=btn.ovqatList)

@dp.message(F.text == "⬅️Ortga")
async def go_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🖤 Bosh menyu. Kerakli bo‘limni tanlang:", reply_markup=btn.menuBtn)

@dp.message(F.text.in_(CATEGORY_BUTTONS.keys()))
async def show_category(message: Message):
    text = message.text
    keyboard, title = CATEGORY_BUTTONS[text]
    try:
        await message.answer_photo(CATEGORY_PHOTOS[text], caption=f"🔴 <b>{escape(title)}</b>\nKerakli mahsulotni tanlang:", reply_markup=keyboard)
    except TelegramAPIError as e:
        logging.warning("Kategoriya rasmi yuborilmadi (%s): %s", text, e)
        await message.answer(f"🔴 <b>{escape(title)}</b>\nKerakli mahsulotni tanlang:", reply_markup=keyboard)

@dp.message(F.text == "🛒 Savatim")
@dp.message(F.text == "Savat 🛒")
async def show_cart(message: Message):
    rows = cart_rows(message.from_user.id)
    if not rows:
        await message.answer("🛒 Savatingiz hozircha bo‘sh. Menyudan taom tanlang.", reply_markup=btn.menuBtn)
        return
    lines = ["🛒 <b>SIZNING SAVATINGIZ</b>"]
    for name, qty in rows:
        lines.append(f"• {escape(name)} × {qty} = <b>{money(product_price(name)*qty)} so‘m</b>")
    lines.append(f"\n💰 <b>Jami: {money(cart_total(message.from_user.id))} so‘m</b>")
    await message.answer("\n".join(lines), reply_markup=cart_keyboard(message.from_user.id))

@dp.callback_query(F.data.startswith("cartadd:"))
async def add_to_cart(callback: types.CallbackQuery):
    name = callback.data.split(":", 1)[1]
    if name not in PRODUCTS:
        await callback.answer("Mahsulot topilmadi", show_alert=True); return
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO cart(user_id, product, quantity) VALUES(?,?,1) ON CONFLICT(user_id,product) DO UPDATE SET quantity=quantity+1", (callback.from_user.id, name))
        conn.commit()
    await callback.answer("Savatga qo‘shildi ✅")
    try:
        await callback.message.edit_reply_markup(reply_markup=product_keyboard(name, callback.from_user.id))
    except TelegramAPIError:
        pass
    await callback.message.answer(f"✅ <b>{escape(name)}</b> savatga qo‘shildi.\n🛒 Savat jami: <b>{money(cart_total(callback.from_user.id))} so‘m</b>", reply_markup=btn.menuBtn)

@dp.callback_query(F.data.startswith("qtyplus:"))
async def qty_plus(callback: types.CallbackQuery):
    name=callback.data.split(":",1)[1]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE cart SET quantity=quantity+1 WHERE user_id=? AND product=?",(callback.from_user.id,name)); conn.commit()
    await callback.answer("Soni oshirildi")
    await show_cart_from_callback(callback)

@dp.callback_query(F.data.startswith("qtyminus:"))
async def qty_minus(callback: types.CallbackQuery):
    name=callback.data.split(":",1)[1]
    with sqlite3.connect(DB_PATH) as conn:
        row=conn.execute("SELECT quantity FROM cart WHERE user_id=? AND product=?",(callback.from_user.id,name)).fetchone()
        if row:
            if row[0] <= 1: conn.execute("DELETE FROM cart WHERE user_id=? AND product=?",(callback.from_user.id,name))
            else: conn.execute("UPDATE cart SET quantity=quantity-1 WHERE user_id=? AND product=?",(callback.from_user.id,name))
        conn.commit()
    await callback.answer("Soni yangilandi")
    await show_cart_from_callback(callback)

async def show_cart_from_callback(callback: types.CallbackQuery):
    rows=cart_rows(callback.from_user.id)
    if not rows:
        await callback.message.edit_text("🛒 Savat bo‘shab qoldi.")
        return
    lines=["🛒 <b>SIZNING SAVATINGIZ</b>"]+[f"• {escape(n)} × {q} = <b>{money(product_price(n)*q)} so‘m</b>" for n,q in rows]
    lines.append(f"\n💰 <b>Jami: {money(cart_total(callback.from_user.id))} so‘m</b>")
    await callback.message.edit_text("\n".join(lines),reply_markup=cart_keyboard(callback.from_user.id))

@dp.callback_query(F.data == "cart:refresh")
async def cart_refresh(callback: types.CallbackQuery):
    await callback.answer(); await show_cart_from_callback(callback)

@dp.callback_query(F.data == "cart:clear")
async def cart_clear(callback: types.CallbackQuery):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM cart WHERE user_id=?",(callback.from_user.id,)); conn.commit()
    await callback.answer("Savat tozalandi")
    await callback.message.edit_text("🧹 Savatingiz tozalandi.")

@dp.callback_query(F.data == "cart:menu")
async def cart_menu(callback: types.CallbackQuery):
    await callback.answer(); await callback.message.answer("Menyuni oching:",reply_markup=btn.menuBtn)

@dp.callback_query(F.data.startswith("fav:"))
async def toggle_favorite(callback: types.CallbackQuery):
    name=callback.data.split(":",1)[1]
    if name not in PRODUCTS: await callback.answer("Mahsulot topilmadi",show_alert=True); return
    with sqlite3.connect(DB_PATH) as conn:
        exists=conn.execute("SELECT 1 FROM favorites WHERE user_id=? AND product=?",(callback.from_user.id,name)).fetchone()
        if exists: conn.execute("DELETE FROM favorites WHERE user_id=? AND product=?",(callback.from_user.id,name)); note="Sevimlilardan olib tashlandi"
        else: conn.execute("INSERT OR IGNORE INTO favorites(user_id,product) VALUES(?,?)",(callback.from_user.id,name)); note="Sevimlilarga qo‘shildi ❤️"
        conn.commit()
    await callback.answer(note)
    try: await callback.message.edit_reply_markup(reply_markup=product_keyboard(name,callback.from_user.id))
    except TelegramAPIError: pass

@dp.message(F.text == "❤️ Sevimlilar")
async def favorites(message: Message):
    with sqlite3.connect(DB_PATH) as conn:
        rows=conn.execute("SELECT product FROM favorites WHERE user_id=? ORDER BY product",(message.from_user.id,)).fetchall()
    if not rows:
        await message.answer("❤️ Hozircha sevimli taomlaringiz yo‘q. Mahsulot kartasidagi tugma orqali qo‘shing.",reply_markup=btn.menuBtn); return
    await message.answer("❤️ <b>SEVIMLI TAOMLAR</b>\n"+"\n".join(f"• {escape(r[0])} — {PRODUCTS[r[0]][2]} so‘m" for r in rows if r[0] in PRODUCTS),reply_markup=btn.menuBtn)
    for (name,) in rows:
        if name in PRODUCTS:
            try: await message.answer_photo(PRODUCTS[name][0],caption=f"🍽 <b>{escape(name)}</b>\n💰 {PRODUCTS[name][2]} so‘m",reply_markup=product_keyboard(name,message.from_user.id))
            except TelegramAPIError: await message.answer(f"🍽 <b>{escape(name)}</b> — {PRODUCTS[name][2]} so‘m",reply_markup=product_keyboard(name,message.from_user.id))

@dp.message(F.text == "🔎 Taom qidirish")
async def search_start(message: Message, state: FSMContext):
    await state.set_state(OrderState.search)
    await message.answer("🔎 Qaysi taomni qidiryapsiz? Nomini yozing. Bekor qilish: /start")

@dp.message(OrderState.search)
async def search_results(message: Message, state: FSMContext):
    query=(message.text or "").strip().casefold()
    if query == "/start": await state.clear(); await start(message,state); return
    matches=[n for n in PRODUCTS if query in n.casefold()]
    await state.clear()
    if not matches:
        await message.answer("😕 Bunday taom topilmadi. Boshqa nom bilan qidiring.",reply_markup=btn.menuBtn); return
    await message.answer(f"🔎 Topildi: {len(matches)} ta mahsulot")
    for name in matches[:10]:
        try: await message.answer_photo(PRODUCTS[name][0],caption=f"🍽 <b>{escape(name)}</b>\n{escape(PRODUCTS[name][1])}\n\n💰 <b>{PRODUCTS[name][2]} so‘m</b>",reply_markup=product_keyboard(name,message.from_user.id))
        except TelegramAPIError: await message.answer(f"🍽 <b>{escape(name)}</b> — {PRODUCTS[name][2]} so‘m",reply_markup=product_keyboard(name,message.from_user.id))

@dp.message(F.text == "🎁 Promokod")
async def promo_start(message: Message, state: FSMContext):
    await state.set_state(OrderState.promo)
    await message.answer("🎁 Promokodingizni yuboring. Hozircha sinov promokodi: <code>WELCOME10</code> (10% chegirma). Bekor qilish: /start")

@dp.message(OrderState.promo)
async def promo_check(message: Message, state: FSMContext):
    code=(message.text or "").strip().upper()
    if code=="/START": await state.clear(); await start(message,state); return
    with sqlite3.connect(DB_PATH) as conn:
        row=conn.execute("SELECT percent FROM promo_codes WHERE code=? AND active=1",(code,)).fetchone()
    await state.clear()
    if row:
        await message.answer(f"✅ Promokod qabul qilindi: <b>{escape(code)}</b> — {row[0]}% chegirma.\nEndi savatdan buyurtmani rasmiylashtiring.",reply_markup=btn.menuBtn)
        # Save validated promo in profile-local preference table for next checkout.
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS user_promos(user_id INTEGER PRIMARY KEY, code TEXT NOT NULL)")
            conn.execute("INSERT INTO user_promos(user_id,code) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET code=excluded.code",(message.from_user.id,code)); conn.commit()
    else: await message.answer("❌ Promokod topilmadi yoki faol emas.",reply_markup=btn.menuBtn)

@dp.callback_query(F.data == "checkout:start")
async def checkout_start(callback: types.CallbackQuery, state: FSMContext):
    if not cart_rows(callback.from_user.id): await callback.answer("Savatingiz bo‘sh",show_alert=True); return
    await callback.answer()
    with sqlite3.connect(DB_PATH) as conn:
        promo=conn.execute("SELECT code FROM user_promos WHERE user_id=?",(callback.from_user.id,)).fetchone() if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_promos'").fetchone() else None
    await state.update_data(promo=promo[0] if promo else "")
    await state.set_state(OrderState.name)
    await callback.message.answer("🧾 <b>BUYURTMANI RASMIYLASHTIRISH</b>\n👤 Ism-familiyangizni kiriting:")

@dp.message(OrderState.name)
async def receive_name(message: Message, state: FSMContext):
    name=(message.text or "").strip()
    if len(name)<2: await message.answer("Ismingizni to‘g‘ri kiriting:"); return
    await state.update_data(name=name); await state.set_state(OrderState.phone)
    await message.answer("📞 Telefon raqamingizni kiriting (masalan, +998901234567):")

@dp.message(OrderState.phone)
async def receive_phone(message: Message, state: FSMContext):
    phone=(message.text or "").strip(); digits=''.join(ch for ch in phone if ch.isdigit())
    if len(digits)<9: await message.answer("Telefon raqami noto‘g‘ri. Qayta kiriting, masalan: +998901234567"); return
    await state.update_data(phone=phone); await state.set_state(OrderState.address)
    zones_text = "\n".join(f"• {z} — {money(fee)} so‘m, taxminan {eta} daqiqa" for z,(fee,eta) in DELIVERY_ZONES.items())
    await message.answer("📍 Manzil va hududni yozing. Avval hudud nomini, keyin to‘liq manzilni kiriting.\n\n" + zones_text + "\n\nOlib ketish uchun <code>OLIB KETAMAN</code> deb yozing:")

@dp.message(OrderState.address)
async def receive_address(message: Message, state: FSMContext):
    address=(message.text or "").strip()
    if len(address)<4: await message.answer("Iltimos, manzilni batafsilroq yozing:"); return
    data=await state.get_data(); user_id=message.from_user.id
    items=cart_rows(user_id)
    if not items: await state.clear(); await message.answer("Savat bo‘sh. Menyudan qayta taom tanlang.",reply_markup=btn.menuBtn); return
    subtotal=sum(product_price(n)*q for n,q in items)
    if address.upper() == "OLIB KETAMAN":
        delivery, zone, eta = 0, "Olib ketish", 0
    else:
        first_line = address.splitlines()[0].strip()
        zone = first_line if first_line in DELIVERY_ZONES else "Standart"
        delivery, eta = DELIVERY_ZONES.get(zone, (DELIVERY_FEE, 35))
    discount=0; promo=(data.get("promo") or "").upper()
    if promo:
        with sqlite3.connect(DB_PATH) as conn: p=conn.execute("SELECT percent FROM promo_codes WHERE code=? AND active=1",(promo,)).fetchone()
        if p: discount=subtotal*int(p[0])//100
    total=max(0,subtotal-discount)+delivery
    items_json={n:q for n,q in items}; product_text="; ".join(f"{n} x{q}" for n,q in items)
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_PATH) as conn:
        cur=conn.execute("INSERT INTO orders(user_id,product,price,customer_name,phone,created_at,total,address,status,discount,delivery_fee,items_json,eta_minutes,zone) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(user_id,product_text,money(total),data.get("name",""),data.get("phone",""),now,total,address,"Qabul qilindi",discount,delivery,__import__('json').dumps(items_json,ensure_ascii=False),eta,zone))
        order_id=cur.lastrowid
        conn.execute("INSERT INTO profiles(user_id,phone) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET phone=excluded.phone",(user_id,data.get("phone","")))
        conn.execute("DELETE FROM cart WHERE user_id=?",(user_id,)); conn.commit()
    lines=[f"🔴 <b>YANGI BUYURTMA #{order_id}</b>",f"👤 {escape(data.get('name',''))}",f"📞 {escape(data.get('phone',''))}",f"📍 {escape(address)}","", "🍽 <b>Taomlar:</b>"]
    lines += [f"• {escape(n)} × {q} — {money(product_price(n)*q)} so‘m" for n,q in items]
    lines += ["",f"🧾 Oraliq jami: {money(subtotal)} so‘m",f"🎁 Chegirma: −{money(discount)} so‘m",f"🛵 Yetkazish ({escape(zone)}): {money(delivery)} so‘m",(f"⏱ Taxminiy yetib borish: {eta} daqiqa" if eta else "📦 Olib ketish"),f"💰 <b>JAMI: {money(total)} so‘m</b>",f"🕒 {now}","📌 Holat: Qabul qilindi"]
    order_text="\n".join(lines)
    await message.answer("✅ <b>BUYURTMANGIZ QABUL QILINDI!</b>\n\n"+order_text+"\n\n🔎 Holatini «Mening buyurtmalarim🛒» bo‘limidan kuzatishingiz mumkin.",reply_markup=btn.menuBtn)
    if ADMIN_ID:
        admin_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"🔄 {status}",callback_data=f"status:{order_id}:{i}")] for i,status in enumerate(STATUS_OPTIONS)])
        try: await message.bot.send_message(ADMIN_ID,order_text,reply_markup=admin_markup)
        except TelegramAPIError as e: logging.error("Admin xabari yuborilmadi: %s",e)
    else:
        logging.warning("ADMIN_ID sozlanmagan: buyurtma bazaga saqlandi, admin xabari yuborilmadi.")
    await state.clear()

@dp.callback_query(F.data.startswith("status:"))
async def admin_set_status(callback: types.CallbackQuery):
    if not ADMIN_ID or callback.from_user.id != ADMIN_ID:
        await callback.answer("Bu amal faqat admin uchun",show_alert=True); return
    try: _, order_id, index=callback.data.split(":"); order_id=int(order_id); status=STATUS_OPTIONS[int(index)]
    except (ValueError,IndexError): await callback.answer("Noto‘g‘ri so‘rov",show_alert=True); return
    with sqlite3.connect(DB_PATH) as conn:
        row=conn.execute("SELECT user_id FROM orders WHERE id=?",(order_id,)).fetchone()
        if not row: await callback.answer("Buyurtma topilmadi",show_alert=True); return
        conn.execute("UPDATE orders SET status=? WHERE id=?",(status,order_id)); conn.commit()
    await callback.answer(f"Holat: {status}")
    try: await callback.bot.send_message(row[0],f"📦 <b>#{order_id} buyurtmangiz holati yangilandi</b>\nYangi holat: <b>{escape(status)}</b>")
    except TelegramAPIError: pass
    try: await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramAPIError: pass

@dp.message(F.text == "Mening buyurtmalarim🛒")
async def my_orders(message: Message):
    with sqlite3.connect(DB_PATH) as conn:
        rows=conn.execute("SELECT id,product,total,price,created_at,status,address FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10",(message.from_user.id,)).fetchall()
    if not rows: await message.answer("🛒 Sizda hali buyurtmalar yo‘q. Menyudan taom tanlab buyurtma bering.",reply_markup=btn.menuBtn); return
    lines=["📦 <b>OXIRGI BUYURTMALARINGIZ</b>"]
    for oid,product,total,price,created,status,address in rows:
        amount=total or price_to_int(price)
        lines.append(f"\n🔴 <b>Buyurtma #{oid}</b>\n🍽 {escape(product)}\n💰 {money(amount)} so‘m\n📌 Holat: <b>{escape(status)}</b>\n📍 {escape(address or '')}\n🕒 {escape(created)}")
    lines.append("\n⭐ Buyurtmaga baho berish uchun /review buyrug‘ini yuboring.")
    await message.answer("\n".join(lines),reply_markup=btn.menuBtn)

@dp.message(F.text == "📊 Statistika")
async def sales_stats(message: Message):
    if not ADMIN_ID or message.from_user.id != ADMIN_ID: await message.answer("⛔ Bu bo‘lim faqat admin uchun.",reply_markup=btn.menuBtn); return
    today=datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as conn:
        total_orders=conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        today_orders=conn.execute("SELECT COUNT(*) FROM orders WHERE created_at LIKE ?",(today+'%',)).fetchone()[0]
        today_sum=conn.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE created_at LIKE ? AND status!='Bekor qilindi'",(today+'%',)).fetchone()[0]
        all_sum=conn.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status!='Bekor qilindi'").fetchone()[0]
        pending=conn.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Qabul qilindi','Tayyorlanmoqda','Yo‘lda')").fetchone()[0]
    await message.answer(f"📊 <b>FASTFOOD SAVDO STATISTIKASI</b>\n\n📅 Bugungi buyurtmalar: <b>{today_orders}</b>\n💰 Bugungi savdo: <b>{money(today_sum)} so‘m</b>\n📦 Jami buyurtmalar: <b>{total_orders}</b>\n💵 Jami savdo: <b>{money(all_sum)} so‘m</b>\n🛵 Jarayondagi buyurtmalar: <b>{pending}</b>",reply_markup=btn.menuBtn)

@dp.message(F.text == "Fikr bildirish📨")
async def feedback(message: Message, state: FSMContext):
    await state.set_state(OrderState.feedback)
    await message.answer("📨 Taklif yoki fikringizni yozing. Bekor qilish: /start")

@dp.message(OrderState.feedback)
async def save_feedback(message: Message, state: FSMContext):
    text=(message.text or "").strip()
    if not text: await message.answer("Iltimos, fikringizni matn ko‘rinishida yuboring:"); return
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO feedback(user_id,username,message,created_at) VALUES(?,?,?,?)",(message.from_user.id,message.from_user.username or "",text,datetime.now().strftime("%Y-%m-%d %H:%M:%S"))); conn.commit()
    await state.clear(); await message.answer("✅ Fikringiz saqlandi. Rahmat!",reply_markup=btn.menuBtn)

@dp.message(F.text == "/review")
async def review_start(message: Message, state: FSMContext):
    with sqlite3.connect(DB_PATH) as conn:
        row=conn.execute("SELECT id FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 1",(message.from_user.id,)).fetchone()
    if not row: await message.answer("Avval buyurtma berishingiz kerak."); return
    await state.update_data(review_order_id=row[0]); await state.set_state(OrderState.review)
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"⭐ {i}",callback_data=f"rating:{i}") for i in range(1,6)]])
    await message.answer(f"⭐ #{row[0]} buyurtmangizga 1 dan 5 gacha baho bering:",reply_markup=kb)

@dp.callback_query(F.data.startswith("rating:"))
async def review_rating(callback: types.CallbackQuery, state: FSMContext):
    try: rating=int(callback.data.split(":",1)[1])
    except ValueError: await callback.answer("Baho noto‘g‘ri"); return
    data=await state.get_data(); order_id=data.get("review_order_id")
    if rating<1 or rating>5 or not order_id: await callback.answer("Avval /review buyrug‘ini yuboring",show_alert=True); return
    await state.update_data(review_rating=rating, review_order_id=order_id)
    await state.set_state(OrderState.review_comment)
    await callback.answer("Baho qabul qilindi ⭐")
    await callback.message.answer(f"Rahmat! Buyurtma #{order_id} uchun bahoyingiz: {'⭐'*rating}.\nIzoh ham qoldirmoqchimisiz? Matn yuboring yoki /skip deb yozing:")

@dp.message(OrderState.review_comment)
async def review_save_comment(message: Message, state: FSMContext):
    data=await state.get_data()
    comment=(message.text or '').strip()
    if comment.lower() == '/skip': comment=''
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO reviews(user_id,order_id,rating,comment,created_at) VALUES(?,?,?,?,?)",(message.from_user.id,data.get('review_order_id'),data.get('review_rating',5),comment,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    await state.clear()
    await message.answer("✅ Bahoyingiz va izohingiz saqlandi. Rahmat!",reply_markup=btn.menuBtn)

@dp.message(F.text.in_(PRODUCTS.keys()))
async def show_product(message: Message):
    name=message.text; photo_url,caption,price=PRODUCTS[name]
    markup=product_keyboard(name,message.from_user.id)
    try:
        await message.answer_photo(photo=photo_url,caption=f"🍽 <b>{escape(caption.splitlines()[0])}</b>\n\n{escape(chr(10).join(caption.splitlines()[1:]).strip())}\n\n💰 Narxi: <b>{escape(price)} so‘m</b>",reply_markup=markup)
    except TelegramAPIError as e:
        logging.warning("Mahsulot rasmi yuborilmadi (%s): %s",name,e)
        await message.answer(f"🍽 <b>{escape(name)}</b>\n{escape(caption)}\n\n💰 Narxi: <b>{escape(price)} so‘m</b>",reply_markup=markup)

@dp.message(F.text.startswith("/assign"))
async def assign_courier(message: Message):
    """Admin: /assign BUYURTMA_ID KURYER_TELEGRAM_ID"""
    if not ADMIN_ID or message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Bu buyruq faqat admin uchun."); return
    parts=(message.text or "").split()
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await message.answer("Foydalanish: <code>/assign BUYURTMA_ID KURYER_TELEGRAM_ID</code>"); return
    order_id, courier_id=int(parts[1]), int(parts[2])
    with sqlite3.connect(DB_PATH) as conn:
        row=conn.execute("SELECT user_id,customer_name,address,eta_minutes,latitude,longitude FROM orders WHERE id=?",(order_id,)).fetchone()
        if not row:
            await message.answer("Buyurtma topilmadi."); return
        conn.execute("UPDATE orders SET courier_id=?, status='Kuryer biriktirildi' WHERE id=?",(courier_id,order_id)); conn.commit()
    try:
        map_link = f'\n🗺 Xarita: https://www.google.com/maps?q={row[4]},{row[5]}' if row[4] is not None and row[5] is not None else ''
        await message.bot.send_message(courier_id, f"🛵 Sizga #{order_id} buyurtma biriktirildi.\n👤 {escape(row[1])}\n📍 {escape(row[2])}{map_link}\n⏱ Taxminiy vaqt: {row[3] or 35} daqiqa\n\nHolatni yangilash uchun /courier buyrug‘ini yuboring.")
        await message.answer(f"✅ #{order_id} buyurtma kuryer <code>{courier_id}</code> ga biriktirildi.")
    except TelegramAPIError:
        await message.answer("Kuryerga xabar yuborilmadi. U botni avval /start bilan ishga tushirganini va ID to‘g‘riligini tekshiring.")

@dp.message(F.text == "/courier")
async def courier_orders(message: Message):
    with sqlite3.connect(DB_PATH) as conn:
        rows=conn.execute("SELECT id,product,address,status,eta_minutes,latitude,longitude FROM orders WHERE courier_id=? AND status NOT IN ('Yetkazildi','Bekor qilindi') ORDER BY id DESC",(message.from_user.id,)).fetchall()
    if not rows:
        await message.answer("Sizga biriktirilgan faol buyurtmalar yo‘q."); return
    for oid, product, address, status, eta, latitude, longitude in rows:
        kb=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍳 Tayyorlanmoqda",callback_data=f"courierstatus:{oid}:1")],
            [InlineKeyboardButton(text="🛵 Yo‘lda",callback_data=f"courierstatus:{oid}:2")],
            [InlineKeyboardButton(text="✅ Yetkazildi",callback_data=f"courierstatus:{oid}:3")],
        ])
        map_link = f"\n🗺 <a href='https://www.google.com/maps?q={latitude},{longitude}'>Xaritada ochish</a>" if latitude is not None and longitude is not None else ""
        await message.answer(f"📦 <b>Buyurtma #{oid}</b>\n🍽 {escape(product)}\n📍 {escape(address)}{map_link}\n📌 {escape(status)}\n⏱ {eta or 35} daqiqa",reply_markup=kb)

@dp.callback_query(F.data.startswith("courierstatus:"))
async def courier_update_status(callback: types.CallbackQuery):
    try:
        _, oid, idx=callback.data.split(":"); oid=int(oid); idx=int(idx)
        status={1:"Tayyorlanmoqda",2:"Yo‘lda",3:"Yetkazildi"}[idx]
    except (ValueError,KeyError):
        await callback.answer("Noto‘g‘ri so‘rov",show_alert=True); return
    with sqlite3.connect(DB_PATH) as conn:
        row=conn.execute("SELECT user_id,courier_id FROM orders WHERE id=?",(oid,)).fetchone()
        if not row or row[1] != callback.from_user.id:
            await callback.answer("Bu buyurtma sizga biriktirilmagan",show_alert=True); return
        conn.execute("UPDATE orders SET status=? WHERE id=?",(status,oid)); conn.commit()
    await callback.answer("Holat yangilandi")
    try: await callback.bot.send_message(row[0],f"📦 <b>#{oid} buyurtmangiz</b> holati: <b>{escape(status)}</b>")
    except TelegramAPIError: pass
    try: await callback.message.edit_text(callback.message.text + f"\n\n✅ Yangi holat: <b>{escape(status)}</b>",reply_markup=None)
    except TelegramAPIError: pass

@dp.message()
async def unknown_message(message: Message):
    await message.answer("Tushunmadim 🙂 «Menyu 🍽» tugmasini bosing yoki /start yuboring.",reply_markup=btn.menuBtn)





async def main():
    token = os.getenv("8518492736:AAEf4JdvJdO17zc1oUaEreR_ElI5y4TqVJQ", "").strip()

    if not token:
        logging.error("BOT_TOKEN FadeHost sozlamalarida topilmadi.")
        return

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


    try:
        logging.info("FASTFOOD PREMIUM ishga tushmoqda...")

        if ADMIN_ID:
            logging.info("Admin ID sozlangan: %s", ADMIN_ID)
        else:
            logging.warning(
                "ADMIN_ID sozlanmagan. "
                "Buyurtmalar bazaga saqlanishi mumkin, "
                "lekin admin xabari yuborilmaydi."
            )

        await dp.start_polling(bot)

    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to‘xtatildi.")

