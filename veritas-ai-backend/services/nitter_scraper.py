"""
Nitter scraper service for continuous tweet streaming using Selenium
"""
import time
import logging
import re
import random
from datetime import datetime, timedelta
from typing import Generator, Dict, Set, List
from urllib.parse import quote_plus

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not available, falling back to requests")

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Multiple Nitter instances to try (fallback if one is blocked)
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.it",
    "https://nitter.42l.fr",
    "https://nitter.pussthecat.org",
    "https://nitter.fdn.fr",
    "https://nitter.1d4.us",
    "https://nitter.kavin.rocks",
    "https://nitter.unixfox.eu",
]

# Rotating User-Agents to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

def get_random_headers(base_url: str) -> Dict[str, str]:
    """Get randomized browser-like headers"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "Referer": base_url,  # Important: set referer to same domain
        "DNT": "1",
    }


def parse_tweet_from_timeline_item(timeline_item, base_url: str = "https://nitter.net") -> Dict | None:
    """
    Parse a tweet from a timeline-item div (used for search results)
    
    Args:
        timeline_item: BeautifulSoup element of timeline-item div
        base_url: Base URL for Nitter instance
    
    Returns:
        Dictionary with tweet data or None if parsing fails
    """
    try:
        print(f"         🔍 Starting parse_tweet_from_timeline_item...")
        
        # Find tweet-body within timeline-item
        tweet_body = timeline_item.find('div', class_='tweet-body')
        if not tweet_body:
            print(f"         ❌ No tweet-body found in timeline-item")
            # Debug: Show what divs we do have
            all_divs = timeline_item.find_all('div', recursive=False)
            print(f"         📋 Direct child divs: {len(all_divs)}")
            for i, div in enumerate(all_divs[:3]):
                print(f"            Div #{i+1} classes: {div.get('class')}")
            return None
        
        print(f"         ✅ Found tweet-body")
        
        # Extract username from data attribute or from tweet-body
        username = timeline_item.get('data-username', 'unknown')
        print(f"         👤 Username from data-username: {username}")
        
        # Try to get username from tweet-body if available
        username_elem = tweet_body.find('a', class_='username')
        if username_elem:
            username_text = username_elem.get_text(strip=True).replace('@', '')
            if username_text:
                username = username_text
                print(f"         👤 Username from tweet-body: {username}")
        
        # Extract fullname
        fullname_elem = tweet_body.find('a', class_='fullname')
        fullname = fullname_elem.get_text(strip=True) if fullname_elem else username
        
        # Extract tweet text - try multiple class combinations
        text = ''
        # Try exact class match first
        content_elem = tweet_body.find('div', class_='tweet-content')
        if not content_elem:
            # Try with media-body class (common in search results)
            content_elem = tweet_body.find('div', class_=lambda x: x and 'tweet-content' in x)
        if content_elem:
            text = content_elem.get_text(strip=True)
            print(f"         📝 Text length: {len(text)} chars")
            if text:
                print(f"         ✅ Text preview: {text[:100]}...")
        else:
            print(f"         ⚠️  No tweet-content div found")
            # Fallback: try to get any text from tweet-body
            all_text = tweet_body.get_text(strip=True, separator=' ')
            # Remove username, fullname, and stats text
            if username in all_text:
                all_text = all_text.replace(f"@{username}", "").strip()
            if fullname in all_text:
                all_text = all_text.replace(fullname, "").strip()
            # Try to extract meaningful text (skip stats)
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            # Filter out lines that look like stats (numbers, short text)
            text_lines = [line for line in lines if len(line) > 10 and not re.match(r'^\d+$', line)]
            if text_lines:
                text = ' '.join(text_lines[:3])  # Take first 3 meaningful lines
                print(f"         📝 Extracted text via fallback: {len(text)} chars")
        
        if not text:
            print(f"         ⚠️  No text found in tweet")
        
        # Extract tweet URL and ID from tweet-link
        tweet_link = timeline_item.find('a', class_='tweet-link')
        tweet_url = ''
        tweet_id = ''
        if tweet_link:
            href = tweet_link.get('href', '')
            print(f"         🔗 Tweet-link href: {href}")
            if href:
                # Extract ID from URL like /username/status/1234567890
                match = re.search(r'/status/(\d+)', href)
                if match:
                    tweet_id = match.group(1)
                    tweet_url = f"{base_url}{href.split('#')[0]}"
                    print(f"         ✅ Extracted tweet_id: {tweet_id}")
                else:
                    print(f"         ⚠️  Could not extract tweet_id from href: {href}")
        else:
            print(f"         ❌ No tweet-link found")
        
        # Extract timestamp
        date_elem = tweet_body.find('span', class_='tweet-date')
        timestamp_str = ''
        if date_elem:
            date_link = date_elem.find('a')
            if date_link:
                timestamp_str = date_link.get('title', '')
        
        timestamp = None
        if timestamp_str:
            try:
                # Parse format like "Nov 28, 2025 · 5:03 PM UTC"
                timestamp = datetime.strptime(timestamp_str, "%b %d, %Y · %I:%M %p UTC")
            except:
                pass
        
        # Extract stats
        stats = tweet_body.find('div', class_='tweet-stats')
        likes = 0
        retweets = 0
        replies = 0
        
        if stats:
            stat_spans = stats.find_all('span', class_='tweet-stat')
            for span in stat_spans:
                stat_text = span.get_text(strip=True)  # Use different variable name!
                # Check for retweets
                if 'icon-retweet' in str(span):
                    match = re.search(r'(\d+)', stat_text)
                    if match:
                        retweets = int(match.group(1))
                # Check for likes
                elif 'icon-heart' in str(span):
                    match = re.search(r'(\d+)', stat_text)
                    if match:
                        likes = int(match.group(1))
                # Check for replies
                elif 'icon-comment' in str(span):
                    match = re.search(r'(\d+)', stat_text)
                    if match:
                        replies = int(match.group(1))
        
        # Extract media URLs
        media_urls = []
        attachments = tweet_body.find('div', class_='attachments')
        if attachments:
            images = attachments.find_all('img')
            for img in images:
                src = img.get('src', '')
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('/'):
                        media_urls.append(f"{base_url}{src}")
                    else:
                        media_urls.append(src)
        
        if not tweet_id:
            print(f"         ❌ Missing tweet_id, cannot create tweet data")
            return None
        if not text:
            print(f"         ⚠️  Missing text, but continuing with empty text")
        
        print(f"         ✅ Successfully parsed tweet: {tweet_id} by @{username}")
        
        return {
            'tweet_id': tweet_id,
            'text': text,
            'username': username,
            'fullname': fullname,
            'timestamp': timestamp.isoformat() if timestamp else datetime.utcnow().isoformat(),
            'likes': likes,
            'retweets': retweets,
            'replies': replies,
            'tweet_url': tweet_url,
            'media_urls': media_urls
        }
    except Exception as e:
        logger.error(f"Error parsing timeline-item: {e}")
        print(f"      ❌ Error parsing timeline-item: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_tweet_html(tweet_html: str, base_url: str = "https://nitter.net") -> Dict | None:
    """
    Parse a single tweet from HTML
    
    Args:
        tweet_html: HTML content of a tweet div
        base_url: Base URL for Nitter instance
    
    Returns:
        Dictionary with tweet data or None if parsing fails
    """
    try:
        soup = BeautifulSoup(tweet_html, 'html.parser')
        
        # Extract tweet ID from the main tweet div
        main_tweet = soup.find('div', class_='main-tweet')
        if not main_tweet:
            return None
        
        tweet_body = main_tweet.find('div', class_='tweet-body')
        if not tweet_body:
            return None
        
        # Extract username
        username_elem = tweet_body.find('a', class_='username')
        username = username_elem.get_text(strip=True).replace('@', '') if username_elem else 'unknown'
        
        # Extract fullname
        fullname_elem = tweet_body.find('a', class_='fullname')
        fullname = fullname_elem.get_text(strip=True) if fullname_elem else username
        
        # Extract tweet text
        content_elem = tweet_body.find('div', class_='tweet-content')
        text = content_elem.get_text(strip=True) if content_elem else ''
        
        # Extract tweet URL and ID
        tweet_link = tweet_body.find('a', class_='tweet-date')
        tweet_url = ''
        tweet_id = ''
        if tweet_link:
            href = tweet_link.get('href', '')
            if href:
                # Extract ID from URL like /username/status/1234567890
                match = re.search(r'/status/(\d+)', href)
                if match:
                    tweet_id = match.group(1)
                    tweet_url = f"{base_url}{href.split('#')[0]}"
        
        # Extract timestamp
        published_elem = tweet_body.find('p', class_='tweet-published')
        timestamp_str = published_elem.get_text(strip=True) if published_elem else ''
        timestamp = None
        if timestamp_str:
            try:
                # Parse format like "Nov 28, 2025 · 4:53 AM UTC"
                timestamp = datetime.strptime(timestamp_str, "%b %d, %Y · %I:%M %p UTC")
            except:
                pass
        
        # Extract stats
        stats = tweet_body.find('div', class_='tweet-stats')
        likes = 0
        retweets = 0
        replies = 0
        
        if stats:
            # Find retweet count
            retweet_elem = stats.find('span', class_='tweet-stat')
            if retweet_elem:
                retweet_text = retweet_elem.get_text(strip=True)
                retweet_match = re.search(r'(\d+)', retweet_text)
                if retweet_match:
                    retweets = int(retweet_match.group(1))
            
            # Find all stat spans
            stat_spans = stats.find_all('span', class_='tweet-stat')
            for span in stat_spans:
                stat_text = span.get_text(strip=True)  # Use different variable name to avoid overwriting tweet text!
                # Check for retweets
                if 'icon-retweet' in str(span):
                    match = re.search(r'(\d+)', stat_text)
                    if match:
                        retweets = int(match.group(1))
                # Check for likes
                elif 'icon-heart' in str(span):
                    match = re.search(r'(\d+)', stat_text)
                    if match:
                        likes = int(match.group(1))
                # Check for replies
                elif 'icon-comment' in str(span):
                    match = re.search(r'(\d+)', stat_text)
                    if match:
                        replies = int(match.group(1))
        
        # Extract media URLs
        media_urls = []
        attachments = tweet_body.find('div', class_='attachments')
        if attachments:
            images = attachments.find_all('img')
            for img in images:
                src = img.get('src', '')
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('/'):
                        media_urls.append(f"{base_url}{src}")
                    else:
                        media_urls.append(src)
        
        if not tweet_id or not text:
            return None
        
        return {
            'tweet_id': tweet_id,
            'text': text,
            'username': username,
            'fullname': fullname,
            'timestamp': timestamp.isoformat() if timestamp else datetime.utcnow().isoformat(),
            'likes': likes,
            'retweets': retweets,
            'replies': replies,
            'tweet_url': tweet_url,
            'media_urls': media_urls
        }
    except Exception as e:
        logger.error(f"Error parsing tweet HTML: {e}")
        return None


def setup_selenium_driver(headless: bool = True):
    """Setup Selenium Chrome driver"""
    if not SELENIUM_AVAILABLE:
        raise ImportError("Selenium is not installed. Install with: pip install selenium")
    
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        # Remove webdriver property to avoid detection
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        return driver
    except Exception as e:
        print(f"   ❌ Failed to create Chrome driver: {e}")
        print(f"   💡 Make sure ChromeDriver is installed and in PATH")
        raise


def scrape_nitter_search_selenium(
    query: str,
    seen_ids: Set[str],
    refresh_interval: int = 120,  # Increased to 2 minutes to avoid rate limiting
    base_url: str = None
) -> Generator[Dict, None, None]:
    """
    Continuously scrape Nitter search results using Selenium (real browser)
    
    Args:
        query: Search query string
        seen_ids: Set of already seen tweet IDs
        refresh_interval: Seconds between requests
        base_url: Nitter instance base URL (will try multiple if None)
    
    Yields:
        Dictionary with tweet data
    """
    logger.info(f"Starting Nitter scraper (Selenium) for query: {query}")
    print(f"\n🔍 STARTING NITTER SCRAPER (SELENIUM)")
    print(f"Query: '{query}'")
    print(f"Refresh interval: {refresh_interval} seconds")
    
    # Calculate since date (last 24 hours)
    since_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"Searching tweets since: {since_date}")
    
    # Try multiple instances if base_url not specified
    instances_to_try = [base_url] if base_url else NITTER_INSTANCES
    current_instance_idx = 0
    consecutive_failures = 0
    max_failures = 3
    
    driver = None
    
    try:
        # Setup Selenium driver once
        print(f"   🚀 Setting up Selenium Chrome driver...")
        driver = setup_selenium_driver(headless=True)
        print(f"   ✅ Chrome driver ready")
        
        while True:
            try:
                # Rotate through instances if we're having issues
                if consecutive_failures >= max_failures:
                    current_instance_idx = (current_instance_idx + 1) % len(instances_to_try)
                    consecutive_failures = 0
                    print(f"   🔄 Switching to new Nitter instance...")
                
                current_base_url = instances_to_try[current_instance_idx]
                print(f"   🌐 Using Nitter instance: {current_base_url}")
                
                # Build search URL
                encoded_query = quote_plus(query)
                search_url = f"{current_base_url}/search?f=tweets&q={encoded_query}&since={since_date}"
                
                logger.info(f"Fetching: {search_url}")
                print(f"\n📡 Navigating to: {search_url}")
                
                # Navigate to search page
                driver.get(search_url)
                
                # Wait for page to load
                print(f"   ⏳ Waiting for page to load...")
                try:
                    # Wait for timeline to appear
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "timeline"))
                    )
                    print(f"   ✅ Timeline loaded")
                except TimeoutException:
                    print(f"   ⚠️  Timeline not found, trying to continue anyway...")
                
                # Small delay to let JavaScript finish
                time.sleep(2)
                
                # Get page source
                page_source = driver.page_source
                print(f"   📏 Page source size: {len(page_source)} bytes")
                
                if len(page_source) < 1000:
                    print(f"   ❌ Page source too small, might be blocked")
                    consecutive_failures += 1
                    time.sleep(5)
                    continue
                
                # Success! Reset failure counter
                consecutive_failures = 0
                
                print(f"   🔍 Parsing HTML...")
                
                # Parse HTML
                soup = BeautifulSoup(page_source, 'html.parser')
            
                # Debug: Check for timeline container FIRST (this is the key!)
                timeline_container = soup.find('div', class_='timeline')
                items_in_timeline = []
                if timeline_container:
                    print(f"   ✅ Found timeline container!")
                    # Find timeline-items within timeline - THIS IS THE CORRECT WAY
                    items_in_timeline = timeline_container.find_all('div', class_=lambda x: x and 'timeline-item' in str(x).lower())
                    print(f"   📊 Found {len(items_in_timeline)} timeline-items inside timeline container")
                    if items_in_timeline:
                        print(f"   ✅ Using items from timeline container (this is correct!)")
                else:
                    print(f"   ⚠️  No timeline container found")
                    # Try alternative: look for timeline-container
                    timeline_container_alt = soup.find('div', class_='timeline-container')
                    if timeline_container_alt:
                        print(f"   ✅ Found timeline-container instead")
                        items_in_timeline = timeline_container_alt.find_all('div', class_=lambda x: x and 'timeline-item' in str(x).lower())
                        print(f"   📊 Found {len(items_in_timeline)} timeline-items inside timeline-container")
                    else:
                        print(f"   ❌ No timeline or timeline-container found")
                
                # Use items from timeline if found, otherwise try other methods
                if items_in_timeline:
                    timeline_items = items_in_timeline
                    print(f"   ✅ Using {len(timeline_items)} items from timeline container")
                else:
                    # Fallback: try other methods
                    items_with_username = soup.find_all('div', attrs={'data-username': True})
                    timeline_items = items_with_username
                    print(f"   ✅ Using {len(timeline_items)} items from data-username method")
                
                logger.info(f"Found {len(timeline_items)} tweets in response")
                print(f"📊 Found {len(timeline_items)} tweet containers in HTML response")
                
                # Debug: If no items found, show sample HTML
                if len(timeline_items) == 0:
                    print(f"   ⚠️  NO TWEETS FOUND - Debugging HTML structure...")
                    print(f"   📄 Sample HTML (first 3000 chars):")
                    print(f"   {page_source[:3000]}")
                    print(f"   \n   🔍 Looking for any divs with 'timeline' in class...")
                    timeline_divs = soup.find_all('div', class_=lambda x: x and 'timeline' in str(x).lower())
                    print(f"   Found {len(timeline_divs)} divs with 'timeline' in class")
                    if timeline_divs:
                        print(f"   First timeline div classes: {timeline_divs[0].get('class')}")
                        print(f"   First timeline div HTML (first 1000 chars): {str(timeline_divs[0])[:1000]}")
                        # Try to find items inside this div
                        items_inside = timeline_divs[0].find_all('div', class_=lambda x: x and 'timeline-item' in str(x).lower())
                        print(f"   Found {len(items_inside)} timeline-items inside this div")
                        if items_inside:
                            print(f"   ✅ Using items from inside timeline div!")
                            timeline_items = items_inside
                
                new_tweets = 0
                for idx, item in enumerate(timeline_items):
                    print(f"\n   🔍 Processing timeline-item #{idx + 1}/{len(timeline_items)}...")
                    print(f"      📋 Item classes: {item.get('class')}")
                    print(f"      📋 Item data-username: {item.get('data-username', 'N/A')}")
                    
                    # For search results, tweets are directly in timeline-item, not in main-tweet
                    # Try to find main-tweet parent first (for individual tweet pages)
                    main_tweet = item.find_parent('div', class_='main-tweet')
                    
                    # If no main-tweet parent, the tweet is directly in timeline-item (search results)
                    if not main_tweet:
                        # For search results, parse the timeline-item directly
                        print(f"      📄 Parsing as search result timeline-item...")
                        tweet_data = parse_tweet_from_timeline_item(item, current_base_url)
                    else:
                        # For individual tweet pages, parse the main-tweet
                        print(f"      📄 Parsing as main-tweet...")
                        tweet_data = parse_tweet_html(str(main_tweet), current_base_url)
                    
                    if not tweet_data:
                        print(f"      ❌ Failed to parse tweet data, skipping...")
                        # Debug: Show what we found in the item
                        tweet_body = item.find('div', class_='tweet-body')
                        tweet_link = item.find('a', class_='tweet-link')
                        print(f"         - Has tweet-body: {tweet_body is not None}")
                        print(f"         - Has tweet-link: {tweet_link is not None}")
                        if tweet_link:
                            print(f"         - Tweet-link href: {tweet_link.get('href', 'N/A')}")
                        continue
                    
                    tweet_id = tweet_data['tweet_id']
                    
                    # Skip if already seen
                    if tweet_id in seen_ids:
                        print(f"      ⏭️  Tweet {tweet_id} already seen, skipping")
                        continue
                    
                    # Mark as seen
                    seen_ids.add(tweet_id)
                    new_tweets += 1
                    
                    logger.info(f"New tweet found: {tweet_id} by @{tweet_data['username']}")
                    
                    # Print tweet details for visibility
                    print(f"\n{'='*80}")
                    print(f"🐦 NEW TWEET SCRAPED")
                    print(f"{'='*80}")
                    print(f"Tweet ID: {tweet_id}")
                    print(f"Username: @{tweet_data['username']} ({tweet_data['fullname']})")
                    print(f"Text: {tweet_data['text'][:150]}..." if len(tweet_data['text']) > 150 else f"Text: {tweet_data['text']}")
                    print(f"Timestamp: {tweet_data['timestamp']}")
                    print(f"Engagement: {tweet_data['likes']} likes, {tweet_data['retweets']} retweets, {tweet_data['replies']} replies")
                    print(f"URL: {tweet_data['tweet_url']}")
                    if tweet_data['media_urls']:
                        print(f"Media: {len(tweet_data['media_urls'])} image(s)")
                    print(f"{'='*80}\n")
                    
                    # Yield tweet
                    yield tweet_data
                
                logger.info(f"Scraped {new_tweets} new tweets, total seen: {len(seen_ids)}")
                print(f"✅ Scraped {new_tweets} new tweets this cycle (total seen: {len(seen_ids)})")
                
            except TimeoutException as e:
                logger.error(f"Timeout error: {e}")
                print(f"❌ Timeout error: {e}")
                consecutive_failures += 1
                time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                print(f"❌ Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                consecutive_failures += 1
                time.sleep(5)
            
            # Wait before next request (with some randomness to avoid patterns)
            # Use longer wait times to avoid rate limiting
            wait_time = refresh_interval + random.uniform(-10, 10)
            wait_time = max(wait_time, refresh_interval * 0.9)  # Don't go below 90% of interval
            print(f"⏳ Waiting {wait_time:.1f} seconds before next fetch (to avoid rate limiting)...\n")
            time.sleep(wait_time)
                
    finally:
        # Cleanup: close browser
        if driver:
            print(f"   🧹 Closing browser...")
            driver.quit()
            print(f"   ✅ Browser closed")


def scrape_nitter_search(
    query: str,
    seen_ids: Set[str],
    refresh_interval: int = 120,  # Increased to 2 minutes to avoid rate limiting
    base_url: str = None
) -> Generator[Dict, None, None]:
    """
    Continuously scrape Nitter search results
    Uses Selenium if available, falls back to requests
    """
    if SELENIUM_AVAILABLE:
        print(f"   ✅ Using Selenium (real browser)")
        yield from scrape_nitter_search_selenium(query, seen_ids, refresh_interval, base_url)
    else:
        print(f"   ⚠️  Selenium not available, this function needs Selenium")
        raise ImportError("Selenium is required. Install with: pip install selenium")

