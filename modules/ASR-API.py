# -*- encoding:utf-8 -*-
import eventlet

eventlet.monkey_patch()

import json
import base64
import hashlib
import hmac
import time
import threading
import websocket
from urllib.parse import quote
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit


app = Flask(__name__)
app.config['SECRET_KEY'] = 'asr_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# 科大讯飞配置 - 与realtime_rtasr.py保持一致
XUNFEI_CONFIG = {
    'APPID': 'daa9d5d9',              # 使用realtime_rtasr.py中的配置
    'API_KEY': '57e1dcd91156c7b12c078b5ad372870b',  # 使用realtime_rtasr.py中的配置
    'BASE_URL': 'ws://rtasr.xfyun.cn/v1/ws'
}

# 存储WebSocket连接
ws_connections = {}

def parse_rtasr_result(result_json):
    """
    解析讯飞实时语音转写的JSON结果
    """
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

class XunfeiASR:
    def __init__(self, client_id):
        self.client_id = client_id
        self.ws = None
        self.app_id = XUNFEI_CONFIG['APPID']
        self.api_key = XUNFEI_CONFIG['API_KEY']
        
        # 智能录音控制
        self.is_recording = False
        self.last_speech_time = time.time()
        self.transcription_parts = []
        self.all_sentences = []
        self.all_transcriptions = []
        self.accumulated_text = ""
        self.start_time = None
        self.monitor_thread = None
        
    def create_url(self):
        """创建科大讯飞WebSocket连接URL - 与realtime_rtasr.py保持一致"""
        base_url = XUNFEI_CONFIG['BASE_URL']
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
        """按照stop.py逻辑提取最终句子"""
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
                result = parse_rtasr_result(result_str)
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
        url = self.create_url()
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
        """开始智能录音 - 集成stop.py逻辑"""
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
            except:
                pass
            self.ws.close()

# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    print(f'客户端已连接: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'客户端已断开: {request.sid}')
    # 清理连接
    if request.sid in ws_connections:
        ws_connections[request.sid].stop()
        del ws_connections[request.sid]

@socketio.on('start_smart_asr')
def handle_start_smart_asr():
    """开始智能语音识别（自动停止）"""
    client_id = request.sid
    if client_id in ws_connections:
        # 如果已有连接，先停止
        ws_connections[client_id].stop()
        del ws_connections[client_id]
    
    asr = XunfeiASR(client_id)
    ws_connections[client_id] = asr
    asr.connect()
    
    # 等待连接建立后启动智能录音
    def start_after_connection():
        time.sleep(1)  # 等待连接建立
        if client_id in ws_connections:
            ws_connections[client_id].start_smart_recording()
    
    thread = threading.Thread(target=start_after_connection)
    thread.daemon = True
    thread.start()

@socketio.on('stop_asr')
def handle_stop_asr():
    """停止语音识别"""
    client_id = request.sid
    if client_id in ws_connections:
        # 手动停止时也进行最终结果处理
        asr = ws_connections[client_id]
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
        
        ws_connections[client_id].stop()
        del ws_connections[client_id]

@socketio.on('audio_data')
def handle_audio_data(data):
    """处理音频数据"""
    client_id = request.sid
    if client_id in ws_connections:
        # 将base64编码的音频数据解码后发送
        audio_bytes = base64.b64decode(data['audio'])
        ws_connections[client_id].send_audio(audio_bytes)

