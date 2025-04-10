import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = "7923861978:AAGWrEPgItrlkzBtmYmIXdbKNdNJVb4UPBw"
TWELVEDATA_API_KEY = "354c41fa243c4677a4491f35884d1fcb"

SYMBOLS = {
    "eurusd": "EUR/USD",
    "xauusd": "XAU/USD",
    "btcusd": "BTC/USD",
    "ethusd": "ETH/USD",
    "nasdaq": "NDX",
    "eurjpy": "EUR/JPY",
    "usdjpy": "USD/JPY"
}

async def get_price(symbol_code: str) -> str:
    url = f"https://api.twelvedata.com/price?symbol={symbol_code}&apikey={TWELVEDATA_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "price" in data:
        return f"{SYMBOLS[symbol_code.lower()]}: ${data['price']}"
    elif "message" in data:
        return f"Error: {data['message']}"
    else:
        return "Error al obtener el precio."

async def handle_price_command(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol_code: str):
    msg = await get_price(symbol_code)
    await update.message.reply_text(msg)

def create_command(symbol_code):
    return lambda update, context: handle_price_command(update, context, symbol_code)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Comandos para cada símbolo
    app.add_handler(CommandHandler("eurusd", create_command("eurusd")))
    app.add_handler(CommandHandler("xauusd", create_command("xauusd")))
    app.add_handler(CommandHandler("btcusd", create_command("btcusd")))
    app.add_handler(CommandHandler("ethusd", create_command("ethusd")))
    app.add_handler(CommandHandler("nasdaq", create_command("nasdaq")))
    app.add_handler(CommandHandler("eurjpy", create_command("eurjpy")))
    app.add_handler(CommandHandler("usdjpy", create_command("usdjpy")))

    print("✅ Jarvis está en línea...")
    app.run_polling()

if __name__ == "__main__":
    main()
