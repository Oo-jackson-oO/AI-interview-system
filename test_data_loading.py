#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os

def test_data_loading():
    """测试数据加载功能"""
    
    # 测试alivin用户的数据
    user_folder = 'uploads/alivin'
    
    print("=== 测试数据加载 ===")
    print(f"用户文件夹: {user_folder}")
    
    # 检查文件是否存在
    files_to_check = [
        'interview_summary_report.json',
        'facial_analysis_report.json',
        'analysis_result.json'
    ]
    
    for filename in files_to_check:
        file_path = os.path.join(user_folder, filename)
        if os.path.exists(file_path):
            print(f"✅ {filename} 存在")
            
            # 尝试加载JSON数据
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"   - 数据加载成功，包含 {len(data)} 个顶级键")
                
                # 显示主要数据结构
                if filename == 'interview_summary_report.json':
                    if 'section_evaluations' in data:
                        sections = list(data['section_evaluations'].keys())
                        print(f"   - 评估模块: {sections}")
                    if 'overall_assessment' in data:
                        score = data['overall_assessment'].get('final_score', 0)
                        print(f"   - 总分: {score}")
                        
                elif filename == 'facial_analysis_report.json':
                    if 'performance_summary' in data:
                        summary = data['performance_summary']
                        print(f"   - 微表情平均分: {summary.get('微表情表现', {}).get('平均分', 0)}")
                        print(f"   - 肢体动作平均分: {summary.get('肢体动作表现', {}).get('平均分', 0)}")
                        
                elif filename == 'analysis_result.json':
                    if 'analysis_info' in data:
                        overall_score = data['analysis_info'].get('overall_score', 0)
                        print(f"   - 语音语调总分: {overall_score}")
                        
            except Exception as e:
                print(f"   ❌ JSON解析失败: {e}")
        else:
            print(f"❌ {filename} 不存在")
    
    print("\n=== 数据格式验证 ===")
    
    # 模拟JavaScript的数据处理逻辑
    try:
        # 加载所有数据
        summary_data = None
        facial_data = None
        analysis_data = None
        
        summary_path = os.path.join(user_folder, 'interview_summary_report.json')
        facial_path = os.path.join(user_folder, 'facial_analysis_report.json')
        analysis_path = os.path.join(user_folder, 'analysis_result.json')
        
        if os.path.exists(summary_path):
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
                
        if os.path.exists(facial_path):
            with open(facial_path, 'r', encoding='utf-8') as f:
                facial_data = json.load(f)
                
        if os.path.exists(analysis_path):
            with open(analysis_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
        
        # 模拟数据合并逻辑
        modules = {}
        
        # 处理面试总结数据
        if summary_data and 'section_evaluations' in summary_data:
            for section_name, data in summary_data['section_evaluations'].items():
                module_key = None
                
                if section_name == '自我介绍':
                    module_key = 'self_introduction'
                elif section_name == '简历深挖':
                    module_key = 'resume_digging'
                elif section_name == '岗位匹配度':
                    module_key = 'position_matching'
                elif section_name == '反问环节':
                    module_key = 'reverse_question'
                
                if module_key:
                    modules[module_key] = {
                        'score': data.get('score', 0),
                        'evaluation': data.get('evaluation', ''),
                        'suggestions': data.get('suggestions', ''),
                        'active': True
                    }
                    print(f"✅ {section_name} -> {module_key}: {data.get('score', 0)}分")
        
        # 处理面部分析数据
        if facial_data and 'performance_summary' in facial_data:
            # 神态分析
            facial_score = facial_data['performance_summary'].get('微表情表现', {}).get('平均分', 0)
            modules['facial_analysis'] = {
                'score': round(facial_score * 10),
                'evaluation': facial_data['performance_summary'].get('微表情表现', {}).get('表现评级', '一般'),
                'suggestions': '建议保持自然的面部表情',
                'active': True
            }
            print(f"✅ 神态分析: {round(facial_score * 10)}分")
            
            # 肢体语言
            body_score = facial_data['performance_summary'].get('肢体动作表现', {}).get('平均分', 0)
            modules['body_language'] = {
                'score': round(body_score * 10),
                'evaluation': facial_data['performance_summary'].get('肢体动作表现', {}).get('表现评级', '一般'),
                'suggestions': '建议改善坐姿和手势',
                'active': True
            }
            print(f"✅ 肢体语言: {round(body_score * 10)}分")
        
        # 处理语音分析数据
        if analysis_data and 'analysis_info' in analysis_data:
            voice_score = analysis_data['analysis_info'].get('overall_score', 0)
            modules['voice_tone'] = {
                'score': round(voice_score * 100),
                'evaluation': analysis_data.get('fluency_analysis', {}).get('fluency_level', '一般'),
                'suggestions': '建议改善语音语调',
                'active': True
            }
            print(f"✅ 语音语调: {round(voice_score * 100)}分")
        
        # 计算总分 - 只计算有分数的部分
        active_modules = [module for module in modules.values() if module['active'] and module['score'] > 0]
        total_score = sum(module['score'] for module in active_modules)
        
        # 计算有分数的部分的总满分
        module_config = {
            'self_introduction': 10,
            'resume_digging': 15,
            'ability_assessment': 15,
            'position_matching': 10,
            'professional_skills': 20,
            'reverse_question': 5,
            'voice_tone': 5,
            'facial_analysis': 10,
            'body_language': 10
        }
        
        total_max_score = 0
        for module_name, module_data in modules.items():
            if module_data['active'] and module_data['score'] > 0:
                total_max_score += module_config.get(module_name, 0)
        
        # 计算总分：有分数的分数之和除以有分数的模块的总分之和（限制在0-100范围内）
        final_score = min(100, round((total_score / total_max_score) * 100)) if total_max_score > 0 else 0
        
        print(f"\n📊 原始总分: {total_score}")
        print(f"📊 有分数的模块满分: {total_max_score}")
        print(f"📊 最终总分: {final_score}%")
        
        # 显示所有模块
        print("\n=== 所有模块 ===")
        for module_name, module_data in modules.items():
            status = "✅ 活跃" if module_data['active'] and module_data['score'] > 0 else "❌ 黯淡"
            print(f"{module_name}: {module_data['score']}分 ({status})")
            
    except Exception as e:
        print(f"❌ 数据处理失败: {e}")

if __name__ == '__main__':
    test_data_loading() 