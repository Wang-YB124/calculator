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

## 部署

详见 [DEPLOY.md](DEPLOY.md)
