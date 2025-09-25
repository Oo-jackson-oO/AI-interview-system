from flask import Flask, render_template, request, jsonify, send_file, Response, stream_template, redirect, url_for, session
import os
import sys
import json
import base64
from datetime import datetime
from werkzeug.utils import secure_filename
import io
from functools import wraps
import time
# TTS相关导入
import ssl
import queue
from datetime import datetime
from urllib.parse import urlparse, urlencode
from wsgiref.handlers import format_date_time
from time import mktime
import _thread as thread
# 添加模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入各个模块
from modules.resume_parsing.backend.resume_parser import ResumeParser
from modules.resume_parsing.backend.resume_analyzer import ResumeAnalyzer
from modules.skill_training import SkillManager
from modules.learning_path import LearningPlanner
from modules.user_management import UserManager

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = 'your-secret-key-here'  # 用于session加密

# ==================== ASR语音识别功能集成 ====================
# 在原有功能基础上添加ASR支持，不影响现有功能

# ASR相关导入
import eventlet
import hashlib
import hmac
import threading
import websocket
from urllib.parse import quote
from flask_socketio import SocketIO, emit

# 初始化SocketIO（如果还没有初始化）
try:
    # 尝试检查是否已经有socketio实例
    if 'socketio' not in globals():
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
        print("✅ SocketIO已初始化用于ASR功能")
    else:
        print("✅ 使用现有的SocketIO实例")
except Exception as e:
    # 如果初始化失败，创建新的实例
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    print(f"✅ 新建SocketIO实例: {e}")

# 科大讯飞ASR配置
XUNFEI_ASR_CONFIG = {
    'APPID': 'daa9d5d9',
    'API_KEY': '57e1dcd91156c7b12c078b5ad372870b',
    'BASE_URL': 'ws://rtasr.xfyun.cn/v1/ws'
}

# ASR连接存储
asr_connections = {}

def parse_xunfei_result(result_json):
    """解析科大讯飞实时语音转写的JSON结果"""
    try:
        result = json.loads(result_json)
        
        if result.get("action") == "started":
            return "连接成功，开始转写..."
        
        elif result.get("action") == "result":
            # 直接处理result中的data字段
            data = result.get("data", "")
            if data:
                # 尝试解析data字段
                try:
                    data_obj = json.loads(data)
                    # 提取转写文本
                    text = ""
                    if "cn" in data_obj and "st" in data_obj["cn"]:
                        st = data_obj["cn"]["st"]
                        if "rt" in st:
                            for rt_item in st["rt"]:
                                if "ws" in rt_item:
                                    for ws_item in rt_item["ws"]:
                                        if "cw" in ws_item:
                                            for cw_item in ws_item["cw"]:
                                                text += cw_item.get("w", "")
                    return text.strip()
                except:
                    # 如果data不是JSON格式，直接返回
                    return data
        
        elif result.get("action") == "error":
            return f"错误: {result_json}"
        
        else:
            # 处理没有action字段的情况，可能是直接的转写结果
            if "cn" in result and "st" in result["cn"]:
                st = result["cn"]["st"]
                if "rt" in st:
                    text = ""
                    for rt_item in st["rt"]:
                        if "ws" in rt_item:
                            for ws_item in rt_item["ws"]:
                                if "cw" in ws_item:
                                    for cw_item in ws_item["cw"]:
                                        text += cw_item.get("w", "")
                    return text.strip()
            
            return f"未知结果: {result_json}"
            
    except Exception as e:
        return f"解析错误: {e}"

