#!/bin/bash

# Define the search engines to use (comma-separated)
SEARCH_ENGINES="google,duckduckgo,serpapi"

# Read dkeywords.txt line by line
while IFS= read -r dork_keyword; do
    # Skip empty lines
    if [ -z "$dork_keyword" ]; then
        continue
    fi

    # Execute the advanced dork crawler for the current keyword across all specified engines
    python3 advanced_dork_crawler.py "$SEARCH_ENGINES" "$dork_keyword"
    echo ""
    
    # Add a longer delay between each dork keyword to prevent rate limiting across engines
    sleep 10

done < dkeywords.txt