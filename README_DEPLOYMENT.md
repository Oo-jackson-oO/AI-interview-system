# Render部署配置说明

## 部署到Render的步骤

### 1. 基本配置
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`

### 2. 环境变量（可选）
- `FLASK_ENV`: `production`
- `PORT`: 自动分配（不需要手动设置）

### 3. 注意事项
- 应用会自动绑定到Render分配的端口
- 某些音频相关的包可能在Render上无法安装（已注释）
- WebSocket功能正常工作
- 静态文件会自动服务

### 4. 部署后访问
部署完成后，您将获得一个类似这样的URL：
```
https://ai-interview-system.onrender.com
```

### 5. 功能限制
- 某些本地音频处理功能可能受限
- 建议主要使用Web端的音频处理功能
- 文件上传功能正常工作
