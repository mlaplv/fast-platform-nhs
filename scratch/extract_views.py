import json

log_path = '/home/lv/.gemini/antigravity/brain/8394de1e-58f3-44cf-aa79-3daa17ae0c3c/.system_generated/logs/overview.txt'

with open(log_path, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        if 'AdsCampaignManager.svelte' in line:
            try:
                data = json.loads(line)
                step = data.get('step_index', '?')
                type_ = data.get('type', '?')
                created = data.get('created_at', '?')
                content = data.get('content', '')
                print(f"Line {line_num} | Step {step} | Type {type_} | Created {created}")
                if content:
                    # Print first 200 chars of content
                    print(f"  Content: {content[:300]}...")
                if 'tool_calls' in data:
                    print(f"  Tool calls: {data['tool_calls']}")
            except Exception as e:
                print(f"Line {line_num} parse error: {e}")
