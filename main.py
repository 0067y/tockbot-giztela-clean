import os
import asyncio
import sqlite3
import nest_asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Token desde variable de entorno
TOKEN = os.environ["TELEGRAM_TOKEN"]

# Conexión a base de datos
conn = sqlite3.connect("stock.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS stock (
    tela TEXT PRIMARY KEY,
    cantidad INTEGER
)
''')
conn.commit()

# Funciones base de datos
def obtener_stock(tela):
    cursor.execute("SELECT cantidad FROM stock WHERE tela = ?", (tela,))
    fila = cursor.fetchone()
    return fila[0] if fila else 0

def actualizar_stock(tela, cantidad):
    actual = obtener_stock(tela)
    nuevo = max(actual + cantidad, 0)
    cursor.execute("REPLACE INTO stock (tela, cantidad) VALUES (?, ?)", (tela, nuevo))
    conn.commit()
    return nuevo

def stock_por_tipo(tipo):
    cursor.execute("SELECT tela, cantidad FROM stock WHERE LOWER(tela) LIKE ?", (f"%{tipo.lower()}%",))
    return cursor.fetchall()

# Bot: comandos y botones
async def tela(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("✍️ Ingresar", callback_data="plantilla_ingreso"),
         InlineKeyboardButton("🔍 Consultar", callback_data="plantilla_consulta")],
        [InlineKeyboardButton("💸 Venta", callback_data="plantilla_vendido"),
         InlineKeyboardButton("📈 Ver Stock", callback_data="plantilla_stock")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Elegí una opción:", reply_markup=reply_markup)

async def botones_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    respuestas = {
        "plantilla_ingreso": "`/ingreso tela_color cantidad`",
        "plantilla_consulta": "`/consulta tela_color cantidad`",
        "plantilla_vendido": "`/vendido tela_color cantidad`",
        "plantilla_stock": "`/stock tipo`"
    }
    await query.edit_message_text(respuestas.get(query.data, "Opción no reconocida."), parse_mode="Markdown")

async def ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tela, cantidad = context.args[0], int(context.args[1])
        nuevo = actualizar_stock(tela, cantidad)
        await update.message.reply_text(f"✅ Ingresado: +{cantidad} de {tela} (Total: {nuevo})")
    except:
        await update.message.reply_text("❌ Formato incorrecto.\nUsá: `/ingreso tela_color cantidad`", parse_mode="Markdown")

async def consulta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tela, cantidad_pedida = context.args[0], int(context.args[1])
        actual = obtener_stock(tela)
        mensaje = f"📦 Stock actual de *{tela}*: {actual}\n"
        mensaje += "✅ Hay suficiente stock." if actual >= cantidad_pedida else "❌ No hay suficiente stock."
        await update.message.reply_text(mensaje, parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Formato incorrecto.\nUsá: `/consulta tela_color cantidad`", parse_mode="Markdown")

async def vendido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tela, cantidad = context.args[0], int(context.args[1])
        nuevo = actualizar_stock(tela, -cantidad)
        await update.message.reply_text(f"🛒 Vendido: -{cantidad} de {tela} (Queda: {nuevo})")
    except:
        await update.message.reply_text("❌ Formato incorrecto.\nUsá: `/vendido tela_color cantidad`", parse_mode="Markdown")

async def stock_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Tenés que escribir el tipo.\nEjemplo: `/stock lino`", parse_mode="Markdown")
        return
    tipo = context.args[0]
    resultados = stock_por_tipo(tipo)
    if resultados:
        mensaje = "\n".join([f"{tela}: {cant}" for tela, cant in resultados])
    else:
        mensaje = "⚠️ No se encontró stock relacionado."
    await update.message.reply_text(f"📦 *Stock encontrado:*\n{mensaje}", parse_mode="Markdown")

# Iniciar bot
async def main():
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("tela", tela))
    app_bot.add_handler(CallbackQueryHandler(botones_callback))
    app_bot.add_handler(CommandHandler("ingreso", ingreso))
    app_bot.add_handler(CommandHandler("consulta", consulta))
    app_bot.add_handler(CommandHandler("vendido", vendido))
    app_bot.add_handler(CommandHandler("stock", stock_tipo))

    print("✅ Bot corriendo con Flask + Telegram Bot")
    await app_bot.run_polling()

# Ejecutar todo (modificado levemente para reiniciar Render)

if __name__ == '__main__':
    from keep_alive import keep_alive
    keep_alive()

    import nest_asyncio
    nest_asyncio.apply()

    import asyncio

    try:
        asyncio.run(main())
    except RuntimeError:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        asyncio.run(main())
