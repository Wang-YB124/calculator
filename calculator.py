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
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError


# ─── 超时控制 ────────────────────────────────────────────────

def _timeout_call(func, args=(), kwargs={}, timeout=15):
    """带超时的函数调用"""
    try:
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            return future.result(timeout=timeout)
    except FuturesTimeoutError:
        return None
    except Exception:
        return None


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

        steps = []
        steps.append(f"原函数: $f({var_name}) = {_safe_latex(expr)}$")

        if order == 1:
            # 一阶导数：展示详细求导过程
            result = diff(expr, var)
            result_simplified = _smart_simplify(result)
            latex_result = _safe_latex(result_simplified)

            steps.append(f"求一阶导数: $f'({var_name}) = \\frac{{d}}{{d{var_name}}} {_safe_latex(expr)}$")

            # 分析表达式结构并展示求导法则
            _add_derivative_detailed_steps(steps, expr, var, var_name)

            steps.append(f"求导结果: ${_safe_latex(result)}$")

            if result_simplified != result:
                steps.append("化简:")
                steps.append(f"$f'({var_name}) = {latex_result}$")

            steps.append(f"最终结果: $f'({var_name}) = {latex_result}$")
        else:
            # 高阶导数：逐步展示
            current_expr = expr
            for i in range(1, order + 1):
                next_expr = diff(current_expr, var)
                next_simplified = _smart_simplify(next_expr)

                if i == 1:
                    steps.append(f"第 {i} 阶导数:")
                else:
                    steps.append(f"第 {i} 阶导数 (对 $f^{{({i-1})}}$ 再求导):")

                steps.append(f"$f^{{({i})}}({var_name}) = {_safe_latex(next_simplified)}$")
                current_expr = next_simplified

            latex_result = _safe_latex(current_expr)
            steps.append(f"最终结果: $f^{{({order})}}({var_name}) = {latex_result}$")

        return {
            'success': True,
            'latex': latex_result if order > 1 else _safe_latex(_smart_simplify(diff(expr, var))),
            'steps': steps,
            'expression': str(_smart_simplify(diff(expr, var, order)))
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'latex': None, 'steps': []}


