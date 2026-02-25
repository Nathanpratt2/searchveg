# SearchVeg.com

A high-performance, minimal-maintenance discovery engine for new vegan recipes. This project is built with a "Creator First" philosophy, designed to send traffic directly to bloggers while remaining robust enough to rarely break.

# 🎯 Core Philosophy
1. Simple & Robust
The goal is to have as few moving parts as possible. It is better to have fewer features that work perfectly than complex features that require constant fixing. If a feature isn't essential to finding a meal, it isn't included.
2. Creator First (Traffic to Real People)
This site is a bridge, not a destination. We do not display ingredients or instructions. By keeping "time on site" low, we ensure that the value—and the traffic—is passed directly to the original creators.
3. Zero Dependencies & "No-Break" Programming
To ensure the site remains functional for years with zero intervention:
No Image Proxies: We load original images directly. We do not use services like weserv.nl because they create a single point of failure.
No Production LLMs: We do not use AI in the live environment. This prevents API failures and allows the site to run completely free.
No Frameworks: Built with 100% Vanilla JS, HTML, and CSS. There are no libraries to update or build-tools to manage.

# 📊 Data & Inventory Logic
This site is designed to be seasonally relevant, not a permanent archive of every recipe ever.
The Cap: To prevent a single large blog from dominating the feed, we cap each creator at 250 recipes (with strict pruning for older content). This ensures a diverse mix of voices.
Categorization (Top vs. Disruptors)
We avoid complex, subjective ranking systems. Creators are categorized simply:
- Top Bloggers: High-traffic, established vegan heavyweights (e.g., Minimalist Baker, Rainbow Plant Life).
- Disruptors / Rising Blogs: Up-and-coming creators or niche specialists (e.g., Full of Plants, Mary's Test Kitchen).
The Mix: The feed naturally balances these sources to ensure users discover new creators alongside established favorites.

# 🛠 Technical Implementation
The backend is a Python-based worker (fetch_recipes.py) that acts as a "Static Site Generator" for our data, transforming fragmented RSS feeds and HTML pages into a single, clean data.json file.
1. The Hybrid Fetching Pipeline
RSS Parsing: Uses feedparser to grab the latest entries from over 80+ curated vegan blogs.
Direct HTML Scraping: For blogs that don't provide RSS feeds (or provide poor ones), we use BeautifulSoup and custom scrapers (supports WordPress archives and custom site structures).
Robust Fallbacks:
CloudScraper: Bypasses basic bot protection.
Selenium (Headless Chrome): Used as a "last resort" fetcher for sites heavily reliant on JavaScript or strict firewalls.
SSL & Network Hardening: Custom adapters handle legacy SSL ciphers to ensure connection to older servers.
2. Intelligent Data Extraction
Image Logic: The script uses a multi-step fallback system:
Check RSS media tags (media_content, media_thumbnail).
Scrape the post HTML for high-res images (filtering out pixels/emojis).
Fetch OpenGraph (og:image) tags via a secondary request if needed.
Date Normalization: extracting accurate publication dates from JSON-LD schema, meta tags, or URL patterns.
3. Automated Tagging (Logic-Based)
To avoid the complexity of a manual database or an LLM, the script auto-tags recipes using keyword matching:
WFPB: Looks for things such as "oil-free," "whole food," "no oil," "refined sugar free."
Easy: Looks for things such as "1-pot," "30-minute," "simple," "air fryer," "5-ingredient."
Budget: Looks for things such as "cheap," "pantry," "beans," "rice," "economical."
Gluten-Free (GF): Checks titles and source tags, with a safety filter to remove the tag if keywords like "seitan" or "wheat" appear.
4. Database Hygiene & Output
Global Deduplication: Removes duplicate recipes if posted by the same author across different feeds, prioritizing the version with better metadata (e.g., GF specific feeds).
Spam Filtering: aggressive filtering of non-recipe content (e.g., "Gift Guides," "Meal Plans," "Travel," "Giveaways").
LLM Context Generation: Automatically generates an llms.txt file, providing AI models with a structured index of the site's content for better SEO and citations.

# Feed Health Report
Very important - Generates FEED_HEALTH.md to visualize scrape success rates, broken links, and database composition. The ultimate hub for maintaining the website

# 📱 Frontend Architecture (index.html)
The frontend is a single-file Vanilla JS application designed for speed and UX.
Search & Discovery
Fuzzy Search: Implements a Levenshtein distance algorithm for "typo-tolerant" searching directly in the browser.
Smart Filtering:
Meals: Filters for savory keywords while excluding sides/sauces.
Sweets: Filters for dessert keywords while excluding savory terms (e.g., "sweet potato").
Shuffle: A randomized sorting function to surface older or less popular recipes.
User Experience (UX)
Dark Mode: Activated via a long-press on the logo (persisted via LocalStorage).
Infinite Scroll: Renders recipes in batches of 48 to keep the DOM light.
Skeleton Loading: CSS-based skeleton screens prevent layout shifts (CLS) during load.
PWA Support: Includes a manifest and install logic for "Add to Home Screen" functionality.
SEO & Performance
Lazy Loading: Native loading="lazy" for images below the fold; fetchpriority="high" for LCP images.
JSON-LD Schema: Dynamically injects WebSite, BreadcrumbList, and ItemList schema for rich results.
Dynamic Meta: Updates <title> and <meta description> based on current search/filters.

# 🚀 How to Run
Requirements
Python 3.9+
Chrome (for Selenium fallback)
Installation
code
Bash
Install Python dependencies
pip install -r requirements.txt
(Optional) Ensure Chrome is installed for Selenium
Execution
code
Bash
Run the scraper: python fetch_recipes.py
This will generate data.json, sitemap.xml, llms.txt, and FEED_HEALTH.md.

# 🛡 Maintenance
Updates: Content updates are handled by pushing a new data.json file via a scheduled task (e.g., GitHub Actions).
Monitoring: Check FEED_HEALTH.md periodically to identify:
Blogs that have changed domains or structures (❌ Blocked/HTML Fail).
Feeds returning 0 items (⚠️ Low Count).
Configuration: Add or remove blogs simply by editing the TOP_BLOGGERS, DISRUPTORS, or HTML_SOURCES lists in fetch_recipes.py
