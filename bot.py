import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ------------- CONFIG -------------
TOKEN = os.environ.get("8483432244:AAG8bf8uzKbr6QRN6-4dE5Vfadkia8PZQCE")       # Telegram bot token
ADMIN_ID = int(os.environ.get("1250890646"))  # Your Telegram ID
EXAM_FILE = "exams.json"

departments = ["ECE", "Mechanical", "Civil", "IT", "Computer CS", "Software", "Management"]
years = ["2014", "2015", "2016", "2017"]

# ------------- LOAD/SAVE EXAMS -------------
def load_exams():
    with open(EXAM_FILE, "r") as f:
        return json.load(f)

def save_exams(exams):
    with open(EXAM_FILE, "w") as f:
        json.dump(exams, f, indent=4)

# ------------- START -------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [["Start Exam"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🎓 Welcome to Exam Bot!\nPress Start Exam to begin or /addexam if you are admin.",
        reply_markup=reply_markup
    )

# ------------- STUDENT & ADMIN FLOW -------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    exams = load_exams()

    # ADMIN ADD EXAM FLOW
    if update.message.from_user.id == ADMIN_ID and context.user_data.get("admin_adding"):
        stage = context.user_data.get("stage")
        # (Admin flow code as in previous messages; handles department, year, questions, options, answers)
        # Copy the full admin flow code from previous messages here
        return

    # STUDENT FLOW
    if text == "Start Exam":
        keyboard = [[dept] for dept in departments]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Select your Department:", reply_markup=reply_markup)
    elif text in departments:
        context.user_data["department"] = text
        keyboard = [["Exit Exam"], ["Back"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"{text} Department\nChoose Exam Type:", reply_markup=reply_markup)
    elif text == "Exit Exam":
        dept = context.user_data.get("department")
        keyboard = [years[i:i+2] for i in range(0, len(years), 2)]
        keyboard.append(["Back"])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Select Year:", reply_markup=reply_markup)
    elif text in years:
        dept = context.user_data.get("department")
        context.user_data["year"] = text
        context.user_data["q_index"] = 0
        context.user_data["score"] = 0
        questions = exams[dept].get(text)
        if questions:
            await send_question(update, context)
        else:
            await update.message.reply_text("❌ No exams uploaded yet for this year.")
    elif text == "Back":
        await start(update, context)
    else:
        await update.message.reply_text("Please use the menu buttons.")

# ------------- SEND QUESTION -------------
async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exams = load_exams()
    dept = context.user_data["department"]
    year = context.user_data["year"]
    q_index = context.user_data["q_index"]
    question_list = exams[dept][year]

    if q_index < len(question_list):
        q = question_list[q_index]
        keyboard = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in q["options"]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.message:
            await update.message.reply_text(q["question"], reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.reply_text(q["question"], reply_markup=reply_markup)
    else:
        score = context.user_data.get("score", 0)
        await update.callback_query.message.reply_text(f"🎉 Exam finished!\nYour total score: {score}/{len(question_list)}")

# ------------- HANDLE ANSWERS -------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    exams = load_exams()
    dept = context.user_data["department"]
    year = context.user_data["year"]
    q_index = context.user_data["q_index"]
    question_list = exams[dept][year]
    q = question_list[q_index]

    if query.data == q["answer"]:
        feedback = "✅ Correct!"
        context.user_data["score"] += 1
    elif query.data == "next":
        context.user_data["q_index"] += 1
        await send_question(update, context)
        return
    else:
        feedback = f"❌ Wrong! Correct answer: {q['answer']}"

    keyboard = [[InlineKeyboardButton("Next ➡️", callback_data="next")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=f"{q['question']}\nYour answer: {query.data}\n{feedback}",
                                  reply_markup=reply_markup)

# ------------- ADD EXAM COMMAND -------------
async def addexam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to add exams.")
        return
    context.user_data.clear()
    context.user_data["admin_adding"] = True
    context.user_data["stage"] = "department"
    keyboard = [[dept] for dept in departments]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Select Department for the new exam:", reply_markup=reply_markup)

# ------------- MAIN -------------
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addexam", addexam))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button))

print("Professional Exam Bot Running...")
app.run_polling()
