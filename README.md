# AI智能面试系统 🎯

一个基于AI大模型、Live2D数字人和多模态技术的智能面试系统，集成了语音识别、语音合成、微表情分析、语调分析等先进技术，为用户提供沉浸式的AI面试体验。

## ✨ 项目特色

### 🤖 AI数字人面试官
- **Live2D数字人**：高质量2D数字人模型，支持嘴部同步动画
- **智能互动**：基于讯飞星火大模型的智能对话
- **太空科幻主题**：星空背景、粒子特效、流星动画等视觉效果
- **实时表情同步**：TTS语音播放时的嘴部动画同步

### 🎙️ 多模态语音技术
- **ASR实时语音识别**：基于讯飞语音识别API的智能转写
- **TTS语音合成**：超拟人语音合成，支持流式和一次性模式
- **语调情感分析**：多维度语音特征分析（语速、情感、流利度）
- **微表情识别**：基于计算机视觉的面部表情分析

### 🎯 智能面试系统
- **六大面试板块**：自我介绍、简历深挖、能力评估、岗位匹配、专业测试、反问环节
- **个性化配置**：根据岗位和简历定制面试内容
- **智能评分**：AI多维度评分和详细反馈报告
- **完整流程**：从题目生成到面试实施再到结果分析的全流程

## 🏗️ 技术架构

### 后端技术栈
- **Web框架**：Flask + Socket.IO
- **AI模型**：讯飞星火认知大模型
- **语音技术**：讯飞ASR + TTS APIs
- **图像处理**：OpenCV + Pillow
- **音频处理**：librosa + pydub + pygame
- **文档解析**：python-docx + PyPDF2

### 前端技术栈
- **Live2D**：Easy-Live2D + PixiJS
- **UI框架**：原生HTML5 + CSS3 + JavaScript
- **实时通信**：Socket.IO客户端
- **音频处理**：Web Audio API
- **媒体访问**：MediaDevices API

### 核心组件架构
```
AI面试系统/
├── app.py                 # Flask主应用，集成所有功能
├── modules/               # 功能模块
│   ├── Mock_interview/    # 面试核心模块
│   ├── resume_parsing/    # 简历解析模块
│   ├── skill_training/    # 技能训练模块
│   ├── learning_path/     # 学习路径模块
│   ├── ASR-API.py        # 语音识别服务
│   └── TTS-API.py        # 语音合成服务
├── templates/             # 前端模板
│   ├── live2d.html       # Live2D数字人界面
│   ├── interview.html    # 面试配置界面
│   └── ...
├── live2d/               # Live2D数字人资源
└── static/               # 静态资源
```

## 🚀 主要功能

### 1. 智能面试生成
- **题目智能生成**：基于AI的个性化面试题目生成
- **简历深度分析**：自动解析简历并生成针对性问题
- **多板块支持**：6个专业面试板块，可自由选择组合
- **难度分级**：根据岗位和经验调整题目难度

### 2. Live2D数字人交互
- **沉浸式体验**：高质量2D数字人面试官
- **实时动画**：语音播放时的嘴部同步动画
- **太空主题UI**：科幻风格的用户界面设计
- **智能特效**：粒子系统、流星效果、星空背景

### 3. 多模态分析
- **语音转写**：实时ASR语音识别，支持智能断句
- **语调分析**：语速、情感、流利度三维分析
- **微表情识别**：面部表情和情绪状态分析
- **综合评分**：多维度智能评分系统

### 4. 面试流程管理
- **完整流程**：题目生成→面试实施→结果分析
- **状态管理**：面试进度跟踪和状态控制
- **数据持久化**：问答记录和分析结果保存
- **报告生成**：详细的面试评估报告

## 📦 安装部署

### 环境要求
- Python 3.9——3.12
- 现代浏览器（支持WebRTC）
- 麦克风和摄像头权限
- 稳定的网络连接

### 1. 克隆项目
```bash
git clone https://github.com/yy13213/AI-intervuew-web.git
cd AI-interview-web
```

### 2. 安装依赖
```bash
pip install -r requirements.txt

```

### 3. ffmpeg安装（支持window和linux）

