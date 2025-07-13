# app.py
import traceback
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from user_manager import UserManager, User
from file_manager import FileManager
from rag_system import RAGSystem
from utils import clean_temp_uploads
from config import Config
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = Config.SECRET_KEY

# 初始化组件
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

user_manager = UserManager()
file_manager = FileManager()
rag_system = RAGSystem()

@login_manager.user_loader
def load_user(user_id):
    return user_manager.get_user(user_id)

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(f"Login attempt: username={username}, password={password}")
        
        user = user_manager.verify_user(username, password)
        if user:
            print(f"User authenticated: {username}")
            login_user(user)
            # 更新知识库
            rag_system.update_knowledge_base(user)
            return redirect(url_for('chat'))
        else:
            print(f"Authentication failed: {username}")
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    # 清理临时上传目录
    clean_temp_uploads()
    
    if request.method == 'POST':
        try:
            query = request.form['query']
            use_deepseek = 'use_deepseek' in request.form
            
            # 获取对话历史
            history = session.get('chat_history', [])
            
            # 确保知识库是最新的
            rag_system.update_knowledge_base(current_user)
            
            # 获取AI回复和响应时间
            response, response_time = rag_system.query(query, current_user, history, use_deepseek)
            
            # 更新对话历史
            history.append((query, response))
            session['chat_history'] = history[-10:]  # 保留最近10条
            
            return jsonify({
                'response': response,
                'response_time': response_time
            })
        except Exception as e:
            # 打印详细错误信息
            traceback.print_exc()
            return jsonify({
                'response': f"An error occurred: {str(e)}",
                'response_time': "0.00 seconds"
            }), 500
    
    return render_template('chat.html', 
                           username=current_user.id,
                           access_level=current_user.access_level)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('files')
        access_level = request.form['access_level']
        
        # 验证权限
        if not current_user.has_access(access_level):
            flash('You do not have permission for this access level', 'danger')
            return redirect(url_for('upload_file'))
        
        saved_files = file_manager.save_uploaded_files(files, current_user)
        
        # 移动到永久存储
        uploaded_files = []
        for file_path in saved_files:
            perm_path = file_manager.move_to_permanent(file_path, access_level)
            if perm_path:
                uploaded_files.append(os.path.basename(perm_path))
                flash(f'File uploaded successfully: {os.path.basename(perm_path)}', 'success')
        
        # 更新知识库
        if uploaded_files:
            rag_system.update_knowledge_base(current_user)
        
        return redirect(url_for('chat'))
    
    # 传递配置变量到模板
    return render_template('upload.html', 
                           access_levels=Config.ACCESS_LEVELS,
                           current_level=current_user.access_level,
                           max_file_size=Config.MAX_FILE_SIZE,
                           max_files=Config.MAX_FILES,
                           allowed_extensions=Config.ALLOWED_EXTENSIONS)

if __name__ == '__main__':
    # 确保数据目录存在
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    for level in Config.ACCESS_LEVELS:
        os.makedirs(os.path.join(Config.DATA_DIR, level), exist_ok=True)
    
    # 确保用户文件存在
    user_manager._create_default_users()
    
    # 确保 ChromaDB 目录存在
    os.makedirs(Config.CHROMA_DB_DIR, exist_ok=True)
    
    app.run(host='0.0.0.0', port=5001, debug=True)