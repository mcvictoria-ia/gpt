import os
from io import BytesIO
from telegram.constants import ChatAction
import speech_recognition as sr
from pydub import AudioSegment
import requests
import asyncio
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "0"))
WORKSPACE_SLUG = os.environ.get("WORKSPACE_SLUG", "sabadell")
ANYTHINGLLM_API_CHAT = f"http://localhost:3000/api/v1/workspace/{WORKSPACE_SLUG}/chat"
ANYTHINGLLM_API_UPLOAD = f"http://localhost:3000/api/v1/workspace/{WORKSPACE_SLUG}/upload"
ANYTHINGLLM_API_LIST = f"http://localhost:3000/api/v1/workspace/{WORKSPACE_SLUG}/documents"
API_KEY = os.environ.get("ANYTHINGLLM_API_KEY")

siniestros_activos = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    await update.message.reply_text("\U0001F44B Hola Manuel, soy tu asistente de AnythingLLM.")

async def cerrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    siniestros_activos.pop(update.effective_user.id, None)
    await update.message.reply_text("\u274C Siniestro cerrado. Puedes empezar uno nuevo con #n\u00FAmero.")

async def listar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("\u274C Acceso denegado.")
        return

    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(ANYTHINGLLM_API_LIST, headers=headers)
        if response.status_code == 200:
            docs = response.json()
            if not docs:
                await update.message.reply_text("\U0001F4C2 No hay documentos indexados.")
            else:
                nombres = [doc.get("title", "(sin t\u00edtulo)") for doc in docs]
                await update.message.reply_text("\U0001F4DA Documentos indexados:\n" + "\n".join(nombres))
        else:
            await update.message.reply_text(f"\u274C Error al obtener documentos. C\u00F3digo: {response.status_code}")
    except Exception as e:
        await update.message.reply_text(f"\u274C Error: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("\u274C Acceso denegado.")
        return

    match = re.match(r"#?(\w{6,})", text.strip())
    if match:
        siniestros_activos[user_id] = match.group(1)
        await update.message.reply_text(f"\U0001F4C1 Siniestro activado: {match.group(1)}")
        return

    siniestro = siniestros_activos.get(user_id)
    texto_completo = f"[{siniestro}] {text}" if siniestro else text

    payload = {
        "message": texto_completo,
        "history": [],
        "temperature": 0.7,
        "prompt": "",
    }

    try:
        r = requests.post(
            ANYTHINGLLM_API_CHAT,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
        )
        if r.status_code != 200 or not r.text.strip():
            respuesta = "\u274C Error: la API no devolvi\u00F3 contenido v\u00E1lido."
        else:
            json_data = r.json()
            respuesta = json_data.get("textResponse") or "\U0001F916 No encontr\u00E9 respuesta."
    except Exception as e:
        respuesta = f"\u274C Error: {e}"

    await update.message.reply_text(respuesta)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("\u274C Acceso denegado.")
        return

    await update.message.chat.send_action(action=ChatAction.TYPING)

    voice = await update.message.voice.get_file()
    voice_data = BytesIO()
    await voice.download_to_memory(out=voice_data)
    voice_data.seek(0)

    audio = AudioSegment.from_ogg(voice_data)
    wav_io = BytesIO()
    audio.export(wav_io, format="wav")
    wav_io.seek(0)

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_io) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data, language="es-ES")
        update.message.text = text
        await handle_message(update, context)
    except sr.UnknownValueError:
        await update.message.reply_text("\u274C No entend\u00ED el audio.")
    except sr.RequestError as e:
        await update.message.reply_text(f"\u274C Error al transcribir audio: {e}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("\u274C Acceso denegado.")
        return

    document = update.message.document
    file = await document.get_file()
    file_data = BytesIO()
    await file.download_to_memory(out=file_data)
    file_data.seek(0)

    try:
        files = {"files": (document.file_name, file_data)}
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.post(ANYTHINGLLM_API_UPLOAD, files=files, headers=headers)

        if response.status_code == 200:
            await update.message.reply_text("\U0001F4C4 Documento cargado e indexado correctamente.")
        else:
            await update.message.reply_text(f"\u274C Error al subir el documento. C\u00F3digo: {response.status_code}")
    except Exception as e:
        await update.message.reply_text(f"\u274C Error: {e}")

if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not API_KEY or not ALLOWED_USER_ID:
        raise RuntimeError("Required environment variables are missing")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cerrar", cerrar))
    app.add_handler(CommandHandler("listar", listar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("\u2728 Bot iniciado. Esperando mensajes...")
    app.run_polling()
