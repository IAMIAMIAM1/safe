import requests
import re
import time
import random
import sys
import os
import sqlite3
import hashlib
import json
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any
import logging

# Setup basic logging for SearchCache
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# --- Provided SearchCache Class ---
class SearchCache:
    """
    Persistent cache for search results with TTL and LRU eviction.
    Stores results in SQLite for persistence across sessions.
    """

    def __init__(
        self,
        cache_dir: str = None,
        max_memory_items: int = 1000,
        default_ttl: int = 3600,
    ):
        self.max_memory_items = max_memory_items
        self.default_ttl = default_ttl

        if cache_dir is None:
            cache_dir = os.path.join(
                os.getcwd(), "data", "__CACHE_DIR__", "search_cache"
            )

        os.makedirs(cache_dir, exist_ok=True)
        self.db_path = os.path.join(cache_dir, "search_cache.db")

        self._init_db()
        self._memory_cache = {}
        self._access_times = {}

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS search_cache (
                        query_hash TEXT PRIMARY KEY,
                        query_text TEXT NOT NULL,
                        results TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        expires_at INTEGER NOT NULL,
                        access_count INTEGER DEFAULT 1,
                        last_accessed INTEGER NOT NULL
                    )
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_expires_at ON search_cache(expires_at)
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_last_accessed ON search_cache(last_accessed)
                """
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize search cache database: {e}")

    def _normalize_query(self, query: str) -> str:
        normalized = " ".join(query.lower().strip().split())
        normalized = normalized.replace('"', "").replace("'", "")
        return normalized

    def _get_query_hash(
        self, query: str, search_engine: str = "default"
    ) -> str:
        normalized_query = self._normalize_query(query)
        cache_key = f"{search_engine}:{normalized_query}"
        return hashlib.md5(cache_key.encode()).hexdigest()

    def _cleanup_expired(self):
        try:
            current_time = int(time.time())
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM search_cache WHERE expires_at < ?",
                    (current_time,),
                )
                deleted = cursor.rowcount
                conn.commit()
                if deleted > 0:
                    logger.debug(f"Cleaned up {deleted} expired cache entries")
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache entries: {e}")

    def _evict_lru_memory(self):
        if len(self._memory_cache) <= self.max_memory_items:
            return

        sorted_items = sorted(self._access_times.items(), key=lambda x: x[1])
        items_to_remove = (
            len(self._memory_cache) - self.max_memory_items + 100
        )

        for query_hash, _ in sorted_items[:items_to_remove]:
            self._memory_cache.pop(query_hash, None)
            self._access_times.pop(query_hash, None)

    def get(
        self, query: str, search_engine: str = "default"
    ) -> Optional[List[Dict[str, Any]]]:
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
                    """
                    SELECT results, expires_at FROM search_cache
                    WHERE query_hash = ? AND expires_at > ?
                """,
                    (query_hash, current_time),
                )

                row = cursor.fetchone()
                if row:
                    results_json, expires_at = row
                    results = json.loads(results_json)

                    cursor.execute(
                        """
                        UPDATE search_cache
                        SET access_count = access_count + 1, last_accessed = ?
                        WHERE query_hash = ?
                    """,
                        (current_time, query_hash),
                    )
                    conn.commit()

                    self._memory_cache[query_hash] = {
                        "results": results,
                        "expires_at": expires_at,
                    }
                    self._access_times[query_hash] = current_time
                    self._evict_lru_memory()

                    logger.debug(
                        f"Cache hit (database) for query: {query[:50]}..."
                    )
                    return results

        except Exception as e:
            logger.error(f"Failed to retrieve from search cache: {e}")

        logger.debug(f"Cache miss for query: {query[:50]}...")
        return None

    def put(
        self,
        query: str,
        results: List[Dict[str, Any]],
        search_engine: str = "default",
        ttl: Optional[int] = None,
    ) -> bool:
        if not results:
            return False

        query_hash = self._get_query_hash(query, search_engine)
        current_time = int(time.time())
        expires_at = current_time + (ttl or self.default_ttl)

        try:
            results_json = json.dumps(results)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO search_cache
                    (query_hash, query_text, results, created_at, expires_at, access_count, last_accessed)
                    VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                    (
                        query_hash,
                        self._normalize_query(query),
                        results_json,
                        current_time,
                        expires_at,
                        current_time,
                    ),
                )
                conn.commit()

            self._memory_cache[query_hash] = {
                "results": results,
                "expires_at": expires_at,
            }
            self._access_times[query_hash] = current_time
            self._evict_lru_memory()

            logger.debug(f"Cached results for query: {query[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to store in search cache: {e}")
            return False

    def invalidate(self, query: str, search_engine: str = "default") -> bool:
        query_hash = self._get_query_hash(query, search_engine)

        try:
            self._memory_cache.pop(query_hash, None)
            self._access_times.pop(query_hash, None)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM search_cache WHERE query_hash = ?",
                    (query_hash,),
                )
                deleted = cursor.rowcount
                conn.commit()

            logger.debug(f"Invalidated cache for query: {query[:50]}...")
            return deleted > 0

        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return False

    def clear_all(self) -> bool:
        try:
            self._memory_cache.clear()
            self._access_times.clear()

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM search_cache")
                conn.commit()

            logger.info("Cleared all search cache")
            return True

        except Exception as e:
            logger.error(f"Failed to clear search cache: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        try:
            current_time = int(time.time())
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT COUNT(*) FROM search_cache WHERE expires_at > ?",
                    (current_time,),
                )
                total_entries = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM search_cache WHERE expires_at <= ?",
                    (current_time,),
                )
                expired_entries = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT AVG(access_count) FROM search_cache WHERE expires_at > ?",
                    (current_time,),
                )
                avg_access = cursor.fetchone()[0] or 0

                return {
                    "total_valid_entries": total_entries,
                    "expired_entries": expired_entries,
                    "memory_cache_size": len(self._memory_cache),
                    "average_access_count": round(avg_access, 2),
                    "cache_hit_potential": (
                        f"{(total_entries / (total_entries + 1)) * 100:.1f}%"
                        if total_entries > 0
                        else "0%"
                    ),
                }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

# --- Provided WebContentFetcher Class ---
class WebContentFetcher:
    """Utility class for fetching web content."""

    @staticmethod
    def fetch_content_sync(url: str, timeout: int = 10) -> Optional[str]:
        """
        Synchronously fetch and extract the main content from a webpage.
        This is a synchronous version of the provided async function.

        Args:
            url: The URL to fetch content from
            timeout: Request timeout in seconds

        Returns:
            Extracted text content or None if fetching fails
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers, timeout=timeout)

            if response.status_code != 200:
                logger.warning(
                    f"Failed to fetch content from {url}: HTTP {response.status_code}"
                )
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            for script in soup(["script", "style", "header", "footer", "nav"]):
                script.extract()

            text = soup.get_text(separator="\n", strip=True)

            text = " ".join(text.split())
            return text[:10000] if text else None

        except Exception as e:
            logger.warning(f"Error fetching content from {url}: {e}")
            return None