#### Windows系统安装
```bash
# 方法1：使用chocolatey包管理器（推荐）
# 首先安装chocolatey（如果还没有安装）
# 以管理员身份运行PowerShell，执行：
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# 安装ffmpeg
choco install ffmpeg

# 方法2：手动安装
# 1. 访问 https://ffmpeg.org/download.html
# 2. 下载Windows版本的ffmpeg
# 3. 解压到C:\ffmpeg
# 4. 将C:\ffmpeg\bin添加到系统环境变量PATH中
# 5. 重启命令行工具验证安装
ffmpeg -version

# 方法3：使用winget（Windows 10/11）
winget install ffmpeg
```

#### Linux系统安装
```bash
# Ubuntu/Debian系统
sudo apt update
sudo apt install ffmpeg

# CentOS/RHEL/Fedora系统
# CentOS 7/RHEL 7
sudo yum install epel-release
sudo yum install ffmpeg ffmpeg-devel

# CentOS 8/RHEL 8/Fedora
sudo dnf install ffmpeg ffmpeg-devel

# Arch Linux
sudo pacman -S ffmpeg

# 验证安装
ffmpeg -version
```

#### macOS系统安装
```bash
# 使用Homebrew（推荐）
brew install ffmpeg

# 使用MacPorts
sudo port install ffmpeg

# 验证安装
ffmpeg -version
```

#### 验证安装是否成功
```bash
# 检查ffmpeg版本信息
ffmpeg -version

# 检查支持的编解码器
ffmpeg -codecs

# 如果显示版本信息，说明安装成功
```

#### 常见问题解决
```bash
# 如果提示"ffmpeg不是内部或外部命令"
# Windows：检查环境变量PATH是否包含ffmpeg的bin目录
# Linux：重新安装或检查软件包源

# 如果权限问题
# Linux：使用sudo权限安装
# Windows：以管理员身份运行命令行

# 如果安装失败
# 检查网络连接
# 更新包管理器源
# 尝试从官网直接下载编译好的版本
```

### 4. 可选：配置API密钥（内置默认API）
在项目正常运行前，需要配置以下API密钥：

#### 讯飞API配置
```python
# 在 modules/ASR-API.py 中配置
ASR_APP_ID = "your-asr-app-id"
ASR_API_KEY = "your-asr-api-key"

# 在 modules/TTS-API.py 中配置  
TTS_APP_ID = "your-tts-app-id"
TTS_API_KEY = "your-tts-api-key"
TTS_API_SECRET = "your-tts-api-secret"

# 在 modules/Mock_interview/init.py 中配置星火大模型
client = OpenAI(
    api_key='your-spark-api-key',
    base_url='https://spark-api-open.xf-yun.com/v1/'
)
```

#### API密钥获取方式
1. **访问讯飞开放平台**：https://www.xfyun.cn/
2. **注册并登录账户**
3. **创建应用获取密钥**：
   - 语音听写（ASR）
   - 语音合成（TTS）
   - 星火认知大模型
4. **将获取的密钥填入对应文件**

#### 配置文件位置
```
项目根目录/
├── modules/
│   ├── ASR-API.py          # ASR语音识别密钥
│   ├── TTS-API.py          # TTS语音合成密钥
│   └── Mock_interview/
│       └── init.py         # 星火大模型密钥
```

### 5. 启动系统
```bash
python app.py
```

### 6. 访问系统
打开浏览器访问：`http://localhost:5000`

## 🎮 使用指南

### 1. 用户注册登录
- 访问系统首页
- 注册新用户或登录现有账户
- 完善个人信息

### 2. 简历上传与解析
- 上传PDF/DOCX格式简历
- 系统自动解析简历内容
- 提取关键信息用于面试生成

### 3. 面试配置
- 选择目标岗位和技术领域
- 配置面试模式（普通/严格）
- 选择面试板块组合
- 生成个性化面试题目

### 4. Live2D面试体验
- 进入Live2D数字人界面
- 系统自动开启语音和视频分析
- 与AI面试官进行实时对话
- 系统记录并分析面试过程

### 5. 结果查看
- 查看详细面试报告
- 多维度评分和建议
- 语音和表情分析结果
- 改进建议和学习计划

## 🎯 核心模块介绍

### 面试智能体 (Mock_interview)
```python
# 核心功能
- 题目生成：AI智能生成面试题目
- 面试实施：完整的面试流程管理  
- 结果分析：多维度评分和反馈
- 板块模块：6个专业面试板块
```

