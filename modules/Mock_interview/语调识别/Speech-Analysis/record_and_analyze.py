#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时录音分析启动脚本
简化版本，便于快速使用
"""

import sys
import os

def main():
    """主函数"""
    print("🎵 实时语音分析系统启动")
    print("="*50)
    
    try:
        # 导入实时分析器
        from real_time_analyzer import RealTimeVoiceAnalyzer
        
        # 创建分析器实例
        analyzer = RealTimeVoiceAnalyzer()
        
        # 运行交互式会话
        analyzer.run_interactive_session()
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        print("请确保已安装所有依赖包:")
        print("pip install pyaudio librosa numpy scipy soundfile")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ 程序运行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 