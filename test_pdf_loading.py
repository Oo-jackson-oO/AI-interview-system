#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from urllib.parse import urljoin

def test_pdf_access():
    """测试PDF文件访问"""
    base_url = "http://localhost:5000"
    
    # 测试PDF文件列表
    pdf_files = [
        "军事理论.pdf",
        "第1本书.pdf", 
        "第2本书.pdf"
    ]
    
    print("=== PDF文件访问测试 ===")
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join("modules", "modules", "book", "pdf", pdf_file)
        
        # 检查文件是否存在
        if os.path.exists(pdf_path):
            print(f"✅ {pdf_file} 文件存在")
            
            # 测试API路由
            api_url = f"{base_url}/api/training/pdf/{pdf_file}"
            try:
                response = requests.get(api_url)
                if response.status_code == 200:
                    print(f"✅ {pdf_file} API访问成功")
                else:
                    print(f"❌ {pdf_file} API访问失败: {response.status_code}")
            except Exception as e:
                print(f"❌ {pdf_file} API访问异常: {e}")
        else:
            print(f"❌ {pdf_file} 文件不存在")
    
    print("\n=== 封面文件访问测试 ===")
    
    cover_files = [
        "军事理论.png",
        "第1本书.png",
        "第2本书.png"
    ]
    
    for cover_file in cover_files:
        cover_path = os.path.join("modules", "modules", "book", "cover", cover_file)
        
        if os.path.exists(cover_path):
            print(f"✅ {cover_file} 封面文件存在")
            
            # 测试API路由
            api_url = f"{base_url}/api/training/cover/{cover_file}"
            try:
                response = requests.get(api_url)
                if response.status_code == 200:
                    print(f"✅ {cover_file} API访问成功")
                else:
                    print(f"❌ {cover_file} API访问失败: {response.status_code}")
            except Exception as e:
                print(f"❌ {cover_file} API访问异常: {e}")
        else:
            print(f"❌ {cover_file} 封面文件不存在")

if __name__ == "__main__":
    test_pdf_access() 