def _add_derivative_detailed_steps(steps, expr, var, var_name):
    """根据表达式结构添加详细的求导步骤"""
    if expr.is_Add:
        steps.append("应用加法法则：逐项分别求导")
        terms = expr.as_ordered_terms()
        if len(terms) <= 6:
            for term in terms:
                try:
                    term_deriv = diff(term, var)
                    steps.append(f"$\\frac{{d}}{{d{var_name}}}({_safe_latex(term)}) = {_safe_latex(term_deriv)}$")
                except Exception:
                    pass
    elif expr.is_Mul:
        factors = expr.as_ordered_factors()
        if len(factors) == 2:
            u, v = factors
            steps.append("应用乘法法则: $(uv)' = u'v + uv'$")
            try:
                u_deriv = diff(u, var)
                v_deriv = diff(v, var)
                steps.append(f"$u = {_safe_latex(u)}, \\quad u' = {_safe_latex(u_deriv)}$")
                steps.append(f"$v = {_safe_latex(v)}, \\quad v' = {_safe_latex(v_deriv)}$")
                steps.append(f"$f'({var_name}) = {_safe_latex(u_deriv)} \\cdot {_safe_latex(v)} + {_safe_latex(u)} \\cdot {_safe_latex(v_deriv)}$")
            except Exception:
                pass
        else:
            steps.append("应用广义乘法法则")
    elif expr.is_Pow:
        base, exp_part = expr.as_base_exp()
        if exp_part.has(var) and base.has(var):
            steps.append("应用对数求导法或广义幂法则")
            steps.append(f"$\\frac{{d}}{{d{var_name}}} [{_safe_latex(base)}^{{{_safe_latex(exp_part)}}}]$")
        elif exp_part.has(var):
            steps.append("应用指数函数求导法则: $(a^u)' = a^u \\ln(a) \\cdot u'$")
            try:
                exp_deriv = diff(exp_part, var)
                steps.append(f"$f'({var_name}) = {_safe_latex(expr)} \\cdot \\ln({_safe_latex(base)}) \\cdot {_safe_latex(exp_deriv)}$")
            except Exception:
                pass
        else:
            steps.append(f"应用幂法则: $(u^n)' = n \\cdot u^{{n-1}} \\cdot u'$")
            try:
                base_deriv = diff(base, var)
                steps.append(f"$f'({var_name}) = {_safe_latex(exp_part)} \\cdot {_safe_latex(base)}^{{{_safe_latex(exp_part - 1)}}} \\cdot {_safe_latex(base_deriv)}$")
            except Exception:
                pass
    elif expr.is_Function:
        func_name = type(expr).__name__
        arg = expr.args[0] if expr.args else expr
        rule_map = {
            'sin': ('链式法则', "$\\frac{{d}}{{d{var}}} \\sin(u) = \\cos(u) \\cdot u'$", cos(arg)),
            'cos': ('链式法则', "$\\frac{{d}}{{d{var}}} \\cos(u) = -\\sin(u) \\cdot u'$", -sin(arg)),
            'tan': ('链式法则', "$\\frac{{d}}{{d{var}}} \\tan(u) = \\sec^2(u) \\cdot u'$", 1/cos(arg)**2),
            'log': ('链式法则', "$\\frac{{d}}{{d{var}}} \\ln(u) = \\frac{{u'}}{{u}}$", 1/arg),
            'exp': ('链式法则', "$\\frac{{d}}{{d{var}}} e^u = e^u \\cdot u'$", exp(arg)),
            'asin': ('链式法则', "$\\frac{{d}}{{d{var}}} \\arcsin(u) = \\frac{{u'}}{{\\sqrt{{1-u^2}}}}$", 1/sqrt(1-arg**2)),
            'acos': ('链式法则', "$\\frac{{d}}{{d{var}}} \\arccos(u) = \\frac{{-u'}}{{\\sqrt{{1-u^2}}}}$", -1/sqrt(1-arg**2)),
            'atan': ('链式法则', "$\\frac{{d}}{{d{var}}} \\arctan(u) = \\frac{{u'}}{{1+u^2}}$", 1/(1+arg**2)),
        }
        if func_name in rule_map:
            rule_name, rule_formula, outer_deriv = rule_map[func_name]
            steps.append(f"{rule_name}: {rule_formula.replace('{var}', var_name)}")
            try:
                arg_deriv = diff(arg, var)
                if arg_deriv != 1:
                    steps.append(f"内层函数 $u = {_safe_latex(arg)}$, $u' = {_safe_latex(arg_deriv)}$")
                    steps.append(f"$f'({var_name}) = {_safe_latex(outer_deriv)} \\cdot {_safe_latex(arg_deriv)}$")
                else:
                    steps.append(f"$f'({var_name}) = {_safe_latex(outer_deriv)}$")
            except Exception:
                pass
        else:
            steps.append(f"应用 {func_name} 的求导公式及链式法则")
    elif expr.is_Rational or expr.is_Number:
        steps.append("常数的导数为 0")
        steps.append(f"$f'({var_name}) = 0$")


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
    """不定积分：多策略尝试，生成详细步骤"""
    steps = []
    steps.append(f"计算不定积分: $\\int {_safe_latex(expr)} \\, d{var_name}$")

    # 检测是否适合分部积分（多项式 × 三角/指数/对数）
    should_show_by_parts = _should_use_integration_by_parts(expr, var)

    # 策略 1: 直接积分（带超时）
    result = _timeout_call(integrate, args=(expr, var), timeout=20)

    if result is not None and not result.has(Integral):
        result_simplified = _smart_simplify(result)
        # 如果需要展示分部积分步骤，强制使用分部积分法
        if should_show_by_parts:
            by_parts_result = _try_integration_by_parts(expr, var, var_name, [])
            if by_parts_result:
                return by_parts_result
        return _build_indefinite_result(result_simplified, steps, expr, var, var_name, method="直接积分")

    # 策略 2: 展开后逐项积分
    try:
        expanded = expand(expr)
        if expanded != expr:
            result2 = _timeout_call(integrate, args=(expanded, var), timeout=20)
            if result2 is not None and not result2.has(Integral):
                result_simplified = _smart_simplify(result2)
                return _build_expansion_steps(result_simplified, steps, expr, expanded, var, var_name)
    except Exception:
        pass

    # 策略 3: 三角化简后积分
    try:
        trig_simplified = trigsimp(expr)
        if trig_simplified != expr:
            result3 = _timeout_call(integrate, args=(trig_simplified, var), timeout=20)
            if result3 is not None and not result3.has(Integral):
                result_simplified = _smart_simplify(result3)
                return _build_trigsimp_steps(result_simplified, steps, expr, trig_simplified, var, var_name)
    except Exception:
        pass

    # 策略 4: 分部积分法
    by_parts_result = _try_integration_by_parts(expr, var, var_name, steps)
    if by_parts_result:
        return by_parts_result

    # 策略 5: 换元法尝试 (heurisch)
    try:
        result4 = _timeout_call(heurisch, args=(expr, var), timeout=20)
        if result4 is not None and not result4.has(Integral):
            result_simplified = _smart_simplify(result4)
            return _build_substitution_steps(result_simplified, steps, expr, var, var_name)
    except Exception:
        pass

    # 策略 6: 数值积分后备
    steps.append("SymPy 无法在合理时间内求出该积分的初等原函数")
    steps.append("建议：")
    _suggest_technique(steps, expr, var)
    steps.append("如果是定积分，可尝试数值积分方法")

    return {
        'success': False,
        'error': '该积分计算超时或无初等原函数',
        'latex': None, 'steps': steps,
        'definite': False,
        'suggestion': _get_technique_suggestion(expr, var)
    }


