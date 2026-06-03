import os
import sys

# Whitelist/rules for directory walk to keep it clean and curated.
# We will show the main directories and their files, but for some deep or large directories, we'll only show the dir name or limited items.

EXCLUDE_DIRS = {
    '.git', '.github', '.vscode', '.agents', '.claude', 'node_modules',
    'venv', '.venv', '__pycache__', '.svelte-kit', 'bulk_fix', 'certs',
    'scratch', 'temp_venv', 'temp_restore', 'dist', 'build', '.pytest_cache'
}

ANNOTATIONS = {
    'backend/controllers/client': '[ELITE: CONTROLLERS DÀNH RIÊNG CHO CLIENT]',
    'backend/controllers/client/checkout.py': '[NOTE: TẠO ĐƠN HÀNG, KHÔNG SỬA ĐƠN]',
    'backend/controllers/client/support.py': '[NOTE: KÊNH LIÊN LẠC HỖ TRỢ CỦA KHÁCH HÀNG]',
    'backend/controllers/client/seo.py': '[NOTE: TỐI ƯU HÓA TÌM KIẾM CHO CÁC TRANG CÔNG KHAI]',
    'backend/controllers/client/ctv.py': '[NOTE: NGHIỆP VỤ CỘNG TÁC VIÊN & AFFILIATE]',
    'backend/services/commerce': '[ELITE: DOMAIN ENGINE NGHIỆP VỤ BÁN HÀNG CỦA HỆ THỐNG]',
    'backend/services/commerce/logic': '[NOTE: CÁC SERVICE XỬ LÝ LOGIC ĐẶC THÙ (PRICING, FOMO, SHIELD)]',
    'backend/services/commerce/operatives': '[NOTE: PIPELINE CHUYÊN GIA HỖ TRỢ & AI AGENT (HELEN)]',
    'backend/services/commerce/operatives/support_agent.py': '[NOTE: CORE AI SUPPORT AGENT - HELEN]',
    'backend/services/core': '[ELITE: DỊCH VỤ HỆ THỐNG (AI, AUTH, MEMORY, EVENTBUS)]',
    'backend/services/ads_protection': '[ELITE: HỆ THỐNG PHÒNG THỦ & PHÁT HIỆN GIAN LẬN CLICK ADS]',
    'backend/schemas/client': '[ELITE: SCHEMAS DỮ LIỆU ĐẦU RA/VÀO CHO CLIENT]',
    'frontend/src/lib/components/client': '[ELITE: CÁC COMPONENT GIAO DIỆN TRỰC QUAN CHO SHOP]',
    'frontend/src/lib/components/storefront': '[ELITE: GIAO DIỆN CHÍNH CỦA CỬA HÀNG STOREFRONT]',
    'frontend/src/lib/state/commerce': '[ELITE: STATE STORE (NANOBOT) CHO THƯƠNG MẠI (SHOP, CART)]',
    'frontend/src/lib/state/commerce/shop.svelte.ts': '[NOTE: KHỞI TẠO STATE CHÍNH CỦA CỬA HÀNG]',
    'frontend/src/lib/state/commerce/cart.svelte.ts': '[NOTE: QUẢN LÝ GIỎ HÀNG CỦA KHÁCH HÀNG]',
    'frontend/src/routes/(client)': '[ELITE: ROUTE GROUP CHO SMART_SHOP.TEST (PUBLIC)]',
    'frontend/src/routes/(client)/+layout.svelte': '[NOTE: LAYOUT RIÊNG KHÔNG CHỨA ADMIN UI]',
    'frontend/src/routes/(client)/+layout.ts': '[NOTE: CONFIG CSR/SSR CHO CLIENT]',
}

