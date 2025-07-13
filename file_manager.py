# file_manager.py
import os
import shutil
from config import Config
from user_manager import UserManager
from werkzeug.utils import secure_filename

user_manager = UserManager()

class FileManager:
    def __init__(self):
        self.allowed_extensions = Config.ALLOWED_EXTENSIONS
        self.max_size = Config.MAX_FILE_SIZE
        self.max_files = Config.MAX_FILES
        self.upload_dir = Config.UPLOAD_DIR
        self.data_dir = Config.DATA_DIR
        
        # 创建必要目录
        os.makedirs(self.upload_dir, exist_ok=True)
        for level in Config.ACCESS_LEVELS:
            os.makedirs(os.path.join(self.data_dir, level), exist_ok=True)
    
    def allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def save_uploaded_files(self, files, user):
        saved_files = []
        for file in files:
            if file and file.filename != '' and self.allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(self.upload_dir, filename)
                file.save(file_path)
                saved_files.append(file_path)
                
                # 限制上传文件数量
                if len(saved_files) >= self.max_files:
                    break
        return saved_files
    
    def move_to_permanent(self, file_path, access_level):
        """将文件移动到永久存储"""
        if not os.path.exists(file_path):
            return None
        
        filename = os.path.basename(file_path)
        target_dir = os.path.join(self.data_dir, access_level)
        os.makedirs(target_dir, exist_ok=True)  # 确保目录存在
        target_path = os.path.join(target_dir, filename)
        
        shutil.move(file_path, target_path)
        return target_path
    
    def get_accessible_files(self, user):
        """获取用户可以访问的所有文件路径"""
        accessible_files = []
        user_level = user.get_access_level()
        print(f"User {user.id} has access level: {user_level}")
        
        # 根据权限添加文件
        for level in Config.ACCESS_LEVELS:
            if user.has_access(level):
                level_dir = os.path.join(self.data_dir, level)
                print(f"Checking directory: {level_dir}")
                if os.path.exists(level_dir):
                    # 获取目录下所有文件
                    for root, _, files in os.walk(level_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if os.path.isfile(file_path):
                                accessible_files.append(file_path)
        
        print(f"User {user.id} ({user_level} access) can access {len(accessible_files)} files")
        return accessible_files