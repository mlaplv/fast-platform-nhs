import datetime

task_entry = """
## [2026-06-03] Task: Optimize Telegram Notifications
- [x] Fetch `site_name` from Redis `system:settings:primary_config`.
- [x] Clean up `telegram_msg` format in `handle_system_signal` to remove messy horizontal lines and timestamps.
- [ ] Present PROPOSE plan to Sếp and wait for HALT/Duyệt.
- [ ] Sync changes to production VPS via rsync.
- [ ] Restart backend service on VPS.
"""

walkthrough_entry = """
### [2026-06-03] Walkthrough: Telegram Notification Format Optimization
**Context:** Sếp reported that the Telegram message notifications were messy (contained long separator lines and raw timestamps) and the title was hardcoded as "FAST-PLATFORM ALERTS". Sếp requested to use the site name from settings and concise the message.
**Implementation:**
- Edited `backend/services/xohi_responder.py` -> `handle_system_signal`.
- Implemented a Redis fetch for `system:settings:primary_config` to dynamically retrieve `basic_info.site_name`.
- Formatted the HTML message to remove `───────────────` and the timestamp, resulting in a cleaner UI: `🚨 <b>[{site_name} - {alert_type}]</b>\n{msg}`.
"""

with open("/home/lv/Desktop/fast-platform-core/task.md", "a", encoding="utf-8") as f:
    f.write(task_entry)

with open("/home/lv/Desktop/fast-platform-core/walkthrough.md", "a", encoding="utf-8") as f:
    f.write(walkthrough_entry)

print("Appended to task.md and walkthrough.md")
