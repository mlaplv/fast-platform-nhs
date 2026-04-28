import asyncio
import httpx
import os
import time
import json
import logging
from typing import List, Dict
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("neural-audit")

load_dotenv(".env")

# Override for Host Execution (Fast Platform Elite V2.2)
os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/0"
# Extracting DB user/pass from existing URL if possible, otherwise use defaults
os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "").replace("@db:", "@127.0.0.1:").replace("@db/", "@127.0.0.1/") or "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/fast_platform"

# Standard styling for Elite V2.2 Reports
HEADER = "\033[95m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
ENDC = "\033[0m"

async def audit_neural_stack():
    print(f"\n{HEADER}{BOLD}==== XOHI OS - NEURAL PERFORMANCE AUDIT (V2.2) ===={ENDC}")
    print(f"{BLUE}Giao thức: Kiểm tra Ma trận Năng lực Cần & Đủ{ENDC}\n")

    from backend.services.ai_service import ai_service
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    from backend.services.ai_engine.core.key_rotator import key_rotator
    
    # Ensure keys are loaded
    await key_rotator.load_keys()
    if not key_rotator.keys:
        print(f"{RED}[ERROR] Không tìm thấy API Key nào trong hệ thống!{ENDC}")
        return

    # 1. Discover Models
    print(f"{BOLD}[1/3] Đang quét danh sách Model từ Google API...{ENDC}")
    discovered = await trinity_bridge.models_helper.discover_available()
    print(f"{GREEN}→ Tìm thấy {len(discovered)} model hợp lệ.{ENDC}\n")

    # 2. Capability Stress Test
    print(f"{BOLD}[2/3] Đang tiến hành 'Thử Lửa' Ma Trận Năng Lực...{ENDC}")
    print(f"{'MODEL NAME':<35} | {'CAPABILITY':<10} | {'LATENCY':<8} | {'CONTEXT'}")
    print("-" * 75)

    results = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        for model in discovered[:12]: # Audit top 12 models
            try:
                key = await key_rotator.get_key(model_name=model)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                
                start_time = time.time()
                
                # Level 1 & 2 combined probe
                probe = {
                    "contents": [{"parts":[{"text": "What time is it? Use get_time tool."}]}],
                    "tools": [{"function_declarations": [{"name": "get_time", "description": "Get current time"}]}],
                    "tool_config": {"function_calling_config": {"mode": "ANY"}}
                }
                
                resp = await client.post(url, json=probe)
                latency = round(time.time() - start_time, 2)
                
                capability = f"{RED}UNSTABLE{ENDC}"
                if resp.status_code == 200:
                    capability = f"{YELLOW}LEGACY{ENDC}"
                    res_json = resp.json()
                    parts = res_json.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    if any("functionCall" in p for p in parts):
                        capability = f"{BLUE}AGENTIC{ENDC}"
                        
                        # Level 3: Structural
                        json_probe = {
                            "contents": [{"parts":[{"text": "Return JSON: {'status': 'ok'}"}]}],
                            "generationConfig": {"response_mime_type": "application/json"}
                        }
                        json_resp = await client.post(url, json=json_probe)
                        if json_resp.status_code == 200:
                            capability = f"{GREEN}ELITE{ENDC}"
                
                meta = await key_rotator.get_model_metadata(model)
                ctx = meta.get("inputTokenLimit", "N/A")
                
                print(f"{model:<35} | {capability:<19} | {latency:<8} | {ctx}")
                results.append({"model": model, "cap": capability, "latency": latency})
                
                await asyncio.sleep(0.3)
            except Exception as e:
                print(f"{model:<35} | {RED}FAILED{ENDC} | Error: {str(e)[:30]}")

    # 3. Final Selection Report
    print(f"\n{BOLD}[3/3] Đề xuất Cấu hình Tối ưu cho Dự án:{ENDC}")
    
    # We trigger the official optimizer to sync Redis/DB
    # Note: we need a mock db_session for this, or just rely on our local results
    print(f"\n{BLUE}--- KẾT QUẢ PHÂN TÍCH (BRAIN WATERFALL) ---{ENDC}")
    elites = [r["model"] for r in results if "ELITE" in r["cap"]]
    agentics = [r["model"] for r in results if "AGENTIC" in r["cap"]]
    
    final_waterfall = (elites + agentics)[:5]
    for i, m in enumerate(final_waterfall):
        print(f"{BOLD}Rank {i+1}:{ENDC} {GREEN}{m}{ENDC}")

    print(f"\n{YELLOW}[!] Lưu ý: Các model không có tên trong bảng trên đã bị loại bỏ thông minh do không đạt chuẩn Agentic.{ENDC}")
    print(f"{HEADER}===================================================={ENDC}\n")

if __name__ == "__main__":
    asyncio.run(audit_neural_stack())
