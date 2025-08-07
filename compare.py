@app.route('/api/get_projects', methods=['GET'])
@login_required
def get_user_projects():
    """获取用户的所有项目列表"""
    try:
        # 从session获取用户ID
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'code': 401,
                'message': '请先登录',
                'status': 'fail'
            }), 401

        # 查询该用户创建的所有项目
        projects = project.query.filter_by(creator_id=user_id).all()
        
        if not projects:
            return jsonify({
                'code': 200,
                'message': '未找到相关项目',
                'status': 'success',
                'data': []
            }), 200
            
        # 构建项目列表
        project_list = [{
            'project_id': p.project_id,
            'project_name': p.project_name
        } for p in projects]
        
        app.logger.info(f"用户 {user_id} 查询到 {len(project_list)} 个项目")
        
        return jsonify({
            'code': 200,
            'message': '获取项目列表成功',
            'status': 'success',
            'data': project_list
        }), 200
        
    except Exception as e:
        app.logger.error(f"获取项目列表失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '获取项目列表失败，请稍后重试',
            'status': 'fail'
        }), 500

# 文件对比
def read_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f" 无法读取文件: {filepath}")
        print(e)
        return None
#TODO： 修改提示词，需要的返回是文章具体内容
def compare_patents(patent_text_1, patent_text_2):
    prompt = f"""
    你是一个专业的专利分析助手。请对比下面两篇专利说明书的内容，找出它们在技术方案、技术手段、用途、结构、原理等方面的相似之处。

    请按照以下格式回答，支持多处相似内容：

    <index1>第1处相似：</index1>
    第一篇专利中相似部分：
    起始句：<p1first1>（原文中第一句）</p1first1>
    相似部分结束后的下一句：<p1last1>（相似部分最后一句的下一句）</p1last1>

    第二篇专利中相似部分：
    起始句：<p2first1>（原文中第一句）</p2first1>
    相似部分结束后的下一句：<p2last1>（相似部分最后一句的下一句）</p2last1>

    <index2>第2处相似：</index2>
    第一篇专利中相似部分：
    起始句：<p1first2>（原文中第一句）</p1first2>
    相似部分结束后的下一句：<p1last2>（相似部分最后一句的下一句）</p1last2>

    第二篇专利中相似部分：
    起始句：<p2first2>（原文中第一句）</p2first2>
    相似部分结束后的下一句：<p2last2>（相似部分最后一句的下一句）</p2last2>

    （以此类推）

    针对第一篇专利的修改建议：
    <!-- START: 摘要 -->
    请根据上述相似内容，提出一个具体可行的修改建议，用以增强第一篇专利的独特性或规避重复问题。
    <!-- END: 摘要 -->

    
    注意事项：
    - 请严格从原文中提取句子；
    - 每处相似内容都必须使用编号包裹（如 <index1>、<p1first1>、<p2last1> 等）；
    - 不要添加无关解释或总结，只列出相似内容；
    - 每一处都需要提供修改建议并包裹在 <!-- START: 摘要 --> 和 <!-- END: 摘要 --> 标签内；
    - 如果没有找到相似之处，请明确写“未发现相似内容”。
    - 最多只返回7处,即最多7个编号;

    专利说明书1：
    {patent_text_1}

    专利说明书2：
    {patent_text_2}
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1",  # 或 "gpt-4.0" / "gpt-4.1"，视你的账户权限而定
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )
        return completion.choices[0].message.content

    except Exception as e:
        print(" 调用 ChatGPT 失败：")
        traceback.print_exc()
        return None
#按照关键字进行搜索
def search(keyword):
    # 查询参数配置
    Url= baseUrl+'/s'
    requestsparams = {
        't' : basetoken,
        'q' : keyword,
        #'s' : 'relation',
        'v' : 1
    }

    # 发起接口网络请求
    response = requests.get(Url, params=requestsparams)
    # 解析响应结果
    if response.status_code == 200:
        responseResult = response.json()
        # 网络请求成功。可依据业务逻辑和接口文档说明自行处理。
        patents = responseResult['patents']
        ans5={}
        for i in patents:
            ans5[i['title']]=i['id']
            if len(ans5)==5:
                break
        return ans5

    else:
        # 网络异常等因素，解析结果异常。可依据业务逻辑自行处理。
        return '请求异常'
#获取基本信息
def getpatentbase(id):
    # 查询参数配置
    Url= baseUrl+'/patent/base'
    requestsparams = {
        't' : basetoken,
        'id' : id,
        'v' : 1
    }
    # 发起接口网络请求
    response = requests.get(Url, params=requestsparams)
    # 解析响应结果
    if response.status_code == 200:
        responseResult = response.json()
        # 网络请求成功。可依据业务逻辑和接口文档说明自行处理。
        return responseResult['patent']
    else:
        #
        return '请求异常'
#获取说明书
def getpatent(id):
    # 查询参数配置
    Url= baseUrl+'/patent/desc'
    requestsparams = {
        't' : basetoken,
        'id' : id,
        'v' : 1
    }
    # 发起接口网络请求
    response = requests.get(Url, params=requestsparams)
    # 解析响应结果
    if response.status_code == 200:
        responseResult = response.json()
        # 网络请求成功。可依据业务逻辑和接口文档说明自行处理。
        return responseResult['patent']['description']
    else:
        # 网络异常等因素，解析结果异常。可依据业务逻辑自行处理。
        return '请求异常'
# 获取权利要求书
def getpatentclaims(id):
    # 查询参数配置
    Url= baseUrl+'/patent/claims'
    requestsparams = {
        't' : basetoken,
        'id' : id,
        'v' : 1
    }
    # 发起接口网络请求
    response = requests.get(Url, params=requestsparams)
    # 解析响应结果
    if response.status_code == 200:
        responseResult = response.json()
        # 网络请求成功。可依据业务逻辑和接口文档说明自行处理。
        return responseResult['patent']['claims']
    else:
        return '请求异常'
#获取整个pdf，返回的是存储的路径
def getpdf(id, user_id, project_name):
    # 查询参数配置
    tmpkey = getpatentbase(id)['pdfList'][0]
    Url= baseUrl+'/pdf'
    requestsparams = {
        'key': tmpkey,
        't' : basetoken,
        'v' : 1
    }
    # 发起接口网络请求
    response = requests.get(Url, params=requestsparams)
    # 解析响应结果
    if response.status_code == 200:
       # 构建保存路径
        current_dir = Path(__file__).parent # 获取当前文件的上级目录
        base_dir = current_dir.parent  # 再上一级目录
        # 构建用户项目目录路径
        user_id = str(user_id)
        user_project_dir = f"{user_id}_{project_name}" if user_id and project_name else 'temp'
        save_dir = base_dir / 'uploads' / user_project_dir / '专利对比'
        # 创建目录（如果不存在）
        os.makedirs(save_dir, exist_ok=True)
        # 构建完整的文件保存路径
        filepath = save_dir / f"{id}.pdf"
        # 保存为 PDF 文件
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
    else:
        #print("下载失败，状态码：", response.status_code)
        return response.status_code
def read_file(filepath):
    """读取文件内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ 无法读取文件: {filepath}")
        print(e)
        return None
