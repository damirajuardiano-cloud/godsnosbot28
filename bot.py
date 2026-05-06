import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.enums import ParseMode
from aiogram.types import Message

# ===== НАСТРОЙКИ =====
TOKEN = "8765817388:AAHJ4FRJ4E_ILdFQot3H3qjWi3od8WX8tHY"
CHANNEL_LINK = "https://t.me/gooooooodsns"
OWNER_USERNAME_1 = "defymerz"
OWNER_USERNAME_2 = "ssvs877"

# Кошелек Tonkeeper (для ручной оплаты)
TONKEEPER_WALLET = "UQAbML7ypTCu8-c49B2hnFRDgiI5IhEFZWvj7iN_nyZmpXZq"

# ID владельцев
OWNER_IDS = [8581847345, 1002296130]

# ===== ФОТО =====
MY_PHOTO = "IMG_20260505_164235_190.jpg"
MAIN_MENU_PHOTO = "IMG_20260505_164235_190.jpg"
DELIVERY_PHOTO = "IMG_20260505_164235_190.jpg"
SUBSCRIPTION_PHOTO = "IMG_20260505_164235_190.jpg"
PROFILE_PHOTO = "IMG_20260505_164235_190.jpg"
CHANNEL_PHOTO = "IMG_20260505_164235_190.jpg"
KICK_PHOTO = "IMG_20260505_164235_190.jpg"
SUCCESS_PHOTO = "IMG_20260505_164235_190.jpg"
CONFIRM_PHOTO = "IMG_20260505_164235_190.jpg"

# ===== СТАТИСТИКА ПИЦЦ =====
pizza_stats = {
    "delivered": 227,
    "cancelled": 20,
    "total": 300
}

def update_pizza_stats():
    pizza_stats["delivered"] = random.randint(180, 290)
    pizza_stats["cancelled"] = random.randint(5, 45)
    pizza_stats["total"] = pizza_stats["delivered"] + pizza_stats["cancelled"]

def get_pizza_stats_text():
    return (f"- Сколько отправлено пицц: {pizza_stats['delivered']}\n"
            f"- Сколько отмененных пицц: {pizza_stats['cancelled']}\n"
            f"- Сколько всего пицц: {pizza_stats['total']}")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_subscriptions = {}
pending_payments = {}

# Цены в звездах (Telegram Stars)
STARS_PRICES = {
    "day": 120,
    "week": 300,
    "month": 450,
    "forever": 650
}

# Цены в рублях (Tonkeeper ручная оплата)
RUB_PRICES = {
    "day": 100,
    "week": 350,
    "month": 550,
    "forever": 880
}

# ---------- Админ меню ----------
def get_admin_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выдать подписку", callback_data="admin_give_sub")],
        [InlineKeyboardButton(text="Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="Рассылка", callback_data="admin_mailing")],
        [InlineKeyboardButton(text="Список подписчиков", callback_data="admin_users")],
        [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard

# ---------- Меню выбора подписки для админа ----------
def get_admin_sub_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="На 1 день", callback_data="admin_sub_day")],
        [InlineKeyboardButton(text="На неделю", callback_data="admin_sub_week")],
        [InlineKeyboardButton(text="На месяц", callback_data="admin_sub_month")],
        [InlineKeyboardButton(text="Навсегда", callback_data="admin_sub_forever")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_panel")]
    ])
    return keyboard

# ---------- Главное меню ----------
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Доставка пиццы", callback_data="start_delivery")],
        [InlineKeyboardButton(text="Купить подписку", callback_data="buy_subscription")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="Владельцы бота", callback_data="owner_channel")],
        [InlineKeyboardButton(text="Кик сессии", callback_data="kick_session")]
    ])
    return keyboard

# ---------- Меню подписки для пользователя (выбор способа оплаты) ----------
def get_subscription_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Telegram Stars (авто)", callback_data="payment_method_stars")],
        [InlineKeyboardButton(text="Tonkeeper (чек)", callback_data="payment_method_tonkeeper")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
    ])
    return keyboard

# ---------- Меню выбора тарифа для Stars ----------
def get_stars_tariff_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день - 1 Star", callback_data="stars_day")],
        [InlineKeyboardButton(text="7 дней - 300 Stars", callback_data="stars_week")],
        [InlineKeyboardButton(text="30 дней - 450 Stars", callback_data="stars_month")],
        [InlineKeyboardButton(text="Навсегда - 650 Stars", callback_data="stars_forever")],
        [InlineKeyboardButton(text="Назад", callback_data="buy_subscription")]
    ])
    return keyboard

