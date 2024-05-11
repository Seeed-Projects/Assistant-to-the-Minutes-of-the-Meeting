import requests

# Flask 服务器的 URL
url = 'http://127.0.0.1:7771//api/get-text'

# 发送 GET 请求
response = requests.get(url)

# 检查响应状态码
if response.status_code == 200:
    # 获取并打印 JSON 响应内容
    data = response.json()
    print(data)
else:
    print('Failed to retrieve data:', response.status_code)
