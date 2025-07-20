#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os

def test_interview_result_data():
    """测试面试结果页面的数据加载"""
    
    base_url = "http://127.0.0.1:5000"
    username = "alivin"
    
    print("=== 测试面试结果页面数据加载 ===")
    
    # 测试1: 检查各个JSON文件是否可以访问
    files_to_test = [
        "interview_summary_report.json",
        "facial_analysis_report.json", 
        "analysis_result.json"
    ]
    
    for filename in files_to_test:
        url = f"{base_url}/uploads/{username}/{filename}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {filename} 可以访问")
                print(f"   数据键: {list(data.keys())}")
            else:
                print(f"❌ {filename} 访问失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ {filename} 访问出错: {e}")
    
    # 测试2: 检查面试结果页面
    url = f"{base_url}/interview-result?user={username}"
    try:
        response = requests.get(url)
        print(f"\n面试结果页面状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 面试结果页面可以访问")
        elif response.status_code == 302:
            print("⚠️  面试结果页面需要登录，重定向到登录页面")
        else:
            print(f"❌ 面试结果页面访问失败")
    except Exception as e:
        print(f"❌ 面试结果页面访问出错: {e}")
    
    # 测试3: 检查API端点
    url = f"{base_url}/api/interview-result/data"
    try:
        response = requests.get(url)
        print(f"\nAPI端点状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ API端点可以访问")
            print(f"   返回数据: {data}")
        elif response.status_code == 401:
            print("⚠️  API端点需要登录")
        else:
            print(f"❌ API端点访问失败")
    except Exception as e:
        print(f"❌ API端点访问出错: {e}")

if __name__ == "__main__":
    test_interview_result_data() 