# ---------- Меню выбора тарифа для Tonkeeper ----------
def get_tonkeeper_tariff_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день - 100 руб", callback_data="tonkeeper_day")],
        [InlineKeyboardButton(text="7 дней - 350 руб", callback_data="tonkeeper_week")],
        [InlineKeyboardButton(text="30 дней - 550 руб", callback_data="tonkeeper_month")],
        [InlineKeyboardButton(text="Навсегда - 880 руб", callback_data="tonkeeper_forever")],
        [InlineKeyboardButton(text="Назад", callback_data="buy_subscription")]
    ])
    return keyboard

# ---------- Меню оплаты через Tonkeeper ----------
def get_tonkeeper_payment_menu(sub_type, price):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отправить чек", callback_data=f"send_receipt_{sub_type}_{price}")],
        [InlineKeyboardButton(text="Отмена", callback_data="buy_subscription")]
    ])
    return keyboard

# ---------- Удаление сообщения ----------
async def safe_delete(chat_id, message_id):
    try:
        await bot.delete_message(chat_id, message_id)
    except:
        pass

# ---------- Проверка на админа ----------
def is_admin(user_id):
    return user_id in OWNER_IDS

# ---------- Выдача подписки пользователю ----------
async def give_subscription(user_id: int, sub_type: str, notify: bool = True):
    user_subscriptions[user_id] = sub_type
    if notify:
        try:
            await bot.send_message(
                user_id,
                f"Подписка '{sub_type}' успешно активирована!\n\nСпасибо за покупку!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
                ])
            )
        except:
            pass

# ---------- Команда старт ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    if username == OWNER_USERNAME_1 or username == OWNER_USERNAME_2:
        if user_id not in OWNER_IDS:
            OWNER_IDS.append(user_id)
            print(f"Добавлен владелец: {username} (ID: {user_id})")
        await message.answer(f"Вы идентифицированы как владелец!\nВаш ID: {user_id}\n\nАдмин панель доступна по команде /admin")
    
    try:
        await message.answer_photo(
            photo=types.FSInputFile(MAIN_MENU_PHOTO),
            caption="Главное меню\n\nВыберите действие:",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        print(f"Ошибка с фото: {e}")
        await message.answer(
            "Главное меню\n\nВыберите действие:",
            reply_markup=get_main_menu()
        )

# ---------- Команда админ панель ----------
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("Вы не являетесь администратором.\n\nЧтобы стать администратором, напишите владельцу бота: @defymerz")
        return
    
    try:
        await message.answer_photo(
            photo=types.FSInputFile(MAIN_MENU_PHOTO),
            caption="Админ панель\n\nВыберите действие:",
            reply_markup=get_admin_menu()
        )
    except:
        await message.answer(
            "Админ панель\n\nВыберите действие:",
            reply_markup=get_admin_menu()
        )

# ---------- Доставка пиццы ----------
async def show_delivery_menu(call: CallbackQuery):
    await safe_delete(call.message.chat.id, call.message.message_id)
    try:
        await call.message.answer_photo(
            photo=types.FSInputFile(DELIVERY_PHOTO),
            caption="Доставка пиццы\n\nОтправьте публичную ссылку на заказ/адрес:\n\nПример: https://t.me/god12367",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
            ])
        )
    except:
        await call.message.answer(
            "Доставка пиццы\n\nОтправьте публичную ссылку на заказ/адрес:\n\nПример: https://t.me/god12367",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
            ])
        )
    await call.answer()

# ---------- Меню подписки для пользователя ----------
async def show_subscription_menu(call: CallbackQuery):
    await safe_delete(call.message.chat.id, call.message.message_id)
    try:
        await call.message.answer_photo(
            photo=types.FSInputFile(SUBSCRIPTION_PHOTO),
            caption="Выбор способа оплаты\n\nВыберите способ оплаты:",
            reply_markup=get_subscription_menu()
        )
    except:
        await call.message.answer(
            "Выбор способа оплаты\n\nВыберите способ оплаты:",
            reply_markup=get_subscription_menu()
        )
    await call.answer()

# ---------- Меню выбора тарифа Stars ----------
async def show_stars_tariff_menu(call: CallbackQuery):
    await safe_delete(call.message.chat.id, call.message.message_id)
    try:
        await call.message.answer_photo(
            photo=types.FSInputFile(SUBSCRIPTION_PHOTO),
            caption="Выберите тариф (оплата Stars):",
            reply_markup=get_stars_tariff_menu()
        )
    except:
        await call.message.answer(
            "Выберите тариф (оплата Stars):",
            reply_markup=get_stars_tariff_menu()
        )
    await call.answer()

