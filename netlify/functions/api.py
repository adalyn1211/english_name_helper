from http.server import BaseHTTPRequestHandler
import json
import os
import requests

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        chinese_name = data.get('chinese_name', '').strip()
        gender = data.get('gender', 'male')
        
        if not chinese_name:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "请输入中文名字"}).encode())
            return
            
        try:
            url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get('API_KEY')}"
            }
            
            gender_text = "男性" if gender == "male" else "女性"
            
            data = {
                "model": "ep-20250313233912-4c45k",
                "messages": [
                    {
                        "role": "system",
                        "content": """【英文起名专家指令】..."""  # 这里是您原来的system prompt
                    },
                    {
                        "role": "user",
                        "content": f"""请为这个中文名字推荐英文名字：
姓名：{chinese_name}
性别：{gender_text}

要求：
1. 必须推荐3个名字
2. 每个名字都必须包含：
   - 英文名字
   - 准确的国际音标
   - 发音指导（在50个字符内说明轻重音怎么读）
   - 名字的寓意解释（控制在150-200字之间，分2段呈现，两段间有换行。第1段前面不要有空格，包含名字的典故或故事以及代表的意思，第2段与用户的中文名字寓意相呼应）"""
                    }
                ],
                "temperature": 1.0,
                "max_tokens": 4000,
                "top_p": 0.9,
                "frequency_penalty": 1.2,
                "presence_penalty": 1.0
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                raise Exception(f"API请求失败（状态码：{response.status_code}）")
                
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"suggestions": content}).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
