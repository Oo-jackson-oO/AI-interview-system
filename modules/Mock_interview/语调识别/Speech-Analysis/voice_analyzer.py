import librosa
import numpy as np
import json
import os
from typing import Dict, Any, Tuple
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

def convert_numpy_types(obj):
    """
    递归转换NumPy类型为Python原生类型，以便JSON序列化
    """
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

class VoiceAnalyzer:
    def __init__(self):
        """初始化语音分析器"""
        self.sample_rate = 22050
        self.hop_length = 512
        self.frame_length = 2048
        
    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, float]:
        import os
        
        # 首先检查原始路径是否存在
        if os.path.exists(audio_path):
            final_path = audio_path
        # 如果原始路径不存在且不是绝对路径，尝试uploads目录
        elif not os.path.isabs(audio_path):
            uploads_path = os.path.join("uploads", audio_path)
            if os.path.exists(uploads_path):
                final_path = uploads_path
            else:
                final_path = audio_path  # 使用原始路径，让librosa报错
        else:
            final_path = audio_path
            
        try:
            audio_data, sample_rate = librosa.load(final_path, sr=self.sample_rate)
            print(f"音频加载成功: {final_path}")
            print(f"音频长度: {len(audio_data)/sample_rate:.2f}秒")
            return audio_data, sample_rate
        except Exception as e:
            print(f"音频加载失败: {e}")
            raise e
    
    def extract_speech_rate(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        分析语速特征
        
        Args:
            audio_data: 音频数据
            
        Returns:
            语速分析结果
        """
        # 计算音频总时长
        duration = len(audio_data) / self.sample_rate
        
        # 使用librosa检测语音活动
        # 计算能量包络
        energy = librosa.feature.rms(y=audio_data, frame_length=self.frame_length, hop_length=self.hop_length)[0]
        
        # 设置能量阈值来检测语音段
        energy_threshold = np.mean(energy) + 0.5 * np.std(energy)
        speech_segments = energy > energy_threshold
        
        # 计算语音活动时间
        speech_time = np.sum(speech_segments) * self.hop_length / self.sample_rate
        
        # 计算语速指标
        speech_ratio = speech_time / duration if duration > 0 else 0
        
        # 计算音节率（简化版本）
        # 使用过零率作为音节检测的代理
        zero_crossing_rate = librosa.feature.zero_crossing_rate(audio_data, frame_length=self.frame_length, hop_length=self.hop_length)[0]
        syllable_rate = np.mean(zero_crossing_rate) * 10  # 缩放因子
        
        # 语速评估
        if syllable_rate > 0.15:
            speed_level = "快"
            speed_score = 0.8
        elif syllable_rate > 0.08:
            speed_level = "中等"
            speed_score = 0.5
        else:
            speed_level = "慢"
            speed_score = 0.2
            
        return {
            "语速等级": speed_level,
            "语速得分": round(speed_score, 2),
            "音节率": round(syllable_rate, 3),
            "语音活动比例": round(speech_ratio, 3),
            "总时长": round(duration, 2)
        }
    
    def extract_emotion_tone(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        分析情感语调特征
        
        Args:
            audio_data: 音频数据
            
        Returns:
            情感语调分析结果
        """
        # 提取音调特征
        pitches, magnitudes = librosa.piptrack(y=audio_data, sr=self.sample_rate, hop_length=self.hop_length)
        
        # 计算平均音调
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if pitch_values:
            mean_pitch = np.mean(pitch_values)
            pitch_std = np.std(pitch_values)
            pitch_range = np.max(pitch_values) - np.min(pitch_values)
        else:
            mean_pitch = 0
            pitch_std = 0
            pitch_range = 0
        
        # 提取音色特征
        mfcc = librosa.feature.mfcc(y=audio_data, sr=self.sample_rate, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        
        # 计算能量变化
        energy = librosa.feature.rms(y=audio_data, frame_length=self.frame_length, hop_length=self.hop_length)[0]
        energy_variance = np.var(energy)
        
        # 情感分析（基于声学特征）
        emotion_score = 0.5  # 默认中性
        
        # 基于音调变化判断情感
        if pitch_std > 50:
            if mean_pitch > 200:
                emotion = "兴奋/激动"
                emotion_score = 0.8
            else:
                emotion = "紧张/焦虑"
                emotion_score = 0.7
        elif pitch_std > 20:
            emotion = "平静/中性"
            emotion_score = 0.5
        else:
            emotion = "低沉/悲伤"
            emotion_score = 0.3
            
        # 基于能量变化调整情感
        if energy_variance > 0.1:
            emotion_score = min(emotion_score + 0.1, 1.0)
            
        return {
            "情感类型": emotion,
            "情感得分": round(emotion_score, 2),
            "平均音调": round(mean_pitch, 1),
            "音调变化": round(pitch_std, 1),
            "音调范围": round(pitch_range, 1),
            "能量变化": round(energy_variance, 3)
        }
    
    def extract_fluency(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        分析流利度特征
        
        Args:
            audio_data: 音频数据
            
        Returns:
            流利度分析结果
        """
        # 计算停顿
        energy = librosa.feature.rms(y=audio_data, frame_length=self.frame_length, hop_length=self.hop_length)[0]
        
        # 检测停顿
        energy_threshold = np.mean(energy) * 0.3
        silence_segments = energy < energy_threshold
        
        # 计算停顿次数和时长
        silence_changes = np.diff(silence_segments.astype(int))
        pause_count = np.sum(silence_changes == 1)  # 从语音到停顿的转换
        
        # 计算停顿总时长
        silence_time = np.sum(silence_segments) * self.hop_length / self.sample_rate
        total_time = len(audio_data) / self.sample_rate
        silence_ratio = silence_time / total_time if total_time > 0 else 0
        
        # 计算语音连续性
        speech_continuity = 1 - silence_ratio
        
        # 计算语音节奏稳定性
        # 使用自相关分析
        if len(energy) > 10:
            autocorr = np.correlate(energy, energy, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            rhythm_stability = np.max(autocorr[1:min(50, len(autocorr))]) / autocorr[0]
        else:
            rhythm_stability = 0.5
        
        # 流利度评估
        fluency_score = 0.5  # 默认中等
        
        # 基于停顿比例调整
        if silence_ratio < 0.1:
            fluency_score += 0.2
        elif silence_ratio > 0.3:
            fluency_score -= 0.2
            
        # 基于节奏稳定性调整
        if rhythm_stability > 0.7:
            fluency_score += 0.1
        elif rhythm_stability < 0.3:
            fluency_score -= 0.1
            
        # 基于停顿次数调整
        if pause_count < 5:
            fluency_score += 0.1
        elif pause_count > 15:
            fluency_score -= 0.1
            
        fluency_score = max(0, min(1, fluency_score))
        
        # 流利度等级
        if fluency_score > 0.7:
            fluency_level = "流利"
        elif fluency_score > 0.4:
            fluency_level = "一般"
        else:
            fluency_level = "不流利"
            
        return {
            "流利度等级": fluency_level,
            "流利度得分": round(fluency_score, 2),
            "停顿次数": pause_count,
            "停顿比例": round(silence_ratio, 3),
            "语音连续性": round(speech_continuity, 3),
            "节奏稳定性": round(rhythm_stability, 3)
        }
    
    def analyze_voice(self, audio_path: str) -> Dict[str, Any]:
        """
        综合分析语音特征
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            完整的语音分析结果
        """
        print(f"开始分析音频文件: {audio_path}")
        
        # 加载音频
        try:
            audio_data, sample_rate = self.load_audio(audio_path)
        except Exception as e:
            return {"错误": f"音频文件加载失败: {str(e)}"}
        
        # 提取各项特征
        speech_rate_analysis = self.extract_speech_rate(audio_data)
        emotion_tone_analysis = self.extract_emotion_tone(audio_data)
        fluency_analysis = self.extract_fluency(audio_data)
        
        # 综合评估
        overall_score = (
            speech_rate_analysis["语速得分"] * 0.3 +
            emotion_tone_analysis["情感得分"] * 0.4 +
            fluency_analysis["流利度得分"] * 0.3
        )
        
        # 生成分析结果
        analysis_result = {
            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "音频文件": os.path.basename(audio_path) if audio_path else "未知文件",
            "综合得分": round(overall_score, 2),
            "语速分析": speech_rate_analysis,
            "情感语调": emotion_tone_analysis,
            "流利度": fluency_analysis
        }
        
        print("语音分析完成")
        return analysis_result
    
    def save_analysis_result(self, result: Dict[str, Any], output_path: Optional[str] = None):
        import os
        
        if output_path is None:
            # 创建results目录（如果不存在）
            os.makedirs("results", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join("results", f"voice_analysis_result_{timestamp}.json")
        else:
            # 如果指定了输出路径但不是绝对路径，且没有指定目录，则放在results目录下
            if not os.path.isabs(output_path) and os.path.dirname(output_path) == "":
                os.makedirs("results", exist_ok=True)
                output_path = os.path.join("results", output_path)
            elif not os.path.isabs(output_path):
                # 确保父目录存在
                parent_dir = os.path.dirname(output_path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
        
        try:
            # 转换NumPy类型为Python原生类型
            serializable_result = convert_numpy_types(result)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_result, f, ensure_ascii=False, indent=2)
            print(f"分析结果已保存到: {output_path}")
        except Exception as e:
            print(f"保存结果失败: {e}")