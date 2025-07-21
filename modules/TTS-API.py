# coding: utf-8
"""
TTS-API: 实时语音合成流式传输系统
基于讯飞语音合成API，提供WebSocket实时音频流服务
配音：聆小琪 (x4_lingxiaoqi_oral)
"""

import json
import base64
import hashlib
import hmac
import threading
import queue
import time
from datetime import datetime
from urllib.parse import urlparse, urlencode
from wsgiref.handlers import format_date_time
from time import mktime
import websocket
import ssl
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
import _thread as thread

# Flask应用初始化
app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'tts_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 讯飞TTS配置
TTS_CONFIG = {
    'appid': 'daa9d5d9',
    'api_secret': 'YTBkNzA5MGVlNzYzNDVkMDk2MzcwOTIy',
    'api_key': 'c52e142d8749090d0caa6c0fab03d2d1',
    'url': 'wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6',
    'vcn': 'x4_lingxiaoqi_oral'  # 聆小琪
}

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

class RealtimeTTSStream:
    """实时TTS音频流处理器"""
    
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
                TTS_CONFIG['appid'],
                TTS_CONFIG['api_key'], 
                TTS_CONFIG['api_secret'],
                TTS_CONFIG['url']
            )
            ws_url = ws_param.create_url()
            
            print(f"[{self.session_id}] 开始合成: {text}")
            print(f"[{self.session_id}] WebSocket URL: {ws_url}")
            
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
            print(f"[{self.session_id}] 合成出错: {e}")
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
                    
                    print(f"[{self.session_id}] 收到音频块 #{self.total_audio_chunks}, 长度: {len(audio_data)}")
                    
                    # 实时发送音频数据到前端
                    self._emit_audio_chunk(audio_data, self.total_audio_chunks)
            
            # 检查合成状态
            if status == 2:  # 合成完成
                print(f"[{self.session_id}] 合成完成，共 {self.total_audio_chunks} 个音频块")
                self._emit_synthesis_complete()
                ws.close()
                
        except Exception as e:
            print(f"[{self.session_id}] 处理消息出错: {e}")
            self._emit_error(f"处理音频数据失败: {str(e)}")
    
    def _on_error(self, ws, error):
        """WebSocket错误处理"""
        print(f"[{self.session_id}] WebSocket错误: {error}")
        self._emit_error(f"连接错误: {str(error)}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket关闭处理"""
        print(f"[{self.session_id}] WebSocket连接已关闭")
        self.is_synthesizing = False
    
    def _on_open(self, ws):
        """WebSocket连接建立"""
        print(f"[{self.session_id}] WebSocket连接已建立")
        thread.start_new_thread(self._send_synthesis_request, (ws,))
    
    def _send_synthesis_request(self, ws):
        """发送TTS合成请求"""
        try:
            # 构建请求体
            request_body = {
                "header": {
                    "app_id": TTS_CONFIG['appid'],
                    "status": 2
                },
                "parameter": {
                    "oral": {
                        "oral_level": "mid"
                    },
                    "tts": {
                        "vcn": TTS_CONFIG['vcn'],
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
            
            print(f"[{ws.session_id}] 发送合成请求: {ws.synthesis_text}")
            ws.send(json.dumps(request_body))
            
        except Exception as e:
            print(f"[{ws.session_id}] 发送请求失败: {e}")
            self._emit_error(f"发送请求失败: {str(e)}")
    
    def _emit_audio_chunk(self, audio_data, chunk_number):
        """发送音频块到前端"""
        socketio.emit('audio_chunk', {
            'session_id': self.session_id,
            'audio_data': audio_data,
            'chunk_number': chunk_number,
            'timestamp': time.time()
        }, room=self.client_id)
    
    def _emit_synthesis_complete(self):
        """发送合成完成消息"""
        socketio.emit('synthesis_complete', {
            'session_id': self.session_id,
            'total_chunks': self.total_audio_chunks,
            'timestamp': time.time()
        }, room=self.client_id)
    
    def _emit_error(self, error_message):
        """发送错误消息"""
        socketio.emit('synthesis_error', {
            'session_id': self.session_id,
            'error': error_message,
            'timestamp': time.time()
        }, room=self.client_id)
        self.is_synthesizing = False

# 全局TTS流处理器管理
tts_streams = {}

@app.route('/')
def index():
    """主页面"""
    return app.send_static_file('index.html')

@app.route('/api/tts/synthesize', methods=['POST'])
def api_synthesize():
    """TTS合成API接口"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        client_id = data.get('client_id', 'default')
        
        if not text:
            return jsonify({'success': False, 'message': '文本不能为空'})
        
        # 获取或创建TTS流处理器
        if client_id not in tts_streams:
            tts_streams[client_id] = RealtimeTTSStream(client_id)
        
        tts_stream = tts_streams[client_id]
        
        # 开始合成
        success, message = tts_stream.start_synthesis(text)
        
        return jsonify({
            'success': success,
            'message': message,
            'session_id': tts_stream.session_id if success else None
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'})

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    client_id = request.sid
    print(f"客户端连接: {client_id}")
    emit('connected', {'client_id': client_id})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    client_id = request.sid
    print(f"客户端断开: {client_id}")
    
    # 清理对应的TTS流处理器
    if client_id in tts_streams:
        del tts_streams[client_id]

@socketio.on('join_room')
def handle_join_room(data):
    """客户端加入房间"""
    client_id = data.get('client_id', request.sid)
    print(f"客户端 {request.sid} 加入房间: {client_id}")

# 前端WAV处理工具函数
WAV_UTILS_JS = '''
// WAV文件头生成工具
function createWAVHeader(dataLength, sampleRate = 24000, channels = 1, bitsPerSample = 16) {
    const buffer = new ArrayBuffer(44);
    const view = new DataView(buffer);
    
    // RIFF chunk descriptor
    view.setUint32(0, 0x52494646, false); // "RIFF"
    view.setUint32(4, 36 + dataLength, true); // File size - 8
    view.setUint32(8, 0x57415645, false); // "WAVE"
    
    // fmt sub-chunk
    view.setUint32(12, 0x666d7420, false); // "fmt "
    view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
    view.setUint16(20, 1, true); // AudioFormat (1 for PCM)
    view.setUint16(22, channels, true); // NumChannels
    view.setUint32(24, sampleRate, true); // SampleRate
    view.setUint32(28, sampleRate * channels * bitsPerSample / 8, true); // ByteRate
    view.setUint16(32, channels * bitsPerSample / 8, true); // BlockAlign
    view.setUint16(34, bitsPerSample, true); // BitsPerSample
    
    // data sub-chunk
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
'''

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>语音合成系统 (WAV)</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            background: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 600px;
            width: 90%;
            backdrop-filter: blur(10px);
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 0.5rem;
            font-size: 2rem;
        }
        
        .header p {
            color: #666;
            font-size: 1rem;
        }
        
        .voice-info {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            text-align: center;
            border-left: 4px solid #007bff;
        }
        
        .format-info {
            background: #e7f3ff;
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            text-align: center;
            border-left: 4px solid #0066cc;
            font-size: 0.9rem;
        }
        
        .input-group {
            margin-bottom: 1.5rem;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        
        .text-input {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1rem;
            resize: vertical;
            min-height: 120px;
            transition: border-color 0.3s ease;
        }
        
        .text-input:focus {
            outline: none;
            border-color: #007bff;
        }
        
        .button-group {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        
        .btn {
            padding: 1rem 2rem;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 0 0.5rem;
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #007bff, #0056b3);
            color: white;
        }
        
        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,123,255,0.4);
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-success {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .status-panel {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }
        
        .status-item:last-child {
            margin-bottom: 0;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e1e5e9;
            border-radius: 4px;
            overflow: hidden;
            margin: 1rem 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(45deg, #28a745, #20c997);
            width: 0%;
            transition: width 0.3s ease;
        }
        
        .audio-player {
            width: 100%;
            margin-top: 1rem;
        }
        
        .download-section {
            text-align: center;
            margin-top: 1rem;
        }
        
        .log-panel {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }
        
        .log-entry {
            margin-bottom: 0.5rem;
            padding: 0.25rem;
            border-radius: 4px;
        }
        
        .log-info {
            color: #007bff;
        }
        
        .log-success {
            background: #d4edda;
            color: #155724;
        }
        
        .log-error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .hidden {
            display: none;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .synthesizing {
            animation: pulse 1.5s infinite;
        }
        
        .auto-play-notification {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            text-align: center;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎤 语音合成系统 (WAV)</h1>
            <p>基于讯飞语音合成API，生成高质量WAV音频</p>
        </div>
        
        <div class="voice-info">
            <strong>🎭 配音员：聆小琪 (x4_lingxiaoqi_oral)</strong>
        </div>
        
        <div class="format-info">
            <strong>🎵 音频格式：WAV (PCM) | 24kHz | 16-bit | 单声道</strong>
        </div>
        
        <div class="auto-play-notification">
            💡 音频将在合成完成后自动播放，请确保已允许浏览器自动播放音频
        </div>
        
        <div class="input-group">
            <label for="textInput">📝 请输入要合成的文本：</label>
            <textarea 
                id="textInput" 
                class="text-input" 
                placeholder="在这里输入您想要转换为语音的文字..."
                maxlength="500"
            ></textarea>
        </div>
        
        <div class="button-group">
            <button id="synthesizeBtn" class="btn btn-primary">
                🚀 开始合成
            </button>
            <button id="stopBtn" class="btn btn-secondary" disabled>
                ⏹️ 停止播放
            </button>
        </div>
        
        <div class="status-panel">
            <div class="status-item">
                <span>连接状态：</span>
                <span id="connectionStatus">🔴 未连接</span>
            </div>
            <div class="status-item">
                <span>合成状态：</span>
                <span id="synthesisStatus">⏸️ 待机中</span>
            </div>
            <div class="status-item">
                <span>音频块数：</span>
                <span id="audioChunks">0</span>
            </div>
        </div>
        
        <div class="progress-bar">
            <div id="progressFill" class="progress-fill"></div>
        </div>
        
        <audio id="audioPlayer" class="audio-player" controls style="display: none;"></audio>
        
        <div class="download-section" id="downloadSection" style="display: none;">
            <button id="downloadBtn" class="btn btn-success">
                📥 下载WAV文件
            </button>
        </div>
        
        <div class="log-panel">
            <div id="logContainer"></div>
        </div>
    </div>

    <script>
        ''' + WAV_UTILS_JS + '''
        
        class TTSClient {
            constructor() {
                this.socket = null;
                this.isConnected = false;
                this.isSynthesizing = false;
                this.audioChunks = [];
                this.currentSessionId = null;
                this.currentAudio = null;
                this.wavFile = null;
                
                this.initializeElements();
                this.connectWebSocket();
                this.setupEventListeners();
            }
            
            initializeElements() {
                this.textInput = document.getElementById('textInput');
                this.synthesizeBtn = document.getElementById('synthesizeBtn');
                this.stopBtn = document.getElementById('stopBtn');
                this.connectionStatus = document.getElementById('connectionStatus');
                this.synthesisStatus = document.getElementById('synthesisStatus');
                this.audioChunksCount = document.getElementById('audioChunks');
                this.progressFill = document.getElementById('progressFill');
                this.audioPlayer = document.getElementById('audioPlayer');
                this.logContainer = document.getElementById('logContainer');
                this.downloadSection = document.getElementById('downloadSection');
                this.downloadBtn = document.getElementById('downloadBtn');
            }
            
            connectWebSocket() {
                this.socket = io();
                
                this.socket.on('connect', () => {
                    this.isConnected = true;
                    this.connectionStatus.textContent = '🟢 已连接';
                    this.log('WebSocket连接成功', 'success');
                });
                
                this.socket.on('disconnect', () => {
                    this.isConnected = false;
                    this.connectionStatus.textContent = '🔴 已断开';
                    this.log('WebSocket连接断开', 'error');
                });
                
                this.socket.on('audio_chunk', (data) => {
                    this.handleAudioChunk(data);
                });
                
                this.socket.on('synthesis_complete', (data) => {
                    this.handleSynthesisComplete(data);
                });
                
                this.socket.on('synthesis_error', (data) => {
                    this.handleSynthesisError(data);
                });
            }
            
            setupEventListeners() {
                this.synthesizeBtn.addEventListener('click', () => {
                    this.startSynthesis();
                });
                
                this.stopBtn.addEventListener('click', () => {
                    this.stopPlayback();
                });
                
                this.downloadBtn.addEventListener('click', () => {
                    this.downloadWAVFile();
                });
                
                this.textInput.addEventListener('input', () => {
                    const length = this.textInput.value.length;
                    if (length > 450) {
                        this.textInput.style.borderColor = '#ffc107';
                    } else {
                        this.textInput.style.borderColor = '#e1e5e9';
                    }
                });
            }
            
            async startSynthesis() {
                const text = this.textInput.value.trim();
                
                if (!text) {
                    alert('请输入要合成的文本');
                    return;
                }
                
                if (!this.isConnected) {
                    alert('WebSocket未连接，请刷新页面重试');
                    return;
                }
                
                if (this.isSynthesizing) {
                    alert('正在合成中，请稍候');
                    return;
                }
                
                this.isSynthesizing = true;
                this.audioChunks = [];
                this.progressFill.style.width = '0%';
                this.audioPlayer.style.display = 'none';
                this.downloadSection.style.display = 'none';
                this.wavFile = null;
                this.updateUI();
                
                try {
                    const response = await fetch('/api/tts/synthesize', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            text: text,
                            client_id: this.socket.id
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        this.currentSessionId = result.session_id;
                        this.log(`开始合成WAV音频: ${text.substring(0, 50)}...`, 'info');
                    } else {
                        throw new Error(result.message);
                    }
                    
                } catch (error) {
                    this.log('合成请求失败: ' + error.message, 'error');
                    this.isSynthesizing = false;
                    this.updateUI();
                }
            }
            
            handleAudioChunk(data) {
                if (data.session_id !== this.currentSessionId) {
                    return;
                }
                
                this.audioChunks.push(data);
                this.audioChunksCount.textContent = data.chunk_number;
                
                // 更新进度条（基于接收到的音频块数量）
                if (data.chunk_number > 0) {
                    const progressPercent = Math.min(90, (data.chunk_number / 20) * 90); // 最多到90%，留10%给合成完成
                    this.progressFill.style.width = progressPercent + '%';
                }
                
                this.log(`收到WAV音频块 #${data.chunk_number}`, 'info');
            }
            
            handleSynthesisComplete(data) {
                if (data.session_id !== this.currentSessionId) {
                    return;
                }
                
                this.isSynthesizing = false;
                this.progressFill.style.width = '100%';
                
                this.log(`WAV音频合成完成，共 ${data.total_chunks} 个音频块`, 'success');
                
                // 合成完成后立即生成并播放WAV文件
                if (this.audioChunks.length > 0) {
                    this.createAndPlayWAVFile();
                }
                
                this.updateUI();
            }
            
            createAndPlayWAVFile() {
                try {
                    this.log('正在生成WAV音频文件...', 'info');
                    
                    // 合并所有PCM音频块
                    const allPCMData = this.audioChunks.map(chunk => {
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
                    
                    // 创建WAV文件（添加WAV头部）
                    this.wavFile = createWAVFile(mergedPCM);
                    const wavBlob = new Blob([this.wavFile], { type: 'audio/wav' });
                    const url = URL.createObjectURL(wavBlob);
                    
                    // 设置音频播放器并自动播放
                    this.audioPlayer.src = url;
                    this.audioPlayer.style.display = 'block';
                    this.downloadSection.style.display = 'block';
                    
                    // 自动播放音频
                    this.audioPlayer.play().then(() => {
                        this.log('WAV音频开始自动播放', 'success');
                        this.stopBtn.disabled = false;
                    }).catch((error) => {
                        this.log('自动播放失败，请手动点击播放: ' + error.message, 'error');
                        this.stopBtn.disabled = true;
                    });
                    
                    // 播放结束时的处理
                    this.audioPlayer.onended = () => {
                        this.log('WAV音频播放完成', 'success');
                        this.stopBtn.disabled = true;
                        URL.revokeObjectURL(url);
                    };
                    
                    this.log(`WAV文件已生成 (${(this.wavFile.length / 1024).toFixed(1)} KB)`, 'success');
                    
                } catch (error) {
                    this.log('生成WAV文件失败: ' + error.message, 'error');
                }
            }
            
            downloadWAVFile() {
                if (!this.wavFile) {
                    this.log('没有可下载的WAV文件', 'error');
                    return;
                }
                
                try {
                    const blob = new Blob([this.wavFile], { type: 'audio/wav' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    
                    // 生成文件名
                    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
                    const filename = `tts_audio_${timestamp}.wav`;
                    
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    
                    URL.revokeObjectURL(url);
                    this.log(`WAV文件已下载: ${filename}`, 'success');
                    
                } catch (error) {
                    this.log('下载失败: ' + error.message, 'error');
                }
            }
            
            handleSynthesisError(data) {
                if (data.session_id !== this.currentSessionId) {
                    return;
                }
                
                this.isSynthesizing = false;
                this.log('合成错误: ' + data.error, 'error');
                this.updateUI();
            }
            
            stopPlayback() {
                // 停止当前播放
                if (this.audioPlayer.src) {
                    this.audioPlayer.pause();
                    this.audioPlayer.currentTime = 0;
                    this.stopBtn.disabled = true;
                    this.log('播放已停止', 'info');
                }
            }
            
            updateUI() {
                this.synthesizeBtn.disabled = this.isSynthesizing;
                
                if (this.isSynthesizing) {
                    this.synthesisStatus.textContent = '🔄 合成中...';
                    this.synthesizeBtn.classList.add('synthesizing');
                    this.stopBtn.disabled = true;
                } else {
                    this.synthesisStatus.textContent = '⏸️ 待机中';
                    this.synthesizeBtn.classList.remove('synthesizing');
                }
            }
            
            log(message, type = 'info') {
                const timestamp = new Date().toLocaleTimeString();
                const entry = document.createElement('div');
                entry.className = `log-entry log-${type}`;
                entry.textContent = `[${timestamp}] ${message}`;
                
                this.logContainer.appendChild(entry);
                this.logContainer.scrollTop = this.logContainer.scrollHeight;
                
                // 限制日志条目数量
                while (this.logContainer.children.length > 50) {
                    this.logContainer.removeChild(this.logContainer.firstChild);
                }
            }
        }
        
        // 页面加载完成后初始化客户端
        document.addEventListener('DOMContentLoaded', () => {
            new TTSClient();
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("=" * 60)
    print("🎤 语音合成系统启动中...")
    print("=" * 60)
    print(f"🎭 配音员: 聆小琪 (x4_lingxiaoqi_oral)")
    print(f"🎵 音频格式: WAV (PCM) | 24kHz | 16-bit | 单声道")
    print(f"🌐 访问地址: http://localhost:5001")
    print(f"📡 WebSocket支持: 流式传输，合成完成后播放")
    print("=" * 60)
    
    try:
        socketio.run(app, host='0.0.0.0', port=5001, debug=False)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}") 