class ASRAgent:
    """ASR语音识别代理类"""
    def __init__(self, client_id):
        self.client_id = client_id
        self.ws = None
        self.app_id = XUNFEI_ASR_CONFIG['APPID']
        self.api_key = XUNFEI_ASR_CONFIG['API_KEY']
        
        # 智能录音控制
        self.is_recording = False
        self.last_speech_time = time.time()
        self.transcription_parts = []
        self.all_sentences = []
        self.all_transcriptions = []
        self.accumulated_text = ""
        self.start_time = None
        self.monitor_thread = None
        
    def create_auth_url(self):
        """创建科大讯飞WebSocket连接URL"""
        base_url = XUNFEI_ASR_CONFIG['BASE_URL']
        ts = str(int(time.time()))
        tt = (self.app_id + ts).encode('utf-8')
        md5 = hashlib.md5()
        md5.update(tt)
        baseString = md5.hexdigest()
        baseString = bytes(baseString, encoding='utf-8')

        apiKey = self.api_key.encode('utf-8')
        signa = hmac.new(apiKey, baseString, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        signa = str(signa, 'utf-8')

        url = base_url + "?appid=" + self.app_id + "&ts=" + ts + "&signa=" + quote(signa)
        return url
    
    def monitor_silence(self):
        """监控静音，实现智能停止"""
        if not self.start_time:
            return
            
        # 先等8秒
        while self.is_recording and (time.time() - self.start_time < 8):
            time.sleep(0.2)
        
        # 8秒后，开始检测3秒无新转写
        last_check_time = self.last_speech_time
        while self.is_recording:
            # 检查是否有新的转写更新
            if self.last_speech_time > last_check_time:
                last_check_time = self.last_speech_time
            
            if time.time() - self.last_speech_time > 3.0:
                print(f"\n🔇 3秒无新转写，自动停止录音")
                self.auto_stop()
                break
            time.sleep(0.2)
    
    def auto_stop(self):
        """自动停止录音并发送最终结果"""
        self.is_recording = False
        print("准备发送结束标记")
        self.stop()
        
        # 处理转写内容并提取最终句子
        final_sentences = self.extract_final_sentences()
        
        # 发送最终结果到前端
        if final_sentences:
            final_text = " ".join(final_sentences)
            socketio.emit('asr_final_result', {
                'sentences': final_sentences,
                'full_text': final_text,
                'count': len(final_sentences)
            }, room=self.client_id)
            print(f"📋 最终转写结果({len(final_sentences)}句): {final_text}")
        
        socketio.emit('asr_auto_stopped', room=self.client_id)

    
    def extract_final_sentences(self):
        """提取最终句子"""
        if not self.all_transcriptions:
            return []
        
        print(f"🔍 分析 {len(self.all_transcriptions)} 个转写结果...")
        
        final_sentences = []
        previous_text = ""
        
        for i, current_text in enumerate(self.all_transcriptions):
            if previous_text:
                # 如果当前转写比上一个短或长度相等但内容不同，说明进入下一句
                if (len(current_text) < len(previous_text) or 
                    (len(current_text) == len(previous_text) and current_text != previous_text)):
                    # 保存上一个转写结果（完整的句子）
                    if previous_text.strip():
                        final_sentences.append(previous_text.strip())
                        print(f"✅ 提取句子: '{previous_text.strip()}'")
            
            previous_text = current_text
        
        # 转写终止，保存最后一个转写结果
        if previous_text and previous_text.strip():
            final_sentences.append(previous_text.strip())
            print(f"✅ 提取最后句子: '{previous_text.strip()}'")
        
        return final_sentences

    def on_message(self, ws, message):
        """处理科大讯飞返回的消息"""
        try:
            result_str = str(message)
            result_dict = json.loads(result_str)
            
            if result_dict.get("action") == "started":
                print("转写服务已启动")
                socketio.emit('asr_connected', room=self.client_id)
                
            elif result_dict.get("action") == "result":
                result = parse_xunfei_result(result_str)
                if result and result != "连接成功，开始转写...":
                    # 检查是否是新的转写内容
                    if result != self.accumulated_text:
                        self.accumulated_text = result
                        self.last_speech_time = time.time()  # 重置静音计时器
                        
                        # 存储所有转写结果用于后续分析
                        self.all_transcriptions.append(result)
                        print(f"📝 转写: {result}")
                        
                        # 更新转写部分
                        if self.transcription_parts:
                            self.transcription_parts[-1] = result
                        else:
                            self.transcription_parts.append(result)
                        
                        # 发送实时转写结果到前端
                        socketio.emit('asr_result', {'text': result}, room=self.client_id)
                    
            elif result_dict.get("action") == "error":
                print(f"转写错误: {result_str}")
                socketio.emit('asr_error', {'error': result_str}, room=self.client_id)
                
        except Exception as e:
            print(f"处理消息错误: {e}")

    def on_error(self, ws, error):
        """处理错误"""
        print(f"WebSocket错误: {error}")
        socketio.emit('asr_error', {'error': str(error)}, room=self.client_id)

    def on_close(self, ws, close_status_code, close_msg):
        """连接关闭"""
        print("WebSocket连接已关闭")
        socketio.emit('asr_disconnected', room=self.client_id)

    def on_open(self, ws):
        """连接打开"""
        print("WebSocket连接已建立")
        socketio.emit('asr_connected', room=self.client_id)

    def connect(self):
        """连接到科大讯飞"""
        url = self.create_auth_url()
        print(f"连接URL: {url}")
        self.ws = websocket.WebSocketApp(url,
                                        on_message=self.on_message,
                                        on_error=self.on_error,
                                        on_close=self.on_close,
                                        on_open=self.on_open)
        
        # 在新线程中运行
        def run_ws():
            self.ws.run_forever()
        
        thread = threading.Thread(target=run_ws)
        thread.daemon = True
        thread.start()

    def start_smart_recording(self):
        """开始智能录音"""
        print(f"\n🎙️ 开始录音，请开始说话...")
        print(f"⏰ 录音至少持续8秒，之后3秒无新转写自动停止")
        
        # 初始化录音状态
        self.transcription_parts = []
        self.all_transcriptions = []
        self.all_sentences = []
        self.accumulated_text = ""
        self.is_recording = True
        self.last_speech_time = time.time()
        self.start_time = time.time()
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_silence)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        print("=" * 60)
        print("🎙️ 开始录音，请开始说话...")
        print("⏰ 录音至少持续8秒，之后3秒无新转写自动停止")
        print("=" * 60)

        socketio.emit('asr_smart_started', {
            'message': '智能录音已启动，将自动检测停止'
        }, room=self.client_id)

    def send_audio(self, audio_data):
        """发送音频数据"""
        if self.ws and self.ws.sock and self.ws.sock.connected and self.is_recording:
            self.ws.send(audio_data)

    def stop(self):
        """停止识别"""
        self.is_recording = False
        if self.ws:
            # 发送结束标记
            end_tag = "{\"end\": true}"
            try:
                self.ws.send(bytes(end_tag.encode('utf-8')))
                print("已发送结束标记")
            except Exception as e:
                # 捕获异常并打印日志
                print(f"发送结束标记失败: {e}")
            self.ws.close()

# ==================== ASR SocketIO事件处理 ====================

@socketio.on('connect')
def asr_handle_connect():
    print(f'ASR客户端已连接: {request.sid}')

@socketio.on('disconnect')
def asr_handle_disconnect():
    print(f'ASR客户端已断开: {request.sid}')
    # 清理连接
    if request.sid in asr_connections:
        asr_connections[request.sid].stop()
        del asr_connections[request.sid]

@socketio.on('start_smart_asr')
def handle_start_smart_asr():
    """开始智能语音识别（自动停止）"""
    client_id = request.sid
    if client_id in asr_connections:
        # 如果已有连接，先停止
        asr_connections[client_id].stop()
        del asr_connections[client_id]
    
    asr = ASRAgent(client_id)
    asr_connections[client_id] = asr
    asr.connect()
    
    # 等待连接建立后启动智能录音
    def start_after_connection():
        time.sleep(1)  # 等待连接建立
        if client_id in asr_connections:
            asr_connections[client_id].start_smart_recording()
    
    thread = threading.Thread(target=start_after_connection)
    thread.daemon = True
    thread.start()

@socketio.on('stop_asr')
def handle_stop_asr():
    """停止语音识别"""
    client_id = request.sid
    if client_id in asr_connections:
        # 手动停止时也进行最终结果处理
        asr = asr_connections[client_id]
        if asr.all_transcriptions:
            final_sentences = asr.extract_final_sentences()
            if final_sentences:
                final_text = " ".join(final_sentences)
                socketio.emit('asr_final_result', {
                    'sentences': final_sentences,
                    'full_text': final_text,
                    'count': len(final_sentences)
                }, room=client_id)
                print(f"📋 手动停止 - 最终转写结果({len(final_sentences)}句): {final_text}")
        
        asr_connections[client_id].stop()
        del asr_connections[client_id]


@socketio.on('audio_data')
def handle_audio_data(data):
    """处理音频数据"""
    client_id = request.sid
    if client_id in asr_connections:
        # 将base64编码的音频数据解码后发送
        audio_bytes = base64.b64decode(data['audio'])
        asr_connections[client_id].send_audio(audio_bytes)

# ==================== ASR HTTP路由 ====================

@app.route('/api/asr/status')
def asr_status():
    """ASR服务状态检查"""
    return jsonify({
        'success': True,
        'message': 'ASR服务运行正常',
        'active_connections': len(asr_connections),
        'config': {
            'app_id': XUNFEI_ASR_CONFIG['APPID'],
            'service': '科大讯飞语音转写'
        }
    })

