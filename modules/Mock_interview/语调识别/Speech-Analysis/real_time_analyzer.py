#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时录音分析模块
支持持续录音并在结束后进行语音分析
"""

import pyaudio
import wave
import numpy as np
import threading
import time
import os
from datetime import datetime
from voice_analyzer import VoiceAnalyzer
import signal
import sys

class RealTimeVoiceAnalyzer:
    def __init__(self, sample_rate=22050, chunk_size=1024, channels=1):
        """
        初始化实时语音分析器
        
        Args:
            sample_rate: 采样率
            chunk_size: 音频块大小
            channels: 声道数
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format = pyaudio.paInt16
        
        # 录音控制
        self.is_recording = False
        self.audio_data = []
        self.audio_thread = None
        
        # 音频对象
        self.audio = None
        self.stream = None
        
        # 语音分析器
        self.analyzer = VoiceAnalyzer()
        
        # 信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """处理中断信号"""
        print("\n\n收到终止信号，正在停止录音...")
        self.stop_recording()
        
    def _audio_callback(self):
        """音频录制回调函数"""
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            print("🎙️  开始录音...")
            print("按 Ctrl+C 停止录音并开始分析")
            
            while self.is_recording:
                try:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    self.audio_data.append(data)
                except Exception as e:
                    print(f"录音数据读取错误: {e}")
                    break
                    
        except Exception as e:
            print(f"录音初始化错误: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                
    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            print("录音已在进行中...")
            return False
            
        try:
            # 初始化PyAudio
            self.audio = pyaudio.PyAudio()
            
            # 检查可用的音频设备
            self._list_audio_devices()
            
            # 重置数据
            self.audio_data = []
            self.is_recording = True
            
            # 启动录音线程
            self.audio_thread = threading.Thread(target=self._audio_callback)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            
            return True
            
        except Exception as e:
            print(f"启动录音失败: {e}")
            return False
            
    def stop_recording(self):
        """停止录音"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        # 等待录音线程结束
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2)
            
        # 清理音频资源
        if self.audio:
            self.audio.terminate()
            
        print("🛑 录音已停止")
        
    def _list_audio_devices(self):
        """列出可用的音频设备"""
        print("\n📱 可用的音频输入设备:")
        device_count = self.audio.get_device_count()
        
        for i in range(device_count):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                print(f"  设备 {i}: {device_info['name']} (采样率: {int(device_info['defaultSampleRate'])})")
        print()
        
    def save_audio(self, filename=None):
        """保存录音到文件"""
        if not self.audio_data:
            print("没有录音数据可保存")
            return None
            
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            
        # 确保目录存在
        os.makedirs("recordings", exist_ok=True)
        filepath = os.path.join("recordings", filename)
        
        try:
            # 保存为WAV文件
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.audio_data))
                
            print(f"💾 录音已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"保存录音失败: {e}")
            return None
            
    def analyze_recording(self):
        """分析录音"""
        if not self.audio_data:
            print("没有录音数据可分析")
            return None
            
        print("\n🔍 开始分析录音...")
        
        # 先保存录音文件
        audio_file = self.save_audio()
        if not audio_file:
            return None
            
        try:
            # 使用语音分析器分析
            result = self.analyzer.analyze_voice(audio_file)
            
            if "错误" in result:
                print(f"❌ 分析失败: {result['错误']}")
                return None
                
            return result
            
        except Exception as e:
            print(f"❌ 分析过程出错: {e}")
            return None
            
    def display_analysis_result(self, result):
        """显示分析结果"""
        if not result:
            return
            
        print("\n" + "="*60)
        print("🎵 实时录音分析结果")
        print("="*60)
        
        print(f"📁 音频文件: {result['音频文件']}")
        print(f"⏰ 分析时间: {result['分析时间']}")
        print(f"⭐ 综合得分: {result['综合得分']}")
        
        print(f"\n🚀 语速分析")
        speech_rate = result['语速分析']
        print(f"   等级: {speech_rate['语速等级']}")
        print(f"   得分: {speech_rate['语速得分']}")
        print(f"   音节率: {speech_rate['音节率']}")
        print(f"   语音活动比例: {speech_rate['语音活动比例']}")
        print(f"   总时长: {speech_rate['总时长']}秒")
        
        print(f"\n😊 情感语调")
        emotion = result['情感语调']
        print(f"   类型: {emotion['情感类型']}")
        print(f"   得分: {emotion['情感得分']}")
        print(f"   平均音调: {emotion['平均音调']}Hz")
        print(f"   音调变化: {emotion['音调变化']}")
        print(f"   音调范围: {emotion['音调范围']}")
        print(f"   能量变化: {emotion['能量变化']}")
        
        print(f"\n🗣️  流利度")
        fluency = result['流利度']
        print(f"   等级: {fluency['流利度等级']}")
        print(f"   得分: {fluency['流利度得分']}")
        print(f"   停顿次数: {fluency['停顿次数']}")
        print(f"   停顿比例: {fluency['停顿比例']}")
        print(f"   语音连续性: {fluency['语音连续性']}")
        print(f"   节奏稳定性: {fluency['节奏稳定性']}")
        
    def run_interactive_session(self):
        """运行交互式录音分析会话"""
        print("🎵 实时语音分析系统")
        print("="*60)
        print("功能说明:")
        print("- 按回车键开始录音")
        print("- 录音过程中按 Ctrl+C 停止录音并分析")
        print("- 输入 'quit' 或 'exit' 退出程序")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n请按回车键开始录音 (或输入 'quit' 退出): ").strip().lower()
                
                if user_input in ['quit', 'exit', 'q']:
                    print("👋 感谢使用！")
                    break
                    
                # 开始录音
                if self.start_recording():
                    try:
                        # 等待用户中断
                        while self.is_recording:
                            time.sleep(0.1)
                            
                        # 分析录音
                        result = self.analyze_recording()
                        
                        # 显示结果
                        self.display_analysis_result(result)
                        
                        # 保存结果
                        if result:
                            save_choice = input("\n💾 是否保存分析结果? (y/n): ").strip().lower()
                            if save_choice in ['y', 'yes', '是']:
                                self.analyzer.save_analysis_result(result)
                                
                    except KeyboardInterrupt:
                        # 这里会被signal handler处理
                        pass
                        
                else:
                    print("❌ 录音启动失败")
                    
            except KeyboardInterrupt:
                print("\n\n👋 程序已退出")
                break
            except Exception as e:
                print(f"❌ 程序异常: {e}")
                
def main():
    """主函数"""
    try:
        analyzer = RealTimeVoiceAnalyzer()
        analyzer.run_interactive_session()
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 