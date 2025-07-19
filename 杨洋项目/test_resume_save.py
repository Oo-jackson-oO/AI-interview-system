#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试简历保存功能
"""

import os
import sys
from datetime import datetime

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from modules.user_management import UserManager

def test_resume_save():
    """测试简历保存功能"""
    
    # 初始化用户管理器
    user_manager = UserManager()
    
    # 测试用户数据
    test_username = "test_user"
    test_resume_data = {
        'filename': 'test_resume.pdf',
        'text': '这是一个测试简历内容\n包含姓名：张三\n工作经验：5年\n技能：Python, JavaScript, React',
        'file_size': 1024,
        'file_type': 'pdf'
    }
    
    print("开始测试简历保存功能...")
    
    # 1. 测试用户注册
    print("\n1. 测试用户注册...")
    register_result = user_manager.register_user(test_username, "password123", "test@example.com")
    print(f"注册结果: {register_result}")
    
    # 2. 测试添加简历
    print("\n2. 测试添加简历...")
    add_result = user_manager.add_resume(test_username, test_resume_data)
    print(f"添加简历结果: {add_result}")
    
    # 3. 测试获取用户简历列表
    print("\n3. 测试获取用户简历列表...")
    resumes = user_manager.get_user_resumes(test_username)
    print(f"用户简历数量: {len(resumes)}")
    for i, resume in enumerate(resumes):
        print(f"简历 {i+1}:")
        print(f"  ID: {resume['id']}")
        print(f"  文件名: {resume['filename']}")
        print(f"  文件路径: {resume.get('file_path', 'N/A')}")
        print(f"  创建时间: {resume['created_at']}")
    
    # 4. 测试文件保存功能
    print("\n4. 测试文件保存功能...")
    
    def save_resume_to_file(username, text, original_filename):
        """保存简历文本到文件"""
        try:
            # 创建简历文件夹（如果不存在）
            resume_folder = 'resumes'
            if not os.path.exists(resume_folder):
                os.makedirs(resume_folder)
            
            # 生成文件名：用户名_resume.txt
            safe_username = "".join(c for c in username if c.isalnum() or c in ('-', '_')).rstrip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_username}_resume_{timestamp}.txt"
            filepath = os.path.join(resume_folder, filename)
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"用户: {username}\n")
                f.write(f"原始文件名: {original_filename}\n")
                f.write(f"保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n")
                f.write("简历内容:\n")
                f.write("=" * 50 + "\n")
                f.write(text)
            
            print(f"简历已保存到: {filepath}")
            return True
            
        except Exception as e:
            print(f"保存简历文件失败: {str(e)}")
            return False
    
    # 测试保存文件
    save_result = save_resume_to_file(test_username, test_resume_data['text'], test_resume_data['filename'])
    print(f"文件保存结果: {'成功' if save_result else '失败'}")
    
    # 5. 检查生成的文件
    print("\n5. 检查生成的文件...")
    resume_folder = 'resumes'
    if os.path.exists(resume_folder):
        files = os.listdir(resume_folder)
        print(f"简历文件夹中的文件: {files}")
        
        for file in files:
            if file.endswith('.txt'):
                filepath = os.path.join(resume_folder, file)
                print(f"\n文件: {file}")
                print("文件内容预览:")
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(content[:200] + "..." if len(content) > 200 else content)
                except Exception as e:
                    print(f"读取文件失败: {e}")
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_resume_save() 