import requests
import sqlite3
import schedule
import time
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7923861978:AAGWrEPgItrlkzBtmYmIXdbKNdNJVb4UPBw")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "354c41fa243c4677a4491f35884d1fcb")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "ad9b0b15337042daad8d7597354db4ee")
RENDER_URL = os.getenv("RENDER_URL", "https://trading-bot-jarvis.onrender.com")  # Cambia por tu URL en Render

# Base de datos para alertas
conn = sqlite3.connect("alerts.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS alerts (symbol TEXT, target_price REAL, chat_id INTEGER)")

# Función para obtener precios
def get_real_time_price(symbol: str) -> float:
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVE_DATA_API_KEY}"
    response = requests.get(url).json()
    return float(response["price"])

# Mensaje de inicio personalizado
def start(update: Update, context: CallbackContext):
    update.message.reply_text("¿En qué puedo ayudarle, Señor? 👨💼\n\n"
                            "Comandos disponibles:\n"
                            "/precios - Muestra cotizaciones en tiempo real\n"
                            "/alerta <activo> <precio> - Configura una alerta\n"
                            "/noticias - Últimas noticias financieras")

# Comando /precios
def precios(update: Update, context: CallbackContext):
    symbols = {
        "BTC": "BTC/USD",
        "ETH": "ETH/USD",
        "ORO": "XAU/USD",
        "EURUSD": "EUR/USD",
        "EURJPY": "EUR/JPY",
        "USDJPY": "USD/JPY",
        "NASDAQ": "IXIC"
    }
    
    message = "📊 Cotizaciones en tiempo real:\n"
    for name, symbol in symbols.items():
        try:
            price = get_real_time_price(symbol)
            message += f"{name}: {price:.2f}\n"
        except:
            message += f"{name}: Error al obtener datos\n"
    
    update.message.reply_text(message)

# Comando /alerta
def set_alerta(update: Update, context: CallbackContext):
    args = context.args
    if len(args) != 2:
        update.message.reply_text("Uso: /alerta <activo> <precio>\nEjemplo: /alerta BTC 50000")
        return
    
    symbol, target_price = args[0].upper(), float(args[1])
    cursor.execute("INSERT INTO alerts VALUES (?, ?, ?)", (symbol, target_price, update.message.chat_id))
    conn.commit()
    update.message.reply_text(f"✅ Alerta configurada: {symbol} a {target_price}")

# Función para obtener noticias
def fetch_news(context: CallbackContext, chat_id: int):
    url = f"https://newsapi.org/v2/everything?q=bitcoin+OR+forex+OR+NASDAQ&language=es&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    news = requests.get(url).json()
    for article in news["articles"][:3]:
        context.bot.send_message(
            chat_id=chat_id,
            text=f"📰 *{article['title']}*\n{article['url']}",
            parse_mode="Markdown"
        )

# Comando /noticias
def noticias(update: Update, context: CallbackContext):
    fetch_news(context, update.message.chat_id)

# Verificar alertas
def check_alerts(context: CallbackContext):
    cursor.execute("SELECT * FROM alerts")
    for alert in cursor.fetchall():
        symbol, target_price, chat_id = alert
        current_price = get_real_time_price(symbol)
        if current_price >= target_price:
            context.bot.send_message(
                chat_id=chat_id,
                text=f"🚨 *{symbol}* ha alcanzado *{current_price:.2f}* (Objetivo: {target_price})",
                parse_mode="Markdown"
            )
            cursor.execute("DELETE FROM alerts WHERE symbol=? AND target_price=?", (symbol, target_price))
            conn.commit()

# Enviar noticias al abrir el mercado (8:00 AM UTC)
def send_market_open_news(context: CallbackContext):
    now = datetime.utcnow()
    if now.hour == 8 and now.minute == 0:
        fetch_news(context, context.job.context)

# Inicializar el bot con webhook
def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    # Comandos
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("precios", precios))
    dp.add_handler(CommandHandler("alerta", set_alerta))
    dp.add_handler(CommandHandler("noticias", noticias))

    # Programar tareas
    job_queue = updater.job_queue
    job_queue.run_repeating(check_alerts, interval=60, first=0)  # Cada 1 minuto
    job_queue.run_repeating(lambda ctx: fetch_news(ctx, TU_CHAT_ID), interval=10800, first=0)  # Cada 3 horas
    job_queue.run_repeating(send_market_open_news, interval=60, first=0)  # Verificar apertura del mercado

    # Configuración para Render (webhook)
    PORT = int(os.environ.get("PORT", 10000))
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{RENDER_URL}/{TELEGRAM_TOKEN}"
    )
    updater.bot.setWebhook(f"{RENDER_URL}/{TELEGRAM_TOKEN}")

if __name__ == "__main__":
    main()
