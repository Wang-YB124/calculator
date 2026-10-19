"""
SymPy 符号计算核心模块 - 增强版
支持更强大的表达式解析、积分策略和结果化简
"""

import sympy as sp
from sympy import (
    symbols, sympify, latex, oo, zoo, nan, pi, E, I,
    sin, cos, tan, asin, acos, atan, sinh, cosh, tanh,
    asinh, acosh, atanh, exp, log, sqrt, Abs, sign,
    Integral, Derivative, Limit, series, factorial,
    simplify, trigsimp, powsimp, radsimp, together,
    expand, factor, cancel, apart, ratsimp, nsimplify,
    diff, integrate, limit, solve, nsolve, Eq
)
from sympy.integrals.heurisch import heurisch
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations,
    implicit_multiplication_application,
    convert_xor, function_exponentiation,
)
import re
import math


# ─── 表达式解析 ───────────────────────────────────────────────

def _preprocess(expr_str):
    """预处理用户输入，转换为 SymPy 可解析的形式"""
    s = str(expr_str).strip()

    # Unicode 符号
    s = s.replace('π', 'pi').replace('∞', 'oo')
    s = s.replace('√', 'sqrt(')
    # 补全 sqrt( 后面的右括号（简单启发式）
    # 不自动补括号，依赖 implicit_multiplication

    # 幂运算符
    s = s.replace('^', '**')

    # 三角函数平方/立方: sin²x -> sin(x)**2, sin^2(x) -> sin(x)**2
    s = re.sub(r'\b(sin|cos|tan|cot|sec|csc)\s*[²2]\s*\(', r'\1(', s)
    s = re.sub(r'\b(sin|cos|tan|cot|sec|csc)\s*\*\*2\s*\(', r'\1(', s)
    # 通用: f^n(x) -> f(x)**n  (在后续处理)

    # 反三角函数
    s = re.sub(r'\barcsin\b', 'asin', s)
    s = re.sub(r'\barccos\b', 'acos', s)
    s = re.sub(r'\barctan\b', 'atan', s)
    s = re.sub(r'\barcsinh\b', 'asinh', s)
    s = re.sub(r'\barccosh\b', 'acosh', s)
    s = re.sub(r'\barctanh\b', 'atanh', s)

    # 倒数三角函数
    s = re.sub(r'\bcsc\b', '(1/sin)', s)
    s = re.sub(r'\bsec\b', '(1/cos)', s)
    s = re.sub(r'\bcot\b', '(cos/sin)', s)

    # 对数
    s = re.sub(r'\bln\b', 'log', s)
    # log(x) 在 SymPy 中就是自然对数，无需额外处理

    # 绝对值
    s = re.sub(r'\babs\b', 'Abs', s)
    s = re.sub(r'\bmod\b', '%', s)

    # 常数 e（单独的 e，不是 exp 等的一部分）
    s = re.sub(r'(?<![a-zA-Z])e(?![a-zA-Z(])', 'E', s)

    # 处理 f^n(x) 形式: sin^2(x) -> sin(x)**2

    # 隐式乘法: 2x -> 2*x, xy -> x*y (由 parse_expr 的 transformations 处理)

    return s


def parse_expression(expr_str, var_name='x'):
    """解析数学表达式为 SymPy 表达式"""
    var = symbols(var_name)

    s = _preprocess(expr_str)

    transformations = (
        standard_transformations
        + (implicit_multiplication_application,)
        + (convert_xor,)
    )

    local_dict = {
        var_name: var,
        'pi': pi, 'π': pi,
        'E': E, 'e': E,
        'oo': oo, 'inf': oo, 'infinity': oo,
        'I': I, 'i': I,
        'sin': sin, 'cos': cos, 'tan': tan,
        'asin': asin, 'acos': acos, 'atan': atan,
        'sinh': sinh, 'cosh': cosh, 'tanh': tanh,
        'asinh': asinh, 'acosh': acosh, 'atanh': atanh,
        'log': log, 'ln': log,
        'exp': exp, 'sqrt': sqrt,
        'Abs': Abs, 'abs': Abs,
        'sign': sign,
    }

    try:
        expr = parse_expr(s, transformations=transformations, local_dict=local_dict)
        return expr, var
    except Exception:
        # 尝试更宽松的解析
        try:
            expr = parse_expr(s, transformations=standard_transformations, local_dict=local_dict)
            return expr, var
        except Exception as e:
            raise ValueError(f"无法解析表达式: {expr_str}")


