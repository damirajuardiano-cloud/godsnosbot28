import asyncio
import logging
import random
import json
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.enums import ParseMode
from aiogram.types import Message

# ===== НАСТРОЙКИ =====
TOKEN = "8765817388:AAHJ4FRJ4E_ILdFQot3H3qjWi3od8WX8tHY"
CHANNEL_LINK = "https://t.me/xivviiiiii/3"
OWNER_USERNAME_1 = "defymerz"
OWNER_USERNAME_2 = "ssvs877"

# Кошелек Tonkeeper
TONKEEPER_WALLET = "UQAbML7ypTCu8-c49B2hnFRDgiI5IhEFZWvj7iN_nyZmpXZq"

# ID владельцев
OWNER_IDS = [8581847345, 1002296130]

# Файл для сохранения данных
DATA_FILE = "bot_data.json"

# ===== СТАТИСТИКА =====
pizza_stats = {
    "delivered": 227,
    "cancelled": 20,
    "total": 300
}

user_stats = {
    "total_users": 0,
    "active_today": 0
}

def update_pizza_stats():
    pizza_stats["delivered"] = random.randint(180, 290)
    pizza_stats["cancelled"] = random.randint(5, 45)
    pizza_stats["total"] = pizza_stats["delivered"] + pizza_stats["cancelled"]
    save_data()

def get_pizza_stats_text():
    return (f"- Сколько отправлено пицц: {pizza_stats['delivered']}\n"
            f"- Сколько отмененных пицц: {pizza_stats['cancelled']}\n"
            f"- Сколько всего пицц: {pizza_stats['total']}")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_subs = {}
pending_payments = {}
user_activity = {}

STARS_PRICES = {
    "day": 120,
    "week": 300,
    "month": 450,
    "forever": 650
}

RUB_PRICES = {
    "day": 100,
    "week": 350,
    "month": 550,
    "forever": 880
}

HUMAN_NAMES = {
    "day": "1 день",
    "week": "неделя",
    "month": "месяц",
    "forever": "навсегда"
}

# ===== СОХРАНЕНИЕ И ЗАГРУЗКА ДАННЫХ =====
def save_data():
    """Сохраняет все данные в JSON файл"""
    data = {
        "user_subs": {},
        "pizza_stats": pizza_stats,
        "user_activity": {}
    }
    
    # Сохраняем подписки с датами в строковом формате
    for user_id, sub in user_subs.items():
        data["user_subs"][str(user_id)] = {
            "code": sub["code"],
            "start": sub["start"].isoformat(),
            "end": sub["end"].isoformat() if sub["end"] else None,
            "human": sub["human"]
        }
    
    # Сохраняем активность
    for user_id, days in user_activity.items():
        data["user_activity"][str(user_id)] = days
    
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info("Данные сохранены")
    except Exception as e:
        logging.error(f"Ошибка сохранения данных: {e}")

def load_data():
    """Загружает данные из JSON файла"""
    global user_subs, pizza_stats, user_activity
    
    if not os.path.exists(DATA_FILE):
        logging.info("Файл с данными не найден, создаем новый")
        return
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Загружаем подписки
        for user_id_str, sub_data in data.get("user_subs", {}).items():
            user_id = int(user_id_str)
            start_date = datetime.fromisoformat(sub_data["start"])
            end_date = datetime.fromisoformat(sub_data["end"]) if sub_data["end"] else None
            
            user_subs[user_id] = {
                "code": sub_data["code"],
                "start": start_date,
                "end": end_date,
                "human": sub_data["human"]
            }
        
        # Загружаем статистику пицц
        pizza_stats = data.get("pizza_stats", pizza_stats)
        
        # Загружаем активность
        user_activity = {}
        for user_id_str, days in data.get("user_activity", {}).items():
            user_activity[int(user_id_str)] = days
        
        logging.info(f"Загружено {len(user_subs)} подписок")
    except Exception as e:
        logging.error(f"Ошибка загрузки данных: {e}")

