# 语音分析系统

一个基于免费大模型API的语音分析系统，能够分析语音的情感、语速、流利度等特征，并生成详细的JSON分析报告。

## 功能特点

- 🎵 **多维度分析**: 分析语速、情感语调、流利度三个核心维度
- 🤖 **大模型增强**: 集成免费的大模型API提供更准确的分析
- 📝 **语音转录**: 使用Whisper模型进行语音转文字
- 📊 **详细报告**: 生成包含详细指标的JSON分析报告
- 🆓 **完全免费**: 使用免费的大模型API，无需付费

## 分析维度

### 1. 语速分析
- 语速等级（快/中等/慢）
- 语速得分（0-1分）
- 音节率
- 语音活动比例
- 总时长

### 2. 情感语调
- 情感类型（兴奋/激动、紧张/焦虑、平静/中性、低沉/悲伤）
- 情感得分（0-1分）
- 平均音调（Hz）
- 音调变化
- 音调范围
- 能量变化

### 3. 流利度
- 流利度等级（流利/一般/不流利）
- 流利度得分（0-1分）
- 停顿次数
- 停顿比例
- 语音连续性
- 节奏稳定性

## 安装要求

### 系统要求
- Python 3.8+
- Windows/Linux/macOS

### 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 如果使用增强版（推荐），还需要安装FFmpeg
# Windows: 下载FFmpeg并添加到PATH
# Linux: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
```

## 使用方法

### 基础版本

```bash
# 分析音频文件
python main.py audio_file.wav

# 指定输出文件
python main.py audio_file.wav -o result.json

# 显示详细过程
python main.py audio_file.wav --verbose
```

### 增强版本（推荐）

```bash
# 使用大模型增强分析
python enhanced_main.py audio_file.wav

# 不使用大模型API（仅声学特征）
python enhanced_main.py audio_file.wav --no-llm

# 指定输出文件
python enhanced_main.py audio_file.wav -o enhanced_result.json
```

## 支持的音频格式

- WAV (.wav)
- MP3 (.mp3)
- FLAC (.flac)
- M4A (.m4a)
- OGG (.ogg)

## 输出示例

```json
{
  "分析时间": "2024-01-15 14:30:25",
  "音频文件": "sample.wav",
  "综合得分": 0.65,
  "转录内容": "这是一个测试音频文件，用于演示语音分析功能。",
  "语速分析": {
    "语速等级": "中等",
    "语速得分": 0.5,
    "音节率": 0.12,
    "语音活动比例": 0.85,
    "总时长": 3.45
  },
  "情感语调": {
    "情感类型": "平静/中性",
    "情感得分": 0.5,
    "平均音调": 180.5,
    "音调变化": 25.3,
    "音调范围": 120.0,
    "能量变化": 0.08
  },
  "流利度": {
    "流利度等级": "流利",
    "流利度得分": 0.8,
    "停顿次数": 3,
    "停顿比例": 0.08,
    "语音连续性": 0.92,
    "节奏稳定性": 0.75
  },
  "大模型增强分析": {
    "llm_emotion": "neutral",
    "llm_confidence": 0.85
  }
}
```

## 免费大模型API配置

### Hugging Face API
1. 访问 [Hugging Face](https://huggingface.co/)
2. 注册免费账号
3. 创建API Token
4. 在代码中替换 `hf_xxx` 为你的Token

### Ollama（本地运行）
1. 安装 [Ollama](https://ollama.ai/)
2. 下载模型：`ollama pull llama2`
3. 启动服务：`ollama serve`

## 技术原理

### 声学特征提取
- **语速分析**: 基于过零率和能量包络检测语音活动
- **情感分析**: 通过音调变化、能量变化、MFCC特征判断情感
- **流利度分析**: 检测停顿、计算语音连续性、节奏稳定性

### 大模型增强
- **语音转录**: 使用OpenAI Whisper进行高精度语音转文字
- **情感分析**: 结合文本内容和声学特征进行综合分析
- **语义理解**: 通过大模型理解语音内容的语义信息

## 注意事项

1. **首次运行**: 增强版首次运行会下载Whisper模型（约1GB）
2. **网络连接**: 大模型API需要网络连接
3. **音频质量**: 建议使用清晰的音频文件以获得更好的分析结果
4. **处理时间**: 增强版分析时间较长，请耐心等待

## 故障排除

### 常见问题

1. **音频加载失败**
   - 检查音频文件格式是否支持
   - 确保文件路径正确
   - 安装FFmpeg（增强版需要）

2. **Whisper模型下载失败**
   - 检查网络连接
   - 手动下载模型文件
   - 使用基础版本

3. **大模型API调用失败**
   - 检查API配置
   - 确认网络连接
   - 使用 `--no-llm` 参数跳过

## 开发说明

### 项目结构
```
voice_analysis/
├── voice_analyzer.py          # 基础语音分析器
├── enhanced_voice_analyzer.py # 增强版分析器
├── main.py                    # 基础版本主程序
├── enhanced_main.py           # 增强版主程序
├── requirements.txt           # 依赖文件
└── README.md                  # 说明文档
```

### 扩展开发
- 添加新的声学特征提取方法
- 集成其他免费大模型API
- 开发Web界面
- 添加批量处理功能

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！ 