# --- Advanced Dork Crawler Logic ---
class AdvancedDorkCrawler:
    # --- SerpAPI Configuration ---
    # IMPORTANT: Replace with your actual SerpAPI key or set as environment variable
    SERPAPI_KEY = "941c74017814139a848a0f0684c3dec9d6e7f58c1fcbb1198a76bf9c92f30db8" 

    def __init__(self, search_engine: str = "google"):
        self.search_engine = search_engine.lower()
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"}
        self.cache = SearchCache()

    def _perform_google_search(self, dork_query: str) -> List[Dict[str, Any]]:
        search_url = f"https://www.google.com/search?q={requests.utils.quote(dork_query)}"
        r = requests.get(search_url, headers=self.headers, timeout=15)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for g in soup.find_all('div', class_='g'):
            link_tag = g.find('a')
            if link_tag and 'href' in link_tag.attrs:
                url = link_tag['href']
                title_tag = g.find('h3')
                title = title_tag.get_text() if title_tag else 'No Title'

                cached_link = None
                cache_tag = g.find('a', text='Cached')
                if cache_tag and 'href' in cache_tag.attrs:
                    cached_link = cache_tag['href']
                
                results.append({
                    "title": title,
                    "url": url,
                    "cached_url": cached_link
                })
        
        external_results = []
        seen_urls = set()
        for res in results:
            url = res['url']
            if url and "google.com" not in url and "schemas.google.com" not in url and url not in seen_urls:
                external_results.append(res)
                seen_urls.add(url)
        return external_results

    def _perform_duckduckgo_search(self, dork_query: str) -> List[Dict[str, Any]]:
        search_url = f"https://duckduckgo.com/html/?q={requests.utils.quote(dork_query)}"
        r = requests.get(search_url, headers=self.headers, timeout=15)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for result_div in soup.find_all('div', class_='result'):
            link_tag = result_div.find('a', class_='result__a')
            if link_tag and 'href' in link_tag.attrs:
                url = link_tag['href']
                title = link_tag.get_text(strip=True)
                
                results.append({
                    "title": title,
                    "url": url,
                    "cached_url": None
                })
        
        external_results = []
        seen_urls = set()
        for res in results:
            url = res['url']
            if url and url not in seen_urls:
                external_results.append(res)
                seen_urls.add(url)
        return external_results

    def _perform_serpapi_search(self, dork_query: str) -> List[Dict[str, Any]]:
        if not self.SERPAPI_KEY:
            logger.error("SerpAPI key is not configured.")
            return []

        # SerpAPI uses 'q' for query and 'engine' for search engine (Google, Bing, DuckDuckGo, etc.)
        # We will use Google as the underlying engine for SerpAPI queries by default.
        params = {
            "api_key": self.SERPAPI_KEY,
            "engine": "google",  # Using Google as the backend for SerpAPI
            "q": dork_query,
            "hl": "en",
            "gl": "us"
        }

        try:
            response = requests.get("https://serpapi.com/search", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = []
            if "organic_results" in data:
                for res in data["organic_results"]:
                    cached_url = res.get("cached_page_link")
                    results.append({
                        "title": res.get("title"),
                        "url": res.get("link"),
                        "cached_url": cached_url
                    })
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Error during SerpAPI search for '{dork_query}': {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during SerpAPI search for '{dork_query}': {e}")
            return []


    def _perform_search(self, dork_query: str) -> List[Dict[str, Any]]:
        cached_results = self.cache.get(dork_query, self.search_engine)
        if cached_results:
            logger.info(f"Using cached search results for '{dork_query}' on {self.search_engine}")
            return cached_results

        search_function = None
        if self.search_engine == "google":
            search_function = self._perform_google_search
        elif self.search_engine == "duckduckgo":
            search_function = self._perform_duckduckgo_search
        elif self.search_engine == "serpapi":
            search_function = self._perform_serpapi_search
        else:
            logger.error(f"Unsupported search engine: {self.search_engine}")
            return []

        try:
            results = search_function(dork_query)
            # SerpAPI already provides filtered results, so no extra filtering is typically needed here
            if self.search_engine != "serpapi":
                external_results = []
                seen_urls = set()
                for res in results:
                    url = res.get('url')
                    if url and url not in seen_urls:
                        # Specific Google filtering (already in _perform_google_search) is not needed here
                        # For other direct engines, minimal filtering
                        external_results.append(res)
                        seen_urls.add(url)
                results = external_results # Update results to be filtered version
            
            self.cache.put(dork_query, results, self.search_engine)
            return results
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during search for '{dork_query}' on {self.search_engine}: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during search for '{dork_query}': {e}")
            return []


    def crawl_and_cache_content(self, url: str) -> Optional[str]:
        # Hash the URL to use as a cache key for content
        content_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Check cache for raw content, not just search results
        # Assuming the content is stored directly as a string under a 'content:' prefixed key
        cached_content_entry = self.cache.get(f"content:{content_hash}", "web_content")
        if cached_content_entry:
            logger.info(f"Using cached web content for '{url}'")
            # The cached_content_entry is a list of dicts from SearchCache.get
            # We stored [{"url": url, "content": content}]
            if cached_content_entry and isinstance(cached_content_entry, list) and len(cached_content_entry) > 0:
                return cached_content_entry[0].get('content')
            return None


        content = WebContentFetcher.fetch_content_sync(url)
        if content:
            self.cache.put(f"content:{content_hash}", [{"url": url, "content": content}], "web_content")
        return content

    def run_dork_crawl(self, dork_keyword: str):
        logger.info(f"\n--- Initiating advanced search for DORK: '{dork_keyword}' on {self.search_engine.upper()} ---")
        search_results = self._perform_search(dork_keyword)

        if not search_results:
            logger.info(f"No significant search results found for '{dork_keyword}' on {self.search_engine.upper()}.")
            return

        for i, result in enumerate(search_results):
            logger.info(f"\n[{self.search_engine.upper()}] Result {i+1}:")
            logger.info(f"  Title: {result.get('title', 'N/A')}")
            logger.info(f"  URL: {result.get('url', 'N/A')}")
            
            # Crawl and cache content
            if result.get('url'):
                logger.info(f"  Attempting to crawl content from: {result['url']}")
                crawled_content = self.crawl_and_cache_content(result['url'])
                if crawled_content:
                    logger.info(f"  Crawled Content (first 200 chars): {crawled_content[:200]}...")
                else:
                    logger.info(f"  Failed to crawl content from: {result['url']}")
            
            # Process cached URL from search engine
            if result.get('cached_url'):
                logger.info(f"  Search Engine Cache URL: {result['cached_url']}")
                logger.info(f"  Attempting to crawl cache content from: {result['cached_url']}")
                cached_page_content = self.crawl_and_cache_content(result['cached_url'])
                if cached_page_content:
                    logger.info(f"  Cached Content (first 200 chars): {cached_page_content[:200]}...")
                else:
                    logger.info(f"  Failed to crawl cache content from: {result['cached_url']}")

            time.sleep(random.uniform(1, 3)) # Delay between crawling each result URL

        logger.info(f"--- Advanced search completed for DORK: '{dork_keyword}' on {self.search_engine.upper()} ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python advanced_dork_crawler.py <search_engine1,search_engine2,...> <dork_keyword_1> <dork_keyword_2> ...")
        print("Example: python advanced_dork_crawler.py google,duckduckgo intext:\"password\" site:pastebin.com")
        sys.exit(1)
    
    # First argument is a comma-separated list of search engines
    search_engines_input = sys.argv[1].lower().split(',')
    keywords = sys.argv[2:]

    if not keywords:
        print("No dork keywords provided. Exiting.")
        sys.exit(1)

    supported_engines = ["google", "duckduckgo", "serpapi"]
    valid_engines = [e for e in search_engines_input if e in supported_engines]

    if not valid_engines:
        print(f"No valid search engines specified. Supported: {', '.join(supported_engines)}")
        sys.exit(1)

    for engine in valid_engines:
        crawler = AdvancedDorkCrawler(search_engine=engine)
        for dork_query in keywords:
            crawler.run_dork_crawl(dork_query)
            time.sleep(random.uniform(3, 7)) # Delay between each dork keyword and engine combination
