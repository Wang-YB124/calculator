"""
SymPy 符号计算核心模块
"""

import sympy as sp
from sympy import symbols, sympify, latex, oo, zoo, nan
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import re


def parse_expression(expr_str, var_name='x'):
    """解析数学表达式为 SymPy 表达式"""
    var = symbols(var_name)
    
    s = str(expr_str).strip()
    
    # 替换常见数学符号
    s = s.replace('π', 'pi')
    s = s.replace('∞', 'oo')
    
    # 将 ^ 替换为 ** (SymPy 幂运算符)
    s = s.replace('^', '**')
    
    # 替换数学函数名为 SymPy 函数
    s = re.sub(r'\bln\(', 'log(', s)
    s = re.sub(r'\blog\(', 'log(', s)
    s = re.sub(r'\barcsin\(', 'asin(', s)
    s = re.sub(r'\barccos\(', 'acos(', s)
    s = re.sub(r'\barctan\(', 'atan(', s)
    s = re.sub(r'\barcsinh\(', 'asinh(', s)
    s = re.sub(r'\barccosh\(', 'acosh(', s)
    s = re.sub(r'\barctanh\(', 'atanh(', s)
    s = re.sub(r'\bcsc\(', '1/sin(', s)
    s = re.sub(r'\bsec\(', '1/cos(', s)
    s = re.sub(r'\bcot\(', 'cos(%s)/sin(%s)', s)
    s = re.sub(r'\babs\(', 'Abs(', s)
    s = re.sub(r'\bexp\(', 'exp(', s)
    
    # 处理常数 e (单独的 e，不是 exp 或函数名的一部分)
    s = re.sub(r'\be\b(?!\*)', 'E', s)
    
    # 使用 SymPy 解析器
    transformations = standard_transformations + (implicit_multiplication_application,)
    
    try:
        local_dict = {var_name: var, 'pi': sp.pi, 'E': sp.E, 'oo': oo, 'e': sp.E}
        expr = parse_expr(s, transformations=transformations, local_dict=local_dict)
        return expr, var
    except Exception as e:
        raise ValueError(f"无法解析表达式: {expr_str} (转换后: {s})")


def compute_derivative(expr_str, var_name='x', order=1):
    """
    计算导数
    返回: {success, latex, steps, expression}
    """
    try:
        expr, var = parse_expression(expr_str, var_name)
        
        # 计算导数
        result = sp.diff(expr, var, order)
        
        # 简化结果
        result_simplified = sp.simplify(result)
        
        # 生成 LaTeX
        latex_result = latex(result_simplified)
        
        # 生成步骤
        steps = []
        steps.append(f"原函数: $f({var_name}) = {latex(expr)}$")
        
        if order == 1:
            steps.append(f"对 {var_name} 求导")
        else:
            steps.append(f"对 {var_name} 求 {order} 阶导数")
        
        # 添加中间步骤（如果表达式较复杂）
        if len(str(expr)) > 20:
            if expr.is_Mul:
                steps.append("应用乘法法则")
            elif expr.is_Add:
                steps.append("应用加法法则，逐项求导")
            elif expr.is_Pow:
                steps.append("应用幂法则或链式法则")
        
        steps.append(f"结果: $f^{{({order})}}({var_name}) = {latex_result}$")
        
        return {
            'success': True,
            'latex': latex_result,
            'steps': steps,
            'expression': str(result_simplified)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'latex': None,
            'steps': []
        }


def compute_integral(expr_str, var_name='x', lower=None, upper=None):
    """
    计算积分（不定积分或定积分）
    返回: {success, latex, steps, expression, numerical}
    """
    try:
        expr, var = parse_expression(expr_str, var_name)
        
        # 判断是定积分还是不定积分
        is_definite = lower is not None and upper is not None
        
        if is_definite:
            # 定积分
            lower_sym = parse_expression(str(lower), var_name)[0] if not isinstance(lower, (int, float)) else lower
            upper_sym = parse_expression(str(upper), var_name)[0] if not isinstance(upper, (int, float)) else upper
            
            result = sp.integrate(expr, (var, lower_sym, upper_sym))
            
            # 尝试数值计算
            numerical = None
            try:
                numerical = float(result.evalf())
            except:
                pass
            
            latex_result = latex(result)
            
            steps = []
            steps.append(f"计算定积分: $\\int_{{{latex(lower_sym)}}}^{{{latex(upper_sym)}}} {latex(expr)} \\, d{var_name}$")
            
            # 尝试添加步骤
            if result.is_number:
                steps.append("使用牛顿-莱布尼茨公式")
                antideriv = sp.integrate(expr, var)
                steps.append(f"原函数: $F({var_name}) = {latex(antideriv)}$")
                steps.append(f"代入上下限: $F({latex(upper_sym)}) - F({latex(lower_sym)})$")
            
            steps.append(f"结果: ${latex_result}$")
            if numerical is not None:
                steps.append(f"数值近似: ${numerical:.10f}$")
            
            return {
                'success': True,
                'latex': latex_result,
                'steps': steps,
                'expression': str(result),
                'numerical': numerical,
                'definite': True
            }
        else:
            # 不定积分
            result = sp.integrate(expr, var)
            
            # 检查是否成功
            if result.has(sp.Integral):
                return {
                    'success': False,
                    'error': '该积分无初等原函数',
                    'latex': None,
                    'steps': [],
                    'definite': False
                }
            
            latex_result = latex(result)
            
            steps = []
            steps.append(f"计算不定积分: $\\int {latex(expr)} \\, d{var_name}$")
            
            # 添加积分技巧提示
            if expr.is_Mul:
                steps.append("可能使用了换元积分法或分部积分法")
            elif expr.has(sp.log) or expr.has(sp.exp):
                steps.append("处理对数或指数函数")
            
            steps.append(f"结果: ${latex_result} + C$")
            
            return {
                'success': True,
                'latex': latex_result + ' + C',
                'steps': steps,
                'expression': str(result),
                'definite': False
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'latex': None,
            'steps': [],
            'definite': is_definite if 'is_definite' in locals() else False
        }