def _build_indefinite_result(result, steps, expr, var, var_name, method=""):
    """构建不定积分成功结果 - 显示详细步骤"""
    latex_result = _safe_latex(result)
    steps.append(f"方法：{method}")

    # 根据表达式类型生成详细步骤
    _generate_detailed_integration_steps(steps, expr, result, var, var_name)

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

    steps.append(f"最终结果: ${latex_result} + C$")
    steps.append("其中 C 为任意常数")

    return {
        'success': True,
        'latex': latex_result + ' + C',
        'steps': steps,
        'expression': str(result),
        'definite': False
    }


def _generate_detailed_integration_steps(steps, expr, result, var, var_name):
    """根据表达式类型生成详细的积分步骤"""
    # 如果是加法，逐项积分
    if expr.is_Add:
        terms = expr.as_ordered_terms()
        steps.append("应用加法法则：逐项分别积分")
        steps.append(f"$\\int ({_safe_latex(expr)}) \\, d{var_name} = " +
                     " + ".join([f"\\int {_safe_latex(t)} \\, d{var_name}" for t in terms]) + "$")

        # 对每一项显示积分过程
        for term in terms:
            _integrate_single_term(steps, term, var, var_name)

        steps.append("合并结果:")
        steps.append(f"$\\int {_safe_latex(expr)} \\, d{var_name} = {_safe_latex(result)} + C$")

    # 如果是单项式，直接应用公式
    elif expr.is_Mul or expr.is_Pow or expr.is_Symbol or expr.is_Number:
        _integrate_single_term(steps, expr, var, var_name)
        steps.append(f"$\\int {_safe_latex(expr)} \\, d{var_name} = {_safe_latex(result)} + C$")

    # 如果是函数，显示对应的积分公式
    elif expr.is_Function:
        func_name = type(expr).__name__
        _show_function_integration_rule(steps, func_name, expr, result, var, var_name)
        steps.append(f"$\\int {_safe_latex(expr)} \\, d{var_name} = {_safe_latex(result)} + C$")

    else:
        steps.append("应用积分公式和积分法则")
        steps.append(f"$\\int {_safe_latex(expr)} \\, d{var_name} = {_safe_latex(result)} + C$")


def _integrate_single_term(steps, term, var, var_name):
    """显示单项的积分过程"""
    # 常数倍
    if term.is_Mul:
        coeff = term.as_coeff_Mul()[0]
        rest = term.as_coeff_Mul()[1]
        if coeff != 1 and rest.has(var):
            steps.append(f"提取常数: $\\int {_safe_latex(term)} \\, d{var_name} = {_safe_latex(coeff)} \\int {_safe_latex(rest)} \\, d{var_name}$")
            term = rest

    # 幂函数 x^n
    if term.is_Pow and term.base == var:
        n = term.exp
        if n != -1:
            steps.append(f"应用幂函数积分公式: $\\int x^n dx = \\frac{{x^{{n+1}}}}{{n+1}} + C$ (n ≠ -1)")
            steps.append(f"其中 n = {_safe_latex(n)}")
            result_term = integrate(term, var)
            steps.append(f"$\\int {_safe_latex(term)} \\, d{var_name} = {_safe_latex(result_term)}$")
        else:
            steps.append(f"应用对数积分公式: $\\int x^{{-1}} dx = \\ln|x| + C$")
            steps.append(f"$\\int {_safe_latex(term)} \\, d{var_name} = \\ln|{_safe_latex(var)}|$")

    # 符号 x (即 x^1)
    elif term == var:
        steps.append(f"应用幂函数积分公式: $\\int x dx = \\frac{{x^2}}{2} + C$")
        steps.append(f"$\\int {_safe_latex(term)} \\, d{var_name} = \\frac{{{_safe_latex(var)}^2}}{2}$")

    # 常数
    elif term.is_Number and not term.has(var):
        steps.append(f"常数积分: $\\int {_safe_latex(term)} \\, d{var_name} = {_safe_latex(term)}{_safe_latex(var)}$")

    # 其他情况，直接显示结果
    else:
        result_term = integrate(term, var)
        if result_term.has(Integral):
            steps.append(f"$\\int {_safe_latex(term)} \\, d{var_name}$ (需要进一步化简)")
        else:
            steps.append(f"$\\int {_safe_latex(term)} \\, d{var_name} = {_safe_latex(result_term)}$")


def _show_function_integration_rule(steps, func_name, expr, result, var, var_name):
    """显示函数积分公式"""
    rules = {
        'sin': ("$\\int \\sin(x) dx = -\\cos(x) + C$", "$\\int \\sin(u) du = -\\cos(u) + C$"),
        'cos': ("$\\int \\cos(x) dx = \\sin(x) + C$", "$\\int \\cos(u) du = \\sin(u) + C$"),
        'tan': ("$\\int \\tan(x) dx = -\\ln|\\cos(x)| + C$", None),
        'exp': ("$\\int e^x dx = e^x + C$", "$\\int e^u du = e^u + C$"),
        'log': ("$\\int \\ln(x) dx = x\\ln(x) - x + C$", None),
        'asin': ("$\\int \\arcsin(x) dx = x\\arcsin(x) + \\sqrt{1-x^2} + C$", None),
        'acos': ("$\\int \\arccos(x) dx = x\\arccos(x) - \\sqrt{1-x^2} + C$", None),
        'atan': ("$\\int \\arctan(x) dx = x\\arctan(x) - \\frac{1}{2}\\ln(1+x^2) + C$", None),
    }

    if func_name in rules:
        simple_rule, chain_rule = rules[func_name]
        arg = expr.args[0] if expr.args else var

        if arg == var:
            steps.append(f"应用积分公式：{simple_rule}")
        else:
            steps.append(f"应用积分公式：{simple_rule}")
            if chain_rule:
                steps.append(f"链式法则：{chain_rule}")
            steps.append(f"其中 u = {_safe_latex(arg)}")


def _build_expansion_steps(result, steps, expr, expanded, var, var_name):
    """构建展开后积分的详细步骤"""
    latex_result = _safe_latex(result)
    latex_expanded = _safe_latex(expanded)

    steps.append("方法：展开后逐项积分")
    steps.append("将被积函数展开为多项式或简单分式之和")
    steps.append(f"展开后: ${latex_expanded}$")
    steps.append("对每一项分别应用积分公式")

    # 显示各项的积分
    terms = expanded.as_ordered_terms()
    if len(terms) <= 8:
        term_integrals = []
        for term in terms:
            try:
                term_int = integrate(term, var)
                term_integrals.append(_safe_latex(term_int))
            except Exception:
                term_integrals.append("?")
        if term_integrals:
            steps.append("各项积分结果:")
            for i, (term, ti) in enumerate(zip(terms, term_integrals)):
                steps.append(f"$\\int {_safe_latex(term)} \\, d{var_name} = {ti}$")

    steps.append(f"合并结果: $\\int {_safe_latex(expr)} \\, d{var_name} = {latex_result} + C$")

    # 验证
    try:
        derivative_check = diff(result, var)
        simplified_check = simplify(derivative_check - expr)
        if simplified_check == 0:
            steps.append("验证：对结果求导后等于原被积函数 ✓")
    except Exception:
        pass

    steps.append(f"最终结果: ${latex_result} + C$")
    steps.append("其中 C 为任意常数")

    return {
        'success': True,
        'latex': latex_result + ' + C',
        'steps': steps,
        'expression': str(result),
        'definite': False
    }


def _build_trigsimp_steps(result, steps, expr, trig_simplified, var, var_name):
    """构建三角化简后积分的详细步骤"""
    latex_result = _safe_latex(result)
    latex_simplified = _safe_latex(trig_simplified)

    steps.append("方法：三角化简后积分")
    steps.append("使用三角恒等式化简被积函数")
    steps.append(f"化简后: ${latex_simplified}$")
    steps.append(f"计算化简后的积分: $\\int {_safe_latex(trig_simplified)} \\, d{var_name}$")
    steps.append(f"应用基本积分公式")
    steps.append(f"$\\int {_safe_latex(expr)} \\, d{var_name} = {latex_result} + C$")

    # 验证
    try:
        derivative_check = diff(result, var)
        simplified_check = simplify(derivative_check - expr)
        if simplified_check == 0:
            steps.append("验证：对结果求导后等于原被积函数 ✓")
    except Exception:
        pass

    steps.append(f"最终结果: ${latex_result} + C$")
    steps.append("其中 C 为任意常数")

    return {
        'success': True,
        'latex': latex_result + ' + C',
        'steps': steps,
        'expression': str(result),
        'definite': False
    }


def _should_use_integration_by_parts(expr, var):
    """判断是否应该展示分部积分步骤"""
    if not expr.is_Mul:
        return False

    factors = expr.as_ordered_factors()

    # 检查是否包含对数、反三角函数
    if any(f.has(log, asin, acos, atan) for f in factors):
        return True

    # 检查是否是多项式 × 三角/指数
    has_poly = any(f.is_polynomial(var) for f in factors)
    has_trig_exp = any(f.has(sin, cos, tan, exp) for f in factors)
    if has_poly and has_trig_exp:
        return True

    return False


