import requests
import base64
import re
import time
import urllib3
from urllib.parse import quote
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import cloudscraper

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def format_timestamp(unix_timestamp):
    """Convert Unix timestamp to readable format"""
    if not unix_timestamp:
        return "Unknown"
    dt = datetime.fromtimestamp(unix_timestamp)
    return dt.strftime("%Y-%m-%d %H:%M")

def extract_ppv_proxy_links():
    api_url = "https://ppv.to/api/streams"
    
    # Categories to include
    wanted_categories = ["Basketball", "Football", "Motorsports", "Combat Sports"]
    
    # Proxy base URL
    proxy_base = "https://addon3.gstream.stream/proxy/m3u8"
    referer = "https://ppv.to/"
    
    # Headers mimicking a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'https://ppv.to/',
        'Origin': 'https://ppv.to',
    }

    # Setup cloudscraper instead of plain requests
    # This handles Cloudflare/WAF challenges automatically
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    print(f"Fetching streams from {api_url}...")
    try:
        resp = scraper.get(api_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Error fetching API: {e}")
        return

    streams_data = data.get("streams", [])
    print(f"Found {len(streams_data)} categories.")

    m3u_content = ["#EXTM3U"]

    for category in streams_data:
        cat_name = category.get("category", "Unknown")
        
        # Filter categories
        if cat_name not in wanted_categories:
            print(f"Skipping category: {cat_name}")
            continue
            
        cat_streams = category.get("streams", [])
        print(f"\nProcessing Category: {cat_name} ({len(cat_streams)} streams)")
        
        for s in cat_streams:
            name = s.get("name", "Unknown")
            iframe_url = s.get("iframe")
            poster = s.get("poster", "")
            starts_at = s.get("starts_at")
            ends_at = s.get("ends_at")
            
            if not iframe_url:
                continue

            # Adjust time by +1 hour (3600 seconds)
            if starts_at:
                starts_at += 3600
            if ends_at:
                ends_at += 3600

            # Determine LIVE status
            status_prefix = ""
            if starts_at:
                start_dt = datetime.fromtimestamp(starts_at)
                now = datetime.now()
                # If more than 30 mins (1800s) until start -> NOT LIVE
                # Otherwise (within 30 mins or started) -> LIVE
                if (start_dt - now).total_seconds() > 1800:
                    status_prefix = "[NOT LIVE] "
                else:
                    status_prefix = "[LIVE] "
                
            print(f"  Resolving {name}...")
            
            try:
                # Fetch iframe content using cloudscraper
                # verify=False to ignore SSL errors on embednow.top
                iframe_resp = scraper.get(iframe_url, headers=headers, timeout=30, verify=False)
                
                if iframe_resp.status_code != 200:
                    print(f"    ❌ Failed to fetch iframe: Status {iframe_resp.status_code}")
                    continue

                iframe_text = iframe_resp.text
                
                # Extract base64 encoded URL - improved regex for single/double quotes and spaces
                match = re.search(r'atob\s*\(\s*["\'](.*?)["\']\s*\)', iframe_text)
                
                if match:
                    encoded = match.group(1)
                    try:
                        decoded_bytes = base64.b64decode(encoded)
                        stream_url = decoded_bytes.decode('utf-8')
                        
                        # Build proxy URL
                        encoded_stream_url = quote(stream_url, safe='')
                        encoded_referer = quote(referer, safe='')
                        proxy_url = f"{proxy_base}?u={encoded_stream_url}&ref={encoded_referer}&rw=1"
                        
                        # Format event times
                        start_time = format_timestamp(starts_at)
                        end_time = format_timestamp(ends_at)
                        
                        # Add time info and status to channel name
                        channel_name = f"{status_prefix}{name} [{start_time}]"
                        
                        # Add to M3U with extended info
                        entry = (
                            f'#EXTINF:-1 tvg-logo="{poster}" '
                            f'group-title="{cat_name}" '
                            f'tvg-id="{name}" '
                            f'tvg-name="{channel_name}",'
                            f'{channel_name}\n'
                            f'{proxy_url}'
                        )
                        m3u_content.append(entry)
                        print(f"    ✅ Created proxy link | {status_prefix}| Start: {start_time}")
                    except Exception as decode_err:
                        print(f"    ❌ Error decoding base64: {decode_err}")
                else:
                    # Debug: print a bit of the response if failed
                    snippet = iframe_text[:100].replace('\n', ' ')
                    print(f"    ❌ Could not find encoded URL in iframe. Snippet: {snippet}...")
                    
            except Exception as e:
                print(f"    ⚠️ Error resolving {name}: {e}")
            
            # Slight delay to be nice
            time.sleep(0.5)

    # Save to file
    with open("ppv_proxy.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    
    print(f"\n✅ Saved {len(m3u_content)-1} streams to ppv_proxy.m3u")

if __name__ == "__main__":
    extract_ppv_proxy_links()
