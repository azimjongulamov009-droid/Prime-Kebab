from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

menuBtn = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Menyu 🍽"), KeyboardButton(text="🛒 Savatim")],
    [KeyboardButton(text="Mening buyurtmalarim🛒"), KeyboardButton(text="❤️ Sevimlilar")],
    [KeyboardButton(text="🔎 Taom qidirish"), KeyboardButton(text="🎁 Promokod")],
    [KeyboardButton(text="Fikr bildirish📨")],
    [KeyboardButton(text="📊 Statistika")],
], resize_keyboard=True)

ovqatList = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🍔Burger"), KeyboardButton(text="🌯Lavash")],
    [KeyboardButton(text="🌭Hot-Dog"), KeyboardButton(text="🍟Gazaklar")],
    [KeyboardButton(text="🍗KFC"), KeyboardButton(text="🍕Pizza")],
    [KeyboardButton(text="🍲Taomlar"), KeyboardButton(text="🥪Sendvich")],
    [KeyboardButton(text="🥗Salatlar"), KeyboardButton(text="🍰Shirinliklar")],
    [KeyboardButton(text="🥤Ichimliklar")],
    [KeyboardButton(text="⬅️Ortga")],
], resize_keyboard=True)

burgerList = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Chikenburger"), KeyboardButton(text="Chizburger")],
    [KeyboardButton(text="Gamburger"), KeyboardButton(text="Yovvoyi burger")],
    [KeyboardButton(text="Miks burger"), KeyboardButton(text="Chikencha")],
    [KeyboardButton(text="⬅️Ortga")],
], resize_keyboard=True)

LavashList = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Tandir lavash"), KeyboardButton(text="Tandir lavash pishloqli")],
    [KeyboardButton(text="Lavash"), KeyboardButton(text="Lavash pishloqli")],
    [KeyboardButton(text="Kebab Pita"), KeyboardButton(text="⬅️Ortga")],
], resize_keyboard=True)

Hot_DogList = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Hot-dog (oddiy)"), KeyboardButton(text="Hot-dog (amerikancha)")],
    [KeyboardButton(text="Hot-dog (korolevskiy)"), KeyboardButton(text="Hot-dog (fransuzcha)")],
    [KeyboardButton(text="⬅️Ortga")],
], resize_keyboard=True)

gazaklarList = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Tovuq baytslari"), KeyboardButton(text="Qanotchalar")],
    [KeyboardButton(text="Naggetslar (6 dona)"), KeyboardButton(text="Kotlet")],
    [KeyboardButton(text="Kartoshka fri"), KeyboardButton(text="Guruch")],
    [KeyboardButton(text="⬅️Ortga")],
], resize_keyboard=True)

taomlarrList = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Kebab taom (mol)"), KeyboardButton(text="Kebab taom (tovuqli)")],
    [KeyboardButton(text="⬅️Ortga")],
], resize_keyboard=True)

kfcList = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Tovuq baytslari"), KeyboardButton(text="Qanotchalar")],
    [KeyboardButton(text="Naggetslar (6 dona)"), KeyboardButton(text="⬅️Ortga")],
], resize_keyboard=True)

pizzaList = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Pepperoni"), KeyboardButton(text="Lesnaya Pitsa")],
    [KeyboardButton(text="Yopiq pitsa"), KeyboardButton(text="Tovuqli pitsa")],
    [KeyboardButton(text="Go'shtli miks"), KeyboardButton(text="Master Kebab")],
    [KeyboardButton(text="Pitsa 4 pishloq"), KeyboardButton(text="Pitsa 4 mavsum")],
    [KeyboardButton(text="Go'shtli pitsa"), KeyboardButton(text="Margarita")],
    [KeyboardButton(text="Assorti pitsa"), KeyboardButton(text="⬅️Ortga")],
], resize_keyboard=True)

sendvichList = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Klab sendvich (tovuqli)"), KeyboardButton(text="Starter tovuqli")],
    [KeyboardButton(text="Starter mol go'shtli"), KeyboardButton(text="Klab sendvich (mol")],
    [KeyboardButton(text="⬅️Ortga")],
], resize_keyboard=True)

salatList = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Grekcha salati"), KeyboardButton(text="Sezar salati")],
    [KeyboardButton(text="⬅️Ortga")],
], resize_keyboard=True)

shirinlikList = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Snikers"), KeyboardButton(text="Asalcha")],
    [KeyboardButton(text="Chizkeyk"), KeyboardButton(text="⬅️Ortga")],
], resize_keyboard=True)

ichimlikList = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="IceTea karkade"), KeyboardButton(text="Pepsi")],
    [KeyboardButton(text="Moxito (klassik)"), KeyboardButton(text="Pepsi (quyma)")],
    [KeyboardButton(text="Coca-cola"), KeyboardButton(text="Fuse tea (ko'k choy)")],
    [KeyboardButton(text="Moxito assorti"), KeyboardButton(text="Sharbat 1L")],
    [KeyboardButton(text="Bonaqua"), KeyboardButton(text="Fanta")],
    [KeyboardButton(text="Flash"), KeyboardButton(text="⬅️Ortga")],
], resize_keyboard=True)