def _try_integration_by_parts(expr, var, var_name, steps):
    """尝试分部积分法"""
    # 检测是否适合分部积分
    if not expr.is_Mul:
        return None

    factors = expr.as_ordered_factors()

    # LIATE 规则选择 u: 对数 > 反三角 > 代数 > 三角 > 指数
    u_candidate = None
    dv_candidate = None

    # 优先级 1: 对数或反三角函数作为 u
    for factor in factors:
        if factor.has(log, asin, acos, atan):
            u_candidate = factor
            dv_candidate = expr / factor
            break

    # 优先级 2: 多项式 × 三角/指数 → 多项式作为 u
    if u_candidate is None:
        has_poly = any(f.is_polynomial(var) for f in factors)
        has_trig_exp = any(f.has(sin, cos, tan, exp) for f in factors)
        if has_poly and has_trig_exp:
            for f in factors:
                if f.is_polynomial(var):
                    u_candidate = f
                    dv_candidate = expr / f
                    break

    if u_candidate is None:
        return None

    # 计算 du 和 v
    try:
        du = diff(u_candidate, var)
        v = integrate(dv_candidate, var)

        if v.has(Integral):
            return None

        # 计算 ∫ v du
        remaining_integral = integrate(v * du, var)

        if remaining_integral.has(Integral):
            return None

        # 分部积分公式: ∫ u dv = uv - ∫ v du
        result = u_candidate * v - remaining_integral
        result_simplified = _smart_simplify(result)

        latex_u = _safe_latex(u_candidate)
        latex_dv = _safe_latex(dv_candidate)
        latex_du = _safe_latex(du)
        latex_v = _safe_latex(v)
        latex_remaining = _safe_latex(remaining_integral)
        latex_result = _safe_latex(result_simplified)

        steps.append("方法：分部积分法")
        steps.append("使用公式: $\\int u \\, dv = uv - \\int v \\, du$")
        steps.append("选择:")
        steps.append(f"$u = {latex_u}$")
        steps.append(f"$dv = {latex_dv} \\, d{var_name}$")
        steps.append("计算:")
        steps.append(f"$du = {latex_du} \\, d{var_name}$")
        steps.append(f"$v = \\int {latex_dv} \\, d{var_name} = {latex_v}$")
        steps.append("代入公式:")
        steps.append(f"$\\int {_safe_latex(expr)} \\, d{var_name} = {latex_u} \\cdot {latex_v} - \\int {latex_v} \\cdot {latex_du} \\, d{var_name}$")
        steps.append(f"$= {latex_u} \\cdot {latex_v} - \\int {latex_remaining} \\, d{var_name}$")
        steps.append(f"$= {latex_result} + C$")

        # 验证
        try:
            derivative_check = diff(result_simplified, var)
            simplified_check = simplify(derivative_check - expr)
            if simplified_check == 0:
                steps.append("验证：对结果求导后等于原被积函数 ✓")
        except Exception:
            pass

        steps.append(f"最终结果: ${latex_result} + C$")
        steps.append("其中 C 为任意常数")

        return {
            'success': True,
            'latex': latex_result + ' + C',
            'steps': steps,
            'expression': str(result_simplified),
            'definite': False
        }
    except Exception:
        return None


