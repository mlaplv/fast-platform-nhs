import urllib.request
import xml.etree.ElementTree as ET

url = "https://admin.osmo.vn/google-merchant.xml"
print("Fetching Merchant XML from:", url)

try:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        content = response.read()
        print(f"✅ Fetched successfully! Size: {len(content)} bytes")
        
        # Parse XML
        root = ET.fromstring(content)
        print("✅ XML parsed successfully! No syntax errors.")
        
        # Inspect channel and items
        channel = root.find("channel")
        if channel is not None:
            title = channel.find("title").text if channel.find("title") is not None else "N/A"
            link = channel.find("link").text if channel.find("link") is not None else "N/A"
            items = channel.findall("item")
            print(f"Channel Title: {title}")
            print(f"Channel Link: {link}")
            print(f"Total items found in feed: {len(items)}")
            
            # Print first 2 items details
            for i, item in enumerate(items[:2]):
                item_id = item.find("{http://base.google.com/ns/1.0}id")
                item_title = item.find("{http://base.google.com/ns/1.0}title")
                item_price = item.find("{http://base.google.com/ns/1.0}price")
                item_avail = item.find("{http://base.google.com/ns/1.0}availability")
                
                print(f"\nItem {i+1}:")
                print(f"  ID: {item_id.text if item_id is not None else 'N/A'}")
                print(f"  Title: {item_title.text if item_title is not None else 'N/A'}")
                print(f"  Price: {item_price.text if item_price is not None else 'N/A'}")
                print(f"  Availability: {item_avail.text if item_avail is not None else 'N/A'}")
        else:
            print("❌ Channel tag not found in RSS XML!")
except Exception as e:
    print("❌ Failed:", e)
