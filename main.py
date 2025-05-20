import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
from keep_alive import keep_alive
import nest_asyncio

# Activar keep_alive para Render Web Service
keep_alive()
nest_asyncio.apply()

# 📦 BASE DE DATOS
DB_PATH = "stock_telas.db"

def crear_tabla_si_no_existe():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS telas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            color TEXT NOT NULL,
            cantidad INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

crear_tabla_si_no_existe()

# 📥 INGRESO DE STOCK
async def ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("❌ Tenés que escribir: /ingreso tipo color cantidad")
        return
    tipo, color, cantidad = context.args
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT cantidad FROM telas WHERE tipo=? AND color=?", (tipo, color))
    fila = c.fetchone()
    if fila:
        nueva_cantidad = fila[0] + int(cantidad)
        c.execute("UPDATE telas SET cantidad=? WHERE tipo=? AND color=?", (nueva_cantidad, tipo, color))
    else:
        c.execute("INSERT INTO telas (tipo, color, cantidad) VALUES (?, ?, ?)", (tipo, color, int(cantidad)))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Ingresado {cantidad} de {tipo}_{color}")

# 📤 REGISTRO DE VENTA
async def vendido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("❌ Tenés que escribir: /vendido tipo color cantidad")
        return
    tipo, color, cantidad = context.args
    cantidad = int(cantidad)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT cantidad FROM telas WHERE tipo=? AND color=?", (tipo, color))
    fila = c.fetchone()
    if fila and fila[0] >= cantidad:
        nueva_cantidad = fila[0] - cantidad
        c.execute("UPDATE telas SET cantidad=? WHERE tipo=? AND color=?", (nueva_cantidad, tipo, color))
        mensaje = f"🧾 Vendido {cantidad} de {tipo}_{color}"
    else:
        mensaje = "❌ No hay suficiente stock."
    conn.commit()
    conn.close()
    await update.message.reply_text(mensaje)

# 📊 CONSULTA STOCK DE UN TIPO
async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Tenés que escribir el tipo.\nEjemplo: /stock lino")
        return
    tipo = context.args[0]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT color, cantidad FROM telas WHERE tipo=?", (tipo,))
    filas = c.fetchall()
    conn.close()
    if filas:
        mensaje = f"📦 Stock de *{tipo}*:\n"
        for color, cantidad in filas:
            mensaje += f"- {tipo}_{color}: {cantidad}\n"
        await update.message.reply_text(mensaje, parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ No se encontró stock relacionado.")

# ⌨️ BOTONES DE MENÚ
async def tela(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📥 Ingreso", callback_data="ingreso"),
            InlineKeyboardButton("📤 Vendido", callback_data="vendido"),
        ],
        [
            InlineKeyboardButton("📊 Consulta", callback_data="consulta"),
            InlineKeyboardButton("📦 Stock", callback_data="stock"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Seleccioná una opción:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    comando = query.data
    ejemplo = {
        "ingreso": "/ingreso lino blanco 10",
        "vendido": "/vendido lino blanco 2",
        "consulta": "/stock lino",
        "stock": "/stock lino"
    }
    await query.edit_message_text(f"📌 Escribí el comando:\n```{ejemplo[comando]}```", parse_mode="Markdown")

# 🤖 INICIO DEL BOT
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hola, soy tu bot de stock de telas.")

# 🚀 MAIN
async def main():
    logging.basicConfig(level=logging.INFO)
    TOKEN = os.environ["TELEGRAM_TOKEN"]
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ingreso", ingreso))
    app.add_handler(CommandHandler("vendido", vendido))
    app.add_handler(CommandHandler("stock", stock))
    app.add_handler(CommandHandler("tela", tela))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Bot corriendo 24/7 desde Render Web Service")
    await app.run_polling()

# ⏯️ Ejecutar
if __name__ == "__main__":
    from keep_alive import keep_alive
    keep_alive()

    import nest_asyncio
    nest_asyncio.apply()

    import asyncio

    import logging
    logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "cannot close a running event loop" in str(e):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise