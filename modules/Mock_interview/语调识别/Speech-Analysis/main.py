#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音分析系统主程序
使用免费的大模型API进行语音情感、语速、流利度分析
"""

import os
import sys
import argparse
from voice_analyzer import VoiceAnalyzer

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='语音分析系统')
    parser.add_argument('audio_file', help='要分析的音频文件路径')
    parser.add_argument('-o', '--output', help='输出JSON文件路径（可选）')
    parser.add_argument('--verbose', action='store_true', help='显示详细分析过程')
    
    args = parser.parse_args()
    
    # 检查音频文件是否存在
    if not os.path.exists(args.audio_file):
        print(f"错误: 音频文件 '{args.audio_file}' 不存在")
        sys.exit(1)
    
    # 检查文件扩展名
    supported_formats = ['.wav', '.mp3', '.flac', '.m4a', '.ogg']
    file_ext = os.path.splitext(args.audio_file)[1].lower()
    if file_ext not in supported_formats:
        print(f"警告: 文件格式 '{file_ext}' 可能不被支持")
        print(f"支持的格式: {', '.join(supported_formats)}")
    
    print("=" * 50)
    print("语音分析系统")
    print("=" * 50)
    
    try:
        # 创建语音分析器
        analyzer = VoiceAnalyzer()
        
        # 分析语音
        result = analyzer.analyze_voice(args.audio_file)
        
        # 检查是否有错误
        if "错误" in result:
            print(f"分析失败: {result['错误']}")
            sys.exit(1)
        
        # 显示分析结果
        print("\n" + "=" * 50)
        print("分析结果")
        print("=" * 50)
        
        print(f"音频文件: {result['音频文件']}")
        print(f"分析时间: {result['分析时间']}")
        print(f"综合得分: {result['综合得分']}")
        
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
        
        # 保存结果到JSON文件
        output_path = args.output
        analyzer.save_analysis_result(result, output_path)
        
        print("\n" + "=" * 50)
        print("分析完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"程序执行出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 