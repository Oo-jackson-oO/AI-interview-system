#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.skill_training.backend.skill_manager import SkillManager

def test_skill_manager():
    """测试SkillManager的功能"""
    try:
        skill_manager = SkillManager()
        
        print("=== 测试SkillManager ===")
        print(f"书籍文件夹: {skill_manager.books_folder}")
        print(f"封面文件夹: {skill_manager.cover_folder}")
        print(f"PDF文件夹: {skill_manager.pdf_folder}")
        
        # 检查文件夹是否存在
        print(f"\n=== 文件夹检查 ===")
        print(f"书籍文件夹存在: {os.path.exists(skill_manager.books_folder)}")
        print(f"封面文件夹存在: {os.path.exists(skill_manager.cover_folder)}")
        print(f"PDF文件夹存在: {os.path.exists(skill_manager.pdf_folder)}")
        
        # 列出cover文件夹中的文件
        if os.path.exists(skill_manager.cover_folder):
            print(f"\n=== Cover文件夹内容 ===")
            cover_files = os.listdir(skill_manager.cover_folder)
            for file in cover_files:
                print(f"  - {file}")
        
        # 列出pdf文件夹中的文件
        if os.path.exists(skill_manager.pdf_folder):
            print(f"\n=== PDF文件夹内容 ===")
            pdf_files = os.listdir(skill_manager.pdf_folder)
            for file in pdf_files:
                print(f"  - {file}")
        
        # 测试获取可用书籍
        print(f"\n=== 获取可用书籍 ===")
        books = skill_manager.get_available_books()
        print(f"找到 {len(books)} 本书:")
        
        for i, book in enumerate(books, 1):
            print(f"\n第{i}本书:")
            print(f"  标题: {book['title']}")
            print(f"  封面: {book['cover']}")
            print(f"  PDF: {book['pdf_path']}")
            print(f"  页数: {book['pages']}")
            
            # 检查文件是否存在
            cover_exists = os.path.exists(book['cover']) if book['cover'] else False
            # 检查PDF文件是否存在（需要重建完整路径）
            pdf_full_path = os.path.join(skill_manager.pdf_folder, book['pdf_path'])
            pdf_exists = os.path.exists(pdf_full_path)
            print(f"  封面存在: {cover_exists}")
            print(f"  PDF存在: {pdf_exists}")
            
            # 测试PDF URL生成
            if pdf_exists:
                pdf_url = f"/api/training/pdf/{book['pdf_path']}"
                print(f"  PDF URL: {pdf_url}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_skill_manager() 