import requests

url = "http://localhost:8000/api/v1/intent"
data = {
    "transcript": "tạo sản phẩm mới",
    "timezone": "Asia/Ho_Chi_Minh"
}
headers = {"x-tenant": "admin", "Content-Type": "application/json"}
try:
    response = requests.post(url, json=data, headers=headers)
    print("STATUS:", response.status_code)
    print("JSON:", response.json())
except Exception as e:
    print("ERROR:", e)
