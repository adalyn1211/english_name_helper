from flask import Flask, request, jsonify, render_template
import requests
import json
import re

app = Flask(__name__)

def call_api(chinese_name, gender="male"):
    """调用API获取英文名字推荐"""
    print(f"\n=== 开始生成名字 ===")
    print(f"用户输入的名字: {chinese_name}")
    print(f"用户选择的性别: {gender}")
    
    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 42474320-8359-4ece-be43-271f42035574"
    }
    
    gender_text = "男性" if gender == "male" else "女性"
    
    data = {
        "model": "ep-20250313233912-4c45k",
        "messages": [
            {
                "role": "system",
                "content": """【英文起名专家指令】
你是一位拥有30年经验的专业英文起名专家，精通中西方文化和语言学。请为用户推荐最适合的英文名字。

【极其重要】
1. 输出格式要求：
   每个名字必须严格按以下格式输出：
   
   - 英文名字
   [音标] /具体音标/
   [发音指导] 重点介绍轻重音的读音（在50字符内完成发音指导），例如："第三个音节重读，'Se'读作'赛'，'ra'读作'拉'，'phi'读作'菲'，'na'读作'娜'"
   名字的寓意解释（150-200字，分2段呈现，两段间有换行。第1段前面不要有空格，包含名字的典故或故事以及代表的意思，第2段与用户的中文名字寓意相呼应）
   
   示例：
   - Seraphina
   [音标] /ˌserəˈfiːnə/
   [发音指导] 第三个音节重读，'Se'读作'赛'，'ra'读作'拉'，'phi'读作'菲'，'na'读作'娜'
   这个优雅的名字源自希伯来语，在犹太教和基督教传统中代表"炽天使"，是最高级别的天使之一。在中世纪的传说中，炽天使以六翼环绕，永远守护在上帝身边。这个名字在文学作品中常被用来代表高贵优雅的女性角色，如《龙骑士》小说中的龙族公主Seraphina，她以智慧和勇气闻名。

   这个名字完美呼应名字中温婉贤淑的气质，寓意着神圣的智慧与纯洁的光芒。

2. 名字推荐要求：
   - 必须推荐3个名字
   - 每个名字必须包含准确的国际音标
   - 发音指导必须在50字符内完成，重点完成轻重音的指导
   - 名字寓意解释必须用中文介绍，控制在150-200字之间，分2段呈现，两段间有换行。第1段前面不要有空格，包含名字的典故或故事以及代表的意思，第2段与用户的中文名字寓意相呼应

3. 内容限制：
   - 只使用ASCII字符
   - 每个解释控制在150-200字之间
   - 分段呈现，两段间有换行，第1段前面不要有空格"""
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
   - 名字的寓意解释（控制在150-200字之间，分2段呈现，两段间有换行。第1段前面不要有空格，包含名字的典故或故事以及代表的意思，第2段与用户的中文名字寓意相呼应）

请严格按照系统提示中的格式输出，确保每个名字都有完整的音标、发音指导和详细解释。"""
            }
        ],
        "temperature": 1.0,
        "max_tokens": 4000,
        "top_p": 0.9,
        "frequency_penalty": 1.2,
        "presence_penalty": 1.0
    }
    
    print("=== 发送API请求 ===")
    print("请求数据:", json.dumps(data, ensure_ascii=False, indent=2))
    
    response = requests.post(url, headers=headers, json=data)
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code != 200:
        error_msg = f"API请求失败（状态码：{response.status_code}）"
        print(f"错误: {error_msg}")
        raise Exception(error_msg)
    
    # 获取原始响应文本
    raw_text = response.text
    print("\n=== 原始响应文本 ===")
    print(raw_text)
    
    try:
        result = response.json()
        print("\n=== 解析后的JSON ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if "choices" not in result or not result["choices"]:
            error_msg = "API返回数据格式错误"
            print(f"错误: {error_msg}")
            raise Exception(error_msg)
        
        content = result["choices"][0]["message"]["content"]
        print("\n=== API返回的原始内容 ===")
        print(content)
        
        # 直接返回内容，不进行任何编码/解码处理
        return {"suggestions": content}
        
    except json.JSONDecodeError as e:
        print(f"\n=== JSON解析错误 ===")
        print(f"错误信息: {str(e)}")
        print(f"错误位置: 第{e.lineno}行，第{e.colno}列")
        print(f"错误行内容: {e.doc.splitlines()[e.lineno-1] if e.doc else 'Unknown'}")
        raise Exception("API返回的JSON格式无效")
        
    except Exception as e:
        print(f"\n=== 其他错误 ===")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/suggest_names', methods=['POST'])
def suggest_names():
    try:
        data = request.get_json()
        chinese_name = data.get('chinese_name', '').strip()
        gender = data.get('gender', 'male')
        
        if not chinese_name:
            return jsonify({"error": "请输入中文名字"}), 400
        
        result = call_api(chinese_name, gender)
        return jsonify(result)
    except Exception as e:
        error_msg = str(e)
        print(f"错误：{error_msg}")
        return jsonify({"error": error_msg}), 500

if __name__ == '__main__':
    # 尝试不同的端口
    ports = [5002, 5003, 5004, 5005]
    
    for port in ports:
        try:
            print(f"\n正在尝试启动服务器，端口：{port}")
            app.run(debug=True, port=port)
            break
        except OSError as e:
            print(f"端口 {port} 已被占用，尝试下一个端口...")
            continue
