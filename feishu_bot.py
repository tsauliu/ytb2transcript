from flask import Flask, request, jsonify
import requests
import subprocess
import os
import logging
import threading
from funcs import init_csv_file, check_url_exists, add_to_history, get_video_title
import shutil
# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# 飞书webhook URL
WEBHOOK_URL = "https://www.feishu.cn/flow/api/trigger-webhook/6d134f5e4041432074211abe7e4b467d"
DOWNLOADS_DIR = 'downloads'

def send_to_feishu(text):
    """发送消息到飞书"""
    payload = {"msg_type": "text", "content": text}
    try:
        requests.post(WEBHOOK_URL, json=payload)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message to Feishu: {e}")

def process_message_async(message):
    """异步处理消息的业务逻辑"""
    try:
        if 'youtube.com/' in message or 'youtu.be/' in message:
            # 检查是否已经下载过
            exists, existing_filename = check_url_exists(message)
            if exists:
                send_to_feishu(f"该链接已经下载过了！\n文件名：{existing_filename}\n请在服务器的 '{DOWNLOADS_DIR}' 文件夹中查看。")
                return
            
            # 获取视频标题
            video_title = get_video_title(message)
            filename = f"{video_title}.mp3" if video_title else "音频文件.mp3"
            
            send_to_feishu(f"检测到YouTube链接，开始下载: {video_title or message}")
            
            # 下载音频
            command = f'yt-dlp -o "{DOWNLOADS_DIR}/%(title)s.%(ext)s" --extract-audio --audio-format mp3 "{message}"'
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                add_to_history(message, filename)
                destpath = os.path.expanduser("~/Dropbox/MyServerFiles/VoiceMemos/Auto_Transcribe/YTBnotes/")
                shutil.copy2(f"{DOWNLOADS_DIR}/{filename}", destpath)
                send_to_feishu(f"成功下载音频文件：{filename}，请在服务器的 '{DOWNLOADS_DIR}' 文件夹中查看。")
                logging.info(f"Successfully downloaded: {filename}")
            else:
                send_to_feishu(f"下载失败: {message}\nError: {result.stderr}")
                logging.error(f"Download failed for {message}: {result.stderr}")
        else:
            # 普通消息直接发送到飞书
            send_to_feishu(message)
            logging.info(f"Sent regular message to Feishu: {message}")
    except Exception as e:
        logging.error(f"Error in async processing: {e}")
        send_to_feishu(f"处理消息时出现错误: {str(e)}")

@app.route('/download', methods=['POST'])
def download():
    """处理消息并立即返回响应，异步处理业务逻辑"""
    message = request.data.decode('utf-8') if request.data else ""
    if not message:
        return jsonify({"error": "no message"}), 400

    # 立即返回200 OK响应
    response = jsonify({"status": "received", "message": "Request received and processing"})
    
    # 启动异步线程处理业务逻辑
    thread = threading.Thread(target=process_message_async, args=(message,))
    thread.daemon = True  # 设置为守护线程
    thread.start()
    
    logging.info(f"Received message and started async processing: {message}")
    return response

if __name__ == '__main__':
    init_csv_file()
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    logging.info(f"Flask server starting on port 1234")
    app.run(host='0.0.0.0', port=1234)