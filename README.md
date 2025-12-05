<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Документация: Morning Digest Bot</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #24292e;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f6f8fa;
        }
        .container {
            background: #ffffff;
            padding: 40px;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        h1 { border-bottom: 2px solid #eaecef; padding-bottom: 10px; color: #0366d6; }
        h2 { border-bottom: 1px solid #eaecef; padding-bottom: 5px; margin-top: 35px; }
        h3 { margin-top: 25px; }
        code {
            background-color: #f6f8fa;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
            font-size: 0.9em;
            color: #d73a49;
        }
        pre {
            background-color: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            line-height: 1.45;
            border: 1px solid #e1e4e8;
        }
        pre code {
            background-color: transparent;
            color: #24292e;
            padding: 0;
            border: none;
        }
        .badges img { margin-right: 5px; }
        .feature-list li { margin-bottom: 10px; }
        .warning {
            background-color: #fff5b1;
            padding: 15px;
            border-left: 5px solid #f9c513;
            margin: 20px 0;
        }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #dfe2e5; padding: 10px; text-align: left; }
        th { background-color: #f6f8fa; }
    </style>
</head>
<body>

<div class="container">

    <!-- Заголовок -->
    <header>
        <h1>🌞 Morning Digest Telegram Bot</h1>
        <p>Автономный Telegram-бот для утренних сводок: гороскопы, валюты и новости.</p>
        
        <div class="badges">
            <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python" alt="Python">
            <img src="https://img.shields.io/badge/Aiogram-3.x-blue?logo=telegram" alt="Aiogram">
            <img src="https://img.shields.io/badge/Database-SQLite-green?logo=sqlite" alt="SQLite">
            <img src="https://img.shields.io/badge/Build-Stable-brightgreen" alt="Status">
        </div>
    </header>

    <!-- Описание функционала -->
    <section>
        <h2>✨ Основные возможности</h2>
        <ul class="feature-list">
            <li>🔮 <strong>Персональный гороскоп:</strong> Парсинг сайта <i>1001goroskop.ru</i> с автоматическим исправлением кодировки (fix Windows-1251).</li>
            <li>💱 <strong>Финансы:</strong> Актуальные курсы валют (ЦБ РФ) и криптовалют (CoinGecko API).</li>
            <li>📰 <strong>Умные новости (Smart News):</strong> 
                <ul>
                    <li>Основной источник: РИА Новости.</li>
                    <li>Резервный канал: Lenta.ru (автоматическое переключение при блокировке).</li>
                    <li>Имитация реального браузера для обхода защиты от ботов.</li>
                </ul>
            </li>
            <li>⏰ <strong>Планировщик:</strong> Автоматическая утренняя рассылка (по умолчанию в 08:00).</li>
            <li>💾 <strong>Надежная БД:</strong> SQLite с абсолютными путями (защита от потери данных при перезапуске).</li>
        </ul>
    </section>

    <!-- Установка -->
    <section>
        <h2>🚀 Установка и запуск</h2>
        
        <h3>1. Подготовка окружения</h3>
        <p>Клонируйте репозиторий и создайте виртуальное окружение:</p>
        <pre><code>git clone https://github.com/username/morning-bot.git
cd morning-bot
python -m venv venv
# Активация:
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate</code></pre>

        <h3>2. Установка зависимостей</h3>
        <pre><code>pip install aiogram requests feedparser beautifulsoup4 lxml aioschedule</code></pre>

        <h3>3. Настройка конфигурации</h3>
        <p>Откройте файл <code>main.py</code> и укажите свой токен:</p>
        <pre><code># ================= НАСТРОЙКИ =================
BOT_TOKEN = "ВАШ_ТОКЕН_ОТ_BOTFATHER"
SCHEDULE_TIME = "08:00"  # Время рассылки</code></pre>

        <h3>4. Запуск</h3>
        <pre><code>python main.py</code></pre>
        <p><i>После запуска автоматически создастся файл <code>bot_database.db</code> в папке проекта.</i></p>
    </section>

    <!-- Команды -->
    <section>
        <h2>📱 Команды бота</h2>
        <table>
            <thead>
                <tr>
                    <th>Команда</th>
                    <th>Описание</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><code>/start</code></td>
                    <td>Приветствие, проверка наличия пользователя в БД.</td>
                </tr>
                <tr>
                    <td><code>/set_zodiac</code></td>
                    <td>Выбор знака зодиака через интерактивное меню.</td>
                </tr>
                <tr>
                    <td><code>/today</code></td>
                    <td>Принудительное получение сводки прямо сейчас.</td>
                </tr>
                <tr>
                    <td><code>/check_db</code></td>
                    <td>(Админ) Показать количество пользователей в базе.</td>
                </tr>
            </tbody>
        </table>
    </section>

    <!-- Технические детали -->
    <section>
        <h2>💡 Технические решения</h2>
        <div class="warning">
            <strong>Важно:</strong> Бот использует абсолютные пути для базы данных (<code>os.path.abspath</code>). Это решает проблему "потери" пользователей при запуске через планировщики задач или Docker.
        </div>
        
        <h3>Стек технологий:</h3>
        <ul>
            <li><strong>Язык:</strong> Python 3.9+</li>
            <li><strong>Фреймворк:</strong> Aiogram 3.x (асинхронный)</li>
            <li><strong>Парсинг:</strong> BeautifulSoup4 + lxml</li>
            <li><strong>HTTP Клиент:</strong> Requests (с User-Agent headers)</li>
            <li><strong>База данных:</strong> SQLite3</li>
        </ul>
    </section>

    <!-- Футер -->
    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #eaecef; text-align: center; color: #586069;">
        <p>Разработано на Python ❤️ | 2023</p>
    </footer>

</div>

</body>
</html>
