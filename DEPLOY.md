# 微积分计算器 - Railway 部署指南

## 快速部署步骤

### 1. 准备 GitHub 仓库

```bash
cd E:\website
git init
git add .
git commit -m "Initial commit: SymPy calculus backend"
git branch -M main
git remote add origin https://github.com/你的用户名/calculus-backend.git
git push -u origin main
```

### 2. 部署到 Railway

1. 访问 [railway.app](https://railway.app) 并登录（可用 GitHub 账号）
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 选择 `calculus-backend` 仓库
4. Railway 自动检测 Python 并部署
5. 等待部署完成（约 2-3 分钟）

### 3. 获取后端 URL

部署完成后，在 Railway 项目页面：
- 点击 "Settings" → "Domains"
- 复制生成的域名（如 `https://calculus-backend-production.up.railway.app`）

### 4. 更新前端配置

修改 `C:\Users\HP\Documents\Qoder\2026-10-19\1c712e71\js\app_complete.js`：

```javascript
// 找到这一行（约第 398 行）
const BACKEND_URL = 'http://localhost:5000';

// 改为你的 Railway 地址
const BACKEND_URL = 'https://calculus-backend-production.up.railway.app';
```

### 5. 重新部署前端

```bash
# 复制更新后的文件到 dist
cp js/app_complete.js dist/js/
cp index.html dist/
cp css/style.css dist/css/

# 发布到 Qoder Sites（或你使用的托管平台）
```

## 本地测试

部署前可在本地测试生产配置：

```bash
cd E:\website
pip install -r requirements.txt
gunicorn app:app --bind 0.0.0.0:8080
```

访问 `http://localhost:8080/api/health` 验证。

## 环境变量（可选）

Railway 项目 Settings → Variables 可添加：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| PORT | 服务端口 | 自动分配 |
| CORS_ORIGIN | 允许的前端域名 | * |

如需限制 CORS，修改 `app.py`：

```python
CORS(app, origins=[os.environ.get('CORS_ORIGIN', '*')])
```

## 故障排查

### 部署失败
- 检查 Railway 项目 Logs 查看错误信息
- 确保 `requirements.txt` 和 `Procfile` 在根目录

### 后端超时
- SymPy 复杂计算可能超时，Railway 免费套餐限制 30s
- 已设置 `--timeout 120` 延长到 120 秒

### CORS 错误
- 确保前端 `BACKEND_URL` 正确
- 检查浏览器控制台错误信息

## 费用说明

- Railway 免费套餐：$5/月额度，约 500 小时运行时间
- 微积分计算器访问量不大时，免费套餐足够
- 如需更高配额，Pro 计划 $5/月

## 其他部署平台

### Render.com
- 类似 Railway，免费套餐可用
- 创建 Web Service，连接 GitHub 仓库
- 构建命令：`pip install -r requirements.txt`
- 启动命令：`gunicorn app:app`

### PythonAnywhere
- 专为 Python 设计
- 免费套餐支持 Web 应用
- 手动上传代码或 Git 部署

### 自建服务器
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-pip nginx
pip3 install gunicorn flask flask-cors sympy

# 运行
gunicorn app:app --bind 0.0.0.0:8000 --workers 2

# Nginx 配置反向代理
sudo nano /etc/nginx/sites-available/calculator
```

Nginx 配置示例：
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
