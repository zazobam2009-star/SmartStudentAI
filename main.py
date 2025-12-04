import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
import requests
import json
import base64

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
user_state = {}
user_queue = {}  # Navbatim uchun

# ==============================

# Menyu tugmalari

# ==============================

def main_menu():
kb = InlineKeyboardMarkup(row_width=2)
kb.add(
InlineKeyboardButton("Referat", callback_data="referat"),
InlineKeyboardButton("Prezentatsiya", callback_data="prezentatsiya"),
InlineKeyboardButton("Rasm", callback_data="rasm"),
InlineKeyboardButton("AI yordamchi", callback_data="chat"),
InlineKeyboardButton("Navbatim", callback_data="navbatim"),
InlineKeyboardButton("Bekor qilish", callback_data="cancel")
)
return kb

def create_number_buttons(start, end, prefix):
kb = InlineKeyboardMarkup(row_width=5)
buttons = [InlineKeyboardButton(str(i), callback_data=f"{prefix}_{i}") for i in range(start, end+1)]
kb.add(*buttons)
kb.add(InlineKeyboardButton("Bekor qilish", callback_data="cancel"))
return kb

# ==============================

# AI funksiyalari

# ==============================

def generate_text(prompt, max_tokens=500):
url = "[https://api.openai.com/v1/chat/completions](https://api.openai.com/v1/chat/completions)"
headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
data = {
"model": "gpt-4.1-mini",
"messages": [{"role": "user", "content": prompt}],
"max_tokens": max_tokens
}
response = requests.post(url, headers=headers, json=data)
if response.status_code == 200:
return response.json()["choices"][0]["message"]["content"]
else:
return f"Xatolik yuz berdi: {response.status_code}"

def generate_image(prompt):
url = "[https://api.stability.ai/v1/generation/stable-diffusion-3/ai-image](https://api.stability.ai/v1/generation/stable-diffusion-3/ai-image)"
headers = {
"Authorization": f"Bearer {STABILITY_API_KEY}",
"Content-Type": "application/json"
}
payload = {"prompt": prompt, "width":512, "height":512, "samples":1}
response = requests.post(url, headers=headers, json=payload)
if response.status_code == 200:
image_base64 = response.json()["artifacts"][0]["base64"]
return image_base64
else:
return None

# ==============================

# /start

# ==============================

@dp.message()
async def start(message: types.Message):
await message.answer("Salom! Men sizning AI yordamchingizman.", reply_markup=main_menu())
user_state[message.from_user.id] = {}

# ==============================

# Callback handler

# ==============================

@dp.callback_query()
async def callbacks(call: types.CallbackQuery):
user_id = call.from_user.id
data = call.data

```
# ---------- Referat ----------
if data == "referat":
    user_state[user_id]["step"] = "referat_topic"
    await call.message.answer("Referat mavzusini kiriting:")

elif user_state.get(user_id, {}).get("step") == "referat_topic":
    user_state[user_id]["topic"] = call.message.text
    user_state[user_id]["step"] = "referat_pages"
    await call.message.answer("Referat betlar sonini tanlang (5–20):", reply_markup=create_number_buttons(5, 20, "ref_pages"))

elif data.startswith("ref_pages_"):
    pages = int(data.split("_")[2])
    user_state[user_id]["pages"] = pages
    user_state[user_id]["step"] = "referat_outline"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Ha", callback_data="ref_outline_yes"))
    kb.add(InlineKeyboardButton("Yo‘q", callback_data="ref_outline_no"))
    kb.add(InlineKeyboardButton("Bekor qilish", callback_data="cancel"))
    await call.message.answer("Referat uchun reja kerakmi?", reply_markup=kb)

elif data in ["ref_outline_yes", "ref_outline_no"]:
    user_state[user_id]["outline"] = data.split("_")[-1]
    topic = user_state[user_id]["topic"]
    pages = user_state[user_id]["pages"]
    outline = user_state[user_id]["outline"]
    prompt = f"Referat yozing: {topic}, {pages} bet, reja kerak: {outline}"
    text = generate_text(prompt, max_tokens=1500)
    await call.message.answer(text)
    await call.message.answer("Referat tayyor! ✅", reply_markup=main_menu())
    user_state[user_id] = {}

# ---------- Prezentatsiya ----------
elif data == "prezentatsiya":
    user_state[user_id]["step"] = "presentation_slides"
    await call.message.answer("Slaydlar sonini tanlang (10–15):", reply_markup=create_number_buttons(10, 15, "slides"))

elif data.startswith("slides_"):
    slides = int(data.split("_")[1])
    user_state[user_id]["slides"] = slides
    user_state[user_id]["step"] = "presentation_bullets"
    await call.message.answer("Har slaydda bullet pointlar sonini tanlang (3–10):", reply_markup=create_number_buttons(3, 10, "bullets"))

elif data.startswith("bullets_"):
    bullets = int(data.split("_")[1])
    slides = user_state[user_id]["slides"]
    prompt = f"Prezentatsiya yozing: {slides} slayd, har slaydda {bullets} bullet point"
    text = generate_text(prompt, max_tokens=1000)
    await call.message.answer(text)
    await call.message.answer("Prezentatsiya tayyor! ✅", reply_markup=main_menu())
    user_state[user_id] = {}

# ---------- Rasm ----------
elif data == "rasm":
    user_state[user_id]["step"] = "image_prompt"
    await call.message.answer("Rasm promptini yozing:")

elif user_state.get(user_id, {}).get("step") == "image_prompt":
    prompt = call.message.text
    image_base64 = generate_image(prompt)
    if image_base64:
        image_bytes = base64.b64decode(image_base64)
        with open(f"{user_id}_image.png", "wb") as f:
            f.write(image_bytes)
        with open(f"{user_id}_image.png", "rb") as f:
            await call.message.answer_photo(f)
    else:
        await call.message.answer("Rasm yaratishda xatolik yuz berdi.")
    await call.message.answer("Rasm tayyor! ✅", reply_markup=main_menu())
    user_state[user_id] = {}

# ---------- AI chat ----------
elif data == "chat":
    user_state[user_id]["step"] = "chat"
    await call.message.answer("Savolingizni yozing:")

elif user_state.get(user_id, {}).get("step") == "chat":
    question = call.message.text
    answer = generate_text(question, max_tokens=500)
    await call.message.answer(answer)
    await call.message.answer("Yana savol bering yoki asosiy menyuga qayting.", reply_markup=main_menu())
    user_state[user_id] = {}

# ---------- Navbatim ----------
elif data == "navbatim":
    queue = user_queue.get(user_id, [])
    task_number = len(queue) + 1
    queue.append(f"Vazifa {task_number}")
    user_queue[user_id] = queue
    await call.message.answer(f"Sizning navbat raqamingiz: {task_number}\nVazifa: {queue[-1]}", reply_markup=main_menu())

# ---------- Cancel ----------
elif data == "cancel":
    await call.message.answer("Jarayon bekor qilindi.", reply_markup=main_menu())
    user_state[user_id] = {}

await call.answer()
```

# ==============================

# Botni ishga tushirish

# ==============================

async def main():
await dp.start_polling(bot)

if **name** == "**main**":
asyncio.run(main())


