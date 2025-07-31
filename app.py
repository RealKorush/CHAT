from flask import Flask, render_template, request, jsonify
import requests
import json
import time
import threading # برای اجرای تابع fetch_chats_continuously در پس‌زمینه

app = Flask(__name__)

# لیست برای نگهداری لینک‌های چت. این لیست با هر بار ریست شدن/دیپلوی مجدد پاک می‌شود.
chat_urls = []
current_chats = [] # برای نگهداری آخرین وضعیت چت‌ها

# دیکشنری برای نگهداری آیکون‌های پلتفرم‌ها. میتونید از ایموجی یا متن کوتاه استفاده کنید.
PLATFORM_ICONS = {
    "youtube": "📺 ",  # آیکون برای یوتیوب
    "twitch": "🟣 ",   # آیکون برای توییچ
    "aparat": "🇮🇷 ",   # آیکون برای آپارات (اگر استریم‌لبز/المنتز پشتیبانی کنه)
    "tiktok": "🎵 "    # آیکون برای تیک تاک (اگر استریم‌لبز/المنتز پشتیبانی کنه)
}

# تابع برای دریافت و پردازش چت‌ها
def fetch_chats_continuously():
    global current_chats # دسترسی به متغیر سراسری
    while True:
        all_new_chats = []
        for url_info in chat_urls:
            url = url_info['url']
            try:
                response = requests.get(url, timeout=5) # 5 ثانیه مهلت برای پاسخ
                response.raise_for_status() # اگر خطایی (مثل 404 یا 500) در درخواست بود، خطا بده

                # فرض میکنیم پاسخ به فرمت JSON هست و حاوی یک لیست از چت‌هاست
                # بسته به فرمت خروجی Streamlabs/StreamElements، ممکن است نیاز به تغییر این بخش باشد
                raw_chats = response.json() 

                # در اینجا فرض می کنیم که raw_chats یک لیست از دیکشنری هاست
                # و هر دیکشنری شامل keys 'platform', 'user', 'message' است.
                # شما باید فرمت دقیق خروجی Streamlabs/StreamElements را بررسی کنید.
                for chat in raw_chats:
                    platform = chat.get("platform", "unknown").lower()
                    user = chat.get("user", "ناشناس")
                    message = chat.get("message", "")
                    
                    icon = PLATFORM_ICONS.get(platform, "💬 ") # آیکون پیش‌فرض
                    
                    all_new_chats.append(f"{icon}<strong>{user}</strong>: {message}")
            except requests.exceptions.RequestException as e:
                print(f"Error fetching chat from {url}: {e}")
            except json.JSONDecodeError:
                print(f"Error decoding JSON from {url}")
            except Exception as e:
                print(f"An unexpected error occurred for {url}: {e}")
        
        current_chats = all_new_chats # به‌روزرسانی لیست چت‌های فعلی
        time.sleep(2) # هر 2 ثانیه یک بار چت‌ها رو چک کن

# شروع یک thread جداگانه برای تابع fetch_chats_continuously
# این باعث میشه که دریافت چت‌ها در پس‌زمینه انجام بشه و وب‌سایت ما بلاک نشه.
threading.Thread(target=fetch_chats_continuously, daemon=True).start()

# -------------------------------------------------------------------------------------
# مسیرها (Routes) وب‌سایت
# -------------------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_url', methods=['POST'])
def add_url():
    url = request.form['chat_url'].strip() # لینک رو از فرم دریافت میکنیم و فاصله‌های اضافی رو حذف میکنیم
    if url and url not in [u['url'] for u in chat_urls]: # اگر لینک خالی نبود و تکراری نبود
        chat_urls.append({'url': url})
        print(f"Added URL: {url}")
    return render_template('index.html', urls=chat_urls)

@app.route('/remove_url/<int:index>')
def remove_url(index):
    if 0 <= index < len(chat_urls):
        removed_url = chat_urls.pop(index)
        print(f"Removed URL: {removed_url['url']}")
    return render_template('index.html', urls=chat_urls)

@app.route('/clear_urls')
def clear_urls():
    global chat_urls
    chat_urls = [] # خالی کردن لیست لینک‌ها
    print("All URLs cleared.")
    return render_template('index.html', urls=chat_urls)

@app.route('/chat_display')
def chat_display():
    return render_template('chat.html', chats=current_chats)

@app.route('/get_latest_chats')
def get_latest_chats():
    # این مسیر برای JavaScript در صفحه chat.html استفاده می‌شود تا چت‌های جدید را دریافت کند.
    return jsonify(chats=current_chats)

if __name__ == '__main__':
    # در محیط توسعه (روی کامپیوتر شما)
    # برای دیپلوی روی Render، نیازی به این خطوط نیست و gunicorn اجرا را مدیریت می کند.
    app.run(debug=True, host='0.0.0.0', port=5000)