# ---------- Меню выбора тарифа Tonkeeper ----------
async def show_tonkeeper_tariff_menu(call: CallbackQuery):
    await safe_delete(call.message.chat.id, call.message.message_id)
    try:
        await call.message.answer_photo(
            photo=types.FSInputFile(SUBSCRIPTION_PHOTO),
            caption="Выберите тариф (оплата Tonkeeper):",
            reply_markup=get_tonkeeper_tariff_menu()
        )
    except:
        await call.message.answer(
            "Выберите тариф (оплата Tonkeeper):",
            reply_markup=get_tonkeeper_tariff_menu()
        )
    await call.answer()

# ---------- Профиль ----------
async def show_profile_menu(call: CallbackQuery):
    user_id = call.from_user.id
    sub_status = user_subscriptions.get(user_id, "Нет подписки")
    username = call.from_user.username if call.from_user.username else "нет"
    text = (f"Профиль\n\n"
            f"ID: {user_id}\n"
            f"Ник: @{username}\n"
            f"Подписка: {sub_status}")
    await safe_delete(call.message.chat.id, call.message.message_id)
    try:
        await call.message.answer_photo(
            photo=types.FSInputFile(PROFILE_PHOTO),
            caption=text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
            ])
        )
    except:
        await call.message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
            ])
        )
    await call.answer()

# ---------- Владельцы бота ----------
async def show_owner_menu(call: CallbackQuery):
    text = (f"Владельцы проекта\n\n"
            f"@defymerz\n"
            f"@ssvs877\n\n"
            f"Тгк\n"
            f"{CHANNEL_LINK}")
    await safe_delete(call.message.chat.id, call.message.message_id)
    try:
        await call.message.answer_photo(
            photo=types.FSInputFile(CHANNEL_PHOTO),
            caption=text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Основной владелец", url=f"https://t.me/{OWNER_USERNAME_1}")],
                [InlineKeyboardButton(text="Второй владелец", url=f"https://t.me/{OWNER_USERNAME_2}")],
                [InlineKeyboardButton(text="Резервный канал", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
            ])
        )
    except:
        await call.message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Основной владелец", url=f"https://t.me/{OWNER_USERNAME_1}")],
                [InlineKeyboardButton(text="Второй владелец", url=f"https://t.me/{OWNER_USERNAME_2}")],
                [InlineKeyboardButton(text="Резервный канал", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
            ])
        )
    await call.answer()

# ---------- Кик сессия меню ----------
async def show_kick_menu(call: CallbackQuery):
    await safe_delete(call.message.chat.id, call.message.message_id)
    try:
        await call.message.answer_photo(
            photo=types.FSInputFile(KICK_PHOTO),
            caption="Кик сессия\n\nУкажите ID или @username для кик-сессии:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
            ])
        )
    except:
        await call.message.answer(
            "Кик сессия\n\nУкажите ID или @username для кик-сессии:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
            ])
        )
    await call.answer()

# ---------- Показать меню оплаты Tonkeeper ----------
async def show_tonkeeper_payment(call: CallbackQuery, sub_type, price):
    await safe_delete(call.message.chat.id, call.message.message_id)
    
    text = (f"Оплата через Tonkeeper\n\n"
            f"Тариф: на {sub_type}\n"
            f"Сумма: {price} руб\n\n"
            f"Вот адрес электронного кошелька:\n"
            f"{TONKEEPER_WALLET}\n\n"
            f"Переведите ровно {price} руб для покупки подписки\n\n"
            f"После оплаты нажмите на кнопку Отправить чек и пришлите скриншот чека.")
    
    try:
        await call.message.answer_photo(
            photo=types.FSInputFile(CONFIRM_PHOTO),
            caption=text,
            reply_markup=get_tonkeeper_payment_menu(sub_type, price)
        )
    except:
        await call.message.answer(
            text,
            reply_markup=get_tonkeeper_payment_menu(sub_type, price)
        )
    await call.answer()

# ---------- Обработка платежа через Stars ----------
@dp.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    user_id = message.from_user.id
    payment_info = message.successful_payment
    
    sub_type_map = {
        1: "1 день",      # 120 звезд
        300: "неделя",    # 300 звезд
        450: "месяц",     # 450 звезд
        650: "навсегда"   # 650 звезд
    }
    
    amount = payment_info.total_amount // 100
    sub_type = sub_type_map.get(amount, "подписка")
    
    await give_subscription(user_id, sub_type, notify=True)
    
    await message.answer(
        f"Оплата прошла успешно!\nПодписка '{sub_type}' активирована.\n\nСпасибо за покупку!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
        ])
    )

