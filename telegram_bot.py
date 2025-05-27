import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import json
import logging
#from bank_analyzer import analyze_bank_reviews  # Теперь функция возвращает строку
from telegram.constants import ParseMode

import asyncio
from typing import Optional

# Загрузка вашего существующего кода
from main import analyze_bank_reviews, shared_memory  # Импортируем основные функции и память

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- Новая функция для разбивки сообщений ---
def split_message(text: str, max_length: int = 4000) -> list:
    """Умная разбивка текста с сохранением структуры"""
    if not text:
        return []
    
    if len(text) <= max_length:
        return [text]
    
    # Приоритеты разбивки: абзацы → предложения → слова → принудительно
    split_chars = ['\n\n', '\n', '. ', '! ', '? ', ' ', '']
    
    parts = []
    remaining = text
    
    while remaining:
        for delimiter in split_chars:
            pos = remaining.rfind(delimiter, 0, max_length) if delimiter else max_length
            if pos > 0:
                part = remaining[:pos + (len(delimiter) if delimiter else pos)]
                parts.append(part.strip())
                remaining = remaining[pos + len(delimiter):].strip()
                break
        else:
            parts.append(remaining[:max_length])
            remaining = remaining[max_length:]
    
    return parts
# -------------------------------------------

# Глобальное хранилище сессий
user_sessions = {}

logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class UserSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.current_query = None
        self.analysis_in_progress = False
        self.last_results = None
        self.full_report = None  
        self.context = ""

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_sessions[user_id] = UserSession(user_id)
    
    keyboard = [
        [InlineKeyboardButton("🔍 Анализ рисков", callback_data='start_analysis')],
        [InlineKeyboardButton("📊 Последние результаты", callback_data='last_results')],
        [InlineKeyboardButton("🧠 Показать контекст", callback_data='show_memory')]
    ]
    
    await update.message.reply_text(
        "🤖 Бот-аналитик банковских рисков готов к работе!\n\n"
        "Вы можете:\n"
        "1. Запустить новый анализ операционных рисков\n"
        "2. Просмотреть предыдущие результаты\n"
        "3. Изучить контекст памяти агентов",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    session = user_sessions.get(user_id, UserSession(user_id))

    if query.data == 'start_analysis':
        session.analysis_in_progress = True
        await query.edit_message_text("📝 Введите ваш запрос для анализа (например: 'Найти инциденты с навязыванием услуг за последний месяц')")
    
    elif query.data == 'last_results' and session.last_results:
        await query.edit_message_text(f"📋 Последние результаты:\n\n{session.last_results[:4000]}...")
    
    elif query.data == 'show_memory':
        memory_context = shared_memory.get_context()
        await query.edit_message_text(f"🧠 Текущий контекст памяти:\n\n{memory_context[:4000]}...")
    
    elif query.data == 'full_report':
        if session.last_results:
            chunks = split_message(session.last_results)
            for chunk in chunks:
                await query.message.reply_text(chunk)
        else:
            await query.edit_message_text("⚠️ Нет доступных результатов для отображения.")
    elif query.data == 'show_context':
        # Получаем актуальный контекст из общей памяти
        current_context = shared_memory.get_context()
        if current_context:
            chunks = split_message(current_context)
            for chunk in chunks:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=chunk
                )
        else:
            await query.edit_message_text("⚠️ Контекст пуст.")

    elif query.data == 'clear_context':
        session.context = ""  # Или session.context = ""
        await query.edit_message_text("✅ Контекст очищен.")

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    if not session or not session.analysis_in_progress:
        await update.message.reply_text("Пожалуйста, выберите действие через меню /start")
        return
    try:
        await update.message.reply_text("🔄 Агенты анализируют данные...")
        
        # Получаем ОТЧЕТ (не вывод критика)
        report = analyze_bank_reviews(update.message.text)
        
        # Сохраняем и отправляем
        session.last_results = report
        session.analysis_in_progress = False
        
        # Разбиваем отчет на части
        chunks = split_message(report)
        for chunk in chunks:
            await update.message.reply_text(chunk)
        session.context = shared_memory.get_context()
            
        # Отдельно показываем кнопки
        keyboard = [
            [InlineKeyboardButton("🔄 Новый анализ", callback_data='start_analysis')],
            [InlineKeyboardButton("📋 Полный отчет", callback_data='full_report')],
            [InlineKeyboardButton("🧠 Показать контекст", callback_data='show_context')],
            [InlineKeyboardButton("❌ Очистить контекст", callback_data='clear_context')]
            

        ]
        await update.message.reply_text("Выберите действие:",  reply_markup=InlineKeyboardMarkup(keyboard))        
    except Exception as e:
        logging.error(f"Ошибка: {str(e)}")
        await update.message.reply_text(f"❌ Ошибка при анализе: {str(e)[:300]}")

async def error_handler(update: Update, context: CallbackContext):
    await update.message.reply_text(f"⚠️ Произошла ошибка: {context.error}")

def main():
    # Создаем приложение бота
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    print("🤖 Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()