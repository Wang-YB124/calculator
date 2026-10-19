"""
微积分计算器 - SymPy 后端
提供符号计算 API，支持求导、积分、极限、级数、方程求解
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from calculator import (
    compute_derivative,
    compute_integral,
    compute_limit,
    compute_series,
    compute_solve
)

app = Flask(__name__)
CORS(app)


@app.route('/api/derivative', methods=['POST'])
def derivative():
    """计算导数"""
    try:
        data = request.get_json()
        expr = data.get('expression', '')
        var = data.get('variable', 'x')
        order = int(data.get('order', 1))
        
        result = compute_derivative(expr, var, order)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 400


@app.route('/api/integral', methods=['POST'])
def integral():
    """计算积分"""
    try:
        data = request.get_json()
        expr = data.get('expression', '')
        var = data.get('variable', 'x')
        lower = data.get('lower')
        upper = data.get('upper')
        
        result = compute_integral(expr, var, lower, upper)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 400


@app.route('/api/limit', methods=['POST'])
def limit():
    """计算极限"""
    try:
        data = request.get_json()
        expr = data.get('expression', '')
        var = data.get('variable', 'x')
        point = data.get('point', '0')
        direction = data.get('direction', None)
        
        result = compute_limit(expr, var, point, direction)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 400


@app.route('/api/series', methods=['POST'])
def series():
    """计算泰勒级数"""
    try:
        data = request.get_json()
        expr = data.get('expression', '')
        var = data.get('variable', 'x')
        point = data.get('point', '0')
        order = int(data.get('order', 6))
        
        result = compute_series(expr, var, point, order)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 400


@app.route('/api/solve', methods=['POST'])
def solve():
    """求解方程"""
    try:
        data = request.get_json()
        expr = data.get('expression', '')
        var = data.get('variable', 'x')
        
        result = compute_solve(expr, var)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 400


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'message': '微积分计算器后端运行中'})


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