# 前端模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>智能语音识别系统</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            text-align: center;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .button-group {
            margin: 20px 0;
        }
        button {
            padding: 18px 30px;
            margin: 10px;
            font-size: 18px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            min-width: 180px;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .btn-smart {
            background-color: #2196F3;
            color: white;
        }
        .btn-danger {
            background-color: #f44336;
            color: white;
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        #status {
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 16px;
        }
        .status-disconnected {
            background-color: #ffebee;
            color: #c62828;
            border: 1px solid #ffcdd2;
        }
        .status-connected {
            background-color: #e8f5e8;
            color: #2e7d32;
            border: 1px solid #c8e6c9;
        }
        .status-recording {
            background-color: #fff3e0;
            color: #ef6c00;
            border: 1px solid #ffcc02;
        }
        .status-smart {
            background-color: #e3f2fd;
            color: #1976d2;
            border: 1px solid #bbdefb;
        }
        #result {
            margin: 20px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #f9f9f9;
            min-height: 120px;
            text-align: left;
            max-height: 400px;
            overflow-y: auto;
        }
        .config-notice {
            background-color: #e3f2fd;
            color: #1565c0;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid #bbdefb;
        }
        .result-text {
            padding: 8px 12px;
            margin: 5px 0;
            border-left: 3px solid #4CAF50;
            background: white;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .final-result {
            padding: 12px 16px;
            margin: 10px 0;
            border-left: 4px solid #2196F3;
            background: #e3f2fd;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-weight: bold;
        }
        .sentence-item {
            padding: 6px 10px;
            margin: 3px 0;
            background: #f8f9fa;
            border-radius: 4px;
            border-left: 2px solid #007bff;
        }
        .error-text {
            color: #d32f2f;
            background: #ffebee;
            border-left: 3px solid #f44336;
        }
        .mode-info {
            background-color: #fff8e1;
            color: #f57c00;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
            font-size: 15px;
            text-align: left;
        }
        .feature-list {
            background-color: #f3e5f5;
            color: #7b1fa2;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: left;
        }
        .feature-list ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        .feature-list li {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 智能语音识别系统</h1>
        
        <div class="config-notice">
            <strong>✅ 已配置科大讯飞API</strong><br>
            APPID: {{ app_id }}<br>
            状态: 就绪
        </div>
        
        <div class="feature-list">
            <strong>🎯 智能功能特点:</strong>
            <ul>
                <li>📝 实时语音转写</li>
                <li>⏰ 自动检测停止（8秒后开始监控，3秒无新转写自动停止）</li>
                <li>🔍 智能句子分割</li>
                <li>📋 最终结果自动整理</li>
            </ul>
        </div>
        
        <div id="status" class="status-disconnected">未连接</div>
        
        <div class="button-group">
            <button id="smartBtn" onclick="startSmartRecording()" class="btn-smart">🧠 开始智能录音</button>
            <button id="stopBtn" onclick="stopRecording()" disabled class="btn-danger">⏹️ 停止录音</button>
        </div>
        
        <div class="mode-info" id="modeInfo" style="display: none;">
            <strong>🎙️ 智能录音进行中:</strong><br>
            • 正在实时转写您的语音<br>
            • 录音至少8秒，然后3秒无新转写将自动停止<br>
            • 停止后将自动整理完整的句子结果
        </div>
        
        <div id="result">
            <p style="color: #666; text-align: center;">点击"开始智能录音"开始使用...</p>
        </div>
    </div>

    <script>
        const socket = io();
        let mediaRecorder;
        let audioContext;
        let isRecording = false;
        
        const smartBtn = document.getElementById('smartBtn');
        const stopBtn = document.getElementById('stopBtn');
        const status = document.getElementById('status');
        const result = document.getElementById('result');
        const modeInfo = document.getElementById('modeInfo');

        // Socket事件处理
        socket.on('connect', function() {
            updateStatus('✅ 已连接到服务器', 'connected');
        });

        socket.on('disconnect', function() {
            updateStatus('❌ 与服务器断开连接', 'disconnected');
            resetButtons();
        });

        socket.on('asr_connected', function() {
            updateStatus('🧠 智能语音识别已连接', 'smart');
        });

        socket.on('asr_smart_started', function(data) {
            updateStatus('🔴 智能录音中...（自动检测停止）', 'smart');
            modeInfo.style.display = 'block';
        });

        socket.on('asr_disconnected', function() {
            updateStatus('⏹️ 语音识别已断开', 'disconnected');
            resetButtons();
        });

        socket.on('asr_auto_stopped', function() {
            updateStatus('🛑 智能录音已自动停止', 'connected');
            resetButtons();
            modeInfo.style.display = 'none';
        });

        socket.on('asr_result', function(data) {
            if (data.text) {
                const p = document.createElement('p');
                p.textContent = '📝 ' + data.text;
                p.className = 'result-text';
                result.appendChild(p);
                result.scrollTop = result.scrollHeight;
            }
        });

        socket.on('asr_final_result', function(data) {
            const finalDiv = document.createElement('div');
            finalDiv.className = 'final-result';
            
            const header = document.createElement('div');
            header.innerHTML = `<strong>🎯 最终结果 (${data.count}句话):</strong>`;
            finalDiv.appendChild(header);
            
            const fullText = document.createElement('div');
            fullText.textContent = data.full_text;
            fullText.style.marginTop = '8px';
            finalDiv.appendChild(fullText);
            
            if (data.sentences && data.sentences.length > 1) {
                const sentencesList = document.createElement('div');
                sentencesList.innerHTML = '<br><strong>分句详情:</strong>';
                data.sentences.forEach((sentence, index) => {
                    const sentenceItem = document.createElement('div');
                    sentenceItem.className = 'sentence-item';
                    sentenceItem.textContent = `${index + 1}. ${sentence}`;
                    sentencesList.appendChild(sentenceItem);
                });
                finalDiv.appendChild(sentencesList);
            }
            
            result.appendChild(finalDiv);
            result.scrollTop = result.scrollHeight;
        });

        socket.on('asr_error', function(data) {
            const p = document.createElement('p');
            p.textContent = '❌ 错误: ' + data.error;
            p.className = 'result-text error-text';
            result.appendChild(p);
        });

        function updateStatus(message, type) {
            status.textContent = message;
            status.className = 'status-' + type;
        }

        function resetButtons() {
            smartBtn.disabled = false;
            stopBtn.disabled = true;
            isRecording = false;
            modeInfo.style.display = 'none';
        }

        async function startSmartRecording() {
            await initializeRecording();
            socket.emit('start_smart_asr');
        }

        async function initializeRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        sampleRate: 16000,
                        channelCount: 1,
                        sampleSize: 16
                    } 
                });
                
                audioContext = new AudioContext({ sampleRate: 16000 });
                const source = audioContext.createMediaStreamSource(stream);
                const processor = audioContext.createScriptProcessor(1024, 1, 1);
                
                processor.onaudioprocess = function(e) {
                    if (isRecording) {
                        const audioData = e.inputBuffer.getChannelData(0);
                        // 转换为16位PCM
                        const pcmData = new Int16Array(audioData.length);
                        for (let i = 0; i < audioData.length; i++) {
                            pcmData[i] = audioData[i] * 32767;
                        }
                        
                        // 转换为base64并发送
                        const audioBytes = new Uint8Array(pcmData.buffer);
                        const base64Audio = btoa(String.fromCharCode.apply(null, audioBytes));
                        socket.emit('audio_data', { audio: base64Audio });
                    }
                };
                
                source.connect(processor);
                processor.connect(audioContext.destination);
                
                isRecording = true;
                smartBtn.disabled = true;
                stopBtn.disabled = false;
                updateStatus('🔴 准备智能录音...', 'smart');
                
                // 清空结果
                result.innerHTML = '<p style="color: #666; text-align: center;">🎙️ 开始识别...</p>';
                
            } catch (err) {
                console.error('录音启动失败:', err);
                alert('❌ 无法访问麦克风，请检查权限设置');
                resetButtons();
            }
        }

        function stopRecording() {
            isRecording = false;
            resetButtons();
            updateStatus('⏹️ 录音已停止', 'connected');
            
            if (audioContext) {
                audioContext.close();
            }
            
            // 停止ASR
            socket.emit('stop_asr');
        }

        // 页面加载完成后的初始化
        window.onload = function() {
            updateStatus('🔄 准备就绪，等待连接...', 'disconnected');
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE, app_id=XUNFEI_CONFIG['APPID'])

if __name__ == '__main__':
    print("=" * 60)
    print("🎤 实时语音识别系统启动中...")
    print("=" * 60)
    print("📝 API配置:")
    print(f"   APPID: {XUNFEI_CONFIG['APPID']}")
    print(f"   API_KEY: {XUNFEI_CONFIG['API_KEY'][:20]}...")
    print("=" * 60)
    print("🌐 访问地址: http://localhost:5003")
    print("🎙️ 点击'开始录音'进行测试")
    print("=" * 60)
    
    try:
        socketio.run(app, host='0.0.0.0', port=5003, debug=False, use_reloader=False)
    except Exception as e:
        print(f"启动服务器失败: {e}")
        print("请检查端口5003是否被占用") 