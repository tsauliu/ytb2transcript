import csv
import os
import logging
from datetime import datetime

HISTORY_CSV = 'download_history.csv'

def init_csv_file():
    """初始化CSV文件，如果不存在则创建"""
    if not os.path.exists(HISTORY_CSV):
        with open(HISTORY_CSV, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['url', 'filename', 'download_time'])
        logging.info(f"Created download history file: {HISTORY_CSV}")

def check_url_exists(url):
    """检查URL是否已经下载过"""
    if not os.path.exists(HISTORY_CSV):
        return False, None
    
    try:
        with open(HISTORY_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['url'] == url:
                    return True, row['filename']
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
    
    return False, None

def add_to_history(url, filename):
    """将下载记录添加到CSV文件"""
    try:
        with open(HISTORY_CSV, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([url, filename, datetime.now().isoformat()])
        logging.info(f"Added to history: {url} -> {filename}")
    except Exception as e:
        logging.error(f"Error writing to CSV file: {e}")

def get_video_title(url):
    """获取YouTube视频标题"""
    import subprocess
    try:
        title_command = f'yt-dlp --get-title "{url}"'
        result = subprocess.run(title_command, shell=True, capture_output=True, text=True, check=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        logging.warning(f"无法获取视频标题: {e}")
    return None 