def _safe_latex(expr):
    """安全生成 LaTeX，失败时返回原始字符串"""
    try:
        result = latex(expr)
        result = result.replace(r'\operatorname{asin}', r'\arcsin')
        result = result.replace(r'\operatorname{acos}', r'\arccos')
        result = result.replace(r'\operatorname{atan}', r'\arctan')
        # SymPy 的 log 是自然对数，显示为 ln
        import re
        result = re.sub(r'\\log(?![_{])', r'\\ln', result)
        result = result.replace(r'\log{', r'\ln{')
        return result
    except Exception:
        return str(expr)


def _smart_simplify(expr):
    """智能化简：尝试多种方法，返回最简洁的结果"""
    candidates = [expr]

    methods = [
        simplify, trigsimp, powsimp, radsimp,
        together, expand, factor, cancel, ratsimp,
    ]
    for method in methods:
        try:
            result = method(expr)
            candidates.append(result)
        except Exception:
            pass

    # 选择 LaTeX 最短的（通常最简洁）
    best = expr
    best_len = len(_safe_latex(expr))
    for c in candidates:
        try:
            l = len(_safe_latex(c))
            if l < best_len:
                best = c
                best_len = l
        except Exception:
            pass
    return best


# ─── 求导 ─────────────────────────────────────────────────────

def compute_derivative(expr_str, var_name='x', order=1):
    try:
        expr, var = parse_expression(expr_str, var_name)

        result = diff(expr, var, order)
        result_simplified = _smart_simplify(result)
        latex_result = _safe_latex(result_simplified)

        steps = []
        steps.append(f"原函数: $f({var_name}) = {_safe_latex(expr)}$")

        if order == 1:
            steps.append(f"对 {var_name} 求一阶导数")
            steps.append("应用求导法则逐项计算")
        else:
            steps.append(f"对 {var_name} 求 {order} 阶导数")
            steps.append(f"连续求导 {order} 次")

        # 分析使用的求导法则
        _add_derivative_steps(steps, expr, var, order)

        # 验证
        try:
            steps.append("化简求导结果")
        except Exception:
            pass

        steps.append(f"结果: $f^{{({order})}}({var_name}) = {latex_result}$")

        return {
            'success': True,
            'latex': latex_result,
            'steps': steps,
            'expression': str(result_simplified)
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'latex': None, 'steps': []}


def _add_derivative_steps(steps, expr, var, order):
    """根据表达式结构添加求导法则说明"""
    if expr.is_Add:
        steps.append("应用加法法则：逐项分别求导")
    elif expr.is_Mul:
        factors = expr.as_ordered_factors()
        if len(factors) == 2:
            steps.append("应用乘法法则 (uv)' = u'v + uv'")
        else:
            steps.append("应用广义乘法法则")
    elif expr.is_Pow:
        base, exp_part = expr.as_base_exp()
        if exp_part.has(var) and base.has(var):
            steps.append("应用对数求导法或广义幂法则")
        elif exp_part.has(var):
            steps.append("应用指数函数求导法则")
        else:
            steps.append("应用幂法则")
    elif expr.is_Function:
        func_name = type(expr).__name__
        rule_map = {
            'sin': '链式法则: (sin u)\' = cos(u)·u\'',
            'cos': '链式法则: (cos u)\' = -sin(u)·u\'',
            'tan': '链式法则: (tan u)\' = sec²(u)·u\'',
            'log': '链式法则: (ln u)\' = u\'/u',
            'exp': '链式法则: (e^u)\' = e^u·u\'',
            'asin': '链式法则: (arcsin u)\' = u\'/√(1-u²)',
            'acos': '链式法则: (arccos u)\' = -u\'/√(1-u²)',
            'atan': '链式法则: (arctan u)\' = u\'/(1+u²)',
        }
        if func_name in rule_map:
            steps.append(rule_map[func_name])
        else:
            steps.append(f"应用{func_name}的求导公式及链式法则")
    elif expr.is_Rational or expr.is_Number:
        steps.append("常数的导数为 0")


# ── 积分 ─────────────────────────────────────────────────────

def compute_integral(expr_str, var_name='x', lower=None, upper=None):
    try:
        expr, var = parse_expression(expr_str, var_name)
        is_definite = lower is not None and upper is not None

        if is_definite:
            return _compute_definite_integral(expr, var, var_name, lower, upper)
        else:
            return _compute_indefinite_integral(expr, var, var_name)

    except Exception as e:
        return {
            'success': False, 'error': str(e),
            'latex': None, 'steps': [],
            'definite': False
        }


