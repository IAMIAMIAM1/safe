"""
ULTIMATE DORKING ENGINE (2025)
Harnessing advanced fingerprinting and browser spoofing to evade all blocks.
"""

import os
import re
import sys
import time
import random
import json
import base64
import sqlite3
import hashlib
import string
from typing import Optional, List, Dict, Any
import logging
from urllib.parse import quote

from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

# --- Logging Configuration ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# --- Spoofing Data ---
UA_2025 = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 14; Mobile; rv:131.0) Gecko/131.0 Firefox/131.0",
]

def fake_chrome_ua():
    chrome_versions = [f"13{random.randint(0,2)}.0.0.0" for _ in range(5)]
    windows_builds = ["Win64; x64", "WOW64"]
    return f"Mozilla/5.0 (Windows NT 10.0; {random.choice(windows_builds)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36"

# --- Spoofing Functions ---

def spoof_hardware_fingerprint(driver):
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        // === CPU & RAM ===
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });

        // === Screen Resolution (random common) ===
        const widths = [1920, 1366, 1536, 1440, 1280];
        const heights = [1080, 768, 864, 900, 800];
        let w = widths[Math.floor(Math.random() * widths.length)];
        let h = heights[Math.floor(Math.random() * heights.length)];
        Object.defineProperty(screen, 'width', { get: () => w });
        Object.defineProperty(screen, 'height', { get: () => h });
        Object.defineProperty(screen, 'availWidth', { get: () => w });
        Object.defineProperty(screen, 'availHeight', { get: () => h - 80 });

        // === Timezone (random major city) ===
        const zones = ['America/New_York', 'Europe/London', 'Asia/Tokyo', 'Europe/Paris', 'Australia/Sydney'];
        Intl.DateTimeFormat = () => ({ resolvedOptions: () => ({ timeZone: zones[Math.floor(Math.random() * zones.length)] }) });

        // === Canvas Noise (5–8% random) ===
        const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function() {
            const data = origGetImageData.apply(this, arguments);
            for (let i = 0; i < data.data.length; i += 4) {
                data.data[i] += Math.floor(Math.random() * 15 - 7);
                data.data[i+1] += Math.floor(Math.random() * 15 - 7);
                data.data[i+2] += Math.floor(Math.random() * 15 - 7);
            }
            return data;
        };

        // === WebGL Vendor/Renderer Spoof ===
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.';
            if (parameter === 37446) return 'Intel Iris OpenGL Engine';
            return getParameter(parameter);
        };

        // === AudioContext Fingerprint Noise ===
        const audioCtx = AudioContext.prototype.constructor;
        AudioContext.prototype.constructor = function() {
            const ctx = new audioCtx();
            const osc = ctx.createOscillator();
            osc.frequency.value = 440 + Math.random() * 10;
            return ctx;
        };

        // === Battery API Spoof ===
        navigator.getBattery = () => Promise.resolve({
            charging: true,
            chargingTime: 0,
            dischargingTime: Infinity,
            level: 0.99
        });
        """
    })

def spoof_gpu(driver):
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        const realGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            const spoofed = {
                37445: 'Intel Inc.',
                37446: 'Intel(R) UHD Graphics 630',
                7937: 'WebGL 1.0',
                35724: 'WebKit',
                7938: 'WebGL GLSL ES 1.0'
            };
            if (spoofed[parameter]) return spoofed[parameter];
            return realGetParameter(parameter);
        };
        """
    })

def kill_font_fingerprint(driver):
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        const fonts = ['Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Verdana', 'Georgia', 'Comic Sans MS', 'Trebuchet MS'];
        const detect = () => fonts[Math.floor(Math.random() * fonts.length)];
        Object.defineProperty(document, 'fonts', { get: detect });
        // Block font enumeration via CSS
        const style = document.createElement('style');
        style.innerHTML = `* { font-family: Arial !important; }`;
        document.head.appendChild(style);
        """
    })

def get_perfect_browser():
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = uc.Chrome(options=options, version_main=132)

    spoof_hardware_fingerprint(driver)
    spoof_gpu(driver)
    kill_font_fingerprint(driver)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
    driver.execute_cdp_cmd("Network.setUserAgentOverride", {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    })

    return driver

def android_spoofer():
    mobile_emulation = {
        "deviceMetrics": { "width": 390, "height": 844, "pixelRatio": 3.0 },
        "userAgent": "Mozilla/5.0 (Linux; Android 14; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.78 Mobile Safari/537.36"
    }
    
    options = Options()
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(options=options)
    
    # Full mobile hardware spoof
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
        Object.defineProperty(navigator, 'platform', { get: () => 'Android' });
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 5 });
        
        // Spoof sensors
        Object.defineProperty(navigator, 'deviceOrientation', { get: () => ({}) });
        navigator.getBattery = () => Promise.resolve({
            charging: true,
            level: 0.87,
            chargingTime: 1200,
            dischargingTime: Infinity
        });
        
        // Kill mobile-specific fingerprints
        delete navigator.webdriver;
        window.chrome = { runtime: {} };
        """
    })
    return driver

