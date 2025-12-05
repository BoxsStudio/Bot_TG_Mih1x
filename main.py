import asyncio
import logging
import feedparser
import requests
import aioschedule
import sqlite3
import os  # Добавили для работы с путями
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН"

SCHEDULE_TIME = "10:00"

# === ВАЖНОЕ ИСПРАВЛЕНИЕ: АБСОЛЮТНЫЙ ПУТЬ К БАЗЕ ===
# Это гарантирует, что файл создается в той же папке, где лежит скрипт
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "bot_database.db")

# Ссылки
RSS_RIA = "https://ria.ru/export/rss2/archive/index.xml"
RSS_LENTA = "https://lenta.ru/rss/news"
HOROSCOPE_URL_TEMPLATE = "https://1001goroskop.ru/?znak={}"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

ZODIAC_SIGNS = {
    "овен": "aries", "телец": "taurus", "близнецы": "gemini",
    "рак": "cancer", "лев": "leo", "дева": "virgo",
    "весы": "libra", "скорпион": "scorpio", "стрелец": "sagittarius",
    "козерог": "capricorn", "водолей": "aquarius", "рыбы": "pisces"
}


# ================= БАЗА ДАННЫХ (С ОТЛАДКОЙ) =================
def init_db():
    """Создает таблицу при старте"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    zodiac TEXT
                )
            """)
            conn.commit()
        print(f"📂 База данных подключена: {DB_FILE}")
    except Exception as e:
        print(f"❌ ОШИБКА СОЗДАНИЯ БД: {e}")


