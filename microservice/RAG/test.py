import requests

# Flask 应用的 URL
url = 'http://127.0.0.1:7774/api/rag-query'

# 发送请求的数据
params = {'prompt': 'What wish did Leo make in the end, and why did he choose that particular wish?'}

# 发起 GET 请求
response = requests.get(url, params=params)

# 检查响应状态码
if response.status_code == 200:
    # 获取并打印 JSON 响应内容
    data = response.json()
    print(data)
else:
    print('Failed to retrieve data:', response.status_code)

