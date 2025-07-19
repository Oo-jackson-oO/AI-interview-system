#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音分析系统快速启动脚本
提供简单的交互式界面
"""

import os
import sys
import glob
from voice_analyzer import VoiceAnalyzer
import numpy as np

def safe_to_builtin(obj):
    if isinstance(obj, dict):
        return {k: safe_to_builtin(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_to_builtin(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.generic):
        return obj.item()
    else:
        return obj

def get_audio_files():
    audio_extensions = ['*.wav', '*.mp3', '*.flac', '*.m4a', '*.ogg']
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(glob.glob(os.path.join('uploads', ext)))
    return sorted(audio_files)

def select_audio_file():
    """
    让用户选择音频文件
    """
    audio_files = get_audio_files()
    
    if not audio_files:
        print("❌ 当前目录下没有找到音频文件")
        print("支持的格式: .wav, .mp3, .flac, .m4a, .ogg")
        return None
    
    print("\n可用的音频文件:")
    for i, file in enumerate(audio_files, 1):
        print(f"  {i}. {file}")
    
    while True:
        try:
            choice = input(f"\n请选择音频文件 (1-{len(audio_files)}): ").strip()
            if choice.lower() == 'q':
                return None
            
            index = int(choice) - 1
            if 0 <= index < len(audio_files):
                return audio_files[index]
            else:
                print(f"请输入 1-{len(audio_files)} 之间的数字")
        except ValueError:
            print("请输入有效的数字")
        except KeyboardInterrupt:
            return None

def analyze_audio(audio_file):
    """
    分析音频文件（仅基础版）
    """
    print(f"\n正在分析: {audio_file}")
    print("请稍候...")
    try:
        analyzer = VoiceAnalyzer()
        result = analyzer.analyze_voice(audio_file)
        if "错误" in result:
            print(f"❌ 分析失败: {result['错误']}")
            return None
        return result
    except Exception as e:
        print(f"❌ 分析异常: {e}")
        return None

def display_results(result):
    """
    显示分析结果
    """
    print("\n" + "="*60)
    print("分析结果")
    print("="*60)
    
    print(f"音频文件: {result['音频文件']}")
    print(f"分析时间: {result['分析时间']}")
    print(f"综合得分: {result['综合得分']}")
    
    # 显示转录内容（如果有）
    if result.get('转录内容'):
        print(f"\n转录内容: {result['转录内容']}")
    
    print("\n--- 语速分析 ---")
    speech_rate = result['语速分析']
    print(f"语速等级: {speech_rate['语速等级']}")
    print(f"语速得分: {speech_rate['语速得分']}")
    print(f"音节率: {speech_rate['音节率']}")
    print(f"语音活动比例: {speech_rate['语音活动比例']}")
    print(f"总时长: {speech_rate['总时长']}秒")
    
    print("\n--- 情感语调 ---")
    emotion = result['情感语调']
    print(f"情感类型: {emotion['情感类型']}")
    print(f"情感得分: {emotion['情感得分']}")
    print(f"平均音调: {emotion['平均音调']}Hz")
    print(f"音调变化: {emotion['音调变化']}")
    print(f"音调范围: {emotion['音调范围']}")
    print(f"能量变化: {emotion['能量变化']}")
    
    print("\n--- 流利度 ---")
    fluency = result['流利度']
    print(f"流利度等级: {fluency['流利度等级']}")
    print(f"流利度得分: {fluency['流利度得分']}")
    print(f"停顿次数: {fluency['停顿次数']}")
    print(f"停顿比例: {fluency['停顿比例']}")
    print(f"语音连续性: {fluency['语音连续性']}")
    print(f"节奏稳定性: {fluency['节奏稳定性']}")

def save_results(result, audio_file):
    import pprint
    import os
    while True:
        save_choice = input("\n是否保存分析结果？(y/n): ").lower().strip()
        if save_choice in ['y', 'yes', '是']:
            base_name = os.path.splitext(os.path.basename(audio_file))[0]
            output_file = os.path.join('results', f"{base_name}_analysis.json")
            try:
                print("[DEBUG] 即将保存的 result 内容如下：")
                pprint.pprint(result)
                result = safe_to_builtin(result)
                if not isinstance(result, dict):
                    raise ValueError(f"Result must be a dict, got {type(result)}: {result}")
                analyzer = VoiceAnalyzer()
                analyzer.save_analysis_result(result, output_file)
                print(f"✅ 结果已保存到: {output_file}")
                print("[DEBUG] 保存后请检查文件内容是否完整。")
                break
            except Exception as e:
                print(f"❌ 保存失败: {e}")
                print("[DEBUG] 保存失败时的 result 内容如下：")
                pprint.pprint(result)
                break
        elif save_choice in ['n', 'no', '否']:
            break
        else:
            print("请输入 y 或 n")

def main():
    """
    主函数
    """
    print("🎵 语音分析系统 - 快速启动")
    print("="*60)
    print("本系统可以分析语音的情感、语速、流利度等特征")
    print("支持格式: WAV, MP3, FLAC, M4A, OGG")
    print("按 Ctrl+C 退出程序")
    while True:
        try:
            # 选择音频文件
            audio_file = select_audio_file()
            if not audio_file:
                print("退出程序")
                break
            # 分析音频（只用基础版）
            result = analyze_audio(audio_file)
            if not result:
                continue
            # 显示结果
            display_results(result)
            # 保存结果
            save_results(result, audio_file)
            # 询问是否继续
            while True:
                continue_choice = input("\n是否分析其他音频文件？(y/n): ").lower().strip()
                if continue_choice in ['y', 'yes', '是']:
                    break
                elif continue_choice in ['n', 'no', '否']:
                    print("感谢使用！")
                    return
                else:
                    print("请输入 y 或 n")
        except KeyboardInterrupt:
            print("\n\n程序已退出")
            break
        except Exception as e:
            print(f"\n❌ 程序异常: {e}")
            continue

if __name__ == "__main__":
    main() 