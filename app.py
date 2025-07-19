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
        username = current_user.get('username', data['candidate_name'])
        
        # 导入面试模块
        import sys
        import os
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
                from init import InterviewAgent
            except ImportError as e:
                print(f"导入面试模块失败: {e}")
                return jsonify({'success': False, 'message': '面试模块导入失败'})
        
        # 创建面试智能体
        agent = InterviewAgent()
        
        # 设置面试配置，使用用户名作为candidate_name
        agent.interview_config = {
            'candidate_name': username,  # 使用登录用户名
            'position': data['position'],
            'target_company': data['target_company'],
            'tech_domain': data['tech_domain'],
            'has_resume': data.get('has_resume', False),
            'resume_path': '',  # 暂时为空，后续可以处理文件上传
            'interview_type': '单人',  # 固定为单人模式
            'strict_mode': data.get('strict_mode', False),
            'selected_sections': data['selected_sections']
        }
        
        # 处理简历内容（如果有）
        if data.get('has_resume') and data.get('resume_content'):
            agent.resume_content = data['resume_content']
        
        # 生成面试题目
        import asyncio
        questions = asyncio.run(agent.generate_interview_questions())
        
        # 保存面试配置和题目到用户特定文件夹
        agent.save_interview_questions(questions)
        
        # 将面试配置存储到session中，供面试页面使用
        session['interview_config'] = agent.interview_config
        session['interview_questions'] = questions
        
        return jsonify({
            'success': True,
            'message': '面试题目生成成功',
            'questions_count': len(questions)
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
        import sys
        import os
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
                from main import InterviewSystem
            except ImportError as e:
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

if __name__ == '__main__':
    app.run(debug=True)