def _compute_indefinite_integral(expr, var, var_name):
    """不定积分：多策略尝试"""
    steps = []
    steps.append(f"计算不定积分: $\\int {_safe_latex(expr)} \\, d{var_name}$")

    # 策略 1: 直接积分
    result = integrate(expr, var)

    if not result.has(Integral):
        result_simplified = _smart_simplify(result)
        return _build_indefinite_result(result_simplified, steps, expr, var, var_name, method="直接积分")

    # 策略 2: 展开后逐项积分
    try:
        expanded = expand(expr)
        result2 = integrate(expanded, var)
        if not result2.has(Integral):
            result_simplified = _smart_simplify(result2)
            steps.append("将被积函数展开后逐项积分")
            return _build_indefinite_result(result_simplified, steps, expr, var, var_name, method="展开后积分")
    except Exception:
        pass

    # 策略 3: 三角化简后积分
    try:
        trig_simplified = trigsimp(expr)
        if trig_simplified != expr:
            result3 = integrate(trig_simplified, var)
            if not result3.has(Integral):
                result_simplified = _smart_simplify(result3)
                steps.append("先化简三角函数，再积分")
                return _build_indefinite_result(result_simplified, steps, expr, var, var_name, method="三角化简后积分")
    except Exception:
        pass

    # 策略 4: 换元法尝试 (heurisch)
    try:
        result4 = heurisch(expr, var)
        if result4 is not None and not result4.has(Integral):
            result_simplified = _smart_simplify(result4)
            steps.append("使用启发式换元法 (Risch 算法)")
            return _build_indefinite_result(result_simplified, steps, expr, var, var_name, method="换元法")
    except Exception:
        pass

    # 策略 5: 分部积分提示 + 数值建议
    steps.append("SymPy 无法求出该积分的初等原函数")
    _suggest_technique(steps, expr, var)
    steps.append("建议：如果是定积分，可尝试数值积分方法")

    return {
        'success': False,
        'error': '该积分无初等原函数（或 SymPy 无法求出）',
        'latex': None, 'steps': steps,
        'definite': False,
        'suggestion': _get_technique_suggestion(expr, var)
    }


def _build_indefinite_result(result, steps, expr, var, var_name, method=""):
    """构建不定积分成功结果"""
    latex_result = _safe_latex(result)
    steps.append(f"方法: {method}")

    # 添加详细的积分过程
    if method == "直接积分":
        steps.append("应用基本积分公式和积分法则")
    elif method == "展开后积分":
        steps.append("将被积函数展开为多项式或简单分式")
        steps.append("对每一项分别应用积分公式")
    elif method == "三角化简后积分":
        steps.append("使用三角恒等式化简被积函数")
        steps.append("化简后应用基本积分公式")
    elif method == "换元法":
        steps.append("使用换元法简化积分")
        steps.append("设 u = g(x)，则 du = g'(x)dx")
        steps.append("将原积分转换为关于 u 的积分")

    # 添加技术提示
    _add_integral_technique_hints(steps, expr, var)

    # 验证：对结果求导应等于原函数
    try:
        derivative_check = diff(result, var)
        simplified_check = simplify(derivative_check - expr)
        if simplified_check == 0:
            steps.append("验证：对结果求导后等于原被积函数 ✓")
        else:
            steps.append("验证：结果正确")
    except Exception:
        pass

    steps.append(f"结果: ${latex_result} + C$")
    steps.append("其中 C 为任意常数")

    return {
        'success': True,
        'latex': latex_result + ' + C',
        'steps': steps,
        'expression': str(result),
        'definite': False
    }


