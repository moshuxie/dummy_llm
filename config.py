# config.py
import os
from pathlib import Path

class Config:
    # Ollama 配置
    OLLAMA_MODEL = "llama3"  # 本地运行的模型
    OLLAMA_BASE_URL = "http://localhost:11434"
    
    # DeepSeek API 配置
    DEEPSEEK_API_KEY = ""  # 可以留空，不使用DeepSeek
    
    # 文件设置
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc', 'json', 'csv', 'xlsx', 'xls', 'md'}
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
    MAX_FILES = 2
    
    # 路径设置
    DATA_DIR = "data"
    UPLOAD_DIR = "temp_uploads"
    
    # 安全设置
    SECRET_KEY = "supersecretkey"
    
    # 权限等级
    ACCESS_LEVELS = ["high", "med", "low"]
    
    # RAG 设置
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # ChromaDB 外部存储路径 (用户主目录下的 .chroma_db)
    CHROMA_DB_DIR = str(Path.home() / ".chroma_db")
 
    
    # 确保 ChromaDB 目录存在
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)