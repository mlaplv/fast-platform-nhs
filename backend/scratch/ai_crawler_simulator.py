#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse
import re
import sys

# Color formatting for beautiful CLI reporting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

BOT_USER_AGENTS = {
    "Gemini / Googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "ChatGPT Search / GPTBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)",
    "PerplexityBot": "Mozilla/5.0 (compatible; PerplexityBot/1.0; +http://www.perplexity.ai/bot.html)",
    "ClaudeBot / Anthropic": "Mozilla/5.0 (compatible; ClaudeBot/1.0; +http://www.anthropic.com/claudebot)"
}

def check_robots_policy(user_agent: str, path: str) -> str:
    """Mock-check the robots.txt logic against our static robots.txt patterns."""
    segments = [s for s in path.split("/") if s]
    
    if path.endswith(".html"):
        return "ALLOWED (Matches Allow: /*.html$)"
    elif len(segments) == 1:
        return "ALLOWED (Matches Allow: /*$)"
    elif len(segments) > 1:
        return "DISALLOWED (Matches Disallow: /*/*$)"
    elif path == "/" or path == "/sitemap.xml":
        return "ALLOWED"
    return "UNKNOWN"

def run_simulation(target_url: str):
    print(f"\n{BOLD}{CYAN}===================================================================={RESET}")
    print(f"{BOLD}{CYAN}       AI SEARCH ENGINE & GEO COMPLIANCE SIMULATION AUDIT           {RESET}")
    print(f"{BOLD}{CYAN}===================================================================={RESET}")
    print(f"Target URL: {BOLD}{target_url}{RESET}\n")

    parsed_url = urllib.parse.urlparse(target_url)
    path = parsed_url.path

    for bot_name, ua in BOT_USER_AGENTS.items():
        print(f"🤖 Testing Bot: {BOLD}{bot_name}{RESET}")
        print(f"   User-Agent: {CYAN}{ua}{RESET}")
        
        # Check robots.txt status
        robots_status = check_robots_policy(ua, path)
        print(f"   Robots.txt Policy: {GREEN if 'ALLOWED' in robots_status else RED}{robots_status}{RESET}")
        
        try:
            # Setup request
            req = urllib.request.Request(
                target_url,
                headers={'User-Agent': ua}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                status_code = response.status
                html_bytes = response.read()
                html = html_bytes.decode('utf-8')
                
                print(f"   HTTP Response: {GREEN}{status_code} OK{RESET}")
                
                # Check 1: Find Schema Tag
                schema_matches = re.findall(
                    r'<script type="application/ld\+json" id="seo-schema-graph">(.*?)</script>', 
                    html, 
                    re.DOTALL
                )
                
                if not schema_matches:
                    print(f"   {RED}✗ ERROR: Could not find <script type=\"application/ld+json\" id=\"seo-schema-graph\"> tag!{RESET}")
                    continue
                
                # Check for multiple script tags (duplication verification)
                total_scripts = html.count('<script type="application/ld+json"')
                if total_scripts == 1:
                    print(f"   Deduplication Status: {GREEN}PASS (Exactly 1 JSON-LD schema block found){RESET}")
                else:
                    print(f"   Deduplication Status: {RED}FAIL ({total_scripts} JSON-LD schema blocks found!){RESET}")
                
                # Parse JSON-LD
                schema_json = json.loads(schema_matches[0])
                print(f"   JSON-LD Parse: {GREEN}SUCCESS (Valid JSON syntax){RESET}")
                
                # Check 2: Verify W3C Graph structure
                if "@graph" not in schema_json:
                    print(f"   Structure Check: {RED}FAIL (Missing '@graph' root array - invalid structure for AI bots){RESET}")
                    continue
                
                graph = schema_json["@graph"]
                print(f"   Structure Check: {GREEN}PASS ('@graph' structured array of length {len(graph)}){RESET}")
                
                # Locate Product, Article, BreadcrumbList, FAQPage in graph
                product = None
                article_entity = None
                breadcrumb = None
                faq = None
                
                for entity in graph:
                    ent_type = entity.get("@type")
                    if ent_type == "Product":
                        product = entity
                    elif ent_type in ["Article", "NewsArticle"]:
                        article_entity = entity
                    elif ent_type == "BreadcrumbList":
                        breadcrumb = entity
                    elif ent_type == "FAQPage":
                        faq = entity
                
                # Verify Product
                if product:
                    print(f"   Product Schema: {GREEN}FOUND{RESET}")
                    # Stable @id IRI checks
                    prod_id = product.get("@id", "")
                    expected_id = f"{target_url}#product"
                    if prod_id == expected_id:
                        print(f"     └─ Stable @id IRI: {GREEN}PASS ({prod_id}){RESET}")
                    else:
                        print(f"     └─ Stable @id IRI: {RED}FAIL (Got '{prod_id}', expected '{expected_id}'){RESET}")
                    
                    # Freshness checks (dateModified)
                    date_modified = product.get("dateModified")
                    if date_modified:
                        print(f"     └─ Freshness Signal (dateModified): {GREEN}PASS ({date_modified}){RESET}")
                    else:
                        print(f"     └─ Freshness Signal (dateModified): {RED}FAIL (Missing dateModified field!){RESET}")
                        
                    # Offers checks
                    offers = product.get("offers", {})
                    offer_id = offers.get("@id", "")
                    expected_offer_id = f"{target_url}#offer"
                    if offer_id == expected_offer_id:
                        print(f"     └─ Stable Offer @id IRI: {GREEN}PASS ({offer_id}){RESET}")
                    else:
                        print(f"     └─ Stable Offer @id IRI: {RED}FAIL (Got '{offer_id}', expected '{expected_offer_id}'){RESET}")
                
                # Verify Article
                if article_entity:
                    print(f"   Article Schema ({article_entity.get('@type')}): {GREEN}FOUND{RESET}")
                    # Stable @id IRI checks
                    art_id = article_entity.get("@id", "")
                    expected_id = f"{target_url}#article"
                    if art_id == expected_id:
                        print(f"     └─ Stable @id IRI: {GREEN}PASS ({art_id}){RESET}")
                    else:
                        print(f"     └─ Stable @id IRI: {RED}FAIL (Got '{art_id}', expected '{expected_id}'){RESET}")
                    
                    # Freshness checks (dateModified)
                    date_modified = article_entity.get("dateModified")
                    if date_modified:
                        print(f"     └─ Freshness Signal (dateModified): {GREEN}PASS ({date_modified}){RESET}")
                    else:
                        print(f"     └─ Freshness Signal (dateModified): {RED}FAIL (Missing dateModified field!){RESET}")
                
                if not product and not article_entity:
                    print(f"   {RED}✗ Schema Error: Neither Product nor Article schema found in graph!{RESET}")
                
                # Verify BreadcrumbList
                if breadcrumb:
                    print(f"   BreadcrumbList Schema: {GREEN}FOUND{RESET}")
                    items = breadcrumb.get("itemListElement", [])
                    print(f"     └─ Items: {GREEN}PASS ({len(items)} levels found){RESET}")
                else:
                    print(f"   BreadcrumbList Schema: {RED}NOT FOUND in graph!{RESET}")
                    
                # Verify FAQPage
                if faq:
                    print(f"   FAQPage Schema: {GREEN}FOUND{RESET}")
                    main_entities = faq.get("mainEntity", [])
                    print(f"     └─ Questions: {GREEN}PASS ({len(main_entities)} questions found){RESET}")
                else:
                    print(f"   FAQPage Schema: {YELLOW}NOT FOUND (Optional, but recommended for SGE FAQ rich results){RESET}")
                
                 # Check 3: Verify Outbound link authority security flags
                outbound_links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>', html)
                external_links = [l for l in outbound_links if not l.startswith('/') and not l.startswith('#') and 'osmo.vn' not in l and not l.startswith(('tel:', 'mailto:', 'javascript:'))]
                
                print(f"   Outbound Authority Links: {len(external_links)} external links detected.")
                
                # Find all <a> tags with rel attribute
                a_tags = re.findall(r'<a[^>]+>', html)
                violations = 0
                for a in a_tags:
                    href_match = re.search(r'href="([^"]+)"', a)
                    if href_match:
                        href = href_match.group(1)
                        if not href.startswith('/') and not href.startswith('#') and 'osmo.vn' not in href and not href.startswith(('tel:', 'mailto:', 'javascript:')):
                            # External link: must have rel="nofollow noopener noreferrer"
                            rel_match = re.search(r'rel="([^"]+)"', a)
                            if rel_match:
                                rel = rel_match.group(1)
                                if "nofollow" in rel and "noopener" in rel and "noreferrer" in rel:
                                    # Safe
                                    pass
                                else:
                                    print(f"     {RED}✗ Vulnerability: External link to {href} has weak rel='{rel}'{RESET}")
                                    violations += 1
                            else:
                                print(f"     {RED}✗ Vulnerability: External link to {href} lacks rel attribute entirely!{RESET}")
                                violations += 1
                                
                if violations == 0:
                    print(f"     └─ Rel Authority Flags: {GREEN}PASS (All external links are protected){RESET}")
                else:
                    print(f"     └─ Rel Authority Flags: {RED}FAIL ({violations} unprotected links found!){RESET}")
                
        except Exception as e:
            print(f"   {RED}✗ HTTP/FETCH ERROR: {e}{RESET}")
        print()

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://osmo.vn/miccosmo-hurry-harry-premium-neck-cream-rich-40gr-kem-duong-sang-co"
    run_simulation(url)
