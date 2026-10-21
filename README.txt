FASTFOOD PREMIUM — Telegram bot + Mini App + kuryer boshqaruvi

FAYLLAR
- main.py: aiogram bot, savat, buyurtmalar, admin holatlari, kuryer buyruqlari
- buttons.py: Telegram menyu tugmalari
- webapp.py: Mini App sayti va buyurtma API
- webapp/index.html: telefon uchun vizual menyu
- fastfood.db: birinchi ishga tushganda yaratiladi

WINDOWSDA ISHGA TUSHIRISH
1) Python 3.11 o‘rnatilgan bo‘lsin.
2) Shu papkada terminal oching.
3) pip install -r requirements.txt
4) .env.example faylidan .env nusxa yarating va BOT_TOKEN, ADMIN_ID ni sozlang.
   Agar python-dotenv o‘rnatilmagan bo‘lsa, eng osoni terminalda:
   PowerShell: $env:BOT_TOKEN='BOT_TOKEN'; $env:ADMIN_ID='123456789'; $env:WEBAPP_URL=''
5) Ikki alohida terminal oching.
   Terminal 1: python webapp.py
   Terminal 2: python main.py

MUHIM: Telegram Mini App Telegram ichida ishlashi uchun WEBAPP_URL ommaviy HTTPS manzil bo‘lishi kerak.
Localhost manzil telefondagi Telegram uchun ishlamaydi. WEBAPP_URL bo‘sh bo‘lsa botning odatiy menyusi ishlaydi, Mini App tugmasi ko‘rinmaydi.

KURYER ISHLATISH
1) Kuryer o‘z Telegramidan botga /start yuborsin.
2) Admin buyurtmani biriktiradi: /assign BUYURTMA_ID KURYER_TELEGRAM_ID
3) Kuryer /courier yuboradi va unga biriktirilgan buyurtmalarni ko‘radi.
4) Kuryer “Tayyorlanmoqda”, “Yo‘lda”, “Yetkazildi” tugmalaridan holatni yangilaydi. Mijozga xabar boradi.

HUDUDLAR
main.py ichidagi DELIVERY_ZONES lug‘atida hudud narxi va taxminiy daqiqalar sozlanadi.
Mini App hozir Markaz / Yaqin hudud / Uzoq hudud variantlarini ko‘rsatadi.

XAVFSIZLIK
Bot tokenini hech qachon ommaga yubormang. Agar token chat yoki rasmda oshkor bo‘lgan bo‘lsa, @BotFather orqali /revoke qiling va yangisini BOT_TOKEN ga qo‘ying.
Mini App buyurtmasi Telegram initData imzosi bilan tekshiriladi; sahifani oddiy brauzerda ochib buyurtma berish bloklanadi.
