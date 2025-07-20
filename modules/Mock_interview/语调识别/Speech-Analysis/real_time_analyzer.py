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
import json
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
        
    def _convert_numpy_types(self, obj):
        """递归转换numpy类型为Python原生类型"""
        if hasattr(obj, 'item'):  # numpy scalar
            return obj.item()
        elif hasattr(obj, 'tolist'):  # numpy array
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._convert_numpy_types(item) for item in obj)
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            # 对于其他类型，尝试转换为字符串
            return str(obj)
    
    def format_result_for_json(self, result):
        """将分析结果格式化为结构化的JSON数据"""
        if not result:
            return None
        
        # 先转换所有numpy类型
        result = self._convert_numpy_types(result)
        
        # 创建结构化的数据
        formatted_result = {
            "analysis_info": {
                "audio_file": result.get('音频文件', ''),
                "analysis_time": result.get('分析时间', ''),
                "analysis_timestamp": datetime.now().isoformat(),
                "overall_score": float(result.get('综合得分', 0))
            },
            "speech_rate_analysis": {
                "level": result.get('语速分析', {}).get('语速等级', ''),
                "score": float(result.get('语速分析', {}).get('语速得分', 0)),
                "syllable_rate": float(result.get('语速分析', {}).get('音节率', 0)),
                "speech_activity_ratio": float(result.get('语速分析', {}).get('语音活动比例', 0)),
                "total_duration": float(result.get('语速分析', {}).get('总时长', 0))
            },
            "emotion_tone_analysis": {
                "emotion_type": result.get('情感语调', {}).get('情感类型', ''),
                "emotion_score": float(result.get('情感语调', {}).get('情感得分', 0)),
                "average_pitch": float(result.get('情感语调', {}).get('平均音调', 0)),
                "pitch_variation": float(result.get('情感语调', {}).get('音调变化', 0)),
                "pitch_range": float(result.get('情感语调', {}).get('音调范围', 0)),
                "energy_variation": float(result.get('情感语调', {}).get('能量变化', 0))
            },
            "fluency_analysis": {
                "fluency_level": result.get('流利度', {}).get('流利度等级', ''),
                "fluency_score": float(result.get('流利度', {}).get('流利度得分', 0)),
                "pause_count": int(result.get('流利度', {}).get('停顿次数', 0)),
                "pause_ratio": float(result.get('流利度', {}).get('停顿比例', 0)),
                "speech_continuity": float(result.get('流利度', {}).get('语音连续性', 0)),
                "rhythm_stability": float(result.get('流利度', {}).get('节奏稳定性', 0))
            },
            "recommendations": {
                "speech_rate_advice": self._get_speech_rate_advice(result.get('语速分析', {})),
                "emotion_advice": self._get_emotion_advice(result.get('情感语调', {})),
                "fluency_advice": self._get_fluency_advice(result.get('流利度', {}))
            },
            "metadata": {
                "analysis_version": "1.0",
                "analyzer": "RealTimeVoiceAnalyzer",
                "sample_rate": self.sample_rate,
                "channels": self.channels
            }
        }
        
        return formatted_result
    
    def _get_speech_rate_advice(self, speech_rate_data):
        """根据语速分析给出建议"""
        level = speech_rate_data.get('语速等级', '')
        if level == '过快':
            return "语速较快，建议适当放慢以增强理解度"
        elif level == '过慢':
            return "语速较慢，可适当加快以保持听众注意力"
        elif level == '适中':
            return "语速适中，保持当前节奏"
        else:
            return "建议调整语速到适中范围"
    
    def _get_emotion_advice(self, emotion_data):
        """根据情感语调给出建议"""
        emotion_type = emotion_data.get('情感类型', '')
        score = emotion_data.get('情感得分', 0)
        
        if score >= 80:
            return f"情感表达{emotion_type}，语调自然，继续保持"
        elif score >= 60:
            return f"情感表达{emotion_type}，可增强语调变化以提升表现力"
        else:
            return f"建议增强情感表达，使语调更加生动有感染力"
    
    def _get_fluency_advice(self, fluency_data):
        """根据流利度给出建议"""
        level = fluency_data.get('流利度等级', '')
        pause_count = fluency_data.get('停顿次数', 0)
        
        if level == '流利':
            return "语言流利度很好，表达自然流畅"
        elif level == '一般':
            return f"流利度一般，检测到{pause_count}次停顿，可通过练习减少不必要停顿"
        else:
            return f"流利度需要改善，建议多加练习以减少停顿和提高连贯性"
    
    def save_analysis_result_json(self, result, filename=None):
        """保存分析结果为JSON文件"""
        if not result:
            print("没有分析结果可保存")
            return
            
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_result_{timestamp}.json"
            
        # 确保目录存在
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(results_dir, exist_ok=True)
        filepath = os.path.join(results_dir, filename)
        
        try:
            # 格式化结果数据
            formatted_result = self.format_result_for_json(result)
            
            # 保存JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(formatted_result, f, ensure_ascii=False, indent=2)
            
            print(f"💾 JSON格式分析结果已保存到: {filepath}")
            print(f"📊 综合得分: {formatted_result['analysis_info']['overall_score']}")
            print(f"🎵 语速等级: {formatted_result['speech_rate_analysis']['level']}")
            print(f"😊 情感类型: {formatted_result['emotion_tone_analysis']['emotion_type']}")
            print(f"🗣️  流利度等级: {formatted_result['fluency_analysis']['fluency_level']}")
            
            return filepath
        except Exception as e:
            print(f"保存JSON分析结果失败: {e}")
            return None
            
    def load_analysis_result_json(self, filepath):
        """从JSON文件加载分析结果"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                result = json.load(f)
            print(f"✅ 成功加载分析结果: {filepath}")
            return result
        except Exception as e:
            print(f"❌ 加载JSON分析结果失败: {e}")
            return None
    
    def list_saved_results(self):
        """列出已保存的JSON分析结果"""
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        if not os.path.exists(results_dir):
            print("📁 没有找到结果目录")
            return []
        
        json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
        
        if not json_files:
            print("📄 没有找到JSON格式的分析结果")
            return []
        
        print(f"\n📋 找到 {len(json_files)} 个JSON格式的分析结果:")
        for i, filename in enumerate(json_files, 1):
            filepath = os.path.join(results_dir, filename)
            try:
                # 尝试读取文件以获取基本信息
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                analysis_time = data.get('analysis_info', {}).get('analysis_time', '未知')
                overall_score = data.get('analysis_info', {}).get('overall_score', 0)
                
                print(f"  {i}. {filename}")
                print(f"     分析时间: {analysis_time}")
                print(f"     综合得分: {overall_score}")
                
            except Exception as e:
                print(f"  {i}. {filename} (文件损坏: {e})")
        
        return json_files
    
    def compare_results(self, result_files):
        """比较多个分析结果"""
        if len(result_files) < 2:
            print("❌ 需要至少2个结果文件进行比较")
            return
        
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        comparison_data = []
        
        print(f"\n📊 比较 {len(result_files)} 个分析结果:")
        print("="*80)
        
        for filename in result_files:
            filepath = os.path.join(results_dir, filename)
            result = self.load_analysis_result_json(filepath)
            
            if result:
                comparison_data.append({
                    'filename': filename,
                    'overall_score': result.get('analysis_info', {}).get('overall_score', 0),
                    'speech_rate_score': result.get('speech_rate_analysis', {}).get('score', 0),
                    'emotion_score': result.get('emotion_tone_analysis', {}).get('emotion_score', 0),
                    'fluency_score': result.get('fluency_analysis', {}).get('fluency_score', 0),
                    'analysis_time': result.get('analysis_info', {}).get('analysis_time', ''),
                })
        
        if len(comparison_data) < 2:
            print("❌ 无法加载足够的结果进行比较")
            return
        
        # 显示比较表格
        print(f"{'文件名':<30} {'综合得分':<10} {'语速得分':<10} {'情感得分':<10} {'流利度得分':<10}")
        print("-" * 80)
        
        for data in comparison_data:
            print(f"{data['filename']:<30} {data['overall_score']:<10.1f} {data['speech_rate_score']:<10.1f} {data['emotion_score']:<10.1f} {data['fluency_score']:<10.1f}")
        
        # 计算统计信息
        overall_scores = [d['overall_score'] for d in comparison_data]
        best_idx = overall_scores.index(max(overall_scores))
        worst_idx = overall_scores.index(min(overall_scores))
        
        print("\n📈 比较总结:")
        print(f"最佳表现: {comparison_data[best_idx]['filename']} (综合得分: {overall_scores[best_idx]:.1f})")
        print(f"最差表现: {comparison_data[worst_idx]['filename']} (综合得分: {overall_scores[worst_idx]:.1f})")
        print(f"平均得分: {sum(overall_scores)/len(overall_scores):.1f}")
        print(f"得分范围: {min(overall_scores):.1f} - {max(overall_scores):.1f}")
        
        return comparison_data
            
    def run_interactive_session(self):
        """运行交互式录音分析会话"""
        print("🎵 实时语音分析系统")
        print("="*60)
        print("功能说明:")
        print("- 按回车键开始录音")
        print("- 录音过程中按 Ctrl+C 停止录音并分析")
        print("- 输入 'list' 查看历史分析结果")
        print("- 输入 'compare' 比较多个分析结果")
        print("- 输入 'quit' 或 'exit' 退出程序")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n请按回车键开始录音 (或输入命令): ").strip().lower()
                
                if user_input in ['quit', 'exit', 'q']:
                    print("👋 感谢使用！")
                    break
                elif user_input == 'list':
                    self.list_saved_results()
                    continue
                elif user_input == 'compare':
                    self._handle_compare_command()
                    continue
                    
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
                                # 直接保存为JSON格式
                                saved_file = self.save_analysis_result_json(result)
                                if saved_file:
                                    print(f"✅ 分析结果已保存为JSON格式")
                                
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
    
    def _handle_compare_command(self):
        """处理比较命令"""
        json_files = self.list_saved_results()
        
        if len(json_files) < 2:
            print("❌ 需要至少2个分析结果才能进行比较")
            return
        
        try:
            print(f"\n请选择要比较的结果文件 (输入数字，用逗号分隔，如: 1,2,3):")
            choice = input("选择: ").strip()
            
            if not choice:
                return
            
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected_files = [json_files[i] for i in indices if 0 <= i < len(json_files)]
            
            if len(selected_files) >= 2:
                self.compare_results(selected_files)
            else:
                print("❌ 请选择至少2个有效的文件")
                
        except (ValueError, IndexError):
            print("❌ 输入格式错误，请输入有效的数字")
        except Exception as e:
            print(f"❌ 比较过程出错: {e}")
            
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