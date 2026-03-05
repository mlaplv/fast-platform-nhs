import sys
import re

combined_lower = "tạo nhân viên mới tên là trần văn hải với email hotro@company.com"
extracted_entities = {}
verb = "create"

create_kw = ["thêm", "tạo", "them", "tao", "create", "mới", "moi"]
delete_kw = ["xóa", "xoa", "delete", "hủy", "huy"]
edit_kw = ["sửa", "sua", "edit", "update", "cập nhật", "cap nhat", "đổi", "doi"]

if any(kw in combined_lower for kw in delete_kw):
    verb = "delete"
elif any(kw in combined_lower for kw in edit_kw):
    verb = "edit"
else:
    verb = "create"

for marker in ["tên là ", "ten la ", "tên ", "ten "]:
    if marker in combined_lower:
        name_part = combined_lower.split(marker)[1].strip()
        for stop in ["email", "mật khẩu", "vai trò", "với"]:
            if stop in name_part:
                name_part = name_part.split(stop)[0].strip()
        extracted_entities["name"] = name_part.title()
        break

email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', combined_lower)
if email_match:
    extracted_entities["email"] = email_match.group(0)

print(f"VERB: {verb}")
print(f"ENTITIES: {extracted_entities}")