### 语音技术模块 (ASR/TTS)
```python
# ASR语音识别
- 实时转写：流式语音识别
- 智能断句：自动识别语句边界
- 静音检测：智能开始/停止录音

# TTS语音合成
- 超拟人合成：高质量语音输出
- 流式播放：边合成边播放
- 嘴部同步：Live2D动画同步
```

### 多模态分析
```python
# 语调分析
- 语速检测：快/中等/慢级别
- 情感识别：兴奋/紧张/平静/低沉
- 流利度评估：停顿分析和连贯性

# 微表情识别  
- 面部检测：实时面部关键点
- 表情分类：喜怒哀乐等情绪
- 置信度评分：表情识别准确度
```

## 🔧 配置说明

### 面试配置文件
```json
{
  "interview_config": {
    "candidate_name": "张三",
    "position": "Python开发工程师", 
    "target_company": "科技公司",
    "tech_domain": "Python, Django, Flask",
    "strict_mode": true,
    "selected_sections": ["自我介绍", "简历深挖", "专业能力测试"]
  }
}
```

### 系统设置
```javascript
{
  "voice": false,           // 语音播放
  "voiceAnalysis": true,    // 语调分析
  "facialAnalysis": true,   // 微表情识别
  "asrRecognition": false,  // ASR语音识别
  "ttsEnabled": false,      // TTS语音合成
  "mouseFollow": true,      // 鼠标跟随
  "particles": true         // 粒子特效
}
```

## 📊 数据流程

### 面试数据流
```
用户注册 → 简历上传 → 简历解析 → 面试配置 → 题目生成 
→ Live2D面试 → 实时分析 → 结果保存 → 报告生成
```

### 语音处理流
```
麦克风输入 → Web Audio API → Socket.IO → ASR API 
→ 实时转写 → 结果显示 → 语调分析 → 评分输出
```

### 视频分析流  
```
摄像头输入 → Canvas捕获 → 图像处理 → 面部检测
→ 特征提取 → 表情识别 → 情绪分析 → 报告生成
```

## 🎨 界面特色

### 太空科幻主题
- **星空背景**：动态星空粒子效果
- **流星动画**：周期性流星划过效果
- **行星装饰**：土星、木星等行星元素
- **空间站**：科幻感的空间站装饰
- **火箭鼠标**：火箭形状的鼠标指针

### 交互体验
- **毛玻璃效果**：现代化的UI视觉效果
- **平滑动画**：流畅的过渡和交互动画
- **响应式设计**：适配不同屏幕尺寸
- **实时反馈**：即时的操作反馈和状态显示

## 🔬 技术亮点

### 1. 实时多模态融合
- 同时处理语音、视频、文本多种模态
- 实时分析和反馈用户状态
- 多维度综合评估面试表现

### 2. AI驱动的个性化  
- 基于简历内容生成针对性题目
- 根据岗位要求调整面试难度
- 智能化的评分和建议系统

### 3. 高质量用户体验
- Live2D数字人提供沉浸式体验
- 太空主题UI设计独特美观
- 流畅的实时语音视频交互

### 4. 模块化架构设计
- 功能模块独立可扩展
- API接口统一标准化
- 支持灵活的功能组合

## 📈 性能特点

- **低延迟**：实时语音识别延迟<500ms
- **高准确率**：语音识别准确率>95%
- **稳定性**：支持长时间连续使用
- **并发支持**：多用户同时使用
- **资源优化**：合理的内存和CPU使用

## 🛠️ 开发扩展

### 添加新的面试板块
```python
# 在Mock_interview模块中添加新板块
class NewInterviewSection:
    def conduct_interview(self, num_questions=2):
        # 实现面试逻辑
        pass
```

### 集成新的AI模型
```python
# 替换AI模型配置
client = OpenAI(
    api_key='your-api-key',
    base_url='new-api-endpoint'
)
```

### 自定义分析维度
```python
# 添加新的分析维度
analysis_dimensions = {
    "new_dimension": {
        "weight": 0.1,
        "analyzer": NewAnalyzer()
    }
}
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- 讯飞开放平台提供语音技术支持
- Live2D提供数字人技术

## 📞 联系方式

- 项目地址：[GitHub Repository](https://github.com/your-repo/AI-interview-system)
- 问题反馈：[Issues](https://github.com/your-repo/AI-interview-system/issues)
- 技术交流：[Discussions](https://github.com/your-repo/AI-interview-system/discussions)

---

**🚀 让AI面试更智能，让求职更高效！**
