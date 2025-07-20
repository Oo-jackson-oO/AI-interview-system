from flask import Flask, render_template, request, jsonify, send_file, Response, stream_template, redirect, url_for, session
import os
import sys
import json
import base64
from datetime import datetime
from werkzeug.utils import secure_filename
import io
from functools import wraps

# 添加模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入各个模块
from modules.resume_parsing import ResumeParser
from modules.skill_training import SkillManager
from modules.learning_path import LearningPlanner
from modules.user_management import UserManager

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = 'your-secret-key-here'  # 用于session加密

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查session中是否有用户信息
        if 'user' not in session:
            # 如果没有登录，重定向到登录页面并传递当前URL
            current_url = request.url
            return redirect(url_for('auth_page', redirect=current_url))
        return f(*args, **kwargs)
    return decorated_function

# 初始化各个模块
resume_parser = ResumeParser()
skill_manager = SkillManager()
learning_planner = LearningPlanner()
user_manager = UserManager()

# 文件上传配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_resume_to_file(username, text, original_filename):
    """保存简历文本到文件"""
    try:
        # 创建uploads文件夹（如果不存在）
        uploads_folder = 'uploads'
        if not os.path.exists(uploads_folder):
            os.makedirs(uploads_folder)
        
        # 创建用户文件夹
        safe_username = "".join(c for c in username if c.isalnum() or c in ('-', '_')).rstrip()
        user_folder = os.path.join(uploads_folder, safe_username)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        
        # 计算文件夹内简历数量
        existing_files = [f for f in os.listdir(user_folder) if f.endswith('.txt')]
        resume_count = len(existing_files) + 1
        
        # 生成文件名：用户名_简历_(n).txt
        filename = f"{safe_username}_简历_{resume_count}.txt"
        filepath = os.path.join(user_folder, filename)
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"用户: {username}\n")
            f.write(f"原始文件名: {original_filename}\n")
            f.write(f"保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n")
            f.write("简历内容:\n")
            f.write("=" * 50 + "\n")
            f.write(text)
        
        print(f"简历已保存到: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"保存简历文件失败: {str(e)}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test/stream')
def test_stream():
    """测试流式输出"""
    def generate():
        for i in range(10):
            yield f"这是第 {i+1} 条测试消息\n"
            import time
            time.sleep(0.5)
    
    return Response(
        generate(),
        mimetype='text/plain; charset=utf-8',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )

# 用户认证相关路由
@app.route('/auth')
def auth_page():
    # 获取重定向参数
    redirect_url = request.args.get('redirect', '')
    return render_template('auth.html', redirect_url=redirect_url)

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': '请填写完整信息'})
        
        result = user_manager.register_user(username, password, email)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'})

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'message': '请填写完整信息'})
        
        result = user_manager.login_user(username, password)
        
        # 如果登录成功，设置session
        if result['success']:
            session['user'] = result['user']
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    try:
        # 清除session
        session.pop('user', None)
        return jsonify({'success': True, 'message': '登出成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'登出失败: {str(e)}'})

@app.route('/api/auth/user', methods=['GET'])
def get_current_user():
    try:
        # 从请求头或session中获取用户信息
        # 这里简化处理，实际应该从session或token中获取
        return jsonify({'success': True, 'user': None})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取用户信息失败: {str(e)}'})

@app.route('/api/profile/info', methods=['GET'])
def get_user_profile():
    """获取用户个人信息"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return jsonify({'error': '请先登录'}), 401
        
        profile = user_manager.get_user_profile(username)
        if not profile:
            return jsonify({'error': '用户不存在'}), 404
        
        return jsonify({
            'success': True,
            'profile': profile
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/update', methods=['POST'])
def update_user_profile():
    """更新用户个人信息"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return jsonify({'error': '请先登录'}), 401
        
        data = request.get_json()
        result = user_manager.update_user_profile(username, data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/resume/list', methods=['GET'])
def get_user_resumes():
    try:
        if 'user' not in session:
            return jsonify({'error': '请先登录'}), 401
        
        username = session['user']['username']
        resumes = user_manager.get_user_resumes(username)
        return jsonify({
            'success': True,
            'resumes': resumes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/resume/count', methods=['GET'])
def get_user_resume_count():
    """获取用户简历数量"""
    try:
        if 'user' not in session:
            return jsonify({'error': '请先登录'}), 401
        
        username = session['user']['username']
        resumes = user_manager.get_user_resumes(username)
        return jsonify({
            'success': True,
            'count': len(resumes)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/resume/<resume_id>', methods=['GET'])
def get_resume_detail(resume_id):
    try:
        if 'user' not in session:
            return jsonify({'error': '请先登录'}), 401
        
        username = session['user']['username']
        resume = user_manager.get_resume(username, resume_id)
        if not resume:
            return jsonify({'error': '简历不存在'}), 404
        
        return jsonify({
            'success': True,
            'resume': resume
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/resume/<resume_id>', methods=['DELETE'])
def delete_resume(resume_id):
    try:
        if 'user' not in session:
            return jsonify({'error': '请先登录'}), 401
        
        username = session['user']['username']
        result = user_manager.delete_resume(username, resume_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/resume/<resume_id>/file', methods=['GET'])
def get_resume_file(resume_id):
    """获取简历文件内容"""
    try:
        if 'user' not in session:
            return jsonify({'error': '请先登录'}), 401
        
        username = session['user']['username']
        resume = user_manager.get_resume(username, resume_id)
        if not resume:
            return jsonify({'error': '简历不存在'}), 404
        
        file_path = resume.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': '简历文件不存在'}), 404
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'content': content,
            'filename': resume.get('filename', 'unknown')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/resume/<resume_id>/download', methods=['GET'])
def download_resume_file(resume_id):
    """下载简历文件"""
    try:
        if 'user' not in session:
            return jsonify({'error': '请先登录'}), 401
        
        username = session['user']['username']
        resume = user_manager.get_resume(username, resume_id)
        if not resume:
            return jsonify({'error': '简历不存在'}), 404
        
        file_path = resume.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': '简历文件不存在'}), 404
        
        # 返回文件下载
        return send_file(
            file_path,
            as_attachment=True,
            download_name=resume.get('filename', 'resume.txt')
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 简历解析相关路由
@app.route('/resume')
@login_required
def resume_page():
    return render_template('resume.html')

@app.route('/my-resumes')
@login_required
def my_resumes_page():
    return render_template('my_resumes.html')

@app.route('/profile')
@login_required
def profile_page():
    return render_template('profile.html')

@app.route('/api/resume/analyze', methods=['POST'])
def analyze_resume():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式'}), 400
        
        # 获取用户信息（从session）
        if 'user' not in session:
            return jsonify({'error': '请先登录'}), 401
        
        username = session['user']['username']
        
        # 提取文本
        text = resume_parser.extract_text_from_file(file)
        
        # 保存简历文本到文件
        filepath = save_resume_to_file(username, text, file.filename)
        if not filepath:
            return jsonify({'error': '保存文件失败'}), 500
        
        # 保存简历信息到用户数据
        filename = file.filename or 'unknown'
        resume_data = {
            'filename': filename,
            'text': text,
            'file_path': filepath,
            'file_size': len(file.read()),
            'file_type': filename.split('.')[-1].lower() if '.' in filename else 'unknown',
            'upload_time': datetime.now().isoformat()
        }
        file.seek(0)  # 重置文件指针
        
        # 保存到用户数据
        save_result = user_manager.add_resume(username, resume_data)
        if not save_result['success']:
            return jsonify({'error': save_result['message']}), 500
        
        # 返回流式响应
        return Response(
            resume_parser.analyze_resume_stream(text),
            mimetype='text/plain; charset=utf-8',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/resume/chat', methods=['POST'])
def resume_chat():
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        new_message = data.get('message', '')
        
        # 返回流式响应
        return Response(
            resume_parser.chat_with_ai_stream(messages, new_message),
            mimetype='text/plain; charset=utf-8',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 技能培训相关路由
@app.route('/training')
@login_required
def training_page():
    return render_template('training.html')

@app.route('/api/training/books')
def get_books():
    try:
        books = skill_manager.get_available_books()
        return jsonify({
            'success': True,
            'books': books
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/training/upload', methods=['POST'])
def upload_book():
    try:
        if 'title' not in request.form:
            return jsonify({'error': '请提供书籍名称'}), 400
        
        if 'cover' not in request.files or 'pdf' not in request.files:
            return jsonify({'error': '请上传封面和PDF文件'}), 400
        
        title = request.form['title'].strip()
        cover_file = request.files['cover']
        pdf_file = request.files['pdf']
        
        if not title:
            return jsonify({'error': '书籍名称不能为空'}), 400
        
        if cover_file.filename == '' or pdf_file.filename == '':
            return jsonify({'error': '请选择文件'}), 400
        
        result = skill_manager.save_uploaded_book(title, cover_file, pdf_file)
        
        return jsonify({
            'success': True,
            'book': result
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/training/pdf/<path:filename>')
def get_pdf(filename):
    try:
        print(f"请求PDF文件: {filename}")
        
        # 安全检查：防止路径遍历攻击
        if '..' in filename or '/' in filename:
            print(f"无效的文件名: {filename}")
            return jsonify({'error': '无效的文件名'}), 400
        
        # 首先检查pdf文件夹
        pdf_path = os.path.join('modules', 'modules', 'book', 'pdf', filename)
        print(f"检查PDF路径: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            # 如果不在pdf文件夹，检查根目录
            pdf_path = os.path.join('modules', 'modules', 'book', filename)
            print(f"检查备用PDF路径: {pdf_path}")
        
        if os.path.exists(pdf_path):
            print(f"PDF文件存在，大小: {os.path.getsize(pdf_path)} 字节")
            # 添加CORS头，允许跨域访问
            response = send_file(pdf_path, mimetype='application/pdf')
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        else:
            print(f"PDF文件不存在: {pdf_path}")
            return jsonify({'error': f'文件不存在: {filename}'}), 404
    except Exception as e:
        print(f"PDF访问错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/training/cover/<path:filename>')
def get_cover(filename):
    try:
        # 首先检查cover文件夹
        cover_path = os.path.join('modules', 'modules', 'book', 'cover', filename)
        if not os.path.exists(cover_path):
            # 如果不在cover文件夹，检查根目录
            cover_path = os.path.join('modules', 'modules', 'book', filename)
        
        if os.path.exists(cover_path):
            return send_file(cover_path, mimetype='image/png')
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/training/pdf-info/<path:filename>')
def get_pdf_info(filename):
    try:
        # 安全检查：防止路径遍历攻击
        if '..' in filename or '/' in filename:
            return jsonify({'error': '无效的文件名'}), 400
        
        # 首先检查pdf文件夹
        pdf_path = os.path.join('modules', 'modules', 'book', 'pdf', filename)
        if not os.path.exists(pdf_path):
            # 如果不在pdf文件夹，检查根目录
            pdf_path = os.path.join('modules', 'modules', 'book', filename)
        
        if os.path.exists(pdf_path):
            # 获取PDF页数
            page_count = skill_manager.get_pdf_page_count(pdf_path)
            return jsonify({
                'success': True,
                'page_count': page_count,
                'filename': filename
            })
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/interview-result')
@login_required
def interview_result_page():
    """面试结果分析页面"""
    return render_template('interview_result.html')

@app.route('/api/interview-result/data')
@login_required
def get_interview_result_data():
    """获取面试结果数据"""
    try:
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        # 检查用户文件夹中的分析文件
        user_folder = os.path.join('uploads', username)
        
        # 检查三个JSON文件是否存在
        files_to_check = [
            'interview_summary_report.json',
            'facial_analysis_report.json', 
            'analysis_result.json'
        ]
        
        available_files = []
        for filename in files_to_check:
            file_path = os.path.join(user_folder, filename)
            if os.path.exists(file_path):
                available_files.append(filename)
        
        return jsonify({
            'success': True,
            'username': username,
            'available_files': available_files,
            'user_folder': user_folder
        })
        
    except Exception as e:
        print(f"获取面试结果数据失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取数据失败: {str(e)}'})

@app.route('/uploads/<username>/<filename>')
@login_required
def get_user_file(username, filename):
    """获取用户文件"""
    try:
        # 安全检查：确保只能访问uploads目录下的文件
        file_path = os.path.join('uploads', username, filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        # 检查文件是否在uploads目录下
        if not os.path.abspath(file_path).startswith(os.path.abspath('uploads')):
            return jsonify({'error': '访问被拒绝'}), 403
        
        # 根据文件类型返回相应的内容类型
        if filename.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return send_file(file_path)
            
    except Exception as e:
        print(f"获取用户文件失败: {str(e)}")
        return jsonify({'error': f'获取文件失败: {str(e)}'}), 500

@app.route('/book-reader')
@login_required
def book_reader_page():
    return render_template('book_reader.html')

@app.route('/test-book-reader')
def test_book_reader():
    return render_template('test_book_reader.html')

@app.route('/test-fullscreen')
def test_fullscreen():
    return render_template('test_fullscreen.html')

# 学习路径相关路由
@app.route('/learning')
@login_required
def learning_page():
    return render_template('learning.html')

@app.route('/api/learning/generate-plan', methods=['POST'])
def generate_learning_plan():
    try:
        data = request.get_json()
        position = data.get('position', '')
        study_content = data.get('studyContent', '')
        study_goal = data.get('studyGoal', '')
        time_commitment = data.get('timeCommitment', '')
        
        # 返回流式响应
        return Response(
            learning_planner.generate_learning_plan_stream(
                position, study_content, study_goal, time_commitment
            ),
            mimetype='text/plain; charset=utf-8',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/learning/suggestions/<learning_type>')
def get_learning_suggestions(learning_type):
    try:
        suggestions = learning_planner.get_learning_suggestions(learning_type)
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/learning/chat', methods=['POST'])
def learning_chat():
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        new_message = data.get('newMessage', '')
        
        response = learning_planner.chat_with_ai(messages, new_message)
        
        return jsonify({
            'success': True,
            'response': response
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 面试相关路由
@app.route('/interview-config')
@login_required
def interview_config_page():
    return render_template('interview_config.html')

@app.route('/api/interview/generate', methods=['POST'])
@login_required
def generate_interview():
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['candidate_name', 'position', 'target_company', 'tech_domain', 'selected_sections']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'缺少必填字段: {field}'})
        
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        # 检查用户文件夹中的最新简历
        user_folder = os.path.join('uploads', username)
        latest_resume_path = ""
        resume_content = ""
        has_resume = False
        
        if os.path.exists(user_folder):
            # 查找简历文件（匹配"简历"字样，数字越大越新）
            resume_files = []
            for file in os.listdir(user_folder):
                if "简历" in file and file.endswith('.txt'):
                    # 提取文件名中的数字
                    import re
                    numbers = re.findall(r'_(\d+)\.txt$', file)
                    if numbers:
                        resume_files.append((file, int(numbers[-1])))
            
            if resume_files:
                # 按数字排序，取最大的（最新的）
                resume_files.sort(key=lambda x: x[1], reverse=True)
                latest_resume_file = resume_files[0][0]
                latest_resume_path = os.path.join(user_folder, latest_resume_file)
                has_resume = True
                
                # 读取简历内容
                try:
                    with open(latest_resume_path, 'r', encoding='utf-8') as f:
                        resume_content = f.read()
                    print(f"✅ 找到最新简历: {latest_resume_file}")
                except Exception as e:
                    print(f"❌ 读取简历文件失败: {e}")
                    has_resume = False
        
        # 如果没有简历，确保selected_sections中没有"简历深挖"
        selected_sections = data['selected_sections']
        if not has_resume and "简历深挖" in selected_sections:
            selected_sections = [s for s in selected_sections if s != "简历深挖"]
        
        # 导入面试模块
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mock_interview_path = os.path.join(current_dir, 'modules', 'Mock_interview')
        
        # 添加模块路径
        if mock_interview_path not in sys.path:
            sys.path.insert(0, mock_interview_path)
        
        try:
            # 使用绝对导入
            from modules.Mock_interview.init import InterviewAgent
        except ImportError:
            try:
                # 备用导入方式
                sys.path.insert(0, mock_interview_path)
                import importlib.util
                spec = importlib.util.spec_from_file_location("init", os.path.join(mock_interview_path, "init.py"))
                if spec and spec.loader:
                    init_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(init_module)
                    InterviewAgent = init_module.InterviewAgent
                else:
                    raise ImportError("无法加载init模块")
            except Exception as e:
                print(f"导入面试模块失败: {e}")
                return jsonify({'success': False, 'message': '面试模块导入失败'})
        
        # 创建面试智能体
        agent = InterviewAgent()
        
        # 设置面试配置，使用用户输入的候选人姓名
        agent.interview_config = {
            'candidate_name': data['candidate_name'],  # 使用用户输入的候选人姓名
            'current_username': username,  # 添加当前登录用户名，用于确定保存路径
            'position': data['position'],
            'target_company': data['target_company'],
            'tech_domain': data['tech_domain'],
            'has_resume': has_resume,
            'resume_path': latest_resume_path,
            'interview_type': '单人',  # 固定为单人模式
            'strict_mode': data.get('strict_mode', False),
            'selected_sections': selected_sections
        }
        
        # 设置简历内容
        if has_resume and resume_content:
            agent.resume_content = resume_content
        
        # 生成面试题目
        import asyncio
        questions = asyncio.run(agent.generate_interview_questions())
        
        # 保存面试配置和题目到用户特定文件夹，传递当前用户名
        agent.save_interview_questions(questions, current_username=username)
        
        # 将面试配置存储到session中，供面试页面使用
        session['interview_config'] = agent.interview_config
        session['interview_questions'] = questions
        
        return jsonify({
            'success': True,
            'message': '面试题目生成成功',
            'questions_count': len(questions),
            'redirect_url': '/interview',  # 添加跳转URL
            'has_resume': has_resume,
            'resume_file': os.path.basename(latest_resume_path) if latest_resume_path else None
        })
        
    except Exception as e:
        print(f"生成面试题目时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'生成面试题目失败: {str(e)}'})

@app.route('/interview')
@login_required
def interview_page():
    # 检查是否有面试配置
    if 'interview_config' not in session or 'interview_questions' not in session:
        return redirect('/interview-config')
    
    return render_template('interview.html')

@app.route('/api/interview/data')
@login_required
def get_interview_data():
    try:
        # 从session中获取面试配置和题目
        config = session.get('interview_config', {})
        questions = session.get('interview_questions', {})
        
        if not config or not questions:
            return jsonify({'success': False, 'message': '没有找到面试数据'})
        
        return jsonify({
            'success': True,
            'config': config,
            'questions': questions
        })
        
    except Exception as e:
        print(f"获取面试数据时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'获取面试数据失败: {str(e)}'})

@app.route('/api/interview/run', methods=['POST'])
@login_required
def run_interview():
    """运行完整的面试流程"""
    try:
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        # 导入面试系统模块
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mock_interview_path = os.path.join(current_dir, 'modules', 'Mock_interview')
        
        # 添加模块路径
        if mock_interview_path not in sys.path:
            sys.path.insert(0, mock_interview_path)
        
        try:
            # 导入面试系统
            from modules.Mock_interview.main import InterviewSystem
        except ImportError:
            try:
                # 备用导入方式
                sys.path.insert(0, mock_interview_path)
                import importlib.util
                spec = importlib.util.spec_from_file_location("main", os.path.join(mock_interview_path, "main.py"))
                if spec and spec.loader:
                    main_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(main_module)
                    InterviewSystem = main_module.InterviewSystem
                else:
                    raise ImportError("无法加载main模块")
            except Exception as e:
                print(f"导入面试系统失败: {e}")
                return jsonify({'success': False, 'message': '面试系统导入失败'})
        
        # 创建面试系统实例
        interview_system = InterviewSystem()
        
        # 设置配置文件路径为用户特定路径
        user_folder = os.path.join('uploads', username)
        os.makedirs(user_folder, exist_ok=True)
        
        interview_system.config_file = os.path.join(user_folder, "interview_config.json")
        interview_system.questions_file = os.path.join(user_folder, "interview_questions.json")
        
        # 加载现有配置
        if not interview_system.load_existing_config():
            return jsonify({'success': False, 'message': '加载面试配置失败'})
        
        # 运行面试流程
        import asyncio
        asyncio.run(interview_system.run_complete_interview())
        
        return jsonify({
            'success': True,
            'message': '面试流程执行完成'
        })
        
    except Exception as e:
        print(f"运行面试流程时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'运行面试流程失败: {str(e)}'})

@app.route('/api/interview/history')
@login_required
def get_interview_history():
    """获取用户的面试历史记录"""
    try:
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        # 构建用户文件夹路径
        user_folder = os.path.join('uploads', username)
        
        if not os.path.exists(user_folder):
            return jsonify({
                'success': True,
                'history': []
            })
        
        # 查找用户的面试配置文件
        history = []
        for filename in os.listdir(user_folder):
            if filename.endswith('_config.json') or filename.endswith('interview_config.json'):
                filepath = os.path.join(user_folder, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    # 提取面试信息
                    interview_info = {
                        'filename': filename,
                        'created_at': config_data.get('generated_at', ''),
                        'candidate_name': config_data.get('interview_config', {}).get('candidate_name', ''),
                        'position': config_data.get('interview_config', {}).get('position', ''),
                        'target_company': config_data.get('interview_config', {}).get('target_company', ''),
                        'tech_domain': config_data.get('interview_config', {}).get('tech_domain', ''),
                        'selected_sections': config_data.get('interview_config', {}).get('selected_sections', [])
                    }
                    history.append(interview_info)
                except Exception as e:
                    print(f"读取面试配置文件 {filename} 失败: {e}")
                    continue
        
        # 按创建时间排序
        history.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        print(f"获取面试历史时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'获取面试历史失败: {str(e)}'})

@app.route('/api/user/resume-status')
@login_required
def check_resume_status():
    """检查当前用户是否有简历文件"""
    try:
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        # 检查用户文件夹中的简历文件
        user_folder = os.path.join('uploads', username)
        has_resume = False
        latest_resume_file = None
        
        if os.path.exists(user_folder):
            # 查找简历文件（匹配"简历"字样）
            resume_files = []
            for file in os.listdir(user_folder):
                if "简历" in file and file.endswith('.txt'):
                    # 提取文件名中的数字
                    import re
                    numbers = re.findall(r'_(\d+)\.txt$', file)
                    if numbers:
                        resume_files.append((file, int(numbers[-1])))
            
            if resume_files:
                # 按数字排序，取最大的（最新的）
                resume_files.sort(key=lambda x: x[1], reverse=True)
                latest_resume_file = resume_files[0][0]
                has_resume = True
        
        return jsonify({
            'success': True,
            'has_resume': has_resume,
            'latest_resume_file': latest_resume_file
        })
        
    except Exception as e:
        print(f"检查简历状态时出错: {str(e)}")
        return jsonify({
            'success': False,
            'has_resume': False,
            'message': f'检查简历状态失败: {str(e)}'
        })

@app.route('/live2d/<path:filename>')
def live2d_static(filename):
    """服务live2d静态文件"""
    try:
        live2d_dir = os.path.join(current_dir, 'live2d')
        return send_file(os.path.join(live2d_dir, filename))
    except Exception as e:
        print(f"Live2D文件访问错误: {str(e)}")
        return "File not found", 404

@app.route('/live2d')
def live2d_interview():
    """Live2D面试页面"""
    return render_template('live2d.html')

@app.route('/api/interview/start-facial-analysis', methods=['POST'])
@login_required
def start_facial_analysis():
    """开始微表情肢体分析（浏览器端）"""
    try:
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        # 初始化用户分析器
        if not hasattr(app, 'facial_analyzers'):
            app.facial_analyzers = {}
        
        # 导入面试模块
        current_dir = os.path.dirname(os.path.abspath(__file__))
        facial_analysis_path = os.path.join(current_dir, 'modules', 'Mock_interview')
        
        if facial_analysis_path not in sys.path:
            sys.path.insert(0, facial_analysis_path)
        
        from modules.Mock_interview.facial_analysis import FacialAnalysis
        
        # 为用户创建分析实例
        app.facial_analyzers[username] = FacialAnalysis()
        app.facial_analyzers[username].is_analyzing = True
        
        return jsonify({
            'success': True,
            'message': '微表情分析已启动（浏览器端）',
            'username': username
        })
        
    except Exception as e:
        print(f"开始面试分析失败: {str(e)}")
        return jsonify({'success': False, 'message': f'开始分析失败: {str(e)}'})

@app.route('/api/interview/start-voice-analysis', methods=['POST'])
@login_required
def start_voice_analysis():
    """开始语调分析（浏览器端）"""
    try:
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        # 初始化用户分析器
        if not hasattr(app, 'voice_analyzers'):
            app.voice_analyzers = {}
        
        # 导入语调分析模块
        current_dir = os.path.dirname(os.path.abspath(__file__))
        voice_analysis_path = os.path.join(current_dir, 'modules', 'Mock_interview', '语调识别', 'Speech-Analysis')
        
        if voice_analysis_path not in sys.path:
            sys.path.insert(0, voice_analysis_path)
        
        # 直接导入模块
        import real_time_analyzer
        RealTimeVoiceAnalyzer = real_time_analyzer.RealTimeVoiceAnalyzer
        
        # 创建分析实例
        analyzer = RealTimeVoiceAnalyzer()
        analyzer.is_recording = True  # 标记为录音状态
        app.voice_analyzers[username] = analyzer
        
        return jsonify({
            'success': True,
            'message': '语调分析已启动（浏览器端）',
            'username': username
        })
        
    except Exception as e:
        print(f"开始语调分析失败: {str(e)}")
        return jsonify({'success': False, 'message': f'开始分析失败: {str(e)}'})

@app.route('/api/interview/stop-facial-analysis', methods=['POST'])
@login_required
def stop_facial_analysis():
    """停止微表情肢体分析"""
    try:
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        if hasattr(app, 'facial_analyzers') and username in app.facial_analyzers:
            analyzer = app.facial_analyzers[username]
            analyzer.stop_analysis()
            
            # 保存最终报告
            user_folder = os.path.join('uploads', username)
            os.makedirs(user_folder, exist_ok=True)
            report_path = os.path.join(user_folder, "facial_analysis_report.json")
            analyzer.save_analysis_report(report_path)
            
            # 获取分析总结
            summary = analyzer.get_analysis_summary()
            
            # 清理分析实例
            del app.facial_analyzers[username]
            
            return jsonify({
                'success': True,
                'message': '微表情肢体分析已停止',
                'summary': summary,
                'report_saved': True
            })
        else:
            return jsonify({
                'success': False,
                'message': '没有正在运行的分析任务'
            })
            
    except Exception as e:
        print(f"停止面试分析失败: {str(e)}")
        return jsonify({'success': False, 'message': f'停止分析失败: {str(e)}'})

@app.route('/api/interview/facial-analysis-status', methods=['GET'])
@login_required
def get_facial_analysis_status():
    """获取微表情肢体分析状态"""
    try:
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        is_running = False
        analysis_count = 0
        
        if hasattr(app, 'facial_analyzers') and username in app.facial_analyzers:
            analyzer = app.facial_analyzers[username]
            is_running = analyzer.is_analyzing
            analysis_count = len(analyzer.analysis_results)
        
        return jsonify({
            'success': True,
            'is_running': is_running,
            'analysis_count': analysis_count,
            'username': username
        })
        
    except Exception as e:
        print(f"获取分析状态失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取状态失败: {str(e)}'})

@app.route('/api/interview/stop-voice-analysis', methods=['POST'])
@login_required
def stop_voice_analysis():
    """停止语调分析"""
    try:
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        data = request.get_json() or {}
        browser_mode = data.get('browser_mode', False)
        
        if browser_mode:
            # 浏览器模式：只需要清理状态
            if hasattr(app, 'voice_analyzers') and username in app.voice_analyzers:
                del app.voice_analyzers[username]
            
            return jsonify({
                'success': True,
                'message': '语调分析状态已清理',
                'browser_mode': True
            })
        
        # 原始服务器端模式（保留兼容性）
        if hasattr(app, 'voice_analyzers') and username in app.voice_analyzers:
            analyzer = app.voice_analyzers[username]
            analyzer.stop_flask_recording()
            
            # 分析录音
            result = analyzer.analyze_recording()
            
            if result:
                # 保存最终报告到用户文件夹
                user_folder = os.path.join('uploads', username)
                os.makedirs(user_folder, exist_ok=True)
                
                # 使用固定文件名
                report_filename = "voice_analysis_result.json"
                report_path = os.path.join(user_folder, report_filename)
                
                # 直接保存到用户目录
                try:
                    formatted_result = analyzer.format_result_for_json(result)
                    with open(report_path, 'w', encoding='utf-8') as f:
                        json.dump(formatted_result, f, ensure_ascii=False, indent=2)
                    print(f"✅ 语调分析报告已保存到用户文件夹: {report_path}")
                except Exception as e:
                    print(f"保存文件失败: {e}")
                    # 如果直接保存失败，尝试使用分析器的方法
                    saved_path = analyzer.save_analysis_result_json(result, report_filename)
                    if saved_path and os.path.exists(saved_path) and not saved_path.startswith(user_folder):
                        import shutil
                        try:
                            shutil.move(saved_path, report_path)
                            print(f"✅ 语调分析报告已移动到用户文件夹: {report_path}")
                        except:
                            pass
                
                # 获取分析总结
                formatted_result = analyzer.format_result_for_json(result)
                
                # 清理分析实例
                del app.voice_analyzers[username]
                
                return jsonify({
                    'success': True,
                    'message': '语调分析已停止',
                    'result': formatted_result,
                    'report_saved': True,
                    'report_path': report_filename
                })
            else:
                # 清理分析实例
                del app.voice_analyzers[username]
                
                return jsonify({
                    'success': True,
                    'message': '语调分析已停止，但没有录音数据',
                    'report_saved': False
                })
        else:
            return jsonify({
                'success': False,
                'message': '没有正在运行的语调分析任务'
            })
            
    except Exception as e:
        print(f"停止语调分析失败: {str(e)}")
        return jsonify({'success': False, 'message': f'停止分析失败: {str(e)}'})

@app.route('/api/interview/voice-analysis-status', methods=['GET'])
@login_required
def get_voice_analysis_status():
    """获取语调分析状态"""
    try:
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        is_running = False
        is_recording = False
        
        if hasattr(app, 'voice_analyzers') and username in app.voice_analyzers:
            analyzer = app.voice_analyzers[username]
            is_recording = analyzer.is_recording
            is_running = True
        
        return jsonify({
            'success': True,
            'is_running': is_running,
            'is_recording': is_recording,
            'username': username
        })
        
    except Exception as e:
        print(f"获取语调分析状态失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取状态失败: {str(e)}'})

@app.route('/api/interview/analyze-photo', methods=['POST'])
@login_required
def analyze_photo():
    """分析浏览器发送的照片"""
    try:
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': '没有上传图片'})
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        # 保存临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            image_file.save(temp_file.name)
            temp_filepath = temp_file.name
        
        try:
            # 导入面试模块
            current_dir = os.path.dirname(os.path.abspath(__file__))
            facial_analysis_path = os.path.join(current_dir, 'modules', 'Mock_interview')
            
            if facial_analysis_path not in sys.path:
                sys.path.insert(0, facial_analysis_path)
            
            from modules.Mock_interview.facial_analysis import FacialAnalysis
            
            # 创建分析实例
            analyzer = FacialAnalysis()
            
            # 分析图像
            result = analyzer.analyze_image(temp_filepath)
            
            if result:
                # 保存到用户的分析结果中
                if not hasattr(app, 'facial_analyzers'):
                    app.facial_analyzers = {}
                
                if username not in app.facial_analyzers:
                    app.facial_analyzers[username] = FacialAnalysis()
                
                # 添加时间戳
                result['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                result['photo_path'] = f"browser_capture_{len(app.facial_analyzers[username].analysis_results)}.jpg"
                
                app.facial_analyzers[username].analysis_results.append(result)
                
                return jsonify({
                    'success': True,
                    'analysis': result,
                    'count': len(app.facial_analyzers[username].analysis_results)
                })
            else:
                return jsonify({'success': False, 'message': '图像分析失败'})
                
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_filepath)
            except:
                pass
        
    except Exception as e:
        print(f"照片分析失败: {str(e)}")
        return jsonify({'success': False, 'message': f'照片分析失败: {str(e)}'})

@app.route('/api/interview/analyze-audio', methods=['POST'])
@login_required
def analyze_audio():
    """分析浏览器发送的音频"""
    try:
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        if 'audio' not in request.files:
            return jsonify({'success': False, 'message': '没有上传音频'})
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        # 保存临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            audio_file.save(temp_file.name)
            temp_filepath = temp_file.name
        
        print(f"音频文件已保存到临时路径: {temp_filepath}")
        print(f"原始文件大小: {os.path.getsize(temp_filepath)} bytes")
        
        try:
            # 转换webm到wav格式
            import subprocess
            import tempfile
            
            # 创建临时wav文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as wav_file:
                wav_filepath = wav_file.name
            
            print(f"目标WAV文件路径: {wav_filepath}")
            
            # 使用ffmpeg转换（如果有的话）
            conversion_success = False
            try:
                # 尝试使用ffmpeg转换
                print("尝试使用FFmpeg转换...")
                result = subprocess.run([
                    'ffmpeg', '-i', temp_filepath, '-ar', '22050', '-ac', '1', 
                    '-acodec', 'pcm_s16le', wav_filepath, '-y'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("FFmpeg转换成功")
                    conversion_success = True
                else:
                    print(f"FFmpeg转换失败: {result.stderr}")
                
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                print(f"FFmpeg不可用: {e}")
            
            # 如果FFmpeg失败，使用librosa
            if not conversion_success:
                print("使用librosa进行音频转换...")
                try:
                    import librosa
                    import soundfile as sf
                    print(f"开始加载音频文件: {temp_filepath}")
                    
                    # 检查原始文件是否可读
                    if not os.path.exists(temp_filepath):
                        raise FileNotFoundError(f"临时文件不存在: {temp_filepath}")
                    
                    audio_data, sr = librosa.load(temp_filepath, sr=22050)
                    print(f"音频加载成功，采样率: {sr}, 数据长度: {len(audio_data)}, 时长: {len(audio_data)/sr:.2f}秒")
                    
                    if len(audio_data) == 0:
                        raise ValueError("音频数据为空")
                    
                    sf.write(wav_filepath, audio_data, sr)
                    print(f"音频已转换并保存为: {wav_filepath}")
                    conversion_success = True
                    
                except Exception as librosa_error:
                    print(f"Librosa处理失败: {librosa_error}")
                    import traceback
                    traceback.print_exc()
                    return jsonify({
                        'success': False, 
                        'message': f'音频转换失败: {str(librosa_error)}'
                    })
            
            if not conversion_success:
                return jsonify({
                    'success': False, 
                    'message': '音频转换失败，请检查音频格式'
                })
            
            # 导入语调分析模块
            current_dir = os.path.dirname(os.path.abspath(__file__))
            voice_analysis_path = os.path.join(current_dir, 'modules', 'Mock_interview', '语调识别', 'Speech-Analysis')
            
            if voice_analysis_path not in sys.path:
                sys.path.insert(0, voice_analysis_path)
            
            # 直接导入模块
            import real_time_analyzer
            RealTimeVoiceAnalyzer = real_time_analyzer.RealTimeVoiceAnalyzer
            
            # 创建分析实例
            analyzer = RealTimeVoiceAnalyzer()
            
            # 检查wav文件是否存在和有效
            if not os.path.exists(wav_filepath):
                raise FileNotFoundError(f"转换后的WAV文件不存在: {wav_filepath}")
            
            file_size = os.path.getsize(wav_filepath)
            if file_size < 1000:  # 小于1KB可能是空文件
                raise ValueError(f"WAV文件太小，可能转换失败: {file_size} bytes")
            
            print(f"开始分析WAV文件: {wav_filepath} (大小: {file_size} bytes)")
            
            # 使用语音分析器分析转换后的wav文件
            result = analyzer.analyzer.analyze_voice(wav_filepath)
            print(f"分析结果类型: {type(result)}")
            
            if result and "错误" not in str(result):
                print("音频分析成功，开始格式化结果...")
                # 格式化结果
                formatted_result = analyzer.format_result_for_json(result)
                
                # 保存分析结果到用户文件夹
                user_folder = os.path.join('uploads', username)
                os.makedirs(user_folder, exist_ok=True)
                
                report_path = os.path.join(user_folder, 'voice_analysis_result.json')
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(formatted_result, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 语调分析完成，结果已保存到: {report_path}")
                
                return jsonify({
                    'success': True,
                    'analysis': formatted_result,
                    'message': '语调分析完成',
                    'saved_path': 'voice_analysis_result.json'
                })
            else:
                error_msg = result.get('错误', '分析失败') if isinstance(result, dict) else '音频处理失败'
                print(f"分析失败: {error_msg}")
                return jsonify({
                    'success': False, 
                    'message': f'语调分析失败: {error_msg}'
                })
                
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_filepath)
                if 'wav_filepath' in locals():
                    os.unlink(wav_filepath)
            except:
                pass
        
    except Exception as e:
        print(f"音频分析失败: {str(e)}")
        return jsonify({'success': False, 'message': f'音频分析失败: {str(e)}'})

@app.route('/api/interview/save-voice-analysis', methods=['POST'])
@login_required
def save_voice_analysis():
    """保存语调分析结果"""
    try:
        # 获取当前登录用户
        current_user = session.get('user', {})
        username = current_user.get('username', 'unknown_user')
        
        data = request.get_json()
        analysis = data.get('analysis', {})
        
        if analysis:
            # 保存到用户文件夹
            user_folder = os.path.join('uploads', username)
            os.makedirs(user_folder, exist_ok=True)
            
            report_path = os.path.join(user_folder, 'voice_analysis_result.json')
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'message': '语调分析结果已保存',
                'path': report_path
            })
        else:
            return jsonify({'success': False, 'message': '没有分析数据'})
        
    except Exception as e:
        print(f"保存语调分析结果失败: {str(e)}")
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True)