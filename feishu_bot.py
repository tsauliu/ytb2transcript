from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# 飞书webhook URL
WEBHOOK_URL = "https://www.feishu.cn/flow/api/trigger-webhook/6d134f5e4041432074211abe7e4b467d"

def send_to_feishu(text):
    """发送消息到飞书"""
    payload = {"msg_type": "text", "content":text}
    requests.post(WEBHOOK_URL, json=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    """接收飞书消息"""
    data = request.get_json()
    
    # 提取消息文本
    user_text = ""
    if 'text' in data:
        user_text = data['text']
    elif 'content' in data:
        if isinstance(data['content'], dict):
            user_text = data['content'].get('text', '')
        else:
            user_text = str(data['content'])
    
    # 自动回复
    if user_text:
        reply = f"收到消息：{user_text}"
        send_to_feishu(reply)
    
    return jsonify({"status": "ok"})

@app.route('/send', methods=['POST'])
def send():
    """只保留原始文本"""
    print(f"请求方法: {request.method}")
    print(f"Content-Type: {request.content_type}")
    print(f"原始数据: {request.data}")

    message = ""
    if request.data:
        try:
            message = request.data.decode('utf-8')
            print(f"原始文本: {message}")
        except Exception as e:
            print(f"原始数据解析错误: {e}")
            return jsonify({"error": "decode error"}), 400

    if message:
        send_to_feishu(message)
        print(f"发送成功: {message}")
        return jsonify({"status": "sent"})

    print("没有找到有效消息")
    return jsonify({
        "error": "no message", 
        "help": "直接发送原始文本"
    }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1234) 