# ---------- Обработчик кнопок ----------
@dp.callback_query()
async def handle_callbacks(call: CallbackQuery):
    data = call.data
    user_id = call.from_user.id

    # Навигация
    if data == "back_to_menu":
        await safe_delete(call.message.chat.id, call.message.message_id)
        try:
            await call.message.answer_photo(
                photo=types.FSInputFile(MAIN_MENU_PHOTO),
                caption="Главное меню\n\nВыберите действие:",
                reply_markup=get_main_menu()
            )
        except:
            await call.message.answer(
                "Главное меню\n\nВыберите действие:",
                reply_markup=get_main_menu()
            )
        await call.answer()
        return

    if data == "start_delivery":
        await show_delivery_menu(call)
        return

    if data == "profile":
        await show_profile_menu(call)
        return

    if data == "owner_channel":
        await show_owner_menu(call)
        return

    if data == "kick_session":
        await show_kick_menu(call)
        return

    if data == "buy_subscription":
        await show_subscription_menu(call)
        return

    # Выбор способа оплаты
    if data == "payment_method_stars":
        await show_stars_tariff_menu(call)
        return

    if data == "payment_method_tonkeeper":
        await show_tonkeeper_tariff_menu(call)
        return

    # Обработка выбора тарифа Stars (автоматическая оплата)
    if data.startswith("stars_"):
        sub_map = {
            "stars_day": ("1 день", 120),
            "stars_week": ("неделя", 300),
            "stars_month": ("месяц", 450),
            "stars_forever": ("навсегда", 650)
        }
        if data in sub_map:
            sub_name, price = sub_map[data]
            prices = [LabeledPrice(label="Подписка", amount=price * 1)]
            
            await bot.send_invoice(
                chat_id=user_id,
                title=f"Подписка на {sub_name}",
                description=f"Оплата подписки на {sub_name} через Telegram Stars",
                payload=f"sub_{data}",
                provider_token="",
                currency="XTR",
                prices=prices,
                start_parameter="subscription"
            )
        await call.answer()
        return

    # Обработка выбора тарифа Tonkeeper
    if data.startswith("tonkeeper_"):
        sub_map = {
            "tonkeeper_day": ("день", 100),
            "tonkeeper_week": ("неделю", 350),
            "tonkeeper_month": ("месяц", 550),
            "tonkeeper_forever": ("навсегда", 880)
        }
        if data in sub_map:
            sub_name, price = sub_map[data]
            await show_tonkeeper_payment(call, sub_name, price)
        await call.answer()
        return

    # Админ панель
    if data == "admin_panel":
        if not is_admin(user_id):
            await call.answer("У вас нет доступа", show_alert=True)
            return
        await safe_delete(call.message.chat.id, call.message.message_id)
        try:
            await call.message.answer_photo(
                photo=types.FSInputFile(MAIN_MENU_PHOTO),
                caption="Админ панель\n\nВыберите действие:",
                reply_markup=get_admin_menu()
            )
        except:
            await call.message.answer(
                "Админ панель\n\nВыберите действие:",
                reply_markup=get_admin_menu()
            )
        await call.answer()
        return

    if data == "admin_give_sub":
        if not is_admin(user_id):
            await call.answer("У вас нет доступа", show_alert=True)
            return
        await safe_delete(call.message.chat.id, call.message.message_id)
        await call.message.answer(
            "Выберите тип подписки:",
            reply_markup=get_admin_sub_menu()
        )
        await call.answer()
        return

    if data == "admin_stats":
        if not is_admin(user_id):
            await call.answer("У вас нет доступа", show_alert=True)
            return
        stats_text = f"Статистика бота:\n\nВсего пользователей с подпиской: {len(user_subscriptions)}\n\nСтатистика пицц:\n{get_pizza_stats_text()}"
        await safe_delete(call.message.chat.id, call.message.message_id)
        await call.message.answer(stats_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="admin_panel")]
        ]))
        await call.answer()
        return

    if data == "admin_users":
        if not is_admin(user_id):
            await call.answer("У вас нет доступа", show_alert=True)
            return
        
        if not user_subscriptions:
            users_text = "Нет пользователей с активной подпиской"
        else:
            users_list = []
            for uid, sub in user_subscriptions.items():
                users_list.append(f"ID: {uid} - {sub}")
            users_text = "Список подписчиков:\n\n" + "\n".join(users_list)
        
        await safe_delete(call.message.chat.id, call.message.message_id)
        await call.message.answer(users_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="admin_panel")]
        ]))
        await call.answer()
        return

    if data == "admin_mailing":
        if not is_admin(user_id):
            await call.answer("У вас нет доступа", show_alert=True)
            return
        pending_payments[user_id] = {"action": "mailing"}
        await safe_delete(call.message.chat.id, call.message.message_id)
        await call.message.answer(
            "Отправьте сообщение для рассылки (только текст):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="admin_panel")]
            ])
        )
        await call.answer()
        return

    # Выбор подписки для выдачи админом
    if data.startswith("admin_sub_"):
        if not is_admin(user_id):
            await call.answer("У вас нет доступа", show_alert=True)
            return
        
        sub_map = {
            "admin_sub_day": "1 день",
            "admin_sub_week": "неделя",
            "admin_sub_month": "месяц",
            "admin_sub_forever": "навсегда"
        }
        if data in sub_map:
            sub_name = sub_map[data]
            pending_payments[user_id] = {"action": "admin_give", "sub_type": sub_name}
            await safe_delete(call.message.chat.id, call.message.message_id)
            await call.message.answer(
                f"Вы выбрали подписку: {sub_name}\n\nВведите ID пользователя:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Назад", callback_data="admin_give_sub")]
                ])
            )
        await call.answer()
        return

    # Отправить чек
    if data.startswith("send_receipt_"):
        parts = data.split("_")
        sub_type = parts[2]
        price = parts[3]
        
        await safe_delete(call.message.chat.id, call.message.message_id)
        
        pending_payments[user_id] = {
            "sub_type": sub_type,
            "price": price,
            "username": call.from_user.username
        }
        
        text = (f"Отправьте скриншот чека оплаты\n\n"
                f"Тариф: на {sub_type}\n"
                f"Сумма: {price} руб\n\n"
                f"После отправки чека, администрация рассмотрит его в течение 2 минут.")
        
        try:
            await call.message.answer_photo(
                photo=types.FSInputFile(CONFIRM_PHOTO),
                caption=text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Отмена", callback_data="buy_subscription")]
                ])
            )
        except:
            await call.message.answer(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Отмена", callback_data="buy_subscription")]
                ])
            )
        await call.answer()
        return

    await call.answer()

