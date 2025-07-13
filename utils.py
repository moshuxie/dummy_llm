# utils.py
import os
from datetime import datetime
from config import Config

def clean_temp_uploads():
    """清理临时上传目录"""
    for filename in os.listdir(Config.UPLOAD_DIR):
        file_path = os.path.join(Config.UPLOAD_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"删除临时文件失败 {file_path}: {e}")

def get_timestamp():
    """获取当前时间戳"""
    return datetime.now().strftime("%Y%m%d%H%M%S")

def format_file_size(size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"