def write_file(filepath, content):
    """写入文件内容"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"❌ 无法写入文件: {filepath}")
        print(e)
def fuzzy_find_range(text, start_sentence, end_sentence, color_index):
    """模糊查找并高亮文本范围"""
    text_lower = text.lower()
    start_sentence = start_sentence.strip()
    end_sentence = end_sentence.strip()

    # 1. 句子级别分割（句号/换行）
    sentence_list = re.split(r'[。！？\n]', text)

    # 2. 增加候选数量，降低 cutoff
    start_candidates = difflib.get_close_matches(start_sentence, sentence_list, n=3, cutoff=0.4)
    end_candidates = difflib.get_close_matches(end_sentence, sentence_list, n=3, cutoff=0.4)

    if not start_candidates or not end_candidates:
        print("⚠️ 未找到模糊匹配内容。")
        return text

    # 3. 选取匹配结果中在 text 中都能找到的位置最早的组合
    for start_text in start_candidates:
        for end_text in end_candidates:
            start_text = start_text.strip()
            end_text = end_text.strip()
            start_index = text.find(start_text)
            end_index = text.find(end_text, start_index)
            if start_index != -1 and end_index != -1:
                end_index += len(end_text)

                before = text[:start_index]
                full_text = text[start_index:end_index]
                after = text[end_index:]

                color_name = HIGHLIGHT_COLORS[color_index % len(HIGHLIGHT_COLORS)]
                color = COLOR_MAP[color_name]
                colored_full = f"<span style=\"background-color: {color};\">{full_text}</span>"
                return before + colored_full + after

    print("⚠️ 找到匹配候选，但位置索引失败。")
    return text
def extract_and_highlight(patent_text_1, patent_text_2, comparison_result):
    """提取并高亮相似内容"""
    for i in range(1, 20):
        p1_start_match = re.search(rf"<p1first{i}>(.*?)</p1first{i}>", comparison_result)
        p1_end_match = re.search(rf"<p1last{i}>(.*?)</p1last{i}>", comparison_result)
        p2_start_match = re.search(rf"<p2first{i}>(.*?)</p2first{i}>", comparison_result)
        p2_end_match = re.search(rf"<p2last{i}>(.*?)</p2last{i}>", comparison_result)

        if not all([p1_start_match, p1_end_match, p2_start_match, p2_end_match]):
            break

        p1_start = p1_start_match.group(1).strip()
        p1_end = p1_end_match.group(1).strip()
        p2_start = p2_start_match.group(1).strip()
        p2_end = p2_end_match.group(1).strip()

        patent_text_1 = fuzzy_find_range(patent_text_1, p1_start, p1_end, color_index=i - 1)
        patent_text_2 = fuzzy_find_range(patent_text_2, p2_start, p2_end, color_index=i - 1)

    return patent_text_1, patent_text_2
def extract_summary(result):
    """提取摘要内容"""
    summary_match = re.search(r'<!-- START: 摘要 -->(.*?)<!-- END: 摘要 -->', result, re.DOTALL)
    if summary_match:
        return summary_match.group(1).strip()
    return ""

def collect_all_summaries(result):
    """收集所有摘要"""
    summaries = re.findall(r'<!-- START: 摘要 -->(.*?)<!-- END: 摘要 -->', result, re.DOTALL)
    return '\n\n'.join(summary.strip() for summary in summaries)

@app.route('/api/patent_comparsion_1', methods=['POST'])
def contrast():
    try:
        data = request.json
        app.logger.info(data)
        user_id = session.get('user_id')
        project_id = session.get('project_id')
        if not user_id or not project_id:
            app.logger.warning("Missing user_id or project_id in session")
            return jsonify({
                'code': 400,
                'message': '请先登录并选择项目',
                'status': 'fail'
            }), 400
        original_file = project_file.query.filter_by(
            project_id=project_id,
            type='final_tec'
        ).first()
        if not original_file:
            app.logger.error("❌ 未找到原始技术文件")
            return jsonify({
                'code': 404,
                'message': '未找到原始技术文件，请先上传',
                'status': 'fail'
            }), 404
        keyword = data.get('keyword')
        print(original_file.file_path)
        patent1 = read_file(original_file.file_path)
        if not patent1:
            app.logger.error("❌ 无法读取原始技术文件")
            return jsonify({
                'code': 404,
                'message': '文档读取失败，请稍后重试',
                'status': 'fail'
            }), 404
        current_dir = os.path.dirname(__file__)
        current_dir = os.path.join(current_dir,'uploads')
        patent1 = read_file(original_file.file_path)
        if not patent1:
            app.logger.error("❌ 无法读取第一个专利文档")
            return jsonify({
            'code': 404,
            'message': '文档读取失败，请稍后重试',
            'status': 'fail'
        }), 404
        if not keyword:
            app.logger.error('关键字缺失')
            return jsonify({
            'code': 400,
            'message': '关键字缺失，请重试',
            'status': 'fail'
        }), 400
        
        search_results = search(keyword)
        
        if not search_results:
            app.logger.error("❌ 未找到相关专利")
            return jsonify({
            'code': 400,
            'message': '未找到相关专利，请重试',
            'status': 'fail'
        }), 400
        # 构建搜索结果列表
        patent_list = [{
            'id': id,
            'title': title
        } for title, id in search_results.items()]
        return jsonify({
            'code': 200,
            'message': '获取专利列表成功',
            'status': 'success',
            'data': {
                'patents': patent_list
            }
        }), 200
    except Exception as e:
        app.logger.error(f"对比专利获取失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '获取失败，请稍后重试',
            'status': 'fail'
        }), 500
    
@app.route('/api/patent_comparsion_2', methods=['POST'])
def patent_comparison():
    try:
        data = request.json
        patents = data.get('data',{}).get('patents',[])
        if not patents:
            app.logger.error("❌ 未找到相关返回专利号")
            return jsonify({
            'code': 400,
            'message': '未找到相关专利，请重试',
            'status': 'fail'
        }), 400
        # 获取用户选择的专利序号
        compare_count = len(patents)
        app.logger.info(f"用户选择对比 {compare_count} 个专利")
        patent_ids = []
        user_id = session.get('user_id')
        project_id = session.get('project_id')
        project_name = project.query.filter_by(project_id=project_id).first()
        origin_file = project_file.query.filter_by(
            project_id=project_id,
            type='final_tec'
        ).first()
        comparison_results = []
        if not origin_file:
            return jsonify({
                'code': 404,
                'message': '未找到原始文件',
                'status': 'fail'
            }), 404
        # 获取项目名称，默认为'temp_project'
        for patent in patents:
            if 'id' in patent:
                patent_id = patent['id']
                patent_title = patent['title']
                patent_ids.append(patent_id)
                app.logger.info(f"处理专利: ID={patent_id}")
        # 进行专利对比
        for patent in patent_ids:
            try:
                # 获取选中的专利名称
                # patent2_path = getpdf(patent,user_id, project_name.project_name)
                patent2_path = "D:/patent/backend/uploads/3_智能玉米种植/专利对比/CN106818073A.pdf"
                # TODO：pdf2md
                app.logger.info(patent2_path)
                patent_tool_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(patent2_path)))), 'patent_1', 'patent_tool.py')
                app.logger.info(patent_tool_path)
                patent2_path_out =os.path.dirname(patent2_path) 
                command = f"python {patent_tool_path} convert -i {patent2_path} -o {patent2_path_out}"
                # subprocess.run(command, shell=True, check=True)
                app.logger.info(f"执行命令: {command}")
                patent2_path_out = os.path.join(patent2_path_out,"output.md")
                patent2 = read_file(patent2_path_out)
                if not patent2:
                    continue
                # 生成输出文件名
                # output_name = f"{patent}_vs"
                # patent1_new_path = os.path.join(current_dir, f"{output_name}.md")
                # 对比专利
                patent1 = read_file(origin_file.file_path)
                result = compare_patents(patent1, patent2)
                if result:
                     # 高亮处理
                    patent1_highlighted, patent2_highlighted = extract_and_highlight(
                        patent1, 
                        patent2, 
                        result
                    )
                    patent1_highlight_path = os.path.join(current_dir, f"original_highlighted_{project_name.project_name}.md")
                    patent2_highlight_path = os.path.join(current_dir, f"compare_highlighted_{patent}.md")
                    write_file(patent1_highlight_path, patent1_highlighted)
                    write_file(patent2_highlight_path, patent2_highlighted)
                    content_1 = process_markdown_content(patent1_highlight_path)
                    content_2 = process_markdown_content(patent2_highlight_path)
                    all_summaries = collect_all_summaries(result)
                    # 添加到结果列表
                    comparison_results.append({
                        'patent_id': patent,
                        'patent_title': patent_title,
                        'original_content': content_1,
                        'compared_content': content_2,
                        'comparison_result': result,
                        'modification_suggestions': all_summaries
                    })
                else:
                    app.logger.error("⚠️ 分析失败，请检查错误信息。")
            
            except ValueError:
                app.logger.error(f"处理专利 {patent_id} 时出错: {str(e)}")
                continue
        return jsonify({
                'code': 200,
                'message': '专利对比完成',
                'status': 'success',
                'data': {
                    'comparisons': comparison_results
                }
            }), 200
    except Exception as e:
         app.logger.error(f"❌ 处理过程中出错：{str(e)}")
         return jsonify({
            'code': 500,
            'message': f'处理失败：{str(e)}',
            'status': 'fail'
        }), 500
# 获取项目加工后markdown
def process_markdown_content(file_path: str) -> str:
    """
    处理 Markdown 文件：
    1. 读取文件内容
    2. 删除图片引用
    3. 删除摘要附图相关内容
    
    Args:
        file_path (str): Markdown 文件路径
    
    Returns:
        str: 处理后的 Markdown 内容
    """
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 删除图片引用 (格式如: ![alt text](image.jpg))
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
        
        # 删除"摘要附图"相关内容
        content = re.sub(
            r'<!-- START: 摘要附图 -->.*?<!-- END: 摘要附图 -->\n?',
            '',
            content,
            flags=re.DOTALL
        )
        
        # 删除多余的空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content
        
    except Exception as e:
        app.logger.error(f"处理 Markdown 文件失败: {str(e)}")
        raise

import queue
from datetime import datetime
from urllib.parse import urlparse, urlencode
from wsgiref.handlers import format_date_time
from time import mktime
import _thread as thread
# 添加模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入各个模块
from modules.resume_parsing import ResumeParser
from modules.resume_parsing.backend.resume_analyzer import ResumeAnalyzer

