from flask import Flask, request, jsonify
import requests
import json
import subprocess
import os
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# 飞书webhook URL
WEBHOOK_URL = "https://www.feishu.cn/flow/api/trigger-webhook/6d134f5e4041432074211abe7e4b467d"
DOWNLOADS_DIR = 'downloads'

def send_to_feishu(text):
    """发送消息到飞书"""
    payload = {"msg_type": "text", "content":text}
    try:
        requests.post(WEBHOOK_URL, json=payload)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message to Feishu: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    """接收飞书消息"""
    try:
        data = request.get_json()
    except Exception as e:
        logging.error(f"Failed to parse JSON from request: {e}")
        return jsonify({"error": "Invalid JSON"}), 400
    
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
        if 'youtube.com/' in user_text or 'youtu.be/' in user_text:
            send_to_feishu(f"检测到YouTube链接，开始下载: {user_text}")
            command = f'yt-dlp -o "{DOWNLOADS_DIR}/%(title)s.%(ext)s" --extract-audio --audio-format mp3 "{user_text}"'
            try:
                logging.info(f"Attempting to download audio from: {user_text}")
                result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    logging.info(f"Successfully downloaded audio for: {user_text}")
                    # We need a robust way to get the filename. For now, send generic success.
                    send_to_feishu(f"成功下载音频，请在服务器的 '{DOWNLOADS_DIR}' 文件夹中查看。")
                else:
                    logging.error(f"yt-dlp failed for {user_text}. Stderr: {result.stderr}")
                    send_to_feishu(f"下载失败: {user_text}\nError: {result.stderr}")
            except Exception as e:
                logging.error(f"An error occurred while processing YouTube URL {user_text}: {e}")
                send_to_feishu(f"处理YouTube链接时发生内部错误: {user_text}")
        else:
            reply = f"收到消息：{user_text}"
            send_to_feishu(reply)
    
    return jsonify({"status": "ok"})

@app.route('/send', methods=['POST'])
def send():
    """只保留原始文本"""
    logging.info(f"Request method: {request.method}")
    logging.info(f"Content-Type: {request.content_type}")
    logging.info(f"Raw data: {request.data}")

    message = ""
    if request.data:
        try:
            message = request.data.decode('utf-8')
            logging.info(f"Decoded message: {message}")
        except Exception as e:
            logging.error(f"Error decoding raw data: {e}")
            return jsonify({"error": "decode error"}), 400

    if message:
        send_to_feishu(message)
        logging.info(f"Message sent successfully: {message}")
        return jsonify({"status": "sent"})

    logging.info("No valid message found")
    return jsonify({
        "error": "no message",
        "help": "直接发送原始文本"
    }), 400

if __name__ == '__main__':
    try:
        if not os.path.exists(DOWNLOADS_DIR):
            os.makedirs(DOWNLOADS_DIR)
            logging.info(f"Downloads directory '{DOWNLOADS_DIR}' created.")
        else:
            logging.info(f"Downloads directory '{DOWNLOADS_DIR}' already exists.")
        logging.info(f"Downloads directory '{DOWNLOADS_DIR}' ensured.")
    except Exception as e:
        logging.error(f"Error creating downloads directory '{DOWNLOADS_DIR}': {e}")
        # Depending on the application's needs, you might want to exit here
        # For now, just log and continue

    logging.info(f"Flask server starting on port 1234")
    app.run(host='0.0.0.0', port=1234)