def _build_substitution_steps(result, steps, expr, var, var_name):
    """构建换元法的详细步骤"""
    latex_result = _safe_latex(result)

    steps.append("方法：换元法（启发式算法）")
    steps.append("使用 Risch 算法或启发式换元法")
    steps.append(f"原积分: $\\int {_safe_latex(expr)} \\, d{var_name}$")
    steps.append("通过适当的变量替换化简积分")
    steps.append(f"积分结果: ${latex_result} + C$")

    # 验证
    try:
        derivative_check = diff(result, var)
        simplified_check = simplify(derivative_check - expr)
        if simplified_check == 0:
            steps.append("验证：对结果求导后等于原被积函数 ✓")
    except Exception:
        pass

    steps.append(f"最终结果: ${latex_result} + C$")
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
        result = _timeout_call(integrate, args=(expr, (var, lower_sym, upper_sym)), timeout=20)
        if result is not None and not result.has(Integral):
            return _build_definite_result(result, steps, expr, var, var_name, lower_sym, upper_sym, method="牛顿-莱布尼茨公式")
    except Exception:
        pass

    # 策略 2: 先求不定积分再代入
    try:
        antideriv = _timeout_call(integrate, args=(expr, var), timeout=20)
        if antideriv is not None and not antideriv.has(Integral):
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
        result3 = _timeout_call(integrate, args=(expanded, (var, lower_sym, upper_sym)), timeout=20)
        if result3 is not None and not result3.has(Integral):
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

        steps = []
        steps.append(f"计算极限: $\\lim_{{{var_name} \\to {_safe_latex(point_sym)}}} {_safe_latex(expr)}$")

        # 尝试直接代入
        try:
            direct_val = expr.subs(var, point_sym)
            steps.append(f"尝试直接代入 ${var_name} = {_safe_latex(point_sym)}$")

            if direct_val in (nan, zoo, oo, -oo) or (hasattr(direct_val, 'is_finite') and direct_val.is_finite is False):
                steps.append(f"得到不定型，需要进一步分析")
                is_indeterminate = True
            else:
                steps.append(f"直接代入得: ${_safe_latex(direct_val)}$")
                steps.append(f"结果: ${_safe_latex(direct_val)}$")
                return {
                    'success': True,
                    'latex': _safe_latex(direct_val),
                    'steps': steps,
                    'expression': str(direct_val)
                }
        except Exception:
            is_indeterminate = True
            steps.append("直接代入失败，分析不定型")

        # 计算极限
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

        if is_indeterminate:
            # 尝试判断不定型类型并展示洛必达过程
            try:
                num, den = expr.as_numer_denom()
                num_val = num.subs(var, point_sym)
                den_val = den.subs(var, point_sym)

                if num_val == 0 and den_val == 0:
                    steps.append("类型为 $\\frac{0}{0}$，应用洛必达法则")
                    steps.append("洛必达法则: $\\lim \\frac{f(x)}{g(x)} = \\lim \\frac{f'(x)}{g'(x)}$")

                    # 第一次洛必达
                    num_deriv = diff(num, var)
                    den_deriv = diff(den, var)
                    steps.append(f"分子求导: $\\frac{{d}}{{d{var_name}}}({_safe_latex(num)}) = {_safe_latex(num_deriv)}$")
                    steps.append(f"分母求导: $\\frac{{d}}{{d{var_name}}}({_safe_latex(den)}) = {_safe_latex(den_deriv)}$")
                    steps.append(f"新极限: $\\lim_{{{var_name} \\to {_safe_latex(point_sym)}}} \\frac{{{_safe_latex(num_deriv)}}}{{{_safe_latex(den_deriv)}}}$")

                    # 尝试再次代入
                    try:
                        new_val = (num_deriv / den_deriv).subs(var, point_sym)
                        if new_val not in (nan, zoo, oo, -oo):
                            steps.append(f"代入得: ${_safe_latex(new_val)}$")
                        else:
                            # 第二次洛必达
                            num_deriv2 = diff(num_deriv, var)
                            den_deriv2 = diff(den_deriv, var)
                            steps.append("仍为不定型，再次应用洛必达法则")
                            steps.append(f"分子再求导: ${_safe_latex(num_deriv2)}$")
                            steps.append(f"分母再求导: ${_safe_latex(den_deriv2)}$")
                    except Exception:
                        pass

                elif num_val in (oo, -oo) and den_val in (oo, -oo):
                    steps.append("类型为 $\\frac{\\infty}{\\infty}$，应用洛必达法则")
                    num_deriv = diff(num, var)
                    den_deriv = diff(den, var)
                    steps.append(f"分子求导: ${_safe_latex(num_deriv)}$")
                    steps.append(f"分母求导: ${_safe_latex(den_deriv)}$")
                else:
                    steps.append("尝试洛必达法则或等价无穷小替换")
            except Exception:
                steps.append("尝试洛必达法则或等价无穷小替换")

        steps.append(f"极限结果: ${latex_result}$")

        # 数值验证
        try:
            numerical = float(result.evalf())
            steps.append(f"数值近似: ${numerical:.10f}$")
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

        steps = []
        steps.append(f"原函数: $f({var_name}) = {_safe_latex(expr)}$")
        steps.append(f"在 ${var_name} = {_safe_latex(point_sym)}$ 处展开泰勒级数")
        steps.append(f"展开到 {order} 阶")
        steps.append("泰勒公式: $f(x) = \\sum_{{n=0}}^{{\\infty}} \\frac{{f^{{(n)}}(a)}}{{n!}} (x-a)^n$")

        # 计算级数
        series_result = series(expr, var, point_sym, order + 1)
        series_expr = series_result.removeO()
        series_simplified = _smart_simplify(series_expr)
        latex_result = _safe_latex(series_simplified)

        # 显示各阶导数值和系数
        steps.append("计算各阶导数在展开点的值:")
        for i in range(min(6, order + 1)):
            deriv = diff(expr, var, i)
            deriv_val = deriv.subs(var, point_sym)
            coeff = deriv_val / factorial(i)
            if i == 0:
                steps.append(f"$f({_safe_latex(point_sym)}) = {_safe_latex(deriv_val)}$")
            elif i == 1:
                steps.append(f"$f'({_safe_latex(point_sym)}) = {_safe_latex(deriv_val)}$")
            else:
                steps.append(f"$f^{{({i})}}({_safe_latex(point_sym)}) = {_safe_latex(deriv_val)}$")

            if coeff != 0:
                steps.append(f"  系数 $a_{i} = \\frac{{f^{{({i})}}(a)}}{{{i}!}} = \\frac{{{_safe_latex(deriv_val)}}}{{{i}!}} = {_safe_latex(coeff)}$")

        steps.append("组装泰勒级数:")
        steps.append(f"$f({var_name}) \\approx {latex_result}$")

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
                    steps.append("一元一次方程 $ax + b = 0$")
                    steps.append("解法: $x = -\\frac{b}{a}$")
                    # 提取系数
                    poly = expr.as_poly()
                    coeffs = poly.all_coeffs()
                    if len(coeffs) == 2:
                        a_coef, b_coef = coeffs
                        steps.append(f"其中 $a = {_safe_latex(a_coef)}, b = {_safe_latex(b_coef)}$")
                elif degree == 2:
                    steps.append("一元二次方程 $ax^2 + bx + c = 0$")
                    steps.append("使用求根公式: $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$")
                    # 提取系数
                    poly = expr.as_poly()
                    coeffs = poly.all_coeffs()
                    if len(coeffs) == 3:
                        a_coef, b_coef, c_coef = coeffs
                        steps.append(f"其中 $a = {_safe_latex(a_coef)}, b = {_safe_latex(b_coef)}, c = {_safe_latex(c_coef)}$")
                        discriminant = b_coef**2 - 4*a_coef*c_coef
                        steps.append(f"判别式 $\\Delta = b^2 - 4ac = {_safe_latex(discriminant)}$")
                        if discriminant > 0:
                            steps.append("$\\Delta > 0$，方程有两个不相等的实根")
                        elif discriminant == 0:
                            steps.append("$\\Delta = 0$，方程有两个相等的实根")
                        else:
                            steps.append("$\\Delta < 0$，方程有两个共轭复根")
                elif degree == 3:
                    steps.append("一元三次方程，使用卡尔丹公式或因式分解")
                elif degree == 4:
                    steps.append("一元四次方程")
                else:
                    steps.append(f"{degree} 次多项式方程")
            except Exception:
                pass
        elif expr.has(exp) or expr.has(log):
            steps.append("含指数/对数函数，通过代数变换求解")
            steps.append("利用指数对数性质化简方程")
        elif expr.has(sin, cos, tan):
            steps.append("三角方程，注意周期性，可能有多组解")
            steps.append("利用三角恒等式化简")

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

        if solutions_numeric:
            steps.append("数值近似:")
            for i, (sol, num) in enumerate(zip(solutions, solutions_numeric)):
                if len(solutions) == 1:
                    steps.append(f"${var_name} \\approx {num}$")
                else:
                    steps.append(f"${var_name}_{i+1} \\approx {num}$")

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