# Преобразование человеческого названия в код
def parse_sub_type(sub_type_str: str) -> str:
    sub_type_str = sub_type_str.lower().strip()
    if sub_type_str in ["день", "1 день", "day"]:
        return "day"
    elif sub_type_str in ["неделя", "неделю", "week"]:
        return "week"
    elif sub_type_str in ["месяц", "month"]:
        return "month"
    elif sub_type_str in ["навсегда", "forever"]:
        return "forever"
    return None

# Проверка подписки
def has_active_subscription(user_id: int) -> bool:
    if user_id in OWNER_IDS:
        return True
    if user_id not in user_subs:
        return False
    sub = user_subs[user_id]
    if sub["code"] == "forever":
        return True
    if sub["end"] is None:
        return False
    return sub["end"] > datetime.now()

# Выдача подписки
async def grant_subscription(user_id: int, sub_code: str, start_date: datetime = None, notify: bool = True):
    if start_date is None:
        start_date = datetime.now()
    
    if sub_code == "day":
        end_date = start_date + timedelta(days=1)
    elif sub_code == "week":
        end_date = start_date + timedelta(days=7)
    elif sub_code == "month":
        end_date = start_date + timedelta(days=30)
    else:
        end_date = None
    
    user_subs[user_id] = {
        "code": sub_code,
        "start": start_date,
        "end": end_date,
        "human": HUMAN_NAMES[sub_code]
    }
    
    # Сохраняем данные после выдачи подписки
    save_data()
    
    if notify:
        try:
            await bot.send_message(
                user_id,
                f"Подписка \"{HUMAN_NAMES[sub_code]}\" успешно активирована!\n\n"
                f"Дата начала: {start_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"Действует до: {'бессрочно' if end_date is None else end_date.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Спасибо за покупку!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
                ])
            )
        except:
            pass

# Обновление активности
def update_user_activity(user_id: int):
    today = datetime.now().strftime('%Y%m%d')
    if user_id not in user_activity:
        user_activity[user_id] = {}
    user_activity[user_id][today] = True
    save_data()

# ---------- МЕНЮ ----------
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Запустить доставку", callback_data="start_delivery")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile"),
         InlineKeyboardButton(text="Купить подписку", callback_data="buy_subscription")],
        [InlineKeyboardButton(text="Владельцы бота", callback_data="owner_channel")]
    ])
    return keyboard

def get_owner_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Основной владелец", url="https://t.me/oltdd")],
        [InlineKeyboardButton(text="Второй владелец", url="https://t.me/xivividekorol")],
        [InlineKeyboardButton(text="Резервный канал", url="https://t.me/xivviiiiii")],
        [InlineKeyboardButton(text="Основной канал", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
    ])
    return keyboard

def get_subscription_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Telegram Stars (авто)", callback_data="payment_method_stars")],
        [InlineKeyboardButton(text="Tonkeeper (чек)", callback_data="payment_method_tonkeeper")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
    ])
    return keyboard

def get_stars_tariff_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день - 120 Stars", callback_data="stars_day")],
        [InlineKeyboardButton(text="7 дней - 300 Stars", callback_data="stars_week")],
        [InlineKeyboardButton(text="30 дней - 450 Stars", callback_data="stars_month")],
        [InlineKeyboardButton(text="Навсегда - 650 Stars", callback_data="stars_forever")],
        [InlineKeyboardButton(text="Назад", callback_data="buy_subscription")]
    ])
    return keyboard

def get_tonkeeper_tariff_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день - 100 руб", callback_data="tonkeeper_day")],
        [InlineKeyboardButton(text="7 дней - 350 руб", callback_data="tonkeeper_week")],
        [InlineKeyboardButton(text="30 дней - 550 руб", callback_data="tonkeeper_month")],
        [InlineKeyboardButton(text="Навсегда - 880 руб", callback_data="tonkeeper_forever")],
        [InlineKeyboardButton(text="Назад", callback_data="buy_subscription")]
    ])
    return keyboard

def get_tonkeeper_payment_menu(sub_type, price):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отправить чек", callback_data=f"send_receipt_{sub_type}_{price}")],
        [InlineKeyboardButton(text="Назад", callback_data="payment_method_tonkeeper")]
    ])
    return keyboard