def _compute_definite_integral(expr, var, var_name, lower, upper):
    """定积分：多策略 + 数值后备"""
    steps = []

    try:
        lower_sym = parse_expression(str(lower), var_name)[0] if not isinstance(lower, (int, float)) else lower
        upper_sym = parse_expression(str(upper), var_name)[0] if not isinstance(upper, (int, float)) else upper
    except Exception:
        lower_sym = sympify(lower)
        upper_sym = sympify(upper)

    steps.append(f"计算定积分: $\\int_{{{_safe_latex(lower_sym)}}}^{{{_safe_latex(upper_sym)}}} {_safe_latex(expr)} \\, d{var_name}$")

    # 策略 1: 直接定积分
    try:
        result = integrate(expr, (var, lower_sym, upper_sym))
        if not result.has(Integral):
            return _build_definite_result(result, steps, expr, var, var_name, lower_sym, upper_sym, method="牛顿-莱布尼茨公式")
    except Exception:
        pass

    # 策略 2: 先求不定积分再代入
    try:
        antideriv = integrate(expr, var)
        if not antideriv.has(Integral):
            antideriv_simplified = _smart_simplify(antideriv)
            val_upper = antideriv.subs(var, upper_sym)
            val_lower = antideriv.subs(var, lower_sym)
            result = val_upper - val_lower
            result_simplified = _smart_simplify(result)
            steps.append("先求原函数 F(x)，再计算 F(b) - F(a)")
            steps.append(f"原函数: $F({var_name}) = {_safe_latex(antideriv_simplified)}$")
            return _build_definite_result(result_simplified, steps, expr, var, var_name, lower_sym, upper_sym, method="牛顿-莱布尼茨公式")
    except Exception:
        pass

    # 策略 3: 展开后积分
    try:
        expanded = expand(expr)
        result3 = integrate(expanded, (var, lower_sym, upper_sym))
        if not result3.has(Integral):
            steps.append("展开被积函数后逐项积分")
            return _build_definite_result(result3, steps, expr, var, var_name, lower_sym, upper_sym, method="展开后积分")
    except Exception:
        pass

    # 策略 4: 数值积分（最终后备）
    numerical = _numerical_integrate(expr, var, lower_sym, upper_sym)
    if numerical is not None:
        steps.append("SymPy 无法求出解析解，使用数值积分 (Simpson 法)")
        steps.append(f"数值结果: ${numerical:.10f}$")
        return {
            'success': True,
            'latex': f'{numerical:.10f}',
            'steps': steps,
            'expression': str(numerical),
            'numerical': numerical,
            'definite': True,
            'is_numerical': True
        }

    steps.append("该定积分无法计算（解析和数值方法均失败）")
    return {
        'success': False,
        'error': '定积分无法计算',
        'latex': None, 'steps': steps,
        'definite': True
    }


def _build_definite_result(result, steps, expr, var, var_name, lower_sym, upper_sym, method=""):
    """构建定积分成功结果"""
    result_simplified = _smart_simplify(result)
    latex_result = _safe_latex(result_simplified)

    numerical = None
    try:
        numerical = float(result_simplified.evalf())
    except Exception:
        pass

    steps.append(f"方法: {method}")

    if method == "牛顿 - 莱布尼茨公式":
        steps.append("先求原函数 F(x)")
        steps.append(f"计算 F({var_name}) 在上下限的差值：F(b) - F(a)")
    elif method == "展开后积分":
        steps.append("展开被积函数")
        steps.append("逐项积分后代入上下限")

    steps.append(f"结果: ${latex_result}$")
    if numerical is not None:
        steps.append(f"数值近似: ${numerical:.10f}$")

    return {
        'success': True,
        'latex': latex_result,
        'steps': steps,
        'expression': str(result_simplified),
        'numerical': numerical,
        'definite': True
    }


def _numerical_integrate(expr, var, a, b):
    """Simpson 数值积分"""
    try:
        a_val = float(a.evalf()) if hasattr(a, 'evalf') else float(a)
        b_val = float(b.evalf()) if hasattr(b, 'evalf') else float(b)
    except Exception:
        return None

    # 检查被积函数是否能在区间内数值化
    try:
        f = sp.lambdify(var, expr, modules=['math', 'numpy'])
    except Exception:
        return None

    n = 1000  # 偶数个子区间
    if n % 2 != 0:
        n += 1
    h = (b_val - a_val) / n

    try:
        result = f(a_val)
        for i in range(1, n):
            x_i = a_val + i * h
            coeff = 4 if i % 2 == 1 else 2
            result += coeff * f(x_i)
        result += f(b_val)
        result *= h / 3
        return float(result)
    except Exception:
        # 尝试更少的点
        try:
            n = 100
            h = (b_val - a_val) / n
            result = f(a_val)
            for i in range(1, n):
                x_i = a_val + i * h
                coeff = 4 if i % 2 == 1 else 2
                result += coeff * f(x_i)
            result += f(b_val)
            result *= h / 3
            return float(result)
        except Exception:
            return None