# Directories where we don't want to list files, just directories
COLLAPSED_DIRS = {
    'backend/migrations/versions': '... [MIGRATION FILES]',
    'backend/static/vad': '... [VAD MODELS & BUNDLES]',
    'backend/static/wasm': '... [ONNX RUNTIME WASM BINARIES]',
    'frontend/dist': '... [COMPILED ASSETS]',
    'backend/tests': '... [TEST CASES & INTEGRATION TESTS]',
    'backend/scripts': '... [UTILITY SCRIPTS]',
    'backend/services/xohi/creative_studio': '... [CREATIVE STUDIO GENERATORS & ANALYSTS]',
    'backend/services/xohi/prompts': '... [PROMPTS DATA]',
    'frontend/src/lib/components/admin': '... [ADMIN DASHBOARD COMPONENTS]',
    'frontend/src/lib/components/media': '... [MEDIA GALLERY COMPONENTS]',
    'frontend/src/lib/components/ui': '... [BASE UI COMPONENTS]',
    'frontend/src/lib/components/widgets': '... [WIDGET COMPONENTS]',
    'frontend/src/lib/components/vui': '... [VOICE UI COMPONENTS]',
    'frontend/src/lib/components/xohi': '... [XOHI SPECIALIZED COMPONENTS]',
    'frontend/src/lib/components/client': '... [CLIENT INTERFACES]',
    'frontend/src/lib/components/storefront': '... [STOREFRONT BUYING FLOW INTERFACES]',
    'frontend/src/lib/state/admin': '... [ADMIN MANAGEMENT STORES]',
    'frontend/src/lib/state/intent': '... [AI INTENT STORES]',
    'frontend/src/lib/state/nanobot': '... [NANOBOT CORE SYSTEM STORES]',
    'frontend/src/lib/state/seo': '... [SEO AND ANALYTICS STORES]',
    'frontend/src/lib/types': '... [TYPES DEFINITIONS]',
    'frontend/src/lib/utils': '... [UTILITIES & HELPERS]',
    'frontend/src/lib/styles': '... [STYLES & CSS]',
    'frontend/src/lib/assets': '... [STATIC ASSETS]',
    'frontend/src/lib/vui': '... [VOICE LIBRARIES]',
    'frontend/src/routes/(admin)': '... [ADMIN PRIVATE PAGES & ROUTES]',
    'frontend/src/routes/auth': '... [AUTHENTICATION SYSTEM ROUTES]',
    'frontend/static': '... [STATIC IMAGES, FONTS, UPLOADS & ASSETS]',
}

HIGHLIGHTED_SUBSTRINGS = {
    'client', '(client)', 'shop', 'commerce'
}

def should_highlight(rel_path):
    p = rel_path.lower()
    return any(sub in p for sub in HIGHLIGHTED_SUBSTRINGS)

def get_annotation(rel_path):
    norm_path = rel_path.replace('\\', '/').rstrip('/')
    return ANNOTATIONS.get(norm_path)

def walk_tree(path, rel_path='', indent=''):
    try:
        entries = os.listdir(path)
    except PermissionError:
        return []

    # Filter out excluded dirs/files
    filtered_entries = []
    for entry in entries:
        if entry in EXCLUDE_DIRS:
            continue
        filtered_entries.append(entry)

    # Sort entries: directories first, then files
    dirs = []
    files = []
    for entry in filtered_entries:
        full_p = os.path.join(path, entry)
        if os.path.isdir(full_p):
            dirs.append(entry)
        else:
            files.append(entry)
    dirs.sort()
    files.sort()
    entries_sorted = dirs + files

    lines = []
    for i, entry in enumerate(entries_sorted):
        is_last = (i == len(entries_sorted) - 1)
        full_p = os.path.join(path, entry)
        entry_rel = os.path.join(rel_path, entry).replace('\\', '/')
        
        connector = '`-- ' if is_last else '|-- '
        display_name = entry + ('/' if os.path.isdir(full_p) else '')
        
        # Determine highlighting
        line_highlight = should_highlight(entry_rel)
        prefix = '-   ' if line_highlight else '    '
        
        # Build base line
        base_line = f"{indent}{connector}{display_name}"
        
        # Add annotation if exists
        annotation = get_annotation(entry_rel)
        if annotation:
            # Pad to align comments
            padded_line = base_line.ljust(35)
            line_str = f"{prefix}{padded_line} <-- {annotation}"
        else:
            line_str = f"{prefix}{base_line}"
            
        lines.append(line_str)
        
        # Recurse if directory and not collapsed
        if os.path.isdir(full_p):
            if entry_rel in COLLAPSED_DIRS:
                sub_prefix = '-   ' if line_highlight else '    '
                sub_indent = indent + ('    ' if is_last else '|   ')
                lines.append(f"{sub_prefix}{sub_indent}`-- {COLLAPSED_DIRS[entry_rel]}")
            else:
                next_indent = indent + ('    ' if is_last else '|   ')
                lines.extend(walk_tree(full_p, entry_rel, next_indent))
                
    return lines

if __name__ == '__main__':
    tree_lines = walk_tree('.')
    print('.')
    for line in tree_lines:
        print(line)