def get_no_subscription_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить подписку", callback_data="buy_subscription")],
        [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard

def get_admin_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выдать подписку", callback_data="admin_give_sub")],
        [InlineKeyboardButton(text="Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="Рассылка", callback_data="admin_mailing")],
        [InlineKeyboardButton(text="Список подписчиков", callback_data="admin_users")],
        [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard

def get_admin_sub_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="На 1 день", callback_data="admin_sub_day")],
        [InlineKeyboardButton(text="На неделю", callback_data="admin_sub_week")],
        [InlineKeyboardButton(text="На месяц", callback_data="admin_sub_month")],
        [InlineKeyboardButton(text="Навсегда", callback_data="admin_sub_forever")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_panel")]
    ])
    return keyboard

def is_admin(user_id):
    return user_id in OWNER_IDS

# ---------- ОБНОВЛЕНИЕ СООБЩЕНИЯ ----------
async def update_menu(message, new_text, new_markup):
    try:
        await message.edit_text(
            text=new_text,
            reply_markup=new_markup
        )
    except:
        try:
            await message.edit_caption(
                caption=new_text,
                reply_markup=new_markup
            )
        except:
            await message.delete()
            await message.answer(
                new_text,
                reply_markup=new_markup
            )

# ---------- КОМАНДЫ ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    if username == OWNER_USERNAME_1 or username == OWNER_USERNAME_2:
        if user_id not in OWNER_IDS:
            OWNER_IDS.append(user_id)
            print(f"Добавлен владелец: {username} (ID: {user_id})")
        await message.answer(f"Вы идентифицированы как владелец!\nВаш ID: {user_id}\n\nАдмин панель доступна по команде /admin")
    
    update_user_activity(user_id)
    
    await message.answer(
        "Главное меню\n\nВыберите действие:",
        reply_markup=get_main_menu()
    )

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("Вы не являетесь администратором.\n\nЧтобы стать администратором, напишите владельцу бота: @defymerz")
        return
    
    await message.answer(
        "Админ панель\n\nВыберите действие:",
        reply_markup=get_admin_menu()
    )

@dp.message(Command("confirm_sub"))
async def confirm_subscription(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Использование: /confirm_sub [user_id] [тип_подписки]\nПример: /confirm_sub 123456789 день")
        return
    
    try:
        user_id = int(args[1])
        sub_human = " ".join(args[2:])
        sub_code = parse_sub_type(sub_human)
        
        if sub_code is None:
            await message.answer("Неверный тип подписки. Используйте: день, неделя, месяц, навсегда")
            return
    except ValueError:
        await message.answer("Неверный ID пользователя.")
        return
    
    await grant_subscription(user_id, sub_code, notify=True)
    await message.answer(f"Подписка '{HUMAN_NAMES[sub_code]}' для пользователя {user_id} успешно активирована.")
    
    if user_id in pending_payments:
        del pending_payments[user_id]

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

# ---------- ОБРАБОТЧИКИ КНОПОК ----------
@dp.callback_query()
async def handle_callbacks(call: CallbackQuery):
    data = call.data
    user_id = call.from_user.id
    update_user_activity(user_id)

    if data == "back_to_menu":
        await update_menu(
            call.message,
            "Главное меню\n\nВыберите действие:",
            get_main_menu()
        )
        await call.answer()
        return

    # ДОСТАВКА С ПРОВЕРКОЙ ПОДПИСКИ
    if data == "start_delivery":
        if not has_active_subscription(user_id):
            await update_menu(
                call.message,
                "У вас нет активной подписки!\n\nВы не можете пользоваться доставкой без подписки.\n\nОформите подписку, чтобы получить доступ к сервису.",
                get_no_subscription_menu()
            )
            await call.answer()
            return
        
        await update_menu(
            call.message,
            "Доставка пиццы\n\nОтправьте публичную ссылку на заказ/адрес:\n\nПример: https://t.me/@username",
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
            ])
        )
        await call.answer()
        return

    if data == "profile":
        username = call.from_user.username if call.from_user.username else "нет"
        
        if user_id in user_subs:
            sub = user_subs[user_id]
            if sub["code"] == "forever":
                end_text = "бессрочно"
            else:
                end_text = sub["end"].strftime('%d.%m.%Y %H:%M') if sub["end"] else "бессрочно"
            
            is_active = has_active_subscription(user_id)
            status_text = "Активна" if is_active else "Истекла"
            
            text = (f"Профиль\n\n"
                    f"ID: {user_id}\n"
                    f"Ник: @{username}\n"
                    f"Подписка: {sub['human']}\n"
                    f"Статус: {status_text}\n"
                    f"Дата покупки: {sub['start'].strftime('%d.%m.%Y %H:%M')}\n"
                    f"Действует до: {end_text}")
        else:
            text = (f"Профиль\n\n"
                    f"ID: {user_id}\n"
                    f"Ник: @{username}\n"
                    f"Подписка: Нет подписки\n\n"
                    f"Купите подписку, чтобы пользоваться доставкой!")
        
        await update_menu(
            call.message,
            text,
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Купить подписку", callback_data="buy_subscription")],
                [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
            ])
        )
        await call.answer()
        return

    if data == "owner_channel":
        await update_menu(
            call.message,
            "Владельцы проекта",
            get_owner_menu()
        )
        await call.answer()
        return

    if data == "buy_subscription":
        await update_menu(
            call.message,
            "Выбор способа оплаты\n\nВыберите способ оплаты:",
            get_subscription_menu()
        )
        await call.answer()
        return

    if data == "payment_method_stars":
        await update_menu(
            call.message,
            "Выберите тариф (оплата Stars):",
            get_stars_tariff_menu()
        )
        await call.answer()
        return

    if data == "payment_method_tonkeeper":
        await update_menu(
            call.message,
            "Выберите тариф (оплата Tonkeeper):",
            get_tonkeeper_tariff_menu()
        )
        await call.answer()
        return

    if data.startswith("stars_"):
        sub_map = {
            "stars_day": "day",
            "stars_week": "week",
            "stars_month": "month",
            "stars_forever": "forever"
        }
        if data in sub_map:
            sub_code = sub_map[data]
            price = STARS_PRICES[sub_code]
            prices = [LabeledPrice(label="Подписка", amount=price)]
            
            await bot.send_invoice(
                chat_id=user_id,
                title=f"Подписка на {HUMAN_NAMES[sub_code]}",
                description=f"Оплата подписки на {HUMAN_NAMES[sub_code]} через Telegram Stars",
                payload=f"sub_{data}",
                provider_token="",
                currency="XTR",
                prices=prices,
                start_parameter="subscription"
            )
        await call.answer()
        return

    if data.startswith("tonkeeper_"):
        sub_map = {
            "tonkeeper_day": ("день", 100, "day"),
            "tonkeeper_week": ("неделю", 350, "week"),
            "tonkeeper_month": ("месяц", 550, "month"),
            "tonkeeper_forever": ("навсегда", 880, "forever")
        }
        if data in sub_map:
            sub_name, price, sub_code = sub_map[data]
            pending_payments[user_id] = {
                "action": "awaiting_receipt",
                "sub_name": sub_name,
                "sub_code": sub_code,
                "price": price
            }
            
            text = (f"Оплата через Tonkeeper\n\n"
                    f"Тариф: на {sub_name}\n"
                    f"Сумма: {price} руб\n\n"
                    f"Адрес кошелька:\n{TONKEEPER_WALLET}\n\n"
                    f"Переведите ровно {price} руб для покупки подписки\n\n"
                    f"После оплаты нажмите на кнопку Отправить чек")
            
            await update_menu(
                call.message,
                text,
                get_tonkeeper_payment_menu(sub_name, price)
            )
        await call.answer()
        return

    if data.startswith("send_receipt_"):
        parts = data.split("_")
        sub_type = parts[2]
        price = parts[3]
        
        if user_id in pending_payments and pending_payments[user_id].get("action") == "awaiting_receipt":
            pending_payments[user_id]["sub_name"] = sub_type
            pending_payments[user_id]["price"] = price
        
        text = (f"Отправьте скриншот чека оплаты\n\n"
                f"Тариф: на {sub_type}\n"
                f"Сумма: {price} руб\n\n"
                f"После отправки чека, администрация рассмотрит его в течение 2 минут.")
        
        await update_menu(
            call.message,
            text,
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Отмена", callback_data="buy_subscription")]
            ])
        )
        await call.answer()
        return

    # АДМИН ПАНЕЛЬ
    if data == "admin_panel":
        if not is_admin(user_id):
            await call.answer("У вас нет доступа", show_alert=True)
            return
        await update_menu(
            call.message,
            "Админ панель\n\nВыберите действие:",
            get_admin_menu()
        )
        await call.answer()
        return

    if data == "admin_give_sub":
        if not is_admin(user_id):
            await call.answer("У вас нет доступа", show_alert=True)
            return
        await update_menu(
            call.message,
            "Выберите тип подписки:",
            get_admin_sub_menu()
        )
        await call.answer()
        return

    if data == "admin_stats":
        if not is_admin(user_id):
            await call.answer("У вас нет доступа", show_alert=True)
            return
        
        active_count = 0
        for uid in user_subs:
            if has_active_subscription(uid):
                active_count += 1
        
        today = datetime.now().strftime('%Y%m%d')
        active_today = 0
        for uid, days in user_activity.items():
            if today in days:
                active_today += 1
        
        stats_text = (f"Статистика бота:\n\n"
                      f"Всего пользователей с подпиской: {len(user_subs)}\n"
                      f"Активных подписок: {active_count}\n"
                      f"Активно сегодня: {active_today}\n\n"
                      f"Статистика пицц:\n{get_pizza_stats_text()}")
        
        await update_menu(
            call.message,
            stats_text,
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="admin_panel")]
            ])
        )
        await call.answer()
        return

    if data == "admin_users":
        if not is_admin(user_id):
            await call.answer("У вас нет доступа", show_alert=True)
            return
        
        if not user_subs:
            users_text = "Нет пользователей с подпиской"
        else:
            users_list = []
            for uid, sub in user_subs.items():
                status = "активна" if has_active_subscription(uid) else "просрочена"
                users_list.append(f"ID: {uid} - {sub['human']} ({status})")
            users_text = "Список подписчиков:\n\n" + "\n".join(users_list[:50])
            if len(users_list) > 50:
                users_text += f"\n\n...и еще {len(users_list) - 50} пользователей"
        
        await update_menu(
            call.message,
            users_text,
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="admin_panel")]
            ])
        )
        await call.answer()
        return

    if data == "admin_mailing":
        if not is_admin(user_id):
            await call.answer("У вас нет доступа", show_alert=True)
            return
        pending_payments[user_id] = {"action": "mailing"}
        await update_menu(
            call.message,
            "Отправьте сообщение для рассылки (только текст):\n\nСообщение получит ВСЕ пользователи с подпиской!",
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="admin_panel")]
            ])
        )
        await call.answer()
        return

    if data.startswith("admin_sub_"):
        if not is_admin(user_id):
            await call.answer("У вас нет доступа", show_alert=True)
            return
        
        sub_map = {
            "admin_sub_day": "day",
            "admin_sub_week": "week",
            "admin_sub_month": "month",
            "admin_sub_forever": "forever"
        }
        if data in sub_map:
            sub_code = sub_map[data]
            pending_payments[user_id] = {"action": "admin_give", "sub_code": sub_code}
            await update_menu(
                call.message,
                f"Вы выбрали подписку: {HUMAN_NAMES[sub_code]}\n\nВведите ID пользователя:",
                InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Назад", callback_data="admin_give_sub")]
                ])
            )
        await call.answer()
        return

    await call.answer()