def compute_limit(expr_str, var_name='x', point='0', direction=None):
    """
    计算极限
    返回: {success, latex, steps, expression}
    """
    try:
        expr, var = parse_expression(expr_str, var_name)
        
        # 解析极限点
        point_sym = parse_expression(str(point), var_name)[0] if not isinstance(point, (int, float)) else point
        
        # 计算极限
        if direction == '+':
            result = sp.limit(expr, var, point_sym, '+')
            dir_str = '^+'
        elif direction == '-':
            result = sp.limit(expr, var, point_sym, '-')
            dir_str = '^-'
        else:
            result = sp.limit(expr, var, point_sym)
            dir_str = ''
        
        latex_result = latex(result)
        
        steps = []
        steps.append(f"计算极限: $\\lim_{{{var_name} \\to {latex(point_sym)}}}{dir_str} {latex(expr)}$")
        
        # 检查是否是不定型
        try:
            val = expr.subs(var, point_sym)
            if val == nan or val == zoo:
                steps.append("直接代入得到不定型，需要化简")
                
                # 检查是否是 0/0 或 ∞/∞
                if expr.is_Mul or expr.is_Pow:
                    steps.append("应用洛必达法则或代数化简")
        except:
            steps.append("分析函数行为")
        
        steps.append(f"结果: ${latex_result}$")
        
        return {
            'success': True,
            'latex': latex_result,
            'steps': steps,
            'expression': str(result)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'latex': None,
            'steps': []
        }


def compute_series(expr_str, var_name='x', point='0', order=6):
    """
    计算泰勒级数展开
    返回: {success, latex, steps, expression, terms}
    """
    try:
        expr, var = parse_expression(expr_str, var_name)
        
        # 解析展开点
        point_sym = parse_expression(str(point), var_name)[0] if not isinstance(point, (int, float)) else point
        
        # 计算泰勒级数
        series_result = sp.series(expr, var, point_sym, order + 1)
        
        # 移除 O() 项
        series_expr = series_result.removeO()
        
        latex_result = latex(series_expr)
        
        steps = []
        steps.append(f"在 ${var_name} = {latex(point_sym)}$ 处展开泰勒级数")
        steps.append(f"展开到 {order} 阶")
        
        # 显示前几项的导数
        steps.append("计算各阶导数:")
        for i in range(min(4, order + 1)):
            deriv = sp.diff(expr, var, i)
            deriv_at_point = deriv.subs(var, point_sym)
            if i == 0:
                steps.append(f"$f({latex(point_sym)}) = {latex(deriv_at_point)}$")
            else:
                steps.append(f"$f^{{({i})}}({latex(point_sym)}) = {latex(deriv_at_point)}$")
        
        steps.append(f"结果: ${latex_result} + \\cdots$")
        
        # 提取各项系数
        terms = []
        for i in range(order + 1):
            coeff = sp.diff(expr, var, i).subs(var, point_sym) / sp.factorial(i)
            terms.append({
                'order': i,
                'coefficient': str(coeff),
                'latex': latex(coeff)
            })
        
        return {
            'success': True,
            'latex': latex_result,
            'steps': steps,
            'expression': str(series_expr),
            'terms': terms
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'latex': None,
            'steps': [],
            'terms': []
        }


def compute_solve(expr_str, var_name='x'):
    """
    求解方程
    返回: {success, latex, steps, expression, solutions}
    """
    try:
        expr, var = parse_expression(expr_str, var_name)
        
        # 求解方程 expr = 0
        solutions = sp.solve(expr, var)
        
        if not solutions:
            return {
                'success': False,
                'error': '无解',
                'latex': None,
                'steps': [],
                'solutions': []
            }
        
        # 生成 LaTeX
        solutions_latex = [latex(sol) for sol in solutions]
        
        if len(solutions) == 1:
            latex_result = f"{var_name} = {solutions_latex[0]}"
        else:
            latex_result = f"{var_name} \\in \\{{{', '.join(solutions_latex)}\\}}"
        
        steps = []
        steps.append(f"求解方程: ${latex(expr)} = 0$")
        
        # 添加求解策略提示
        if expr.is_Poly:
            degree = expr.as_poly().degree()
            if degree == 1:
                steps.append("一元一次方程")
            elif degree == 2:
                steps.append("一元二次方程，使用求根公式")
            else:
                steps.append(f"{degree} 次方程")
        elif expr.has(sp.exp) or expr.has(sp.log):
            steps.append("包含指数或对数函数，需要代数变换")
        elif expr.has(sp.sin) or expr.has(sp.cos):
            steps.append("三角方程，考虑周期性")
        
        steps.append(f"解: ${latex_result}$")
        
        # 数值近似
        solutions_numeric = []
        for sol in solutions:
            try:
                numeric = complex(sol.evalf())
                if abs(numeric.imag) < 1e-10:
                    solutions_numeric.append(float(numeric.real))
                else:
                    solutions_numeric.append(str(numeric))
            except:
                solutions_numeric.append(str(sol))
        
        return {
            'success': True,
            'latex': latex_result,
            'steps': steps,
            'expression': str(solutions),
            'solutions': [str(sol) for sol in solutions],
            'solutions_numeric': solutions_numeric
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'latex': None,
            'steps': [],
            'solutions': []
        }
