import requests
import re
import time
import random
import sys

def interactive_dork_search(keywords):
    report = "--- INTERACTIVE DORK SEARCH RESULTS ---"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"}

    for dork_query in keywords:
        if not dork_query.strip():
            continue
        report += f"\nSearching for DORK: {dork_query}\n"
        try:
            # Using Google search URL directly
            search_url = f"https://www.google.com/search?q={requests.utils.quote(dork_query)}"
            r = requests.get(search_url, headers=headers, timeout=15)
            
            # Extracting links (href attributes)
            links = re.findall(r'href="(https?://[^"]+)"', r.text)
            
            # Filter out Google internal links and duplicates
            external_links = []
            for link in links:
                if "google.com" not in link and "schemas.google.com" not in link and link not in external_links:
                    external_links.append(link)

            if external_links:
                for link in external_links:
                    report += f"  LINK: {link}\n"
            else:
                report += "  No external links found.\n"

        except requests.exceptions.RequestException as e:
            report += f"  Error during search for '{dork_query}': {e}\n"
        except Exception as e:
            report += f"  An unexpected error occurred for '{dork_query}': {e}\n"
        
        time.sleep(random.uniform(2, 5)) # Be polite to Google

    return report

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If arguments are provided, treat them as keywords
        keywords = sys.argv[1:]
    else:
        # Otherwise, prompt the user for input
        print("Enter dork keywords (one per line). Press Enter twice to finish:")
        keywords = []
        while True:
            line = input()
            if not line:
                break
            keywords.append(line)
    
    if keywords:
        results = interactive_dork_search(keywords)
        print(results)
    else:
        print("No keywords provided. Exiting.")