def ios_spoofer():
    ios_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
    
    mobile_emulation = {
        "deviceMetrics": { "width": 430, "height": 932, "pixelRatio": 3.0 },
        "userAgent": ios_ua
    }
    
    options = Options()
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(options=options)
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": f"""
        Object.defineProperty(navigator, 'userAgent', {{ get: () => "{ios_ua}" }});
        Object.defineProperty(navigator, 'platform', {{ get: () => 'iPhone' }});
        Object.defineProperty(navigator, 'vendor', {{ get: () => 'Apple Computer, Inc.' }});
        Object.defineProperty(navigator, 'maxTouchPoints', {{ get: () => 5 }});
        Object.defineProperty(screen, 'width', {{ get: () => 430 }});
        Object.defineProperty(screen, 'height', {{ get: () => 932 }});
        """
    })
    return driver

def stealth_cffi_request(url):
    return curl_requests.get(
        url,
        impersonate="chrome132",  # Spoofs real Chrome 132 TLS + HTTP/2 + headers
        headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-CH-UA": '"Google Chrome";v="132", "Chromium";v="132", "Not=A?Brand";v="24"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
        },
        timeout=20
    )

def ultimate_mobile_request(url, rotator):
    # 1. Rotate residential proxy
    proxies = rotator.get()
    
    # 2. Random mobile device
    device = random.choice(["android", "ios"])
    ua = random.choice([
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 Chrome/132 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1"
    ])
    
    # 3. Spoof TLS + headers
    return curl_requests.get(
        url,
        impersonate="chrome124_android" if "Android" in ua else "safari_ios_18",
        headers={
            "User-Agent": ua,
            "Sec-CH-UA-Mobile": "?1",
            "Sec-CH-UA-Platform": '"Android"' if "Android" in ua else '"iOS"',
        },
        proxies=proxies,
        timeout=20
    )


# --- Helper Classes ---

class SearchCache:
    def __init__(self, cache_dir: str = None, max_memory_items: int = 1000, default_ttl: int = 3600):
        self.max_memory_items = max_memory_items
        self.default_ttl = default_ttl
        if cache_dir is None:
            cache_dir = os.path.join(os.getcwd(), "data", "__CACHE_DIR__", "search_cache")
        os.makedirs(cache_dir, exist_ok=True)
        self.db_path = os.path.join(cache_dir, "search_cache.db")
        self._init_db()
        self._memory_cache = {}
        self._access_times = {}

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS search_cache (query_hash TEXT PRIMARY KEY, query_text TEXT NOT NULL, results TEXT NOT NULL, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL, access_count INTEGER DEFAULT 1, last_accessed INTEGER NOT NULL)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON search_cache(expires_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_last_accessed ON search_cache(last_accessed)")
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize search cache database: {e}")

    def get(self, query: str, search_engine: str = "default") -> Optional[List[Dict[str, Any]]]:
        query_hash = self._get_query_hash(query, search_engine)
        current_time = int(time.time())

        if query_hash in self._memory_cache:
            entry = self._memory_cache[query_hash]
            if entry["expires_at"] > current_time:
                self._access_times[query_hash] = current_time
                logger.debug(f"Cache hit (memory) for query: {query[:50]}...")
                return entry["results"]
            else:
                self._memory_cache.pop(query_hash, None)
                self._access_times.pop(query_hash, None)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT results, expires_at FROM search_cache WHERE query_hash = ? AND expires_at > ?",
                    (query_hash, current_time),
                )
                row = cursor.fetchone()
                if row:
                    results_json, expires_at = row
                    results = json.loads(results_json)
                    cursor.execute(
                        "UPDATE search_cache SET access_count = access_count + 1, last_accessed = ? WHERE query_hash = ?",
                        (current_time, query_hash),
                    )
                    conn.commit()
                    self._memory_cache[query_hash] = {"results": results, "expires_at": expires_at}
                    self._access_times[query_hash] = current_time
                    self._evict_lru_memory()
                    logger.debug(f"Cache hit (database) for query: {query[:50]}...")
                    return results
        except Exception as e:
            logger.error(f"Failed to retrieve from search cache: {e}")
        logger.debug(f"Cache miss for query: {query[:50]}...")
        return None

    def put(self, query: str, results: List[Dict[str, Any]], search_engine: str = "default", ttl: Optional[int] = None) -> bool:
        if not results:
            return False
        query_hash = self._get_query_hash(query, search_engine)
        current_time = int(time.time())
        expires_at = current_time + (ttl or self.default_ttl)
        try:
            results_json = json.dumps(results)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO search_cache (query_hash, query_text, results, created_at, expires_at, access_count, last_accessed) VALUES (?, ?, ?, ?, ?, 1, ?)",
                    (query_hash, self._normalize_query(query), results_json, current_time, expires_at, current_time),
                )
                conn.commit()
            self._memory_cache[query_hash] = {"results": results, "expires_at": expires_at}
            self._access_times[query_hash] = current_time
            self._evict_lru_memory()
            logger.debug(f"Cached results for query: {query[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to store in search cache: {e}")
            return False

    def _normalize_query(self, query: str) -> str:
        return " ".join(query.lower().strip().split())

    def _get_query_hash(self, query: str, search_engine: str = "default") -> str:
        normalized_query = self._normalize_query(query)
        cache_key = f"{search_engine}:{normalized_query}"
        return hashlib.md5(cache_key.encode()).hexdigest()

    def _evict_lru_memory(self):
        if len(self._memory_cache) <= self.max_memory_items:
            return
        sorted_items = sorted(self._access_times.items(), key=lambda x: x[1])
        items_to_remove = len(self._memory_cache) - self.max_memory_items + 100
        for query_hash, _ in sorted_items[:items_to_remove]:
            self._memory_cache.pop(query_hash, None)
            self._access_times.pop(query_hash, None)

class StealthHeaders:
    def __init__(self):
        self.ua_pool = UA_2025 + [fake_chrome_ua() for _ in range(10)]
        self.accept_lang = ["en-US,en;q=0.9", "en-GB,en;q=0.8", "de-DE,de;q=0.9", "fr-FR,fr;q=0.9"]
        self.encoding = ["gzip, deflate, br", "gzip, deflate"]
    
    def get(self):
        return {
            'User-Agent': random.choice(self.ua_pool),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': random.choice(self.accept_lang),
            'Accept-Encoding': random.choice(self.encoding),
            'Referer': random.choice(['https://www.google.com/', 'https://www.bing.com/', 'https://duckduckgo.com/', '']),
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Sec-CH-UA': f'"Google Chrome";v="{random.randint(130, 132)}", "Chromium";v="{random.randint(130, 132)}", "Not=A?Brand";v="24"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"',
        }

class ProxyRotator:
    def __init__(self, refresh_interval: int = 300):
        self.current_pia_proxy = None
        self.last_refresh = 0
        self.refresh_interval = refresh_interval
        self.proxy_modes = ["pia_sticky", "pia_random", "tor"]
        self.tor_proxy = "socks5://127.0.0.1:9050"

    def _generate_pia_session(self) -> str:
        sess_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"http://user-superGrok_Y6dbJ-sessid-{sess_id}:SuperAgent12345@proxy.piaproxy.com:7000"

    def get_proxy(self, mode: str = "pia_sticky") -> dict:
        if mode == "pia_random":
            proxy_url = self._generate_pia_session()
            return {'http': proxy_url, 'https': proxy_url}
        if mode == "tor":
            return {'http': self.tor_proxy, 'https': self.tor_proxy}
        now = time.time()
        if not self.current_pia_proxy or (now - self.last_refresh > self.refresh_interval):
            self.current_pia_proxy = self._generate_pia_session()
            self.last_refresh = now
        return {'http': self.current_pia_proxy, 'https': self.current_pia_proxy}

class CookieManager:
    def __init__(self):
        self.cookie_jars = [{"CONSENT": "YES+cb.20250301-00-p0.en+FX+123", "SOCS": "CAISEwgDEgk0ODE3Mjg1MjQaAmVuIAEaBgiA8vqdBg", "AEC": "Ae3random123", "__Secure-1PSID": "g.random123"}]

    def _generate_fresh_google_cookies(self):
        def random_string(length):
            return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        return [
            {"name": "CONSENT", "value": f"YES+srp.gws-{time.strftime('%Y%m%d')}-0-RC2"},
            {"name": "1P_JAR", "value": time.strftime("%Y-%m-%d-%H")},
            {"name": "NID", "value": f"520={random_string(60)}"},
            {"name": "AEC", "value": f"Ae3{random_string(30)}"},
        ]

    def refresh_cookies(self, session):
        print("Before clearing cookies:", session.cookies)
        session.cookies.clear(domain=".google.com")
        print("After clearing cookies:", session.cookies)
        for c in self._generate_fresh_google_cookies():
            session.cookies.set(c["name"], c["value"], domain=".google.com")
        print("After setting new cookies:", session.cookies)
        time.sleep(random.uniform(0.5, 2.0))

class UltimateDorkCrawler:
    def __init__(self):
        self.proxy_rotator = ProxyRotator()
        self.headers_manager = StealthHeaders()
        self.cookie_manager = CookieManager()
        self.cache = SearchCache()
        self.driver = None

    def _make_stealth_request(self, url, strategy="stealth_cffi"):
        if strategy == "stealth_cffi":
            session = curl_requests.Session()
            # For debugging, remove proxy and cookie handling
            # session.proxies = self.proxy_rotator.get_proxy(mode="pia_random")
            session.headers.update({"User-Agent": random.choice(UA_2025)}) # Simplified User-Agent
            # self.cookie_manager.refresh_cookies(session)
            session.impersonate = random.choice(["chrome124", "chrome130", "safari_ios_17", "edge130"])
            time.sleep(random.uniform(4, 11))
            return session.get(url, timeout=20)
        elif strategy == "perfect_browser":
            if self.driver is None:
                self.driver = get_perfect_browser()
            self.driver.get(url)
            return self.driver
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _parse_results(self, content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(content, "html.parser")
        results = []
        for g in soup.find_all('div', class_='g'):
            link_tag = g.find('a')
            if link_tag and 'href' in link_tag.attrs:
                url = link_tag['href']
                title_tag = g.find('h3')
                title = title_tag.get_text() if title_tag else 'No Title'
                results.append({"title": title, "url": url})
        
        external_results = []
        seen_urls = set()
        for res in results:
            url = res['url']
            if url and "google.com" not in url and "schemas.google.com" not in url and url not in seen_urls:
                external_results.append(res)
                seen_urls.add(url)
        return external_results

    def run_dork_crawl(self, dork_keyword: str, search_engine: str = "google"):
        logger.info(f"\n--- Initiating ultimate search for DORK: '{dork_keyword}' on {search_engine.upper()} ---")
        
        cached_results = self.cache.get(dork_keyword, search_engine)
        if cached_results:
            logger.info(f"Using cached search results for '{dork_keyword}' on {search_engine.upper()}")
            search_results = cached_results
        else:
            search_url = f"https://www.google.com/search?q={quote(dork_keyword)}"
            try:
                response = self._make_stealth_request(search_url)
                search_results = self._parse_results(response.text)
                self.cache.put(dork_keyword, search_results, search_engine)
            except Exception as e:
                logger.error(f"Error during ultimate search for '{dork_keyword}': {e}")
                search_results = []

        if not search_results:
            logger.info(f"No significant search results found for '{dork_keyword}' on {search_engine.upper()}.")
            return

        for i, result in enumerate(search_results):
            logger.info(f"\n[{search_engine.upper()}] Result {i+1}:")
            logger.info(f"  Title: {result.get('title', 'N/A')}")
            logger.info(f"  URL: {result.get('url', 'N/A')}")
            
        logger.info(f"--- Ultimate search completed for DORK: '{dork_keyword}' on {search_engine.upper()} ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ultimate_dork_crawler.py <dork_keyword_1> <dork_keyword_2> ...")
        sys.exit(1)
    
    keywords = sys.argv[1:]

    if not keywords:
        print("No dork keywords provided. Exiting.")
        sys.exit(1)

    crawler = UltimateDorkCrawler()
    for dork_query in keywords:
        crawler.run_dork_crawl(dork_query)