def db_set_user(user_id, zodiac):
    """Сохраняет юзера и пишет об этом в консоль"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO users (user_id, zodiac) VALUES (?, ?)", (user_id, zodiac))
            conn.commit()
        print(f"✅ В БАЗУ ЗАПИСАН: ID={user_id}, Знак={zodiac}")  # ВИДИМ В КОНСОЛИ
    except Exception as e:
        print(f"❌ ОШИБКА ЗАПИСИ В БД: {e}")


def db_get_user_zodiac(user_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT zodiac FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"❌ ОШИБКА ЧТЕНИЯ БД: {e}")
        return None


def db_get_all_users():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, zodiac FROM users")
            return cursor.fetchall()
    except Exception:
        return []


# ================= ИНИЦИАЛИЗАЦИЯ =================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class UserState(StatesGroup):
    waiting_for_zodiac = State()


# ================= ФУНКЦИИ СБОРА ДАННЫХ =================

async def get_currency_rates():
    try:
        fiat = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", headers=HEADERS, timeout=10).json()['Valute']
        usd = fiat['USD']['Value']
        eur = fiat['EUR']['Value']

        crypto = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",
                              headers=HEADERS, timeout=10).json()
        btc = crypto['bitcoin']['usd']
        eth = crypto['ethereum']['usd']

        return (
            f"💱 **Курс валют:**\n"
            f"🇺🇸 USD: {usd:.2f} ₽\n"
            f"🇪🇺 EUR: {eur:.2f} ₽\n"
            f"🪙 BTC: ${btc:,.0f}\n"
            f"💎 ETH: ${eth:,.0f}"
        )
    except Exception:
        return "💱 Курсы валют временно недоступны."


async def parse_rss(url, source_name):
    try:
        response = requests.get(url, headers=HEADERS, timeout=8)
        if 'ria.ru' in url: response.encoding = 'utf-8'

        feed = feedparser.parse(response.content)
        if not feed.entries: return None

        entry = feed.entries[0]
        soup = BeautifulSoup(entry.description if hasattr(entry, 'description') else "", "lxml")
        clean_text = soup.get_text(strip=True)[:200] + "..."

        return f"📰 **Новость ({source_name}):**\n**{entry.title}**\n{clean_text}\n🔗 [Читать]({entry.link})"
    except Exception:
        return None


async def get_news():
    news = await parse_rss(RSS_RIA, "RIA")
    if news: return news
    news = await parse_rss(RSS_LENTA, "Lenta")
    if news: return news
    return "📰 Новости не загрузились."


async def get_horoscope(zodiac_rus):
    eng_name = ZODIAC_SIGNS.get(zodiac_rus)
    if not eng_name: return None
    url = HOROSCOPE_URL_TEMPLATE.format(eng_name)
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'lxml')
        block = soup.find('div', itemprop='description')
        if block: return f"🔮 **Гороскоп ({zodiac_rus.capitalize()}):**\n\n{block.get_text(strip=True)}"
        return "🔮 Гороскоп не найден."
    except Exception:
        return "🔮 Ошибка сайта гороскопов."


async def compile_digest(user_id, zodiac_sign=None):
    if not zodiac_sign:
        zodiac_sign = db_get_user_zodiac(user_id)
    if not zodiac_sign: return None

    res_horoscope, res_currency, res_news = await asyncio.gather(
        get_horoscope(zodiac_sign),
        get_currency_rates(),
        get_news()
    )
    return f"{res_horoscope}\n\n{res_currency}\n\n{res_news}"


# ================= ХЕНДЛЕРЫ =================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # ПРОВЕРЯЕМ, ЕСТЬ ЛИ ЮЗЕР В БАЗЕ УЖЕ СЕЙЧАС
    user_zodiac = db_get_user_zodiac(message.from_user.id)

    if user_zodiac:
        await message.answer(
            f"Привет! 👋 Я тебя помню. Твой знак: **{user_zodiac.capitalize()}**.\n"
            "Нажми /today для получения сводки или /set_zodiac, чтобы изменить знак."
        )
    else:
        await message.answer("Привет! ☀️ Я тебя не знаю. Давай познакомимся. Нажми /set_zodiac")


@dp.message(Command("set_zodiac"))
async def cmd_set_zodiac(message: types.Message, state: FSMContext):
    kb = [
        [types.KeyboardButton(text="Овен"), types.KeyboardButton(text="Телец"), types.KeyboardButton(text="Близнецы")],
        [types.KeyboardButton(text="Рак"), types.KeyboardButton(text="Лев"), types.KeyboardButton(text="Дева")],
        [types.KeyboardButton(text="Весы"), types.KeyboardButton(text="Скорпион"),
         types.KeyboardButton(text="Стрелец")],
        [types.KeyboardButton(text="Козерог"), types.KeyboardButton(text="Водолей"), types.KeyboardButton(text="Рыбы")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Выбери свой знак:", reply_markup=keyboard)
    await state.set_state(UserState.waiting_for_zodiac)


@dp.message(UserState.waiting_for_zodiac)
async def process_zodiac(message: types.Message, state: FSMContext):
    sign = message.text.lower().strip()
    if sign not in ZODIAC_SIGNS:
        await message.answer("Выбери знак кнопкой.")
        return

    # === ВЫЗЫВАЕМ СОХРАНЕНИЕ ===
    db_set_user(message.from_user.id, sign)

    await message.answer(f"✅ Отлично! Я сохранил знак **{sign.capitalize()}** в базу данных.\nТеперь нажми /today.",
                         reply_markup=types.ReplyKeyboardRemove())
    await state.clear()


@dp.message(Command("today"))
async def cmd_today(message: types.Message):
    zodiac = db_get_user_zodiac(message.from_user.id)
    if not zodiac:
        await message.answer("Я не нашел тебя в базе. Нажми /set_zodiac")
        return
    wait_msg = await message.answer("☕ Собираю данные...")
    text = await compile_digest(message.from_user.id, zodiac)
    await wait_msg.delete()
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)


# Команда проверки базы (для тебя)
@dp.message(Command("check_db"))
async def cmd_check_db(message: types.Message):
    users = db_get_all_users()
    count = len(users)
    await message.answer(f"📊 В базе данных сейчас: {count} пользователей.")


# ================= ЗАПУСК =================
async def scheduler():
    aioschedule.every().day.at(SCHEDULE_TIME).do(send_daily_broadcast)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def send_daily_broadcast():
    users = db_get_all_users()
    if not users: return
    currency = await get_currency_rates()
    news = await get_news()
    for user_id, zodiac in users:
        horoscope = await get_horoscope(zodiac)
        try:
            await bot.send_message(user_id, f"{horoscope}\n\n{currency}\n\n{news}", parse_mode="Markdown",
                                   disable_web_page_preview=True)
            await asyncio.sleep(0.1)
        except Exception:
            pass


async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()  # Создаем файл БД
    asyncio.create_task(scheduler())
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Бот запущен! Следи за консолью, там будут сообщения о записи в БД.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())