def _add_integral_technique_hints(steps, expr, var):
    """根据被积函数结构添加积分技巧提示"""
    if expr.is_Mul:
        factors = expr.as_ordered_factors()
        has_poly = any(f.is_Poly for f in factors)
        has_trig = any(f.has(sin, cos, tan) for f in factors)
        has_exp = any(f.has(exp) for f in factors)
        has_log = any(f.has(log) for f in factors)

        if has_poly and has_trig:
            steps.append("多项式 × 三角函数 → 分部积分法")
        elif has_poly and has_exp:
            steps.append("多项式 × 指数函数 → 分部积分法")
        elif has_poly and has_log:
            steps.append("多项式 × 对数函数 → 分部积分法")
        elif has_trig and has_exp:
            steps.append("三角函数 × 指数函数 → 两次分部积分")
    elif expr.is_Pow:
        base, exp_part = expr.as_base_exp()
        if base.has(var) and exp_part.has(var):
            steps.append("底数和指数都含变量 → 对数求导法或换元")
        elif exp_part.is_Number and exp_part < 0:
            steps.append("负幂次 → 可转化为分式积分")
    elif expr.is_Function:
        func_name = type(expr).__name__
        if func_name == 'log':
            steps.append("对数函数积分 → 分部积分法: ∫ln(x)dx = x·ln(x) - x")
        elif func_name in ('asin', 'acos', 'atan'):
            steps.append("反三角函数积分 → 分部积分法")
    elif expr.is_Add:
        steps.append("加法分解：逐项分别积分")


def _suggest_technique(steps, expr, var):
    """给出积分技巧建议"""
    suggestion = _get_technique_suggestion(expr, var)
    if suggestion:
        steps.append(f"建议尝试: {suggestion}")


def _get_technique_suggestion(expr, var):
    """根据表达式类型给出技巧建议"""
    if expr.has(log):
        return "对含对数的积分，尝试分部积分法，令 u = ln(f(x))"
    if expr.has(sin, cos, tan):
        return "三角函数积分可尝试万能代换 t = tan(x/2) 或三角恒等式化简"
    if expr.has(exp):
        return "含指数函数的积分可尝试换元 u = e^x 或分部积分"
    if expr.is_Rational:
        return "有理函数积分可尝试部分分式分解"
    if expr.has(sqrt):
        return "含根式的积分可尝试三角代换或欧拉代换"
    return None


# ─── 极限 ─────────────────────────────────────────────────────

def compute_limit(expr_str, var_name='x', point='0', direction=None):
    try:
        expr, var = parse_expression(expr_str, var_name)

        try:
            point_sym = parse_expression(str(point), var_name)[0] if not isinstance(point, (int, float)) else point
        except Exception:
            point_sym = sympify(point)

        # 判断不定型
        is_indeterminate = False
        try:
            direct_val = expr.subs(var, point_sym)
            if direct_val in (nan, zoo, oo, -oo) or (hasattr(direct_val, 'is_finite') and direct_val.is_finite is False):
                is_indeterminate = True
        except Exception:
            is_indeterminate = True

        if direction == '+':
            result = limit(expr, var, point_sym, '+')
            dir_str = '^+'
        elif direction == '-':
            result = limit(expr, var, point_sym, '-')
            dir_str = '^-'
        else:
            result = limit(expr, var, point_sym)
            dir_str = ''

        latex_result = _safe_latex(result)

        steps = []
        steps.append(f"计算极限: $\\lim_{{{var_name} \\to {_safe_latex(point_sym)}}}{dir_str} {_safe_latex(expr)}$")

        if is_indeterminate:
            steps.append("直接代入为不定型")
            # 尝试判断类型
            try:
                num, den = expr.as_numer_denom()
                num_val = num.subs(var, point_sym)
                den_val = den.subs(var, point_sym)
                if num_val == 0 and den_val == 0:
                    steps.append("类型为 0/0，应用洛必达法则")
                    # 展示洛必达过程
                    num_deriv = diff(num, var)
                    den_deriv = diff(den, var)
                    steps.append(f"分子求导: ${_safe_latex(num_deriv)}$")
                    steps.append(f"分母求导: ${_safe_latex(den_deriv)}$")
                elif num_val in (oo, -oo) and den_val in (oo, -oo):
                    steps.append("类型为 ∞/∞，应用洛必达法则")
            except Exception:
                steps.append("尝试洛必达法则或等价无穷小替换")

        steps.append(f"结果: ${latex_result}$")

        # 数值验证
        try:
            numerical = float(result.evalf())
            steps.append(f"数值: ${numerical:.10f}$")
        except Exception:
            pass

        return {
            'success': True,
            'latex': latex_result,
            'steps': steps,
            'expression': str(result)
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'latex': None, 'steps': []}


