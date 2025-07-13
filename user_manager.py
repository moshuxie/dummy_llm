# user_manager.py
import json
import os
from datetime import datetime
from flask_login import UserMixin

USER_DATA_FILE = "users.json"
DEFAULT_USERS = {
    "no_user": {
        "password": "no_password",
        "access_level": "low",
        "created_at": "2023-01-01T00:00:00",
        "deleted_at": None
    },
    "moshu": {
        "password": "admin123",
        "access_level": "med",
        "created_at": "2023-01-01T00:00:00",
        "deleted_at": None
    },
    "root": {
        "password": "admin123",
        "access_level": "high",
        "created_at": "2023-01-01T00:00:00",
        "deleted_at": None
    }
}

class User(UserMixin):
    def __init__(self, user_id, data):
        self.id = user_id
        self.username = user_id
        self.password = data["password"]
        self.access_level = data["access_level"]
        self.created_at = data["created_at"]
        self.deleted_at = data["deleted_at"]

    def get_access_level(self):
        return self.access_level

    def has_access(self, required_level):
        levels = ["high", "med", "low"]
        return levels.index(self.access_level) <= levels.index(required_level)

class UserManager:
    def __init__(self):
        self.users = self._load_users()
    
    def _load_users(self):
        # 确保文件存在并包含默认用户
        if not os.path.exists(USER_DATA_FILE):
            self._create_default_users()
        
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    
    def _create_default_users(self):
        with open(USER_DATA_FILE, "w") as f:
            json.dump(DEFAULT_USERS, f, indent=2)
    
    def get_user(self, user_id):
        # 确保用户数据已加载
        if not hasattr(self, 'users'):
            self.users = self._load_users()
            
        user_data = self.users.get(user_id)
        if user_data and user_data.get("deleted_at") is None:
            return User(user_id, user_data)
        return None
    
    def verify_user(self, username, password):
        user = self.get_user(username)
        if user and user.password == password:
            return user
        return None
    
    def save_users(self):
        with open(USER_DATA_FILE, "w") as f:
            json.dump(self.users, f, indent=2)