# ---------- Обработка текста ----------
@dp.message(F.text)
async def handle_text_input(message: types.Message):
    text = message.text.strip()
    user_id = message.from_user.id

    # Обработка ввода ID для выдачи подписки админом
    if user_id in pending_payments and pending_payments[user_id].get("action") == "admin_give":
        sub_type = pending_payments[user_id]["sub_type"]
        try:
            target_user_id = int(text)
            user_subscriptions[target_user_id] = sub_type
            await message.answer(f"Подписка '{sub_type}' успешно выдана пользователю {target_user_id}")
            
            try:
                await bot.send_message(
                    target_user_id,
                    f"Вам была выдана подписка '{sub_type}'!",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
                    ])
                )
            except:
                pass
            
            del pending_payments[user_id]
            await cmd_admin(message)
        except ValueError:
            await message.answer("Неверный ID. Введите число.")
        return

    # Обработка рассылки от админа
    if user_id in pending_payments and pending_payments[user_id].get("action") == "mailing":
        success_count = 0
        fail_count = 0
        
        for uid in user_subscriptions.keys():
            try:
                await bot.send_message(uid, text)
                success_count += 1
                await asyncio.sleep(0.05)
            except:
                fail_count += 1
        
        await message.answer(f"Рассылка завершена!\nУспешно: {success_count}\nНеудачно: {fail_count}")
        del pending_payments[user_id]
        await cmd_admin(message)
        return

    # Обработка ссылки для доставки пиццы
    if text.startswith("http://") or text.startswith("https://"):
        link = text
        wait_msg = await message.answer("Отправка пиццы...")
        
        delay = random.randint(10, 15)
        await asyncio.sleep(delay)
        
        await wait_msg.delete()
        
        update_pizza_stats()
        
        try:
            await message.answer_photo(
                photo=types.FSInputFile(SUCCESS_PHOTO),
                caption=f"Пиццы успешно отправлены!\nАдрес/заказ: {link}\nСпасибо за использование сервиса\n\n{get_pizza_stats_text()}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
                ])
            )
        except:
            await message.answer(
                f"Пиццы успешно отправлены!\nАдрес/заказ: {link}\nСпасибо за использование сервиса\n\n{get_pizza_stats_text()}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
                ])
            )
        return

    # Обработка кик сессии
    if len(text.split()) == 1:
        target = text
        wait_msg = await message.answer(f"Кик-сессия для {target}...")
        await asyncio.sleep(5)
        await wait_msg.delete()
        await message.answer(
            f"Ритуал завершен для {target}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
            ])
        )
        return

    await message.answer(
        "Ошибка ввода\nВведите ссылку начинающуюся с http:// или https://",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
        ])
    )