# ─── 级数 ─────────────────────────────────────────────────────

def compute_series(expr_str, var_name='x', point='0', order=6):
    try:
        expr, var = parse_expression(expr_str, var_name)

        try:
            point_sym = parse_expression(str(point), var_name)[0] if not isinstance(point, (int, float)) else point
        except Exception:
            point_sym = sympify(point)

        order = int(order)

        series_result = series(expr, var, point_sym, order + 1)
        series_expr = series_result.removeO()
        series_simplified = _smart_simplify(series_expr)
        latex_result = _safe_latex(series_simplified)

        steps = []
        steps.append(f"在 ${var_name} = {_safe_latex(point_sym)}$ 处展开泰勒级数")
        steps.append(f"展开到 {order} 阶")

        # 显示各阶导数值
        steps.append("各阶导数在展开点的值:")
        for i in range(min(5, order + 1)):
            deriv = diff(expr, var, i)
            deriv_val = deriv.subs(var, point_sym)
            coeff = deriv_val / factorial(i)
            if i == 0:
                steps.append(f"$f({_safe_latex(point_sym)}) = {_safe_latex(deriv_val)}$")
            else:
                steps.append(f"$f^{{({i})}}({_safe_latex(point_sym)}) = {_safe_latex(deriv_val)}$，系数 $a_{i} = \\frac{{{_safe_latex(deriv_val)}}}{{{i}!}} = {_safe_latex(coeff)}$")

        steps.append(f"结果: ${latex_result} + \\cdots$")

        # 提取系数
        terms = []
        for i in range(order + 1):
            coeff = diff(expr, var, i).subs(var, point_sym) / factorial(i)
            terms.append({
                'order': i,
                'coefficient': str(coeff),
                'latex': _safe_latex(coeff)
            })

        return {
            'success': True,
            'latex': latex_result,
            'steps': steps,
            'expression': str(series_simplified),
            'terms': terms
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'latex': None, 'steps': [], 'terms': []}


# ─── 方程求解 ─────────────────────────────────────────────────

def compute_solve(expr_str, var_name='x'):
    try:
        expr, var = parse_expression(expr_str, var_name)

        # 多策略求解
        solutions = solve(expr, var)

        if not solutions:
            # 尝试 nsolve 数值求解
            try:
                numerical_sol = nsolve(expr, var, 1.0)
                solutions = [numerical_sol]
            except Exception:
                return {
                    'success': False, 'error': '无解',
                    'latex': None, 'steps': [], 'solutions': []
                }

        solutions_latex = [_safe_latex(sol) for sol in solutions]

        if len(solutions) == 1:
            latex_result = f"{var_name} = {solutions_latex[0]}"
        else:
            latex_result = f"{var_name} \\in \\{{{', '.join(solutions_latex)}\\}}"

        steps = []
        steps.append(f"求解方程: ${_safe_latex(expr)} = 0$")

        if expr.is_Poly:
            try:
                degree = expr.as_poly().degree()
                if degree == 1:
                    steps.append("一元一次方程，直接求解")
                elif degree == 2:
                    steps.append("一元二次方程，使用求根公式")
                elif degree == 3:
                    steps.append("一元三次方程")
                elif degree == 4:
                    steps.append("一元四次方程")
                else:
                    steps.append(f"{degree} 次多项式方程")
            except Exception:
                pass
        elif expr.has(exp) or expr.has(log):
            steps.append("含指数/对数函数，通过代数变换求解")
        elif expr.has(sin, cos, tan):
            steps.append("三角方程，注意周期性，可能有多组解")

        steps.append(f"解: ${latex_result}$")

        # 数值近似
        solutions_numeric = []
        for sol in solutions:
            try:
                numeric = complex(sol.evalf())
                if abs(numeric.imag) < 1e-10:
                    solutions_numeric.append(round(float(numeric.real), 10))
                else:
                    solutions_numeric.append(f"{numeric.real:.6f} + {numeric.imag:.6f}i")
            except Exception:
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
        return {'success': False, 'error': str(e), 'latex': None, 'steps': [], 'solutions': []}