@app.route('/api/asr/test')
def asr_test():
    """ASR测试页面"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>ASR语音识别测试</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .btn { padding: 10px 20px; margin: 10px; border: none; border-radius: 5px; cursor: pointer; }
            .btn-primary { background: #007bff; color: white; }
            .btn-danger { background: #dc3545; color: white; }
            #results { border: 1px solid #ccc; padding: 15px; margin: 20px 0; min-height: 200px; }
            .result-item { margin: 5px 0; padding: 5px; background: #f8f9fa; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🎙️ ASR语音识别测试</h1>
        <div>
            <button class="btn btn-primary" onclick="startASR()">开始智能识别</button>
            <button class="btn btn-danger" onclick="stopASR()">停止识别</button>
        </div>
        <div id="status">状态：未连接</div>
        <div id="results">等待语音输入...</div>
        
        <script>
            const socket = io();
            let mediaRecorder, audioContext, isRecording = false;
            
            socket.on('connect', () => {
                document.getElementById('status').textContent = '状态：已连接';
            });
            
            socket.on('asr_connected', () => {
                document.getElementById('status').textContent = '状态：ASR已连接';
            });
            
            socket.on('asr_smart_started', (data) => {
                document.getElementById('status').textContent = '状态：智能录音中...';
                isRecording = true;
            });
            
            socket.on('asr_result', (data) => {
                const results = document.getElementById('results');
                const item = document.createElement('div');
                item.className = 'result-item';
                item.textContent = '📝 ' + data.text;
                results.appendChild(item);
                results.scrollTop = results.scrollHeight;
            });
            
            socket.on('asr_final_result', (data) => {
                const results = document.getElementById('results');
                const item = document.createElement('div');
                item.className = 'result-item';
                item.style.background = '#d4edda';
                item.style.fontWeight = 'bold';
                item.textContent = '🎯 最终结果: ' + data.full_text;
                results.appendChild(item);
                results.scrollTop = results.scrollHeight;
            });
            
            socket.on('asr_auto_stopped', () => {
                document.getElementById('status').textContent = '状态：自动停止';
                isRecording = false;
            });
            
            async function startASR() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        audio: { sampleRate: 16000, channelCount: 1 } 
                    });
                    
                    audioContext = new AudioContext({ sampleRate: 16000 });
                    const source = audioContext.createMediaStreamSource(stream);
                    const processor = audioContext.createScriptProcessor(1024, 1, 1);
                    
                    processor.onaudioprocess = function(e) {
                        if (isRecording) {
                            const audioData = e.inputBuffer.getChannelData(0);
                            const pcmData = new Int16Array(audioData.length);
                            for (let i = 0; i < audioData.length; i++) {
                                pcmData[i] = audioData[i] * 32767;
                            }
                            const audioBytes = new Uint8Array(pcmData.buffer);
                            const base64Audio = btoa(String.fromCharCode.apply(null, audioBytes));
                            socket.emit('audio_data', { audio: base64Audio });
                        }
                    };
                    
                    source.connect(processor);
                    processor.connect(audioContext.destination);
                    
                    socket.emit('start_smart_asr');
                    document.getElementById('results').innerHTML = '🎙️ 开始识别...';
                    
                } catch (err) {
                    alert('无法访问麦克风: ' + err.message);
                }
            }
            
            function stopASR() {
                isRecording = false;
                if (audioContext) {
                    audioContext.close();
                }
                socket.emit('stop_asr');
            }
        </script>
    </body>
    </html>
    """



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
resume_analyzer = ResumeAnalyzer()

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

@app.route('/resume-analysis')
@login_required
def resume_analysis_page():
    return render_template('resume_analysis.html')

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

