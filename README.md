# 微积分计算器 - Python + SymPy 后端

强大的符号计算后端，支持求导、积分、极限、级数展开和方程求解。

## 功能特性

- **求导**: 支持任意阶导数，自动简化
- **积分**: 不定积分和定积分，支持数值近似
- **极限**: 左右极限，处理不定型
- **级数**: 泰勒级数展开，显示各项系数
- **方程求解**: 代数方程、超越方程

## 安装

```bash
# 进入项目目录
cd E:\website

# 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
python app.py
```

服务器将在 `http://localhost:5000` 启动。

## API 接口

### 1. 求导 `/api/derivative`

```javascript
POST /api/derivative
{
  "expression": "x^2 * sin(x)",
  "variable": "x",
  "order": 1
}
```

响应:
```json
{
  "success": true,
  "latex": "2 x \\sin{\\left(x \\right)} + x^{2} \\cos{\\left(x \\right)}",
  "steps": ["原函数: ...", "对 x 求导", "结果: ..."],
  "expression": "2*x*sin(x) + x**2*cos(x)"
}
```

### 2. 积分 `/api/integral`

```javascript
POST /api/integral
{
  "expression": "x * exp(x)",
  "variable": "x",
  "lower": null,
  "upper": null
}
```

定积分:
```javascript
{
  "expression": "sin(x)",
  "variable": "x",
  "lower": "0",
  "upper": "pi"
}
```

### 3. 极限 `/api/limit`

```javascript
POST /api/limit
{
  "expression": "sin(x)/x",
  "variable": "x",
  "point": "0",
  "direction": null
}
```

方向: `null` (双侧), `"+"` (右极限), `"-"` (左极限)

### 4. 级数 `/api/series`

```javascript
POST /api/series
{
  "expression": "exp(x)",
  "variable": "x",
  "point": "0",
  "order": 6
}
```

### 5. 方程求解 `/api/solve`

```javascript
POST /api/solve
{
  "expression": "x^2 - 4",
  "variable": "x"
}
```

## 前端集成

在 `app_complete.js` 中添加 API 调用函数:

```javascript
async function callBackendAPI(endpoint, data) {
  try {
    const response = await fetch(`http://localhost:5000/api/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return await response.json();
  } catch (error) {
    console.error('Backend API error:', error);
    return null;
  }
}

// 使用示例
async function computeDerivativeBackend(expr, varName = 'x', order = 1) {
  const result = await callBackendAPI('derivative', {
    expression: expr,
    variable: varName,
    order: order
  });
  
  if (result && result.success) {
    return {
      result: result.latex,
      steps: result.steps
    };
  }
  return null;
}
```

## 部署建议

1. **本地开发**: 直接运行 `python app.py`
2. **生产环境**: 使用 gunicorn
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```
3. **反向代理**: 配置 Nginx 转发到后端
4. **云服务**: 部署到 AWS/Azure/阿里云，配置 CORS 允许前端域名

## 注意事项

- SymPy 计算可能较慢，复杂表达式建议设置超时
- 某些积分无解析解，会返回失败，前端应回退到数值方法
- 前端应保留 Algebrite 作为简单计算的后备方案
