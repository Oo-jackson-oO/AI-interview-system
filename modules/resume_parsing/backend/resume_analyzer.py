import json
import os
import re
import difflib
from pathlib import Path
from openai import OpenAI
from datetime import datetime

# 高亮颜色配置 - 优化版本
HIGHLIGHT_COLORS = ['yellow', 'lightblue', 'lightgreen', 'lightcoral', 'lightpink', 'lightyellow', 'lightcyan']
COLOR_MAP = {
    'yellow': '#FFD700',  # 更亮的金黄色
    'lightblue': '#87CEEB',  # 天蓝色
    'lightgreen': '#90EE90',  # 浅绿色
    'lightcoral': '#F08080',  # 浅珊瑚色
    'lightpink': '#FFB6C1',  # 浅粉色
    'lightyellow': '#FFFFE0',  # 浅黄色
    'lightcyan': '#E0FFFF'  # 浅青色
}

class ResumeAnalyzer:
    def __init__(self):
        self.client = OpenAI(
            api_key='QcGCOyVichfHetzkUDeM:AUoiqAJtarlstnrJMcTI',
            base_url='https://spark-api-open.xf-yun.com/v1/'
        )
    
    def analyze_resume_with_suggestions(self, resume_text):
        """分析简历并生成修改建议"""
        prompt = f"""
        你是一个专业的简历分析助手。请分析下面这份简历，找出其中可能存在的问题，并提供具体的修改建议。

        请按照以下格式回答，支持多处修改建议：

        <index1>第1处问题：</index1>
        原文问题部分：
        起始句：<original_first1>（原文中第一句）</original_first1>
        问题部分结束后的下一句：<original_last1>（问题部分最后一句的下一句）</original_last1>

        修改建议：
        起始句：<suggested_first1>（修改后的第一句）</suggested_first1>
        修改部分结束后的下一句：<suggested_last1>（修改后最后一句的下一句）</suggested_last1>

        <index2>第2处问题：</index2>
        原文问题部分：
        起始句：<original_first2>（原文中第一句）</original_first2>
        问题部分结束后的下一句：<original_last2>（问题部分最后一句的下一句）</original_last2>

        修改建议：
        起始句：<suggested_first2>（修改后的第一句）</suggested_first2>
        修改部分结束后的下一句：<suggested_last2>（修改后最后一句的下一句）</suggested_last2>

        （以此类推）

        简历总体评价：
        <!-- START: 评价 -->
        请根据上述问题，给出简历的总体评价和改进建议。
        <!-- END: 评价 -->

        注意事项：
        - 请严格从原文中提取句子；
        - 每处问题都必须使用编号包裹（如 <index1>、<original_first1>、<suggested_first1> 等）；
        - 不要添加无关解释或总结，只列出问题和修改建议；
        - 总体评价需要包裹在 <!-- START: 评价 --> 和 <!-- END: 评价 --> 标签内；
        - 如果没有找到问题，请明确写"简历质量良好，无需修改"。
        - 最多只返回7处问题,即最多7个编号;
        - 重点关注：语法错误、表达不清、信息缺失、格式问题、内容冗余等。
        - **重要**：suggested_first 和 suggested_last 标签中应该包含修改后的内容，不是原文内容！

        简历内容：
        {resume_text}
        """

        try:
            response = self.client.chat.completions.create(
                model='4.0Ultra',
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"调用 AI 失败：{str(e)}")
            return None

    def generate_markdown_resume(self, resume_text):
        """生成Markdown格式的简历"""
        prompt = f"""
        请将以下简历内容转换为规范的Markdown格式，保持原有信息的同时优化结构和排版：

        要求：
        1. 使用标准的Markdown语法
        2. 合理使用标题层级（# ## ###）
        3. 使用列表格式整理信息
        4. 保持信息的完整性和准确性
        5. 优化段落结构，使内容更清晰易读
        6. 突出重要信息（如技能、经验等）

        简历内容：
        {resume_text}
        """

        try:
            response = self.client.chat.completions.create(
                model='4.0Ultra',
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"生成Markdown简历失败：{str(e)}")
            return None

    def fuzzy_find_range(self, text, start_sentence, end_sentence, color_index):
        """模糊查找并高亮文本范围 - 优化版本"""
        if not start_sentence or not end_sentence:
            print("⚠️ 起始句或结束句为空")
            return text
            
        start_sentence = start_sentence.strip()
        end_sentence = end_sentence.strip()
        
        print(f"🔍 查找范围: '{start_sentence[:30]}...' 到 '{end_sentence[:30]}...'")

        # 1. 首先尝试精确匹配
        start_index = text.find(start_sentence)
        end_index = text.find(end_sentence, start_index if start_index != -1 else 0)
        
        if start_index != -1 and end_index != -1:
            end_index += len(end_sentence)
            print(f"✅ 精确匹配成功: 位置 {start_index}-{end_index}")
            return self._highlight_text_range(text, start_index, end_index, color_index)

        print("⚠️ 精确匹配失败，尝试模糊匹配...")

        # 2. 如果精确匹配失败，尝试模糊匹配
        # 将文本按句子分割（支持多种分隔符）
        sentences = re.split(r'[。！？\n\r]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        print(f"📝 文本分割为 {len(sentences)} 个句子")
        
        # 寻找最相似的起始和结束句子
        best_start = None
        best_end = None
        best_start_score = 0
        best_end_score = 0
        
        for i, sentence in enumerate(sentences):
            # 计算与起始句的相似度
            start_similarity = self._calculate_similarity(sentence, start_sentence)
            if start_similarity > best_start_score and start_similarity > 0.6:
                best_start_score = start_similarity
                best_start = (i, sentence)
                print(f"🎯 找到更好的起始句匹配 (相似度: {start_similarity:.2f}): {sentence[:50]}...")
            
            # 计算与结束句的相似度
            end_similarity = self._calculate_similarity(sentence, end_sentence)
            if end_similarity > best_end_score and end_similarity > 0.6:
                best_end_score = end_similarity
                best_end = (i, sentence)
                print(f"🎯 找到更好的结束句匹配 (相似度: {end_similarity:.2f}): {sentence[:50]}...")
        
        # 3. 如果找到了匹配的句子，进行高亮
        if best_start and best_end and best_start[0] <= best_end[0]:
            start_text = best_start[1]
            end_text = best_end[1]
            
            print(f"✅ 模糊匹配成功: 起始句相似度 {best_start_score:.2f}, 结束句相似度 {best_end_score:.2f}")
            
            start_index = text.find(start_text)
            end_index = text.find(end_text, start_index)
            
            if start_index != -1 and end_index != -1:
                end_index += len(end_text)
                return self._highlight_text_range(text, start_index, end_index, color_index)
        
        print("⚠️ 模糊匹配也失败，使用备用方法...")
        # 4. 如果还是没找到，尝试更宽松的匹配
        return self._fallback_highlight(text, start_sentence, end_sentence, color_index)

    def _calculate_similarity(self, text1, text2):
        """计算两个文本的相似度"""
        if not text1 or not text2:
            return 0
        
        # 转换为小写进行比较
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # 使用difflib计算相似度
        similarity = difflib.SequenceMatcher(None, text1_lower, text2_lower).ratio()
        
        # 如果包含关键词，提高相似度
        if any(keyword in text1_lower for keyword in text2_lower.split()):
            similarity += 0.2
        
        return min(similarity, 1.0)

    def _validate_html_format(self, html_content):
        """验证和清理HTML格式"""
        # 修复常见的HTML格式问题
        html_content = re.sub(r'border-radius:\s*(\d+)(?!px)', r'border-radius: \1px', html_content)
        html_content = re.sub(r'padding:\s*(\d+)(?!px)', r'padding: \1px', html_content)
        html_content = re.sub(r'margin:\s*(\d+)(?!px)', r'margin: \1px', html_content)
        
        # 确保所有div标签都正确关闭
        html_content = re.sub(r'<div([^>]*?)(?<!>)$', r'<div\1>', html_content)
        
        return html_content

    def _highlight_text_range(self, text, start_index, end_index, color_index):
        """高亮指定范围的文本 - 优化版本"""
        if start_index >= end_index or start_index < 0 or end_index > len(text):
            return text
            
        before = text[:start_index]
        highlighted_text = text[start_index:end_index]
        after = text[end_index:]
        
        color_name = HIGHLIGHT_COLORS[color_index % len(HIGHLIGHT_COLORS)]
        color = COLOR_MAP[color_name]
        
        # 使用更明显的高亮样式 - 改进版本
        highlighted_html = f'<span style="background-color: {color}; padding: 3px 6px; border-radius: 4px; font-weight: bold; border: 2px solid {color}; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: inline-block; margin: 1px 2px;">{highlighted_text}</span>'
        
        # 验证HTML格式
        highlighted_html = self._validate_html_format(highlighted_html)
        
        return before + highlighted_html + after

    def _fallback_highlight(self, text, start_sentence, end_sentence, color_index):
        """备用高亮方法 - 使用关键词匹配 - 优化版本"""
        # 提取关键词
        start_keywords = [word for word in start_sentence.split() if len(word) > 2]
        end_keywords = [word for word in end_sentence.split() if len(word) > 2]
        
        # 在文本中查找包含关键词的段落
        paragraphs = text.split('\n\n')
        highlighted_paragraphs = []
        
        for paragraph in paragraphs:
            # 检查是否包含起始关键词
            has_start = any(keyword.lower() in paragraph.lower() for keyword in start_keywords)
            # 检查是否包含结束关键词
            has_end = any(keyword.lower() in paragraph.lower() for keyword in end_keywords)
            
            if has_start or has_end:
                # 高亮整个段落 - 修复HTML格式
                color_name = HIGHLIGHT_COLORS[color_index % len(HIGHLIGHT_COLORS)]
                color = COLOR_MAP[color_name]
                highlighted_paragraph = f'<div style="background-color: {color}; padding: 8px 12px; border-radius: 6px; border: 2px solid {color}; box-shadow: 0 3px 6px rgba(0,0,0,0.15); margin: 4px 0; font-weight: 500;">{paragraph}</div>'
                
                # 验证HTML格式
                highlighted_paragraph = self._validate_html_format(highlighted_paragraph)
                
                highlighted_paragraphs.append(highlighted_paragraph)
            else:
                highlighted_paragraphs.append(paragraph)
        
        return '\n\n'.join(highlighted_paragraphs)

    def extract_and_highlight(self, original_text, suggested_text, analysis_result):
        """提取并高亮问题和修改建议 - 优化版本"""
        original_highlighted = original_text
        suggested_highlighted = suggested_text
        
        print("🔍 开始提取高亮内容...")
        print(f"分析结果长度: {len(analysis_result)}")
        print(f"分析结果前500字符: {analysis_result[:500]}")
        print(f"修改建议文本前200字符: {suggested_text[:200]}")

        # 改进正则表达式，支持更灵活的匹配
        for i in range(1, 20):
            # 提取原文问题部分 - 支持多种格式
            original_patterns = [
                rf"<original_first{i}>(.*?)</original_first{i}>",
                rf"起始句：<original_first{i}>(.*?)</original_first{i}>",
                rf"原文问题部分：\s*起始句：<original_first{i}>(.*?)</original_first{i}>"
            ]
            
            original_start_match = None
            original_end_match = None
            suggested_start_match = None
            suggested_end_match = None
            
            # 尝试多种模式匹配
            for pattern in original_patterns:
                original_start_match = re.search(pattern, analysis_result, re.DOTALL | re.IGNORECASE)
                if original_start_match:
                    print(f"✅ 找到第{i}处原文起始句: {original_start_match.group(1)[:50]}...")
                    break
            
            # 匹配结束句
            end_patterns = [
                rf"<original_last{i}>(.*?)</original_last{i}>",
                rf"问题部分结束后的下一句：<original_last{i}>(.*?)</original_last{i}>"
            ]
            
            for pattern in end_patterns:
                original_end_match = re.search(pattern, analysis_result, re.DOTALL | re.IGNORECASE)
                if original_end_match:
                    print(f"✅ 找到第{i}处原文结束句: {original_end_match.group(1)[:50]}...")
                    break
            
            # 匹配修改建议
            suggested_patterns = [
                rf"<suggested_first{i}>(.*?)</suggested_first{i}>",
                rf"修改建议：\s*起始句：<suggested_first{i}>(.*?)</suggested_first{i}>"
            ]
            
            for pattern in suggested_patterns:
                suggested_start_match = re.search(pattern, analysis_result, re.DOTALL | re.IGNORECASE)
                if suggested_start_match:
                    print(f"✅ 找到第{i}处修改建议起始句: {suggested_start_match.group(1)[:50]}...")
                    break
            
            end_suggested_patterns = [
                rf"<suggested_last{i}>(.*?)</suggested_last{i}>",
                rf"修改部分结束后的下一句：<suggested_last{i}>(.*?)</suggested_last{i}>"
            ]
            
            for pattern in end_suggested_patterns:
                suggested_end_match = re.search(pattern, analysis_result, re.DOTALL | re.IGNORECASE)
                if suggested_end_match:
                    print(f"✅ 找到第{i}处修改建议结束句: {suggested_end_match.group(1)[:50]}...")
                    break

            # 如果找到了匹配的内容
            if original_start_match and original_end_match:
                original_start = original_start_match.group(1).strip()
                original_end = original_end_match.group(1).strip()
                
                print(f"🎯 处理第{i}处原文高亮...")
                # 高亮原文问题部分
                original_highlighted = self.fuzzy_find_range(
                    original_highlighted, 
                    original_start, 
                    original_end, 
                    i - 1
                )
            
            if suggested_start_match and suggested_end_match:
                suggested_start = suggested_start_match.group(1).strip()
                suggested_end = suggested_end_match.group(1).strip()
                
                print(f"🎯 处理第{i}处修改建议高亮...")
                print(f"修改建议起始句: '{suggested_start}'")
                print(f"修改建议结束句: '{suggested_end}'")
                # 高亮修改建议部分
                suggested_highlighted = self.fuzzy_find_range(
                    suggested_highlighted, 
                    suggested_start, 
                    suggested_end, 
                    i - 1
                )
                print(f"修改建议高亮后长度: {len(suggested_highlighted)}")
                print(f"修改建议高亮后是否包含HTML: {suggested_highlighted.find('<span') != -1}")
            
            # 如果这一轮没有找到任何匹配，停止循环
            if not any([original_start_match, original_end_match, suggested_start_match, suggested_end_match]):
                print(f"⏹️ 第{i}轮未找到匹配，停止搜索")
                break

        print("✅ 高亮处理完成")
        print(f"最终修改建议长度: {len(suggested_highlighted)}")
        print(f"最终修改建议是否包含HTML: {suggested_highlighted.find('<span') != -1}")
        return original_highlighted, suggested_highlighted

    def extract_evaluation(self, result):
        """提取总体评价内容"""
        evaluation_match = re.search(r'<!-- START: 评价 -->(.*?)<!-- END: 评价 -->', result, re.DOTALL)
        if evaluation_match:
            return evaluation_match.group(1).strip()
        return ""

    def save_analysis_results(self, username, original_text, markdown_text, analysis_result, original_highlighted, suggested_highlighted):
        """保存分析结果到文件 - 优化版本"""
        try:
            # 创建用户目录
            user_dir = Path('uploads') / username / '简历分析'
            user_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存原始简历
            original_file = user_dir / f"original_resume_{timestamp}.txt"
            with open(original_file, 'w', encoding='utf-8') as f:
                f.write(original_text)
            
            # 保存Markdown格式简历
            markdown_file = user_dir / f"markdown_resume_{timestamp}.md"
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            
            # 保存高亮后的原文 - 改进HTML格式
            original_highlighted_file = user_dir / f"original_highlighted_{timestamp}.html"
            with open(original_highlighted_file, 'w', encoding='utf-8') as f:
                f.write(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>简历原文（问题高亮）</title>
                    <style>
                        body {{ 
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                            margin: 20px; 
                            line-height: 1.6; 
                            background-color: #f8f9fa;
                        }}
                        .container {{
                            max-width: 800px;
                            margin: 0 auto;
                            background: white;
                            padding: 30px;
                            border-radius: 10px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }}
                        .highlight {{ 
                            background-color: #FFE6E6; 
                            padding: 3px 6px; 
                            border-radius: 4px;
                            font-weight: bold;
                            border: 2px solid #FFE6E6;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            display: inline-block;
                            margin: 1px 2px;
                        }}
                        /* 高亮样式优化 */
                        span[style*="background-color"] {{
                            border-radius: 4px !important;
                            font-weight: bold !important;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                            display: inline-block !important;
                            margin: 1px 2px !important;
                            transition: all 0.3s ease !important;
                        }}
                        span[style*="background-color"]:hover {{
                            transform: translateY(-1px) !important;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
                        }}
                        div[style*="background-color"] {{
                            border-radius: 6px !important;
                            box-shadow: 0 3px 6px rgba(0,0,0,0.15) !important;
                            margin: 4px 0 !important;
                            font-weight: 500 !important;
                            transition: all 0.3s ease !important;
                        }}
                        div[style*="background-color"]:hover {{
                            transform: translateY(-2px) !important;
                            box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
                        }}
                        h1 {{
                            color: #333;
                            border-bottom: 2px solid #667eea;
                            padding-bottom: 10px;
                        }}
                        .content {{
                            white-space: pre-wrap;
                            background: #f8f9fa;
                            padding: 20px;
                            border-radius: 8px;
                            border: 1px solid #e9ecef;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>📄 简历原文（问题部分已高亮）</h1>
                        <div class="content">{original_highlighted}</div>
                    </div>
                </body>
                </html>
                """)
            
            # 保存高亮后的修改建议 - 改进HTML格式
            suggested_highlighted_file = user_dir / f"suggested_highlighted_{timestamp}.html"
            with open(suggested_highlighted_file, 'w', encoding='utf-8') as f:
                f.write(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>简历修改建议（修改部分高亮）</title>
                    <style>
                        body {{ 
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                            margin: 20px; 
                            line-height: 1.6; 
                            background-color: #f8f9fa;
                        }}
                        .container {{
                            max-width: 800px;
                            margin: 0 auto;
                            background: white;
                            padding: 30px;
                            border-radius: 10px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }}
                        .highlight {{ 
                            background-color: #E6FFE6; 
                            padding: 3px 6px; 
                            border-radius: 4px;
                            font-weight: bold;
                            border: 2px solid #E6FFE6;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            display: inline-block;
                            margin: 1px 2px;
                        }}
                        /* 高亮样式优化 */
                        span[style*="background-color"] {{
                            border-radius: 4px !important;
                            font-weight: bold !important;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                            display: inline-block !important;
                            margin: 1px 2px !important;
                            transition: all 0.3s ease !important;
                        }}
                        span[style*="background-color"]:hover {{
                            transform: translateY(-1px) !important;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
                        }}
                        div[style*="background-color"] {{
                            border-radius: 6px !important;
                            box-shadow: 0 3px 6px rgba(0,0,0,0.15) !important;
                            margin: 4px 0 !important;
                            font-weight: 500 !important;
                            transition: all 0.3s ease !important;
                        }}
                        div[style*="background-color"]:hover {{
                            transform: translateY(-2px) !important;
                            box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
                        }}
                        h1 {{
                            color: #333;
                            border-bottom: 2px solid #28a745;
                            padding-bottom: 10px;
                        }}
                        .content {{
                            white-space: pre-wrap;
                            background: #f8f9fa;
                            padding: 20px;
                            border-radius: 8px;
                            border: 1px solid #e9ecef;
                        }}
                        /* Markdown样式 */
                        .content h1, .content h2, .content h3 {{
                            color: #667eea;
                            margin-top: 20px;
                            margin-bottom: 10px;
                        }}
                        .content ul, .content ol {{
                            margin: 10px 0;
                            padding-left: 20px;
                        }}
                        .content li {{
                            margin: 5px 0;
                        }}
                        .content strong {{
                            color: #667eea;
                            font-weight: 600;
                        }}
                        .content code {{
                            background: rgba(102, 126, 234, 0.2);
                            padding: 2px 6px;
                            border-radius: 3px;
                            font-family: 'Courier New', monospace;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>✨ 简历修改建议（修改部分已高亮）</h1>
                        <div class="content">{suggested_highlighted}</div>
                    </div>
                </body>
                </html>
                """)
            
            # 保存分析结果
            analysis_file = user_dir / f"analysis_result_{timestamp}.json"
            analysis_data = {
                'timestamp': timestamp,
                'original_file': str(original_file),
                'markdown_file': str(markdown_file),
                'original_highlighted_file': str(original_highlighted_file),
                'suggested_highlighted_file': str(suggested_highlighted_file),
                'analysis_result': analysis_result,
                'evaluation': self.extract_evaluation(analysis_result)
            }
            
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'files': {
                    'original': str(original_file),
                    'markdown': str(markdown_file),
                    'original_highlighted': str(original_highlighted_file),
                    'suggested_highlighted': str(suggested_highlighted_file),
                    'analysis': str(analysis_file)
                }
            }
            
        except Exception as e:
            print(f"保存分析结果失败：{str(e)}")
            return {'success': False, 'error': str(e)}

    def analyze_resume_complete(self, resume_text, username):
        """完整的简历分析流程"""
        try:
            print("🚀 开始简历分析流程...")
            
            # 1. 生成Markdown格式简历
            print("📝 生成Markdown格式简历...")
            markdown_resume = self.generate_markdown_resume(resume_text)
            if not markdown_resume:
                return {'success': False, 'error': '生成Markdown简历失败'}
            print(f"✅ Markdown简历生成成功，长度: {len(markdown_resume)}")
            
            # 2. 分析简历并生成修改建议
            print("🔍 分析简历并生成修改建议...")
            analysis_result = self.analyze_resume_with_suggestions(resume_text)
            if not analysis_result:
                return {'success': False, 'error': '简历分析失败'}
            print(f"✅ 简历分析完成，结果长度: {len(analysis_result)}")
            
            # 3. 验证分析结果格式
            print("🔍 验证分析结果格式...")
            if 'suggested_first1' not in analysis_result:
                print("⚠️ 警告：分析结果中可能缺少修改建议标签")
            
            # 4. 高亮处理
            print("🎨 开始高亮处理...")
            original_highlighted, suggested_highlighted = self.extract_and_highlight(
                resume_text, 
                markdown_resume, 
                analysis_result
            )
            print(f"✅ 高亮处理完成，原文高亮长度: {len(original_highlighted)}, 修改建议高亮长度: {len(suggested_highlighted)}")
            
            # 5. 保存结果
            print("💾 保存分析结果...")
            save_result = self.save_analysis_results(
                username, 
                resume_text, 
                markdown_resume, 
                analysis_result, 
                original_highlighted, 
                suggested_highlighted
            )
            
            if not save_result['success']:
                return save_result
            
            print("✅ 分析流程完成！")
            
            # 6. 返回完整结果
            return {
                'success': True,
                'original_text': resume_text,
                'markdown_text': markdown_resume,
                'original_highlighted': original_highlighted,
                'suggested_highlighted': suggested_highlighted,
                'analysis_result': analysis_result,
                'evaluation': self.extract_evaluation(analysis_result),
                'files': save_result['files']
            }
            
        except Exception as e:
            print(f"❌ 分析流程出错: {str(e)}")
            return {'success': False, 'error': str(e)} 