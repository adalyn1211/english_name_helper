from http.server import BaseHTTPRequestHandler
import json
import os
import requests

def process_name_response(content):
    """处理API返回的内容，提取名字和解释"""
    try:
        names = []
        current_name = {}
        
        # 分割成段落
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            # 如果是新的名字（通常以数字开头）
            if paragraph.strip().startswith(('1.', '2.', '3.')):
                if current_name:
                    names.append(current_name)
                current_name = {'name': '', 'explanation': ''}
                
                # 提取名字
                name_line = paragraph.split('\n')[0]
                name = name_line.split('.')[1].split('/')[0].strip()
                current_name['name'] = name
                
                # 收集解释
                explanation_parts = []
                for line in paragraph.split('\n')[1:]:
                    if line.strip() and not line.startswith('/'):
                        explanation_parts.append(line.strip())
                current_name['explanation'] = '\n'.join(explanation_parts)
        
        # 添加最后一个名字
        if current_name:
            names.append(current_name)
            
        return names
    except Exception as e:
        print(f"处理名字响应时出错: {str(e)}")
        return []

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        # 添加CORS头
        self.send_header('Access-Control-Allow-Origin', '*')
        
        try:
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
                        "content": """【英文起名专家指令】
作为一位专业的英文起名专家，你需要根据用户提供的中文名字推荐英文名。每个推荐的名字都应该与中文名的含义相呼应，展现出独特的个性和文化内涵。

【极其重要】
1. 每个名字的解释必须完全不同，禁止使用模板化的句式
2. 解释中要融入具体的历史典故、文化背景或真实人物故事
3. 每个名字都要像是由不同作者写的，给人完全不同的感受
4. 禁止使用"这个名字"、"这是"等开头的句式
5. 禁止提到"2024-2025年流行"、"现代人"等字眼
6. 每个解释都要体现出独特的写作风格和视角"""
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
            
            # 处理返回的内容
            names = process_name_response(content)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"names": names}).encode())
            
        except Exception as e:
            print(f"处理请求时出错: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