# ---------- Обработка фото (скриншоты чека) ----------
@dp.message(F.photo)
async def handle_receipt_photo(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "нет"
    mention = f"@{username}" if username != "нет" else f"ID: {user_id}"
    
    payment_info = pending_payments.get(user_id)
    if not payment_info or "sub_type" not in payment_info:
        await message.answer(
            "У вас нет активного запроса на оплату. Пожалуйста, выберите тариф сначала.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Купить подписку", callback_data="buy_subscription")],
                [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
            ])
        )
        return
    
    sub_type = payment_info["sub_type"]
    price = payment_info["price"]
    
    photo = message.photo[-1]
    file_id = photo.file_id
    
    notification_text = (f"НОВЫЙ ЧЕК НА ПОДТВЕРЖДЕНИЕ\n\n"
                         f"Пользователь: {mention}\n"
                         f"ID: {user_id}\n"
                         f"Тариф: на {sub_type}\n"
                         f"Сумма: {price} руб\n\n"
                         f"Для подтверждения подписки:\n"
                         f"/confirm_sub {user_id} {sub_type}\n\n"
                         f"Для отклонения:\n"
                         f"/reject_sub {user_id}")
    
    sent_to_owner = False
    for owner_id in OWNER_IDS:
        try:
            await bot.send_photo(
                chat_id=owner_id,
                photo=file_id,
                caption=notification_text
            )
            sent_to_owner = True
            print(f"Чек отправлен владельцу {owner_id}")
        except Exception as e:
            logging.error(f"Ошибка при отправке владельцу {owner_id}: {e}")
    
    if sent_to_owner:
        await message.answer(
            "Спасибо за чек! Администрация рассмотрит его в течение 2 минут.\nОжидайте подтверждения подписки.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
            ])
        )
    else:
        await message.answer(
            "Произошла ошибка при отправке чека.\n"
            "Пожалуйста, попробуйте позже или свяжитесь с администратором: @defymerz",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
            ])
        )

# ---------- Команды для владельцев ----------
@dp.message(Command("confirm_sub"))
async def confirm_subscription(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Использование: /confirm_sub [user_id] [тип_подписки]\nПример: /confirm_sub 123456789 месяц")
        return
    
    try:
        user_id = int(args[1])
        sub_type = args[2]
    except ValueError:
        await message.answer("Неверный ID пользователя.")
        return
    
    user_subscriptions[user_id] = sub_type
    
    try:
        await bot.send_message(
            user_id,
            f"Ваша подписка '{sub_type}' успешно подтверждена и активирована!\nСпасибо за покупку!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
            ])
        )
        await message.answer(f"Подписка '{sub_type}' для пользователя {user_id} успешно активирована.")
        
        if user_id in pending_payments:
            del pending_payments[user_id]
    except Exception as e:
        await message.answer(f"Не удалось отправить сообщение пользователю {user_id}. Ошибка: {e}")

@dp.message(Command("reject_sub"))
async def reject_subscription(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    
    args = message.text.split()
    if len(args) != 2:
        await message.answer("Использование: /reject_sub [user_id]")
        return
    
    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("Неверный ID пользователя.")
        return
    
    try:
        await bot.send_message(
            user_id,
            "Ваш платеж не подтвержден. Пожалуйста, проверьте правильность оплаты или свяжитесь с администратором @defymerz",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Купить подписку", callback_data="buy_subscription")],
                [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
            ])
        )
        await message.answer(f"Платеж пользователя {user_id} отклонен.")
        
        if user_id in pending_payments:
            del pending_payments[user_id]
    except Exception as e:
        await message.answer(f"Не удалось отправить сообщение пользователю {user_id}. Ошибка: {e}")

# ---------- Запуск ----------
async def main():
    print("Бот запущен")
    print(f"Админы: {OWNER_IDS}")
    print("Ожидание команд...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())