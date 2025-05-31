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

@app.route('/download', methods=['POST'])
def download():
    """处理消息并下载YouTube音频"""
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
        # 检查是否为YouTube链接
        if 'youtube.com/' in message or 'youtu.be/' in message:
            # 先获取视频标题
            try:
                title_command = f'yt-dlp --get-title "{message}"'
                title_result = subprocess.run(title_command, shell=True, capture_output=True, text=True, check=False)
                if title_result.returncode == 0 and title_result.stdout.strip():
                    video_title = title_result.stdout.strip()
                    filename = f"{video_title}.mp3"
                    send_to_feishu(f"检测到YouTube链接，开始下载: {video_title}")
                else:
                    filename = "音频文件.mp3"
                    send_to_feishu(f"检测到YouTube链接，开始下载: {message}")
            except Exception as e:
                logging.warning(f"无法获取视频标题: {e}")
                filename = "音频文件.mp3"
                send_to_feishu(f"检测到YouTube链接，开始下载: {message}")
            
            command = f'yt-dlp -o "{DOWNLOADS_DIR}/%(title)s.%(ext)s" --extract-audio --audio-format mp3 "{message}"'
            try:
                logging.info(f"Attempting to download audio from: {message}")
                result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    logging.info(f"Successfully downloaded audio for: {message}")
                    send_to_feishu(f"成功下载音频文件：{filename}，请在服务器的 '{DOWNLOADS_DIR}' 文件夹中查看。")
                    return jsonify({"status": "downloaded"})
                else:
                    logging.error(f"yt-dlp failed for {message}. Stderr: {result.stderr}")
                    send_to_feishu(f"下载失败: {message}\nError: {result.stderr}")
                    return jsonify({"error": "download failed", "details": result.stderr}), 500
            except Exception as e:
                logging.error(f"An error occurred while processing YouTube URL {message}: {e}")
                send_to_feishu(f"处理YouTube链接时发生内部错误: {message}")
                return jsonify({"error": "processing error", "details": str(e)}), 500
        else:
            # 普通消息直接发送到飞书
            send_to_feishu(message)
            logging.info(f"Message sent successfully: {message}")
            return jsonify({"status": "sent"})

    logging.info("No valid message found")
    return jsonify({
        "error": "no message",
        "help": "直接发送原始文本或YouTube链接"
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