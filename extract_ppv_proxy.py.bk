import requests
import base64
import re
import time
from urllib.parse import quote
from datetime import datetime

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
    
    headers = {}

    print(f"Fetching streams from {api_url}...")
    try:
        resp = requests.get(api_url, headers=headers, timeout=30)
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
                
            print(f"  Resolving {name}...")
            
            try:
                # Fetch iframe content
                iframe_resp = requests.get(iframe_url, headers=headers, timeout=30)
                iframe_text = iframe_resp.text
                
                # Extract base64 encoded URL
                match = re.search(r'atob\("(.*?)"\)', iframe_text)
                
                if match:
                    encoded = match.group(1)
                    decoded_bytes = base64.b64decode(encoded)
                    stream_url = decoded_bytes.decode('utf-8')
                    
                    # Build proxy URL
                    encoded_stream_url = quote(stream_url, safe='')
                    encoded_referer = quote(referer, safe='')
                    proxy_url = f"{proxy_base}?u={encoded_stream_url}&ref={encoded_referer}&rw=1"
                    
                    # Format event times
                    start_time = format_timestamp(starts_at)
                    end_time = format_timestamp(ends_at)
                    
                    # Add time info to channel name
                    channel_name = f"{name} [{start_time}]"
                    
                    # Add to M3U with extended info
                    # tvg-chno can be used for sorting by time
                    entry = (
                        f'#EXTINF:-1 tvg-logo="{poster}" '
                        f'group-title="{cat_name}" '
                        f'tvg-id="{name}" '
                        f'tvg-name="{channel_name}",'
                        f'{channel_name}\n'
                        f'{proxy_url}'
                    )
                    m3u_content.append(entry)
                    print(f"    ✅ Created proxy link | Start: {start_time} | End: {end_time}")
                else:
                    print(f"    ❌ Could not find encoded URL in iframe.")
                    
            except Exception as e:
                print(f"    ⚠️ Error resolving {name}: {e}")
            
            time.sleep(0.2)

    # Save to file
    with open("ppv_proxy.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    
    print(f"\n✅ Saved {len(m3u_content)-1} streams to ppv_proxy.m3u")

if __name__ == "__main__":
    extract_ppv_proxy_links()