@app.route('/api/resume/analyze-enhanced', methods=['POST'])
@login_required
def analyze_resume_enhanced():
    """增强版简历分析接口 """
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式'}), 400
        
        # 获取用户信息
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
        
        # 使用新的简历分析器进行完整分析
        analysis_result = resume_analyzer.analyze_resume_complete(text, username)
        
        if not analysis_result['success']:
            return jsonify({'error': analysis_result['error']}), 500
        
        # 返回分析结果
        return jsonify({
            'success': True,
            'message': '简历分析完成',
            'data': {
                'original_text': analysis_result['original_text'],
                'markdown_text': analysis_result['markdown_text'],
                'original_highlighted': analysis_result['original_highlighted'],
                'suggested_highlighted': analysis_result['suggested_highlighted'],
                'analysis_result': analysis_result['analysis_result'],
                'evaluation': analysis_result['evaluation'],
                'files': analysis_result['files']
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/resume/analyze-existing', methods=['POST'])
@login_required
def analyze_existing_resume():
    """分析已上传的简历"""
    try:
        data = request.get_json()
        resume_id = data.get('resume_id')
        
        if not resume_id:
            return jsonify({'error': '请提供简历ID'}), 400
        
        # 获取用户信息
        username = session['user']['username']
        
        # 获取简历信息
        resume = user_manager.get_resume(username, resume_id)
        if not resume:
            return jsonify({'error': '简历不存在'}), 404
        
        # 获取简历文本
        resume_text = resume.get('text', '')
        if not resume_text:
            return jsonify({'error': '简历内容为空'}), 400
        
        # 使用新的简历分析器进行完整分析
        analysis_result = resume_analyzer.analyze_resume_complete(resume_text, username)
        
        if not analysis_result['success']:
            return jsonify({'error': analysis_result['error']}), 500
        
        # 返回分析结果
        return jsonify({
            'success': True,
            'message': '简历分析完成',
            'data': {
                'original_text': analysis_result['original_text'],
                'markdown_text': analysis_result['markdown_text'],
                'original_highlighted': analysis_result['original_highlighted'],
                'suggested_highlighted': analysis_result['suggested_highlighted'],
                'analysis_result': analysis_result['analysis_result'],
                'evaluation': analysis_result['evaluation'],
                'files': analysis_result['files']
            }
        }), 200
    
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
        
        # 检查所有可能的分析文件
        files_to_check = [
            'interview_summary_report.json',  # 面试总结报告（新增）
            'latest_interview_result.json',   # 面试结果数据（新增）
            'facial_analysis_report.json',    # 微表情分析报告
            'voice_analysis_result.json',     # 语调分析报告
            'analysis_result.json',           # 其他分析结果
            'interview_config.json',          # 面试配置
            'interview_questions.json',       # 面试题目
            'QA.md'                          # 面试问答记录
        ]
        
        available_files = []
        file_data = {}
        
        for filename in files_to_check:
            file_path = os.path.join(user_folder, filename)
            if os.path.exists(file_path):
                available_files.append(filename)
                
                # 读取文件内容
                try:
                    if filename.endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_data[filename] = json.load(f)
                        print(f"✅ 成功读取文件: {filename}")
                    elif filename.endswith('.md'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_data[filename] = f.read()
                        print(f"✅ 成功读取文件: {filename}")
                except Exception as e:
                    print(f"❌ 读取文件 {filename} 失败: {e}")
        
        # 特别处理面试总结报告
        summary_data = file_data.get('interview_summary_report.json', {})
        
        # 特别处理面试结果数据
        result_data = file_data.get('latest_interview_result.json', {})
        
        # 特别处理面试配置数据
        config_data = file_data.get('interview_config.json', {})
        
        print(f"📁 用户文件夹: {user_folder}")
        print(f"📋 可用文件: {available_files}")
        print(f"📊 面试总结报告: {'✅' if summary_data else '❌'}")
        print(f"📈 面试结果数据: {'✅' if result_data else '❌'}")
        print(f"⚙️ 面试配置数据: {'✅' if config_data else '❌'}")
        
        return jsonify({
            'success': True,
            'available_files': available_files,
            'file_data': file_data,
            'summary_data': summary_data,
            'result_data': result_data,
            'config_data': config_data,
            'username': username
        })
        
    except Exception as e:
        print(f"❌ 获取面试结果数据失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取数据失败: {str(e)}'
        })

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

# ==================== TTS语音合成功能集成 ====================
# 在ASR功能基础上添加TTS支持，不影响现有功能



# 讯飞TTS配置
XUNFEI_TTS_CONFIG = {
    'appid': '2d597818',
    'api_secret': 'OWYxMzM1NmMzMjY4NDIwNTA0ZGNiZTg5',
    'api_key': '0548bfa3f54fc525cbd79b49c33c6001',
    'url': 'wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6',
    'vcn': 'x4_lingxiaoqi_oral'  # 聆小琪
}

# TTS连接存储
tts_connections = {}

class TTSWebSocketParam:
    """TTS WebSocket参数生成器"""
    
    def __init__(self, appid, api_key, api_secret, gpt_url):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.host = urlparse(gpt_url).netloc
        self.path = urlparse(gpt_url).path
        self.gpt_url = gpt_url

    def create_url(self):
        """生成带鉴权的WebSocket URL"""
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'), 
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        
        url = self.gpt_url + '?' + urlencode(v)
        return url

class TTSAgent:
    """TTS语音合成代理类"""
    
    def __init__(self, client_id):
        self.client_id = client_id
        self.audio_queue = queue.Queue()
        self.is_synthesizing = False
        self.ws = None
        self.total_audio_chunks = 0
        self.session_id = f"tts_{int(time.time())}_{client_id}"
        
    def start_synthesis(self, text):
        """开始语音合成"""
        if self.is_synthesizing:
            return False, "正在合成中，请稍候"
            
        if not text or not text.strip():
            return False, "文本不能为空"
            
        self.is_synthesizing = True
        self.total_audio_chunks = 0
        
        # 在新线程中启动WebSocket连接
        synthesis_thread = threading.Thread(
            target=self._synthesis_worker, 
            args=(text,)
        )
        synthesis_thread.daemon = True
        synthesis_thread.start()
        
        return True, "开始合成"
    
    def _synthesis_worker(self, text):
        """语音合成工作线程"""
        try:
            # 创建WebSocket参数
            ws_param = TTSWebSocketParam(
                XUNFEI_TTS_CONFIG['appid'],
                XUNFEI_TTS_CONFIG['api_key'], 
                XUNFEI_TTS_CONFIG['api_secret'],
                XUNFEI_TTS_CONFIG['url']
            )
            ws_url = ws_param.create_url()
            
            print(f"[{self.session_id}] 开始TTS合成: {text}")
            print(f"[{self.session_id}] TTS WebSocket URL: {ws_url}")
            
            # 创建WebSocket连接
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=self._on_message,
                on_error=self._on_error, 
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # 存储文本到WebSocket对象
            self.ws.synthesis_text = text
            self.ws.client_id = self.client_id
            self.ws.session_id = self.session_id
            self.ws.stream_handler = self
            
            # 启动WebSocket连接
            self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            
        except Exception as e:
            print(f"[{self.session_id}] TTS合成出错: {e}")
            self._emit_error(f"语音合成失败: {str(e)}")
        finally:
            self.is_synthesizing = False
    
    def _on_message(self, ws, message):
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            code = data['header']['code']
            
            if code != 0:
                error_msg = data['header'].get('message', '未知错误')
                print(f"[{self.session_id}] TTS API错误: {error_msg}")
                self._emit_error(f"TTS服务错误: {error_msg}")
                return
                
            status = data['header']['status']
            payload = data.get('payload')
            
            # 处理音频数据
            if payload and payload != "null":
                audio_info = payload.get('audio')
                if audio_info and 'audio' in audio_info:
                    audio_data = audio_info['audio']
                    self.total_audio_chunks += 1
                    
                    print(f"[{self.session_id}] 收到TTS音频块 #{self.total_audio_chunks}, 长度: {len(audio_data)}")
                    
                    # 实时发送音频数据到前端
                    self._emit_audio_chunk(audio_data, self.total_audio_chunks)
            
            # 检查合成状态
            if status == 2:  # 合成完成
                print(f"[{self.session_id}] TTS合成完成，共 {self.total_audio_chunks} 个音频块")
                self._emit_synthesis_complete()
                ws.close()
                
        except Exception as e:
            print(f"[{self.session_id}] 处理TTS消息出错: {e}")
            self._emit_error(f"处理音频数据失败: {str(e)}")
    
    def _on_error(self, ws, error):
        """WebSocket错误处理"""
        print(f"[{self.session_id}] TTS WebSocket错误: {error}")
        self._emit_error(f"连接错误: {str(error)}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket关闭处理"""
        print(f"[{self.session_id}] TTS WebSocket连接已关闭")
        self.is_synthesizing = False
    
    def _on_open(self, ws):
        """WebSocket连接建立"""
        print(f"[{self.session_id}] TTS WebSocket连接已建立")
        thread.start_new_thread(self._send_synthesis_request, (ws,))
    
    def _send_synthesis_request(self, ws):
        """发送TTS合成请求"""
        try:
            # 构建请求体
            request_body = {
                "header": {
                    "app_id": XUNFEI_TTS_CONFIG['appid'],
                    "status": 2
                },
                "parameter": {
                    "oral": {
                        "oral_level": "mid"
                    },
                    "tts": {
                        "vcn": XUNFEI_TTS_CONFIG['vcn'],
                        "speed": 50,
                        "volume": 80,
                        "pitch": 50,
                        "bgs": 0,
                        "reg": 0,
                        "rdn": 0,
                        "rhy": 0,
                        "audio": {
                            "encoding": "raw",  # WAV格式 (PCM)
                            "sample_rate": 24000,
                            "channels": 1,
                            "bit_depth": 16,
                            "frame_size": 0
                        }
                    }
                },
                "payload": {
                    "text": {
                        "encoding": "utf8",
                        "compress": "raw",
                        "format": "plain",
                        "status": 2,
                        "seq": 0,
                        "text": str(base64.b64encode(ws.synthesis_text.encode('utf-8')), 'utf8')
                    }
                }
            }
            
            print(f"[{ws.session_id}] 发送TTS合成请求: {ws.synthesis_text}")
            ws.send(json.dumps(request_body))
            
        except Exception as e:
            print(f"[{ws.session_id}] 发送TTS请求失败: {e}")
            self._emit_error(f"发送请求失败: {str(e)}")
    
    def _emit_audio_chunk(self, audio_data, chunk_number):
        """发送音频块到前端"""
        socketio.emit('tts_audio_chunk', {
            'session_id': self.session_id,
            'audio_data': audio_data,
            'chunk_number': chunk_number,
            'timestamp': time.time()
        }, room=self.client_id)
    
    def _emit_synthesis_complete(self):
        """发送合成完成消息"""
        socketio.emit('tts_synthesis_complete', {
            'session_id': self.session_id,
            'total_chunks': self.total_audio_chunks,
            'timestamp': time.time()
        }, room=self.client_id)
    
    def _emit_error(self, error_message):
        """发送错误消息"""
        socketio.emit('tts_synthesis_error', {
            'session_id': self.session_id,
            'error': error_message,
            'timestamp': time.time()
        }, room=self.client_id)
        self.is_synthesizing = False

# ==================== TTS SocketIO事件处理 ====================

@socketio.on('tts_synthesize')
def handle_tts_synthesize(data):
    """处理TTS合成请求"""
    client_id = request.sid
    text = data.get('text', '').strip()
    print("🎤 TTS合成请求"+text)
    
    if not text:
        socketio.emit('tts_synthesis_error', {
            'error': '文本不能为空',
            'timestamp': time.time()
        }, room=client_id)
        return
    
    # 获取或创建TTS代理
    if client_id not in tts_connections:
        tts_connections[client_id] = TTSAgent(client_id)
    
    tts_agent = tts_connections[client_id]
    
    # 开始合成
    success, message = tts_agent.start_synthesis(text)
    
    if success:
        socketio.emit('tts_synthesis_started', {
            'session_id': tts_agent.session_id,
            'message': message,
            'timestamp': time.time()
        }, room=client_id)
    else:
        socketio.emit('tts_synthesis_error', {
            'error': message,
            'timestamp': time.time()
        }, room=client_id)

# ==================== TTS HTTP路由 ====================

@app.route('/api/tts/status')
def tts_status():
    """TTS服务状态检查"""
    return jsonify({
        'success': True,
        'message': 'TTS服务运行正常',
        'active_connections': len(tts_connections),
        'config': {
            'app_id': XUNFEI_TTS_CONFIG['appid'],
            'service': '科大讯飞语音合成',
            'voice': '聆小琪 (x4_lingxiaoqi_oral)'
        }
    })

@app.route('/api/tts/synthesize', methods=['POST'])
def api_tts_synthesize():
    """TTS合成API接口"""
    try:
        #打印日志
        print("🎤 TTS合成API接口")
        data = request.get_json()
        text = data.get('text', '').strip()
        client_id = data.get('client_id', 'default')
        
        if not text:
            return jsonify({'success': False, 'message': '文本不能为空'})
        
        # 获取或创建TTS代理
        if client_id not in tts_connections:
            tts_connections[client_id] = TTSAgent(client_id)
        
        tts_agent = tts_connections[client_id]
        
        # 开始合成
        success, message = tts_agent.start_synthesis(text)
        
        return jsonify({
            'success': success,
            'message': message,
            'session_id': tts_agent.session_id if success else None
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'})

@app.route('/api/tts/test')
def tts_test():
    """TTS测试页面"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>TTS语音合成测试</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .btn { padding: 10px 20px; margin: 10px; border: none; border-radius: 5px; cursor: pointer; }
            .btn-primary { background: #007bff; color: white; }
            .btn-success { background: #28a745; color: white; }
            #results { border: 1px solid #ccc; padding: 15px; margin: 20px 0; min-height: 200px; }
            .result-item { margin: 5px 0; padding: 5px; background: #f8f9fa; border-radius: 3px; }
            textarea { width: 100%; padding: 10px; margin: 10px 0; min-height: 100px; }
            audio { width: 100%; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>🎤 TTS语音合成测试</h1>
        <p><strong>配音员：</strong>聆小琪 (x4_lingxiaoqi_oral)</p>
        <textarea id="textInput" placeholder="请输入要合成的文本...">你好，我是AI语音助手，很高兴为您服务！</textarea>
        <div>
            <button class="btn btn-primary" onclick="startTTS()">开始语音合成</button>
            <button class="btn btn-success" onclick="downloadAudio()" id="downloadBtn" style="display:none;">下载音频</button>
        </div>
        <div id="status">状态：未连接</div>
        <audio id="audioPlayer" controls style="display:none;"></audio>
        <div id="results">等待合成...</div>
        
        <script>
            const socket = io();
            let audioChunks = [];
            let currentSessionId = null;
            let wavFile = null;
            
            // WAV文件头生成工具
            function createWAVHeader(dataLength, sampleRate = 24000, channels = 1, bitsPerSample = 16) {
                const buffer = new ArrayBuffer(44);
                const view = new DataView(buffer);
                
                view.setUint32(0, 0x52494646, false); // "RIFF"
                view.setUint32(4, 36 + dataLength, true); // File size - 8
                view.setUint32(8, 0x57415645, false); // "WAVE"
                view.setUint32(12, 0x666d7420, false); // "fmt "
                view.setUint32(16, 16, true); // Subchunk1Size
                view.setUint16(20, 1, true); // AudioFormat
                view.setUint16(22, channels, true); // NumChannels
                view.setUint32(24, sampleRate, true); // SampleRate
                view.setUint32(28, sampleRate * channels * bitsPerSample / 8, true); // ByteRate
                view.setUint16(32, channels * bitsPerSample / 8, true); // BlockAlign
                view.setUint16(34, bitsPerSample, true); // BitsPerSample
                view.setUint32(36, 0x64617461, false); // "data"
                view.setUint32(40, dataLength, true); // Subchunk2Size
                
                return new Uint8Array(buffer);
            }
            
            function createWAVFile(pcmData) {
                const wavHeader = createWAVHeader(pcmData.length);
                const wavFile = new Uint8Array(wavHeader.length + pcmData.length);
                wavFile.set(wavHeader, 0);
                wavFile.set(pcmData, wavHeader.length);
                return wavFile;
            }
            
            socket.on('connect', () => {
                document.getElementById('status').textContent = '状态：已连接';
            });
            
            socket.on('tts_synthesis_started', (data) => {
                document.getElementById('status').textContent = '状态：开始合成...';
                currentSessionId = data.session_id;
                audioChunks = [];
                const results = document.getElementById('results');
                results.innerHTML = '🎵 开始合成音频...';
            });
            
            socket.on('tts_audio_chunk', (data) => {
                if (data.session_id === currentSessionId) {
                    audioChunks.push(data);
                    const results = document.getElementById('results');
                    const item = document.createElement('div');
                    item.className = 'result-item';
                    item.textContent = `🎵 收到音频块 #${data.chunk_number}`;
                    results.appendChild(item);
                    results.scrollTop = results.scrollHeight;
                }
            });
            
            socket.on('tts_synthesis_complete', (data) => {
                if (data.session_id === currentSessionId) {
                    document.getElementById('status').textContent = '状态：合成完成';
                    const results = document.getElementById('results');
                    const item = document.createElement('div');
                    item.className = 'result-item';
                    item.style.background = '#d4edda';
                    item.style.fontWeight = 'bold';
                    item.textContent = `✅ 合成完成！共${data.total_chunks}个音频块`;
                    results.appendChild(item);
                    
                    // 生成WAV文件
                    if (audioChunks.length > 0) {
                        generateWAVFile();
                    }
                }
            });
            
            socket.on('tts_synthesis_error', (data) => {
                document.getElementById('status').textContent = '状态：合成失败';
                const results = document.getElementById('results');
                const item = document.createElement('div');
                item.className = 'result-item';
                item.style.background = '#f8d7da';
                item.textContent = '❌ 错误: ' + data.error;
                results.appendChild(item);
            });
            
            function generateWAVFile() {
                try {
                    // 合并所有PCM音频块
                    const allPCMData = audioChunks.map(chunk => {
                        const binaryString = atob(chunk.audio_data);
                        const bytes = new Uint8Array(binaryString.length);
                        for (let i = 0; i < binaryString.length; i++) {
                            bytes[i] = binaryString.charCodeAt(i);
                        }
                        return bytes;
                    });
                    
                    // 计算总长度并合并PCM数据
                    const totalLength = allPCMData.reduce((sum, arr) => sum + arr.length, 0);
                    const mergedPCM = new Uint8Array(totalLength);
                    
                    let offset = 0;
                    for (const data of allPCMData) {
                        mergedPCM.set(data, offset);
                        offset += data.length;
                    }
                    
                    // 创建WAV文件
                    wavFile = createWAVFile(mergedPCM);
                    const wavBlob = new Blob([wavFile], { type: 'audio/wav' });
                    const url = URL.createObjectURL(wavBlob);
                    
                    // 设置音频播放器
                    const audioPlayer = document.getElementById('audioPlayer');
                    audioPlayer.src = url;
                    audioPlayer.style.display = 'block';
                    
                    // 显示下载按钮
                    document.getElementById('downloadBtn').style.display = 'inline-block';
                    
                    // 自动播放
                    audioPlayer.play();
                    
                    console.log(`WAV文件已生成 (${(wavFile.length / 1024).toFixed(1)} KB)`);
                    
                } catch (error) {
                    console.error('生成WAV文件失败:', error);
                }
            }
            
            function startTTS() {
                const text = document.getElementById('textInput').value.trim();
                if (!text) {
                    alert('请输入要合成的文本');
                    return;
                }
                socket.emit('tts_synthesize', { text: text });
            }
            
            function downloadAudio() {
                if (!wavFile) {
                    alert('没有可下载的音频文件');
                    return;
                }
                
                const blob = new Blob([wavFile], { type: 'audio/wav' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                
                const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
                const filename = `tts_audio_${timestamp}.wav`;
                
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                
                URL.revokeObjectURL(url);
            }
        </script>
    </body>
    </html>
    """

@app.route('/api/interview/save-results', methods=['POST'])
@login_required
def save_interview_results():
    """保存面试结果到QA.md文件"""
    try:
        data = request.get_json()
        username = data.get('username')
        qa_content = data.get('qa_content')
        interview_data = data.get('interview_data', [])
        config = data.get('config', {})
        
        if not username or not qa_content:
            return jsonify({'success': False, 'message': '缺少必要的参数'})
        
        # 构建用户目录路径
        user_dir = os.path.join('uploads', username)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        # QA.md文件路径
        qa_file_path = os.path.join(user_dir, 'QA.md')
        
        # 追加内容到QA.md文件
        with open(qa_file_path, 'a', encoding='utf-8') as f:
            f.write(qa_content)
        
        # 保存详细的面试数据（JSON格式）
        interview_result_path = os.path.join(user_dir, 'latest_interview_result.json')
        interview_result = {
            'timestamp': datetime.now().isoformat(),
            'interview_data': interview_data,
            'config': config,
            'status': 'completed'
        }
        
        with open(interview_result_path, 'w', encoding='utf-8') as f:
            json.dump(interview_result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 用户 {username} 的面试结果已保存")
        
        return jsonify({
            'success': True,
            'message': '面试结果保存成功',
            'qa_file': qa_file_path,
            'result_file': interview_result_path
        })
        
    except Exception as e:
        print(f"❌ 保存面试结果失败: {str(e)}")
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'})

@app.route('/api/interview/analyze-reverse-question', methods=['POST'])
@login_required
def analyze_reverse_question():
    """使用星火大模型分析反问环节的用户问题"""
    try:
        print("🔍 开始处理反问分析请求...")
        
        # 检查请求数据
        if not request.is_json:
            print("❌ 请求不是JSON格式")
            return jsonify({'success': False, 'message': '请求格式错误，需要JSON数据'})
        
        data = request.get_json()
        print(f"📝 收到请求数据: {data}")
        
        prompt = data.get('prompt')
        user_question = data.get('user_question')
        interview_config = data.get('interview_config', {})
        
        print(f"🎯 用户问题: {user_question}")
        print(f"📋 面试配置: {interview_config}")
        
        if not prompt or not user_question:
            print("❌ 缺少必要参数")
            return jsonify({'success': False, 'message': '缺少必要的参数: prompt或user_question'})
        
        # 星火大模型配置
        try:
            from openai import OpenAI
            import json
            print("✅ 成功导入OpenAI和json模块")
        except ImportError as e:
            print(f"❌ 导入模块失败: {e}")
            return jsonify({'success': False, 'message': f'模块导入失败: {str(e)}'})
        
        try:
            client = OpenAI(
                api_key='QcGCOyVichfHetzkUDeM:AUoiqAJtarlstnrJMcTI',
                base_url='https://spark-api-open.xf-yun.com/v1/'
            )
            print("✅ 星火大模型客户端初始化成功")
        except Exception as e:
            print(f"❌ 星火大模型客户端初始化失败: {e}")
            return jsonify({'success': False, 'message': f'客户端初始化失败: {str(e)}'})
        
        print(f"🤖 准备调用星火大模型分析用户问题: {user_question}")
        print(f"📝 提示词长度: {len(prompt)} 字符")
        
        # 调用星火大模型
        try:
            response = client.chat.completions.create(
                model='generalv3.5',
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            print("✅ 星火大模型API调用成功")
        except Exception as e:
            print(f"❌ 星火大模型API调用失败: {e}")
            return jsonify({
                'success': False, 
                'message': f'AI模型调用失败: {str(e)}',
                'analysis': {
                    "want_to_stop": False,
                    "answer": "抱歉，AI服务暂时不可用，请稍后再试。",
                    "question_type": "服务错误"
                }
            })
        
        try:
            result_text = response.choices[0].message.content
            print(f"🎯 AI原始回复长度: {len(result_text)} 字符")
            print(f"📄 AI原始回复内容: {result_text[:200]}...")  # 只显示前200字符
        except Exception as e:
            print(f"❌ 获取AI回复内容失败: {e}")
            return jsonify({
                'success': False, 
                'message': f'获取AI回复失败: {str(e)}',
                'analysis': {
                    "want_to_stop": False,
                    "answer": "抱歉，无法获取AI回复。",
                    "question_type": "解析错误"
                }
            })
        
        # 清理markdown代码块标记
        print("🧹 开始清理AI回复格式...")
        original_text = result_text
        result_text = result_text.strip()
        
        if result_text.startswith('```json'):
            result_text = result_text[7:]  # 去除 ```json
            print("🔧 移除了```json标记")
        if result_text.startswith('```'):
            result_text = result_text[3:]   # 去除 ```
            print("🔧 移除了```标记")
        if result_text.endswith('```'):
            result_text = result_text[:-3]  # 去除结尾的 ```
            print("🔧 移除了结尾```标记")
        
        result_text = result_text.strip()
        print(f"🧽 清理后的文本长度: {len(result_text)} 字符")
        print(f"📝 清理后的文本: {result_text[:300]}...")  # 显示前300字符
        
        # 尝试解析JSON
        print("🔍 开始解析JSON...")
        try:
            analysis_result = json.loads(result_text)
            print("✅ JSON解析成功")
            print(f"📊 解析结果: {analysis_result}")
            
            # 验证必要字段
            required_fields = ["want_to_stop", "answer", "question_type"]
            missing_fields = [field for field in required_fields if field not in analysis_result]
            
            if missing_fields:
                print(f"⚠️ 缺少必要字段: {missing_fields}")
                # 补充缺失字段
                if "want_to_stop" not in analysis_result:
                    analysis_result["want_to_stop"] = False
                if "answer" not in analysis_result:
                    analysis_result["answer"] = result_text
                if "question_type" not in analysis_result:
                    analysis_result["question_type"] = "其他"
                print(f"🔧 已补充缺失字段: {analysis_result}")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"🔍 原始文本: '{original_text}'")
            print(f"🔍 清理后文本: '{result_text}'")
            # 如果不是有效JSON，创建默认响应
            analysis_result = {
                "want_to_stop": False,
                "answer": result_text if result_text else "抱歉，我暂时无法理解您的问题，请您再详细说明一下。",
                "question_type": "JSON解析失败"
            }
            print(f"🔧 使用默认响应: {analysis_result}")
        except Exception as e:
            print(f"❌ JSON处理时发生未知错误: {e}")
            analysis_result = {
                "want_to_stop": False,
                "answer": "抱歉，处理您的问题时发生错误。",
                "question_type": "处理错误"
            }
        
        print(f"✅ 星火大模型分析完成: {analysis_result}")
        
        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'raw_response': result_text,
            'debug_info': {
                'original_length': len(original_text),
                'cleaned_length': len(result_text),
                'user_question': user_question
            }
        })
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ 反问分析处理失败: {str(e)}")
        print(f"📋 错误详情:\n{error_traceback}")
        
        return jsonify({
            'success': False, 
            'message': f'分析失败: {str(e)}',
            'error_type': type(e).__name__,
            'analysis': {
                "want_to_stop": False,
                "answer": "抱歉，系统暂时无法处理您的问题，请稍后再试。",
                "question_type": "系统错误"
            }
        })

@app.route('/api/interview/run-summary', methods=['POST'])
@login_required
def run_interview_summary():
    """运行面试总结分析"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'success': False, 'message': '缺少用户名参数'})
        
        print(f"🔍 开始为用户 {username} 运行面试总结分析...")
        
        # 检查用户目录和QA.md文件
        user_folder = os.path.join('uploads', username)
        if not os.path.exists(user_folder):
            return jsonify({'success': False, 'message': f'用户目录不存在: {user_folder}'})
        
        qa_file_path = os.path.join(user_folder, 'QA.md')
        if not os.path.exists(qa_file_path):
            return jsonify({'success': False, 'message': f'面试记录文件不存在: {qa_file_path}'})
        
        print(f"✅ 找到面试记录文件: {qa_file_path}")
        
        # 导入面试总结模块
        current_dir = os.path.dirname(os.path.abspath(__file__))
        summary_module_path = os.path.join(current_dir, 'modules', 'Mock_interview')
        
        if summary_module_path not in sys.path:
            sys.path.insert(0, summary_module_path)
        
        try:
            from modules.Mock_interview.interview_summary import InterviewSummary
            print("✅ 成功导入面试总结模块")
        except ImportError as e:
            print(f"❌ 导入面试总结模块失败: {e}")
            return jsonify({'success': False, 'message': f'导入模块失败: {str(e)}'})
        
        # 创建面试总结实例
        summary = InterviewSummary()
        
        # 修改summary实例的文件路径方法，使其从用户目录读取
        def parse_qa_md_from_user_folder():
            """从用户目录解析QA.md文件"""
            try:
                with open(qa_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                sections = {}
                
                # 使用原有的解析逻辑
                import re
                
                # 解析自我介绍
                self_intro_pattern = r'<!-- START: 自我介绍 -->(.*?)<!-- END: 自我介绍 -->'
                self_intro_match = re.search(self_intro_pattern, content, re.DOTALL)
                if self_intro_match:
                    sections["自我介绍"] = self_intro_match.group(1).strip()
                
                # 解析简历深挖（多题模式）
                resume_pattern = r'<!-- START: 简历深挖.*? -->(.*?)<!-- END: 简历深挖.*? -->'
                resume_matches = re.findall(resume_pattern, content, re.DOTALL)
                if resume_matches:
                    sections["简历深挖"] = '\n\n'.join([match.strip() for match in resume_matches])
                
                # 解析能力评估（多题模式）
                ability_pattern = r'<!-- START: 能力评估.*? -->(.*?)<!-- END: 能力评估.*? -->'
                ability_matches = re.findall(ability_pattern, content, re.DOTALL)
                if ability_matches:
                    sections["能力评估"] = '\n\n'.join([match.strip() for match in ability_matches])
                
                # 解析岗位匹配度（多题模式）
                position_pattern = r'<!-- START: 岗位匹配度.*? -->(.*?)<!-- END: 岗位匹配度.*? -->'
                position_matches = re.findall(position_pattern, content, re.DOTALL)
                if position_matches:
                    sections["岗位匹配度"] = '\n\n'.join([match.strip() for match in position_matches])
                
                # 解析专业能力测试（多题模式）
                professional_pattern = r'<!-- START: 专业能力测试.*? -->(.*?)<!-- END: 专业能力测试.*? -->'
                professional_matches = re.findall(professional_pattern, content, re.DOTALL)
                if professional_matches:
                    sections["专业能力测试"] = '\n\n'.join([match.strip() for match in professional_matches])
                
                # 解析反问环节
                reverse_pattern = r'<!-- START: 反问环节 -->(.*?)<!-- END: 反问环节 -->'
                reverse_match = re.search(reverse_pattern, content, re.DOTALL)
                if reverse_match:
                    sections["反问环节"] = reverse_match.group(1).strip()
                
                print(f"✅ 解析用户QA.md成功，找到 {len(sections)} 个板块:")
                for section in sections.keys():
                    print(f"  📋 {section}")
                
                return sections
                
            except Exception as e:
                print(f"❌ 解析用户QA.md失败: {e}")
                return {}
        
        # 替换summary实例的解析方法
        summary.parse_qa_md = parse_qa_md_from_user_folder
        
        # 修改保存方法，确保保存到用户目录
        original_save_method = summary.save_summary_report
        def save_summary_report_to_user_folder(report_data, filename="interview_summary_report.json", current_username=None):
            """保存总结报告到用户目录"""
            try:
                # 强制使用用户目录
                filepath = os.path.join(user_folder, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
                print(f"✅ 面试总结报告已保存到 {filepath}")
                print(f"📊 报告包含 {len(report_data.get('section_evaluations', {}))} 个板块评估")
                print(f"🎯 最终得分: {report_data.get('overall_assessment', {}).get('final_score', 0)} 分")
                print(f"📈 评级: {report_data.get('overall_assessment', {}).get('grade', '未知')}")
                return True
            except Exception as e:
                print(f"❌ 保存报告失败: {e}")
                return False
        
        # 替换保存方法
        summary.save_summary_report = save_summary_report_to_user_folder
        
        # 运行面试总结（使用同步方式）
        import asyncio
        
        # 在新的事件循环中运行异步方法
        async def run_summary_analysis():
            try:
                # 1. 解析QA.md文件
                print("📋 步骤1: 解析面试记录文件...")
                sections_content = summary.parse_qa_md()
                
                if not sections_content:
                    return False, "没有找到可评估的面试内容"
                
                # 2. 并行评估各板块
                print(f"🎯 步骤2: 并行评估 {len(sections_content)} 个面试板块...")
                evaluations = await summary.evaluate_all_sections(sections_content)
                
                if not evaluations:
                    return False, "没有成功评估的板块"
                
                # 3. 计算最终得分
                print(f"🧮 步骤3: 计算加权最终得分...")
                final_score, total_weight = summary.calculate_final_score(evaluations)
                
                # 4. 生成总结报告
                print(f"📝 步骤4: 生成面试总结报告...")
                report_data = summary.generate_summary_report(evaluations, final_score, total_weight)
                
                # 5. 保存报告
                success = summary.save_summary_report(report_data)
                
                if success:
                    return True, f"面试总结分析完成，最终得分: {final_score:.2f}/100"
                else:
                    return False, "报告生成成功，但保存失败"
                    
            except Exception as e:
                return False, f"分析过程出错: {str(e)}"
        
        # 创建新的事件循环来运行异步代码
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success, message = loop.run_until_complete(run_summary_analysis())
        finally:
            loop.close()
        
        if success:
            print(f"✅ 用户 {username} 的面试总结分析完成")
            return jsonify({
                'success': True,
                'message': message,
                'report_file': 'interview_summary_report.json',
                'user_folder': user_folder
            })
        else:
            print(f"❌ 用户 {username} 的面试总结分析失败: {message}")
            return jsonify({
                'success': False,
                'message': message
            })
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ 运行面试总结分析时发生错误: {str(e)}")
        print(f"📋 错误详情:\n{error_traceback}")
        
        return jsonify({
            'success': False,
            'message': f'分析失败: {str(e)}',
            'error_type': type(e).__name__
        })

# ==================== 修改主程序启动方式 ====================

if __name__ == '__main__':
    # 获取Render分配的端口，如果没有则使用默认端口5000
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    print("=" * 60)
    print("🚀 AI面试系统启动中...")
    print("📝 已集成ASR语音识别功能")
    print("🎤 已集成TTS语音合成功能")
    print("=" * 60)
    print(f"🌐 主系统: http://0.0.0.0:{port}")
    print(f"🎙️ ASR测试: http://0.0.0.0:{port}/api/asr/test")
    print(f"🎵 TTS测试: http://0.0.0.0:{port}/api/tts/test")
    print(f"🤖 Live2D: http://0.0.0.0:{port}/live2d")
    print("=" * 60)
    
    # 使用SocketIO运行，同时支持原有功能、ASR功能和TTS功能
    socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode, use_reloader=False)