# ---------- ТЕКСТОВЫЕ СООБЩЕНИЯ ----------
@dp.message(F.text & ~F.text.startswith('/'))
async def handle_text_input(message: types.Message):
    text = message.text.strip()
    user_id = message.from_user.id
    update_user_activity(user_id)

    # Выдача подписки админом
    if user_id in pending_payments and pending_payments[user_id].get("action") == "admin_give":
        sub_code = pending_payments[user_id]["sub_code"]
        try:
            target_user_id = int(text)
            await grant_subscription(target_user_id, sub_code, notify=True)
            await message.answer(f"Подписка '{HUMAN_NAMES[sub_code]}' успешно выдана пользователю {target_user_id}")
            del pending_payments[user_id]
            await cmd_admin(message)
        except ValueError:
            await message.answer("Неверный ID. Введите число.")
        return

    # Рассылка
    if user_id in pending_payments and pending_payments[user_id].get("action") == "mailing":
        success_count = 0
        fail_count = 0
        
        for uid in user_subs.keys():
            try:
                await bot.send_message(uid, f"Рассылка от администрации:\n\n{text}")
                success_count += 1
                await asyncio.sleep(0.05)
            except:
                fail_count += 1
        
        await message.answer(f"Рассылка завершена!\nУспешно: {success_count}\nНеудачно: {fail_count}")
        del pending_payments[user_id]
        await cmd_admin(message)
        return

    # Доставка пиццы (только с подпиской)
    if text.startswith("http://") or text.startswith("https://"):
        if not has_active_subscription(user_id):
            await message.answer(
                "У вас нет активной подписки!\n\nВы не можете пользоваться доставкой без подписки.\n\nОформите подписку, чтобы получить доступ к сервису.",
                reply_markup=get_no_subscription_menu()
            )
            return
        
        link = text
        wait_msg = await message.answer("Отправка пиццы...")
        
        delay = random.randint(10, 15)
        await asyncio.sleep(delay)
        
        await wait_msg.delete()
        update_pizza_stats()
        
        await message.answer(
            f"Пиццы успешно отправлены!\nАдрес/заказ: {link}\nСпасибо за использование сервиса\n\n{get_pizza_stats_text()}",
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

# ---------- ФОТО (ЧЕКИ) ----------
@dp.message(F.photo)
async def handle_receipt_photo(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "нет"
    mention = f"@{username}" if username != "нет" else f"ID: {user_id}"
    
    payment_info = pending_payments.get(user_id)
    if not payment_info or payment_info.get("action") != "awaiting_receipt":
        await message.answer(
            "У вас нет активного запроса на оплату. Пожалуйста, выберите тариф сначала.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Купить подписку", callback_data="buy_subscription")],
                [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
            ])
        )
        return
    
    sub_name = payment_info.get("sub_name", "подписка")
    price = payment_info.get("price", "0")
    
    photo = message.photo[-1]
    file_id = photo.file_id
    
    notification_text = (f"НОВЫЙ ЧЕК НА ПОДТВЕРЖДЕНИЕ\n\n"
                         f"Пользователь: {mention}\n"
                         f"ID: {user_id}\n"
                         f"Тариф: на {sub_name}\n"
                         f"Сумма: {price} руб\n\n"
                         f"Для подтверждения подписки:\n"
                         f"/confirm_sub {user_id} {sub_name}\n\n"
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
        except Exception as e:
            logging.error(f"Ошибка при отправке владельцу {owner_id}: {e}")
    
    if sent_to_owner:
        await message.answer(
            "Спасибо за чек! Администрация рассмотрит его в течение 2 минут. Ожидайте подтверждения подписки.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
            ])
        )
    else:
        await message.answer(
            "Произошла ошибка при отправке чека.\nПожалуйста, попробуйте позже или свяжитесь с администратором: @defymerz",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
            ])
        )

@dp.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    user_id = message.from_user.id
    amount = message.successful_payment.total_amount // 1
    
    if amount == 120:
        sub_code = "day"
    elif amount == 300:
        sub_code = "week"
    elif amount == 450:
        sub_code = "month"
    elif amount == 650:
        sub_code = "forever"
    else:
        sub_code = "day"
    
    await grant_subscription(user_id, sub_code, notify=True)
    
    await message.answer(
        f"Оплата прошла успешно!\nПодписка \"{HUMAN_NAMES[sub_code]}\" активирована.\n\nСпасибо за покупку!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
        ])
    )

# ---------- ЗАПУСК ----------
async def main():
    # Загружаем сохраненные данные
    load_data()
    
    print("Бот запущен")
    print(f"Админы: {OWNER_IDS}")
    print(f"Загружено подписок: {len(user_subs)}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())