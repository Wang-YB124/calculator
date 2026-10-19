(function () {
  'use strict';

  // Check if Algebrite is loaded
  if (typeof Algebrite === 'undefined') {
    console.error('Algebrite library not loaded');
    alert('数学计算库加载失败，请刷新页面');
    return;
  }

  let currentMode = 'derivative';
  let lastResult = null;

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const dom = {
    tabs: $$('.tab'),
    fnInput: $('#fnInput'),
    fnLabel: $('#fnLabel'),
    calcBtn: $('#calcBtn'),
    clearBtn: $('#clearBtn'),
    derivOrder: $('#derivOrder'),
    integralType: $('#integralType'),
    derivativeOptions: $('#derivativeOptions'),
    integralOptions: $('#integralOptions'),
    limitOptions: $('#limitOptions'),
    limitPoint: $('#limitPoint'),
    limitDirection: $('#limitDirection'),
    seriesOptions: $('#seriesOptions'),
    seriesPoint: $('#seriesPoint'),
    seriesOrder: $('#seriesOrder'),
    solveOptions: $('#solveOptions'),
    solveTarget: $('#solveTarget'),
    solveMethod: $('#solveMethod'),
    definiteOptions: $('#definiteOptions'),
    lowerBound: $('#lowerBound'),
    upperBound: $('#upperBound'),
    resultsSection: $('#resultsSection'),
    resultFormula: $('#resultFormula'),
    resultValue: $('#resultValue'),
    stepsContainer: $('#stepsContainer'),
    graphCanvas: $('#graphCanvas'),
    graphContainer: $('#graphContainer'),
    xMin: $('#xMin'),
    xMax: $('#xMax'),
    showOriginal: $('#showOriginal'),
    showResult: $('#showResult'),
    showSpecialPoints: $('#showSpecialPoints'),
    resultLegend: $('#resultLegend'),
    errorToast: $('#errorToast'),
    errorMsg: $('#errorMsg'),
    toastClose: $('#toastClose'),
    symbolGrid: $('#symbolGrid'),
    previewExpr: $('#previewExpr'),
    zoomInBtn: $('#zoomInBtn'),
    zoomOutBtn: $('#zoomOutBtn'),
    resetViewBtn: $('#resetViewBtn'),
  };

  // Helper functions
  function toLatex(expr) {
    if (!expr) return '';
    // 如果表达式包含错误信息，返回友好的提示
    if (expr.includes('Stop') || expr.includes('expected') || expr.includes('undefined') || expr.includes('nil')) {
      return '\\text{无法计算}';
    }
    
    let result = expr;
    
    // 处理 integral(expr,var) -> \int expr \, dvar
    result = result.replace(/integral\(([^,]+),(\w+)\)/g, '\\int $1 \\, d$2');
    // 处理定积分 integral(expr,var,a,b) -> \int_a^b expr \, dvar
    result = result.replace(/integral\(([^,]+),(\w+),([^,]+),([^)]+)\)/g, '\\int_{$3}^{$4} $1 \\, d$2');
    
    // 处理 d(expr,var) -> \frac{d}{dvar}expr
    result = result.replace(/d\(([^,]+),(\w+)\)/g, '\\frac{d}{d$2}$1');
    
    // 处理 limit(expr,var,point) -> \lim_{var \to point} expr
    result = result.replace(/limit\(([^,]+),(\w+),([^)]+)\)/g, '\\lim_{$2 \\to $3} $1');
    
    // 处理分数: a/b -> \frac{a}{b}（简单情况）
    result = result.replace(/(\w+)\s*\/\s*(\w+)/g, '\\frac{$1}{$2}');
    result = result.replace(/\(([^()]+)\)\s*\/\s*\(([^()]+)\)/g, '\\frac{$1}{$2}');
    result = result.replace(/\(([^()]+)\)\s*\/\s*(\w+)/g, '\\frac{$1}{$2}');
    result = result.replace(/(\w+)\s*\/\s*\(([^()]+)\)/g, '\\frac{$1}{$2}');
    
    // 处理平方根
    result = result.replace(/sqrt\(([^)]+)\)/g, '\\sqrt{$1}');
    
    // 处理三角函数和常用函数（反三角必须在三角函数之前处理）
    result = result.replace(/arcsin\(/g, '\\arcsin(');
    result = result.replace(/arccos\(/g, '\\arccos(');
    result = result.replace(/arctan\(/g, '\\arctan(');
    result = result.replace(/asin\(/g, '\\arcsin(');
    result = result.replace(/acos\(/g, '\\arccos(');
    result = result.replace(/atan\(/g, '\\arctan(');
    result = result.replace(/sin\(/g, '\\sin(');
    result = result.replace(/cos\(/g, '\\cos(');
    result = result.replace(/tan\(/g, '\\tan(');
    result = result.replace(/cot\(/g, '\\cot(');
    result = result.replace(/sec\(/g, '\\sec(');
    result = result.replace(/csc\(/g, '\\csc(');
    result = result.replace(/ln\(/g, '\\ln(');
    result = result.replace(/log\(/g, '\\ln(');
    result = result.replace(/abs\(/g, '|');
    
    // 处理常量和特殊值
    result = result.replace(/\bpi\b/g, '\\pi');
    result = result.replace(/\binf\b/g, '\\infty');
    result = result.replace(/Infinity/g, '\\infty');
    
    // 处理希腊字母
    result = result.replace(/\balpha\b/g, '\\alpha');
    result = result.replace(/\bbeta\b/g, '\\beta');
    result = result.replace(/\bgamma\b/g, '\\gamma');
    result = result.replace(/\bdelta\b/g, '\\delta');
    result = result.replace(/\bepsilon\b/g, '\\epsilon');
    result = result.replace(/\btheta\b/g, '\\theta');
    result = result.replace(/\blambda\b/g, '\\lambda');
    result = result.replace(/\bmu\b/g, '\\mu');
    result = result.replace(/\bphi\b/g, '\\phi');
    result = result.replace(/\bomega\b/g, '\\omega');
    result = result.replace(/\bsigma\b/g, '\\sigma');
    
    // 处理 e^x
    result = result.replace(/e\^(\w+)/g, 'e^{$1}');
    result = result.replace(/e\^\(([^)]+)\)/g, 'e^{$1}');
    
    // 处理幂运算: x^n -> x^{n}, x^(expr) -> x^{expr}
    result = result.replace(/\^\(([^)]+)\)/g, '^{$1}');
    result = result.replace(/\^(\w+)/g, '^{$1}');
    
    // 处理乘法符号
    result = result.replace(/\*/g, ' \\cdot ');
    
    return result;
  }

  function renderKatex(element, latex, displayMode = true) {
    if (!element || !latex) return;
    try {
      katex.render(latex, element, { 
        throwOnError: false,
        displayMode: displayMode
      });
    } catch (e) {
      element.textContent = latex;
    }
  }

  function showError(msg) {
    if (dom.errorMsg) dom.errorMsg.textContent = msg;
    if (dom.errorToast) {
      dom.errorToast.classList.remove('hidden');
      setTimeout(() => dom.errorToast.classList.add('hidden'), 5000);
    }
  }

  function normalizeInput(expr) {
    let s = expr.trim();
    // 移除用户可能误输入的数学符号（这些不是有效变量）
    s = s.replace(/[∂∇→Δεδθφωαβγλμσπ]/g, '');
    s = s.replace(/\bdx\b/gi, '');
    s = s.replace(/\bdy\b/gi, '');
    s = s.replace(/\bdt\b/gi, '');
    s = s.replace(/\*\*/g, '^');
    // 数字后跟字母或左括号：2x -> 2*x, 2( -> 2*(
    s = s.replace(/(\d)([a-zA-Z(])/g, '$1*$2');
    // )后跟( ： )( -> )*(
    s = s.replace(/\)\(/g, ')*(');
    // )后跟字母或数字： )x -> )*x, )2 -> )*2
    s = s.replace(/\)([a-zA-Z0-9])/g, ')*$1');
    // 保护函数名，避免在函数名和(之间插入乘号
    const funcNames = ['sin','cos','tan','cot','sec','csc','arcsin','arccos','arctan','ln','log','sqrt','abs','exp','integral','sum','product','limit','subst','simplify','float','expand'];
    const placeholders = {};
    let idx = 0;
    funcNames.forEach(fn => {
      const re = new RegExp('\\b' + fn + '\\(', 'g');
      s = s.replace(re, () => {
        const key = `__FN${idx++}__`;
        placeholders[key] = fn + '(';
        return key;
      });
    });
    // 现在安全地处理剩余的字母后跟(：x( -> x*(
    s = s.replace(/([a-zA-Z])\(/g, '$1*(');
    // 还原函数名
    Object.keys(placeholders).forEach(key => {
      s = s.replace(key, placeholders[key]);
    });
    s = s.replace(/pi/g, 'π');
    s = s.replace(/\binf\b/g, 'Infinity');
    return s;
  }

  // 将表达式转换为JavaScript可执行的函数
  function createEvalFunction(expr) {
    let jsExpr = expr;
    // 转换数学函数为JavaScript函数
    jsExpr = jsExpr.replace(/\bsin\(/g, 'Math.sin(');
    jsExpr = jsExpr.replace(/\bcos\(/g, 'Math.cos(');
    jsExpr = jsExpr.replace(/\btan\(/g, 'Math.tan(');
    jsExpr = jsExpr.replace(/\bcot\(/g, '(1/Math.tan(');
    jsExpr = jsExpr.replace(/\bsec\(/g, '(1/Math.cos(');
    jsExpr = jsExpr.replace(/\bcsc\(/g, '(1/Math.sin(');
    jsExpr = jsExpr.replace(/\barcsin\(/g, 'Math.asin(');
    jsExpr = jsExpr.replace(/\barccos\(/g, 'Math.acos(');
    jsExpr = jsExpr.replace(/\barctan\(/g, 'Math.atan(');
    jsExpr = jsExpr.replace(/\basinh\(/g, 'Math.asinh(');
    jsExpr = jsExpr.replace(/\bacosh\(/g, 'Math.acosh(');
    jsExpr = jsExpr.replace(/\batanh\(/g, 'Math.atanh(');
    jsExpr = jsExpr.replace(/\bln\(/g, 'Math.log(');
    jsExpr = jsExpr.replace(/\blog\(/g, 'Math.log(');
    jsExpr = jsExpr.replace(/\bsqrt\(/g, 'Math.sqrt(');
    jsExpr = jsExpr.replace(/\babs\(/g, 'Math.abs(');
    jsExpr = jsExpr.replace(/\bexp\(/g, 'Math.exp(');
    // 转换常量
    jsExpr = jsExpr.replace(/\bpi\b/g, 'Math.PI');
    jsExpr = jsExpr.replace(/\be\b/g, 'Math.E');
    // 转换幂运算
    jsExpr = jsExpr.replace(/\^/g, '**');
    
    try {
      return new Function('x', 'return ' + jsExpr);
    } catch (e) {
      return null;
    }
  }
  
  function evalFn(expr, xVal) {
    try {
      const fn = createEvalFunction(expr);
      if (!fn) return NaN;
      const result = fn(xVal);
      return typeof result === 'number' ? result : NaN;
    } catch (e) {
      return NaN;
    }
  }

  // Symbol panel
  const symbolSets = {
    basic: [
      { display: 'x', insert: 'x' },
      { display: 'y', insert: 'y' },
      { display: 't', insert: 't' },
      { display: '+', insert: '+' },
      { display: '−', insert: '-' },
      { display: '×', insert: '*' },
      { display: '÷', insert: '/' },
      { display: '(', insert: '(' },
      { display: ')', insert: ')' },
      { display: 'π', insert: 'pi' },
      { display: 'e', insert: 'e' },
      { display: '±', insert: '+-' },
      { display: '∞', insert: 'inf' },
      { display: '0', insert: '0' },
      { display: '1', insert: '1' },
      { display: '2', insert: '2' },
      { display: '3', insert: '3' },
      { display: '4', insert: '4' },
      { display: '5', insert: '5' },
      { display: '6', insert: '6' },
      { display: '7', insert: '7' },
      { display: '8', insert: '8' },
      { display: '9', insert: '9' },
      { display: '.', insert: '.' },
    ],
    power: [
      { display: 'x', insert: '^' },
      { display: 'x²', insert: '^2' },
      { display: 'x³', insert: '^3' },
      { display: 'x⁴', insert: '^4' },
      { display: 'x⁽⁾', insert: '^(' },
      { display: '√x', insert: 'sqrt(' },
      { display: '∛x', insert: '^(1/3)' },
      { display: 'x½', insert: '^(1/2)' },
      { display: 'x⅔', insert: '^(2/3)' },
      { display: '|x|', insert: 'abs(' },
      { display: '1/x', insert: '1/' },
      { display: 'a/b', insert: '/' },
    ],
    functions: [
      { display: 'sin', insert: 'sin(' },
      { display: 'cos', insert: 'cos(' },
      { display: 'tan', insert: 'tan(' },
      { display: 'cot', insert: 'cot(' },
      { display: 'sec', insert: 'sec(' },
      { display: 'csc', insert: 'csc(' },
      { display: 'arcsin', insert: 'arcsin(' },
      { display: 'arccos', insert: 'arccos(' },
      { display: 'arctan', insert: 'arctan(' },
      { display: 'ln', insert: 'ln(' },
      { display: 'log', insert: 'log(' },
      { display: 'eˣ', insert: 'e^(' },
      { display: 'aˣ', insert: '^(' },
    ],
    calculus: [
      { display: '∂', insert: '∂' },
      { display: '∇', insert: '∇' },
      { display: '∞', insert: 'inf' },
      { display: '→', insert: '->' },
      { display: 'ε', insert: 'epsilon' },
      { display: 'δ', insert: 'delta' },
      { display: 'θ', insert: 'theta' },
      { display: 'φ', insert: 'phi' },
      { display: 'ω', insert: 'omega' },
      { display: 'α', insert: 'alpha' },
      { display: 'β', insert: 'beta' },
      { display: 'γ', insert: 'gamma' },
      { display: 'λ', insert: 'lambda' },
      { display: 'μ', insert: 'mu' },
      { display: 'σ', insert: 'sigma' },
      { display: 'π', insert: 'pi' },
    ],
    common: [
      { display: 'x²+1', insert: 'x^2+1' },
      { display: '1/x', insert: '1/x' },
      { display: 'e^(−x²)', insert: 'e^(-x^2)' },
      { display: 'sin(x)/x', insert: 'sin(x)/x' },
      { display: 'x·eˣ', insert: 'x*e^x' },
      { display: 'x²sin(x)', insert: 'x^2*sin(x)' },
      { display: 'ln(x²+1)', insert: 'ln(x^2+1)' },
      { display: '√(1−x²)', insert: 'sqrt(1-x^2)' },
      { display: '1/(1+x²)', insert: '1/(1+x^2)' },
      { display: 'x·ln(x)', insert: 'x*ln(x)' },
      { display: 'tan(x)/x', insert: 'tan(x)/x' },
      { display: 'e^(−x)', insert: 'e^(-x)' },
      { display: 'sin²x+cos²x', insert: 'sin(x)^2+cos(x)^2' },
      { display: 'e^(ix)', insert: 'e^(i*x)' },
      { display: '1/(1−x)', insert: '1/(1-x)' },
    ],
  };

  let currentSymbolPanel = 'basic';

  function renderSymbolGrid() {
    if (!dom.symbolGrid) return;
    const symbols = symbolSets[currentSymbolPanel] || [];
    dom.symbolGrid.innerHTML = '';
    
    symbols.forEach((sym) => {
      const btn = document.createElement('button');
      btn.className = 'symbol-btn';
      btn.textContent = sym.display;
      btn.title = sym.insert;
      btn.addEventListener('click', () => {
        if (dom.fnInput) {
          const start = dom.fnInput.selectionStart;
          const end = dom.fnInput.selectionEnd;
          const value = dom.fnInput.value;
          dom.fnInput.value = value.substring(0, start) + sym.insert + value.substring(end);
          dom.fnInput.focus();
          dom.fnInput.setSelectionRange(start + sym.insert.length, start + sym.insert.length);
          updatePreview();
        }
      });
      dom.symbolGrid.appendChild(btn);
    });
  }

  function updatePreview() {
    if (!dom.previewExpr || !dom.fnInput) return;
    const expr = dom.fnInput.value.trim();
    if (!expr) {
      dom.previewExpr.innerHTML = '<span style="color:#666">输入表达式后这里会显示渲染后的公式</span>';
      return;
    }
    
    try {
      const normalized = normalizeInput(expr);
      const latex = toLatex(normalized);
      renderKatex(dom.previewExpr, `f(x) = ${latex}`, false);
    } catch (e) {
      dom.previewExpr.textContent = expr;
    }
  }

  // Toggle options based on mode
  function toggleOptions() {
    if (!dom.derivativeOptions || !dom.integralOptions) return;
    
    dom.derivativeOptions.classList.add('hidden');
    dom.integralOptions.classList.add('hidden');
    if (dom.limitOptions) dom.limitOptions.classList.add('hidden');
    if (dom.seriesOptions) dom.seriesOptions.classList.add('hidden');
    if (dom.solveOptions) dom.solveOptions.classList.add('hidden');

    if (currentMode === 'derivative') {
      dom.derivativeOptions.classList.remove('hidden');
    } else if (currentMode === 'integral') {
      dom.integralOptions.classList.remove('hidden');
    } else if (currentMode === 'limit' && dom.limitOptions) {
      dom.limitOptions.classList.remove('hidden');
    } else if (currentMode === 'series' && dom.seriesOptions) {
      dom.seriesOptions.classList.remove('hidden');
    } else if (currentMode === 'solve' && dom.solveOptions) {
      dom.solveOptions.classList.remove('hidden');
    }
  }

  // ========== SymPy 后端 API ==========
  const BACKEND_URL = 'https://divine-radiance-production-c1b9.up.railway.app';

  async function checkBackend() {
    try {
      const resp = await fetch(BACKEND_URL + '/api/health', { signal: AbortSignal.timeout(15000) });
      return resp.ok;
    } catch (e) {
      return false;
    }
  }

  function prepareExprForBackend(raw) {
    let s = raw.trim();
    s = s.replace(/\*\*/g, '^');
    s = s.replace(/π/g, 'pi');
    s = s.replace(/∞/g, 'oo');
    return s;
  }

  async function callBackendAPI(endpoint, data) {
    try {
      const resp = await fetch(`${BACKEND_URL}/api/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        signal: AbortSignal.timeout(60000)
      });
      return await resp.json();
    } catch (e) {
      console.warn(`Backend API ${endpoint} failed:`, e);
      return null;
    }
  }

  function parseBackendSteps(backendResult, mode, opts) {
    const rawSteps = backendResult.steps || [];
    const formatted = [];

    const extractLatex = (s) => {
      const m = s.match(/\$([^$]+)\$/);
      return m ? m[1] : null;
    };
    const stripLatex = (s) => s.replace(/\$[^$]*\$/g, '').trim();

    for (let i = 0; i < rawSteps.length; i++) {
      const s = rawSteps[i];
      if (!s || typeof s !== 'string') continue;

      const latex = extractLatex(s);
      const text = stripLatex(s);

      if (/^原函数/.test(text)) {
        formatted.push({
          desc: '原始函数',
          explanation: '需要处理的函数',
          latex: latex || `f(x) = ${toLatex(opts.expr)}`
        });
      } else if (/^计算(不定|定)?积分/.test(text)) {
        formatted.push({
          desc: '设置积分',
          explanation: text.replace(/^计算/, ''),
          latex: latex
        });
      } else if (/^结果/.test(text)) {
        formatted.push({
          desc: '最终结果',
          explanation: '',
          latex: latex || backendResult.resultLatex
        });
      } else if (/^方法[：:]/.test(text)) {
        const method = text.replace(/^方法[：:]\s*/, '');
        formatted.push({
          desc: '计算方法',
          explanation: method,
          latex: null
        });
      } else if (/^数值/.test(text)) {
        formatted.push({
          desc: '数值验证',
          explanation: '',
          latex: latex
        });
      } else if (/^各阶导数/.test(text)) {
        formatted.push({
          desc: '计算各阶导数',
          explanation: '在展开点求值，计算泰勒系数',
          latex: null
        });
      } else if (/^求解方程/.test(text)) {
        formatted.push({
          desc: '建立方程',
          explanation: '令 f(x) = 0',
          latex: latex
        });
      } else if (/^解[：:]/.test(text)) {
        formatted.push({
          desc: '方程的解',
          explanation: '',
          latex: latex
        });
      } else if (/^对.*求.*导数/.test(text)) {
        formatted.push({
          desc: '求导',
          explanation: text,
          latex: null
        });
      } else if (/^(应用|使用|利用)/.test(text)) {
        formatted.push({
          desc: '应用法则',
          explanation: text,
          latex: null
        });
      } else if (/^(多项式|三角|负幂|底数|加法|含|有理)/.test(text) || /→/.test(text)) {
        formatted.push({
          desc: '分析结构',
          explanation: text,
          latex: null
        });
      } else if (/^(被积函数|先|将)/.test(text)) {
        formatted.push({
          desc: '变换处理',
          explanation: text,
          latex: null
        });
      } else if (/^SymPy 无法/.test(text) || /^建议/.test(text)) {
        formatted.push({
          desc: '提示',
          explanation: text,
          latex: null
        });
      } else if (/^类型/.test(text)) {
        formatted.push({
          desc: '判断类型',
          explanation: text,
          latex: null
        });
      } else if (/^分子求导|^分母求导/.test(text)) {
        formatted.push({
          desc: text.replace(/[：:].*$/, ''),
          explanation: '',
          latex: latex
        });
      } else if (/^在.*展开/.test(text)) {
        formatted.push({
          desc: '展开点',
          explanation: text,
          latex: null
        });
      } else if (/^展开到/.test(text)) {
        formatted.push({
          desc: '展开阶数',
          explanation: text,
          latex: null
        });
      } else if (/^直接代入/.test(text)) {
        formatted.push({
          desc: '代入检验',
          explanation: text,
          latex: null
        });
      } else if (/^原函数[：:]/.test(text) && latex) {
        formatted.push({
          desc: '求原函数',
          explanation: '不定积分的结果 F(x)',
          latex: latex
        });
      } else if (/^其中/.test(text)) {
        formatted.push({
          desc: '参数说明',
          explanation: text,
          latex: null
        });
      } else if (/^合并 | 最终/.test(text)) {
        formatted.push({
          desc: text.replace(/[：:].*$/, ''),
          explanation: '',
          latex: latex
        });
      } else if (/^验证/.test(text)) {
        formatted.push({
          desc: '验证结果',
          explanation: text,
          latex: null
        });
      } else if (/^提取常数/.test(text)) {
        formatted.push({
          desc: '提取常数',
          explanation: '',
          latex: latex
        });
      } else if (/^应用幂函数 | 应用积分公式/.test(text)) {
        formatted.push({
          desc: '应用公式',
          explanation: text,
          latex: null
        });
      } else if (latex) {
        const cleanText = text.replace(/^[：:]\s*/, '').trim();
        formatted.push({
          desc: cleanText || '中间结果',
          explanation: '',
          latex: latex
        });
      } else if (text.length > 0) {
        formatted.push({
          desc: text,
          explanation: '',
          latex: null
        });
      }
    }

    if (formatted.length === 0) {
      formatted.push({
        desc: '原始函数',
        explanation: '需要处理的函数',
        latex: `f(x) = ${toLatex(opts.expr)}`
      });
      const modeDesc = {
        derivative: `使用 SymPy 计算${opts.order || 1}阶导数`,
        integral: '使用 SymPy 计算积分',
        limit: '使用 SymPy 计算极限',
        series: '使用 SymPy 计算泰勒级数',
        solve: '使用 SymPy 求解方程'
      };
      formatted.push({
        desc: modeDesc[mode] || '计算',
        explanation: '后端符号计算引擎给出精确结果',
        latex: backendResult.resultLatex
      });
    }

    return formatted;
  }

  async function tryBackendCompute(raw, mode, options) {
    const expr = prepareExprForBackend(raw);
    let result = null;

    if (mode === 'derivative') {
      result = await callBackendAPI('derivative', {
        expression: expr, variable: 'x', order: options.order || 1
      });
      if (result && result.success) {
        return {
          resultLatex: result.latex,
          steps: result.steps,
          expression: result.expression,
          source: 'backend'
        };
      }
    } else if (mode === 'integral') {
      result = await callBackendAPI('integral', {
        expression: expr, variable: 'x',
        lower: options.lower || null,
        upper: options.upper || null
      });
      if (result && result.success) {
        return {
          resultLatex: result.latex,
          steps: result.steps,
          expression: result.expression,
          definite: result.definite,
          numerical: result.numerical,
          source: 'backend'
        };
      }
    } else if (mode === 'limit') {
      const dirMap = { 'left': '-', 'right': '+', 'both': null };
      result = await callBackendAPI('limit', {
        expression: expr, variable: 'x',
        point: options.point || '0',
        direction: dirMap[options.direction] || null
      });
      if (result && result.success) {
        return {
          resultLatex: result.latex,
          steps: result.steps,
          expression: result.expression,
          source: 'backend'
        };
      }
    } else if (mode === 'series') {
      result = await callBackendAPI('series', {
        expression: expr, variable: 'x',
        point: options.point || '0',
        order: options.seriesOrder || 6
      });
      if (result && result.success) {
        return {
          resultLatex: result.latex,
          steps: result.steps,
          expression: result.expression,
          terms: result.terms,
          source: 'backend'
        };
      }
    } else if (mode === 'solve') {
      let solveExpr = expr;
      if (options.target && options.target !== '0') {
        solveExpr = `(${expr}) - (${options.target})`;
      }
      result = await callBackendAPI('solve', {
        expression: solveExpr, variable: 'x'
      });
      if (result && result.success) {
        return {
          resultLatex: result.latex,
          steps: result.steps,
          expression: result.expression,
          solutions: result.solutions,
          solutionsNumeric: result.solutions_numeric,
          source: 'backend'
        };
      }
    }
    return null;
  }

  // Calculation functions
  function computeDerivative(expr, order) {
    let currentExpr = expr;
    
    // 尝试先展开表达式
    try {
      const expanded = Algebrite.run(`expand(${expr})`);
      if (expanded && !expanded.includes('Stop') && !expanded.includes('undefined')) {
        currentExpr = expanded;
      }
    } catch (e) {}
    
    for (let i = 0; i < order; i++) {
      let result = null;
      
      // 尝试直接求导
      try {
        result = Algebrite.run(`d(${currentExpr},x)`);
      } catch (e) {}
      
      // 如果失败，尝试先简化再求导
      if (!result || result.includes('Stop') || result.includes('undefined')) {
        try {
          const simplified = Algebrite.run(`simplify(${currentExpr})`);
          result = Algebrite.run(`d(${simplified},x)`);
        } catch (e) {}
      }
      
      if (!result || result.includes('Stop') || result.includes('undefined')) {
        return '\\text{求导失败}';
      }
      currentExpr = result;
    }
    
    // 尝试多种简化策略
    let simplified = currentExpr;
    try {
      const s1 = Algebrite.run(`simplify(${currentExpr})`);
      if (s1 && !s1.includes('Stop')) simplified = s1;
    } catch (e) {}
    
    try {
      const s2 = Algebrite.run(`expand(${simplified})`);
      if (s2 && !s2.includes('Stop')) simplified = s2;
    } catch (e) {}
    
    return simplified;
  }

  function computeIntegral(expr, type, lower, upper) {
    let antideriv = null;
    
    // 尝试直接积分
    try {
      antideriv = Algebrite.run(`integral(${expr},x)`);
    } catch (e) {}
    
    // 如果失败，尝试先展开再积分
    if (!antideriv || antideriv.includes('integral(') || antideriv.includes('Stop') || antideriv.includes('undefined')) {
      try {
        const expanded = Algebrite.run(`expand(${expr})`);
        if (expanded && !expanded.includes('Stop')) {
          antideriv = Algebrite.run(`integral(${expanded},x)`);
        }
      } catch (e) {}
    }
    
    // 如果还是失败，尝试先简化再积分
    if (!antideriv || antideriv.includes('integral(') || antideriv.includes('Stop') || antideriv.includes('undefined')) {
      try {
        const simplified = Algebrite.run(`simplify(${expr})`);
        if (simplified && !simplified.includes('Stop')) {
          antideriv = Algebrite.run(`integral(${simplified},x)`);
        }
      } catch (e) {}
    }
    
    // 检查是否成功
    if (!antideriv || antideriv.includes('integral(') || antideriv.includes('Stop') || antideriv.includes('undefined')) {
      if (type === 'definite' && lower && upper) {
        const numResult = numericalIntegrate(expr, parseFloat(lower), parseFloat(upper));
        if (isFinite(numResult)) {
          return { 
            result: '\\text{数值积分结果}', 
            definiteValue: numResult, 
            definiteSymbolic: null,
            isNumerical: true 
          };
        }
        return { result: '\\text{数值积分也失败}', definiteValue: null, isNumerical: true };
      }
      // 不定积分无法求解，尝试返回数值近似提示
      return { 
        result: '\\text{该积分无初等原函数}', 
        definiteValue: null,
        suggestion: '可尝试计算定积分获取数值结果',
        isNumerical: true 
      };
    }
    
    // 简化结果
    let simplified = antideriv;
    try {
      const s1 = Algebrite.run(`simplify(${antideriv})`);
      if (s1 && !s1.includes('Stop')) simplified = s1;
    } catch (e) {}
    
    if (type === 'definite' && lower && upper) {
      let definiteResult = null;
      let numericResult = null;
      
      try {
        const upperVal = Algebrite.run(`subst(${upper},x,${simplified})`);
        const lowerVal = Algebrite.run(`subst(${lower},x,${simplified})`);
        definiteResult = Algebrite.run(`simplify(${upperVal}-(${lowerVal}))`);
        numericResult = Algebrite.run(`float(${definiteResult})`);
      } catch (e) {
        numericResult = numericalIntegrate(expr, parseFloat(lower), parseFloat(upper));
      }
      
      return { result: simplified, definiteValue: numericResult, definiteSymbolic: definiteResult };
    }
    
    return { result: simplified, definiteValue: null };
  }
  
  function numericalIntegrate(expr, a, b) {
    // 自适应 Simpson 法，更高精度
    function simpson(f, a, b, n) {
      const h = (b - a) / n;
      let sum = f(a) + f(b);
      for (let i = 1; i < n; i++) {
        const x = a + i * h;
        const y = f(x);
        sum += (i % 2 === 0 ? 2 : 4) * (isFinite(y) ? y : 0);
      }
      return (h / 3) * sum;
    }
    
    const fn = createEvalFunction(expr);
    if (!fn) return NaN;
    
    const f = (x) => {
      try {
        const y = fn(x);
        return isFinite(y) ? y : 0;
      } catch (e) {
        return 0;
      }
    };
    
    // 逐步增加精度直到收敛
    let n = 100;
    let prev = simpson(f, a, b, n);
    for (let iter = 0; iter < 10; iter++) {
      n *= 2;
      const curr = simpson(f, a, b, n);
      if (Math.abs(curr - prev) < 1e-10) {
        return curr;
      }
      prev = curr;
    }
    return prev;
  }

  function computeLimit(expr, point, direction) {
    // 尝试使用Algebrite的limit函数
    try {
      let limitCmd;
      if (direction === 'left') {
        limitCmd = `limit(${expr},x,${point},-)`;
      } else if (direction === 'right') {
        limitCmd = `limit(${expr},x,${point},+)`;
      } else {
        limitCmd = `limit(${expr},x,${point})`;
      }
      const limitResult = Algebrite.run(limitCmd);
      if (limitResult && !limitResult.includes('limit(') && !limitResult.includes('Stop') && !limitResult.includes('undefined')) {
        const simplified = Algebrite.run(`simplify(${limitResult})`);
        const numeric = Algebrite.run(`float(${simplified})`);
        const numVal = parseFloat(numeric);
        return { result: simplified, numericValue: isFinite(numVal) ? numVal : null };
      }
    } catch (e) {}

    // 直接代入尝试
    try {
      const directSub = Algebrite.run(`subst(${point},x,${expr})`);
      const simplified = Algebrite.run(`simplify(${directSub})`);
      const numeric = Algebrite.run(`float(${simplified})`);
      const numVal = parseFloat(numeric);
      if (isFinite(numVal)) {
        return { result: simplified, numericValue: numVal };
      }
    } catch (e) {}

    // 数值逼近
    const h = 0.0001;
    const p = parseFloat(point) || 0;
    let leftVal, rightVal;
    
    try {
      leftVal = evalFn(expr, p - h);
      rightVal = evalFn(expr, p + h);
    } catch (e) {
      return { result: '\\text{无法计算}', numericValue: null };
    }

    if (direction === 'both') {
      if (isFinite(leftVal) && isFinite(rightVal)) {
        const avg = (leftVal + rightVal) / 2;
        return { result: avg.toFixed(6), numericValue: avg };
      }
      if (!isFinite(leftVal) && !isFinite(rightVal)) return { result: '\\infty', numericValue: Infinity };
      return { result: '\\text{不存在}', numericValue: null };
    } else {
      const val = direction === 'left' ? leftVal : rightVal;
      return { result: isFinite(val) ? val.toFixed(6) : '\\infty', numericValue: val };
    }
  }

  function computeSeries(expr, point, order) {
    const coefficients = [];
    let currentExpr = expr;
    
    // f(a) - 使用数值计算更可靠
    let f0Value;
    try {
      const f0 = Algebrite.run(`subst(${point},x,${expr})`);
      f0Value = Algebrite.run(`simplify(${f0})`);
      if (!f0Value || f0Value.includes('Stop')) {
        // 回退到数值计算
        const fn = createEvalFunction(expr);
        if (fn) {
          const numVal = fn(parseFloat(point) || 0);
          f0Value = isFinite(numVal) ? numVal.toString() : '0';
        } else {
          f0Value = '0';
        }
      }
    } catch (e) {
      f0Value = '0';
    }
    coefficients.push({ value: f0Value, factorial: 1 });
    
    // Higher derivatives
    for (let n = 1; n <= order; n++) {
      let derivExpr = null;
      
      // 尝试求导
      try {
        derivExpr = Algebrite.run(`d(${currentExpr},x)`);
      } catch (e) {}
      
      if (!derivExpr || derivExpr.includes('Stop') || derivExpr.includes('undefined')) {
        // 如果求导失败，使用数值微分
        const fn = createEvalFunction(currentExpr);
        if (fn) {
          const h = 0.0001;
          const p = parseFloat(point) || 0;
          const numDeriv = (fn(p + h) - fn(p - h)) / (2 * h);
          coefficients.push({ value: isFinite(numDeriv) ? numDeriv.toString() : '0', factorial: Array.from({length: n}, (_, i) => i + 1).reduce((a, b) => a * b, 1) });
          continue;
        } else {
          coefficients.push({ value: '0', factorial: Array.from({length: n}, (_, i) => i + 1).reduce((a, b) => a * b, 1) });
          continue;
        }
      }
      
      currentExpr = derivExpr;
      
      // 在展开点求值
      let derivAtPoint;
      try {
        derivAtPoint = Algebrite.run(`subst(${point},x,${currentExpr})`);
        derivAtPoint = Algebrite.run(`simplify(${derivAtPoint})`);
        if (!derivAtPoint || derivAtPoint.includes('Stop')) {
          // 数值回退
          const fn = createEvalFunction(currentExpr);
          if (fn) {
            const numVal = fn(parseFloat(point) || 0);
            derivAtPoint = isFinite(numVal) ? numVal.toString() : '0';
          } else {
            derivAtPoint = '0';
          }
        }
      } catch (e) {
        derivAtPoint = '0';
      }
      
      const factorial = Array.from({length: n}, (_, i) => i + 1).reduce((a, b) => a * b, 1);
      coefficients.push({ value: derivAtPoint, factorial: factorial });
    }

    // Build series
    const terms = coefficients.map((coef, n) => {
      const coefValue = coef.value;
      if (n === 0) {
        return toLatex(coefValue);
      } else {
        const coefLatex = toLatex(`(${coefValue})/(${coef.factorial})`);
        return `${coefLatex}(x-${point})^${n}`;
      }
    });

    return {
      result: terms.join(' + '),
      seriesCoefficients: coefficients,
      seriesOrder: order,
      seriesPoint: point
    };
  }

  function computeSolve(expr, target, method) {
    const rearranged = target === '0' ? expr : `(${expr})-(${target})`;
    
    // 尝试符号求解（二次方程等）
    if (method === 'symbolic') {
      try {
        // 对于简单多项式，尝试用roots
        const roots = Algebrite.run(`roots(${rearranged},x)`);
        if (roots && !roots.includes('Stop') && !roots.includes('undefined') && !roots.includes('roots(')) {
          return { result: roots, solutions: [roots] };
        }
      } catch (e) {}
    }

    // 数值求解
    const solutions = [];
    const step = 0.5;
    let prevX = -100;
    let prevY = evalFn(rearranged, prevX);

    for (let x = -99.5; x <= 100; x += step) {
      const y = evalFn(rearranged, x);
      if (isFinite(prevY) && isFinite(y) && prevY * y < 0) {
        let a = prevX, b = x;
        for (let i = 0; i < 50; i++) {
          const mid = (a + b) / 2;
          const fmid = evalFn(rearranged, mid);
          if (!isFinite(fmid)) break;
          if (Math.abs(fmid) < 1e-12 || (b - a) < 1e-10) break;
          if (prevY * fmid < 0) b = mid;
          else a = mid;
        }
        const root = (a + b) / 2;
        if (isFinite(root)) {
          const tooClose = solutions.some(s => Math.abs(s - root) < 0.1);
          if (!tooClose) solutions.push(root);
        }
      }
      prevX = x;
      prevY = y;
    }

    if (solutions.length > 0) {
      return {
        result: solutions.map(s => {
          const rounded = Math.round(s * 1e6) / 1e6;
          return Number.isInteger(rounded) ? rounded.toString() : rounded.toFixed(6);
        }).join(',\\; '),
        solutions
      };
    }

    return { result: '\\text{未找到实数解}', solutions: [] };
  }

  function generateDetailedSteps(expr, mode, order) {
    const steps = [];
    
    steps.push({
      desc: '原始函数',
      explanation: '这是我们需要处理的函数 f(x)',
      latex: `f(x) = ${toLatex(expr)}`
    });

    if (mode === 'derivative') {
      const derivResult = computeDerivative(expr, order);
      const dNotation = order === 1 ? "f'(x)" : order === 2 ? "f''(x)" : `f^{(${order})}(x)`;
      
      steps.push({
        desc: `求${order}阶导数`,
        explanation: `对函数应用求导法则，求得${order}阶导数`,
        latex: `${dNotation} = ${toLatex(derivResult)}`
      });

      return { result: derivResult, steps };
    } else if (mode === 'integral') {
      const type = dom.integralType ? dom.integralType.value : 'indefinite';
      const lower = dom.lowerBound ? dom.lowerBound.value : '';
      const upper = dom.upperBound ? dom.upperBound.value : '';
      
      const intResult = computeIntegral(expr, type, lower, upper);
      
      if (type === 'definite' && lower && upper) {
        steps.push({
          desc: '计算定积分',
          explanation: `使用牛顿-莱布尼茨公式计算从 ${lower} 到 ${upper} 的定积分`,
          latex: `\\int_{${lower}}^{${upper}} f(x)dx = ${toLatex(intResult.definiteSymbolic || intResult.result)}`
        });
        return { result: intResult.definiteSymbolic || intResult.result, steps, definiteValue: intResult.definiteValue };
      } else {
        steps.push({
          desc: '计算不定积分',
          explanation: '求得原函数族，加上积分常数 C',
          latex: `\\int f(x)dx = ${toLatex(intResult.result)} + C`
        });
        return { result: intResult.result, steps };
      }
    } else if (mode === 'limit' && dom.limitPoint) {
      const point = dom.limitPoint.value || '0';
      const direction = dom.limitDirection ? dom.limitDirection.value : 'both';
      const limitResult = computeLimit(expr, point, direction);
      
      const dirStr = direction === 'left' ? '^-' : direction === 'right' ? '^+' : '';
      steps.push({
        desc: '计算极限',
        explanation: `计算当 x 趋向于 ${point} 时的极限`,
        latex: `\\lim_{x \\to ${point}${dirStr}} f(x) = ${toLatex(limitResult.result)}`
      });
      
      return { result: limitResult.result, steps, limitValue: limitResult.numericValue };
    } else if (mode === 'series' && dom.seriesPoint) {
      const point = dom.seriesPoint.value || '0';
      const seriesOrder = parseInt(dom.seriesOrder ? dom.seriesOrder.value : 5);
      const seriesResult = computeSeries(expr, point, seriesOrder);
      
      steps.push({
        desc: '泰勒级数展开',
        explanation: `在 x = ${point} 处展开到 ${seriesOrder} 阶`,
        latex: `f(x) \\approx ${toLatex(seriesResult.result)}`
      });
      
      return { result: seriesResult.result, steps, seriesCoefficients: seriesResult.seriesCoefficients };
    } else if (mode === 'solve' && dom.solveTarget) {
      const target = dom.solveTarget.value || '0';
      const method = dom.solveMethod ? dom.solveMethod.value : 'numerical';
      const solveResult = computeSolve(expr, target, method);
      
      steps.push({
        desc: '求解方程',
        explanation: `求解 f(x) = ${target}`,
        latex: `f(x) = ${toLatex(target)} \\Rightarrow x = ${toLatex(solveResult.result)}`
      });
      
      return { result: solveResult.result, steps, solutions: solveResult.solutions };
    }

    return { result: expr, steps };
  }

  function displayResults(data) {
    if (!dom.resultFormula || !dom.stepsContainer) return;
    
    const resultLatex = data.isBackendLatex ? data.result : toLatex(data.result);
    
    // 检查是否是错误信息
    const isError = resultLatex.includes('\\text{无法') || 
                    resultLatex.includes('\\text{数值') ||
                    resultLatex.includes('无法求得') ||
                    resultLatex.includes('无初等原函数');

    // 统一错误处理
    if (isError) {
      renderKatex(dom.resultFormula, '\\text{计算失败，该表达式可能超出当前引擎能力范围}');
      if (dom.resultValue) {
        dom.resultValue.textContent = '请尝试简化表达式或使用其他计算方式';
        dom.resultValue.classList.remove('hidden');
      }
      // 仍然显示后端返回的步骤（包含建议）
      dom.stepsContainer.innerHTML = '';
      if (data.steps && data.steps.length > 0) {
        data.steps.forEach((step, i) => {
          const stepEl = document.createElement('div');
          stepEl.className = 'step';
          stepEl.innerHTML = `
            <div class="step-number">${i + 1}</div>
            <div class="step-content">
              <div class="step-description">${step.desc}</div>
              <div class="step-explanation">${step.explanation || ''}</div>
              <div class="step-formula"></div>
            </div>
          `;
          
          const formulaEl = stepEl.querySelector('.step-formula');
          if (step.latex) {
            renderKatex(formulaEl, step.latex, false);
          }
          
          dom.stepsContainer.appendChild(stepEl);
        });
      }
      displayRelatedFormulas(data.mode);
      return;
    }

    if (data.mode === 'derivative') {
      const order = parseInt(dom.derivOrder ? dom.derivOrder.value : 1);
      const dNotation = order === 1 ? "f'(x)" : order === 2 ? "f''(x)" : `f^{(${order})}(x)`;
      renderKatex(dom.resultFormula, `${dNotation} = ${resultLatex}`);
      if (dom.resultLegend) dom.resultLegend.textContent = '导函数';
    } else if (data.mode === 'integral') {
      const type = dom.integralType ? dom.integralType.value : 'indefinite';
      if (type === 'indefinite') {
        const hasC = resultLatex.includes('+ C') || resultLatex.includes('+C');
        renderKatex(dom.resultFormula, `\\int f(x)dx = ${resultLatex}${hasC ? '' : ' + C'}`);
        if (data.suggestion && dom.resultValue) {
          dom.resultValue.textContent = data.suggestion;
          dom.resultValue.classList.remove('hidden');
        }
      } else {
        const a = dom.lowerBound ? dom.lowerBound.value : '0';
        const b = dom.upperBound ? dom.upperBound.value : '1';
        renderKatex(dom.resultFormula, `\\int_{${a}}^{${b}} f(x)dx = ${resultLatex}`);
        if (data.definiteValue && dom.resultValue) {
          const numVal = parseFloat(data.definiteValue);
          if (isFinite(numVal)) {
            dom.resultValue.textContent = `数值结果 ≈ ${numVal.toFixed(6)}`;
          } else {
            dom.resultValue.textContent = '数值计算失败';
          }
          dom.resultValue.classList.remove('hidden');
        }
      }
      if (dom.resultLegend) dom.resultLegend.textContent = '积分结果';
    } else if (data.mode === 'limit') {
      const point = dom.limitPoint ? dom.limitPoint.value : '0';
      const direction = dom.limitDirection ? dom.limitDirection.value : 'both';
      const dirStr = direction === 'left' ? '^-' : direction === 'right' ? '^+' : '';
      renderKatex(dom.resultFormula, `\\lim_{x \\to ${point}${dirStr}} f(x) = ${resultLatex}`);
      if (dom.resultLegend) dom.resultLegend.textContent = '极限';
    } else if (data.mode === 'series') {
      const point = dom.seriesPoint ? dom.seriesPoint.value : '0';
      const order = dom.seriesOrder ? dom.seriesOrder.value : 5;
      renderKatex(dom.resultFormula, `f(x) \\approx ${resultLatex}`);
      if (dom.resultValue) {
        dom.resultValue.textContent = `在 x=${point} 处展开到 ${order} 阶`;
        dom.resultValue.classList.remove('hidden');
      }
      if (dom.resultLegend) dom.resultLegend.textContent = '泰勒级数';
    } else if (data.mode === 'solve') {
      const target = dom.solveTarget ? dom.solveTarget.value : '0';
      if (data.solutions && data.solutions.length > 0) {
        renderKatex(dom.resultFormula, `f(x) = ${toLatex(target)} \\Rightarrow x = ${resultLatex}`);
        if (dom.resultValue) {
          dom.resultValue.textContent = `找到 ${data.solutions.length} 个解`;
          dom.resultValue.classList.remove('hidden');
        }
      } else {
        renderKatex(dom.resultFormula, `f(x) = ${toLatex(target)} \\Rightarrow \\text{无实数解}`);
      }
      if (dom.resultLegend) dom.resultLegend.textContent = '方程的解';
    }

    // Display steps
    dom.stepsContainer.innerHTML = '';
    if (data.steps) {
      data.steps.forEach((step, i) => {
        const stepEl = document.createElement('div');
        stepEl.className = 'step';
        stepEl.innerHTML = `
          <div class="step-number">${i + 1}</div>
          <div class="step-content">
            <div class="step-description">${step.desc}</div>
            <div class="step-explanation">${step.explanation || ''}</div>
            <div class="step-formula"></div>
          </div>
        `;
        
        const formulaEl = stepEl.querySelector('.step-formula');
        if (step.latex) {
          renderKatex(formulaEl, step.latex, false);
        }
        
        dom.stepsContainer.appendChild(stepEl);
      });
    }
    
    // 显示相关公式
    displayRelatedFormulas(data.mode);
  }
  
  // 相关公式数据库
  const formulaDatabase = {
    derivative: [
      { name: '幂函数求导', latex: '\\frac{d}{dx}x^n = nx^{n-1}' },
      { name: '指数函数求导', latex: '\\frac{d}{dx}e^x = e^x' },
      { name: '对数函数求导', latex: '\\frac{d}{dx}\\ln(x) = \\frac{1}{x}' },
      { name: '正弦函数求导', latex: '\\frac{d}{dx}\\sin(x) = \\cos(x)' },
      { name: '余弦函数求导', latex: '\\frac{d}{dx}\\cos(x) = -\\sin(x)' },
      { name: '正切函数求导', latex: '\\frac{d}{dx}\\tan(x) = \\sec^2(x)' },
      { name: '乘法法则', latex: '(fg)\' = f\'g + fg\'' },
      { name: '除法法则', latex: '\\left(\\frac{f}{g}\\right)\' = \\frac{f\'g - fg\'}{g^2}' },
      { name: '链式法则', latex: '\\frac{d}{dx}f(g(x)) = f\'(g(x)) \\cdot g\'(x)' },
    ],
    integral: [
      { name: '幂函数积分', latex: '\\int x^n dx = \\frac{x^{n+1}}{n+1} + C \\quad (n \\neq -1)' },
      { name: '指数函数积分', latex: '\\int e^x dx = e^x + C' },
      { name: '对数函数积分', latex: '\\int \\frac{1}{x} dx = \\ln|x| + C' },
      { name: '正弦函数积分', latex: '\\int \\sin(x) dx = -\\cos(x) + C' },
      { name: '余弦函数积分', latex: '\\int \\cos(x) dx = \\sin(x) + C' },
      { name: '正切函数积分', latex: '\\int \\sec^2(x) dx = \\tan(x) + C' },
      { name: '分部积分法', latex: '\\int u \\, dv = uv - \\int v \\, du' },
      { name: '换元积分法', latex: '\\int f(g(x))g\'(x)dx = \\int f(u)du' },
      { name: '牛顿-莱布尼茨公式', latex: '\\int_a^b f(x)dx = F(b) - F(a)' },
    ],
    limit: [
      { name: '重要极限 I', latex: '\\lim_{x \\to 0} \\frac{\\sin(x)}{x} = 1' },
      { name: '重要极限 II', latex: '\\lim_{x \\to \\infty} \\left(1 + \\frac{1}{x}\\right)^x = e' },
      { name: '等价无穷小', latex: '\\sin(x) \\sim x, \\quad \\tan(x) \\sim x \\quad (x \\to 0)' },
      { name: '洛必达法则', latex: '\\lim_{x \\to a} \\frac{f(x)}{g(x)} = \\lim_{x \\to a} \\frac{f\'(x)}{g\'(x)}' },
      { name: '泰勒展开', latex: 'f(x) = f(a) + f\'(a)(x-a) + \\frac{f\'\'(a)}{2!}(x-a)^2 + \\cdots' },
      { name: '夹逼定理', latex: 'g(x) \\leq f(x) \\leq h(x) \\Rightarrow \\lim f(x) = L' },
    ],
    series: [
      { name: '泰勒级数', latex: 'f(x) = \\sum_{n=0}^{\\infty} \\frac{f^{(n)}(a)}{n!}(x-a)^n' },
      { name: '麦克劳林级数', latex: 'f(x) = \\sum_{n=0}^{\\infty} \\frac{f^{(n)}(0)}{n!}x^n' },
      { name: '几何级数', latex: '\\sum_{n=0}^{\\infty} x^n = \\frac{1}{1-x} \\quad (|x| < 1)' },
      { name: 'e^x 展开', latex: 'e^x = \\sum_{n=0}^{\\infty} \\frac{x^n}{n!} = 1 + x + \\frac{x^2}{2!} + \\cdots' },
      { name: 'sin(x) 展开', latex: '\\sin(x) = \\sum_{n=0}^{\\infty} \\frac{(-1)^n x^{2n+1}}{(2n+1)!}' },
      { name: 'cos(x) 展开', latex: '\\cos(x) = \\sum_{n=0}^{\\infty} \\frac{(-1)^n x^{2n}}{(2n)!}' },
      { name: 'ln(1+x) 展开', latex: '\\ln(1+x) = \\sum_{n=1}^{\\infty} \\frac{(-1)^{n+1} x^n}{n} \\quad (|x| < 1)' },
    ],
    solve: [
      { name: '一元二次方程', latex: 'ax^2 + bx + c = 0 \\Rightarrow x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}' },
      { name: '韦达定理', latex: 'x_1 + x_2 = -\\frac{b}{a}, \\quad x_1 x_2 = \\frac{c}{a}' },
      { name: '因式分解', latex: 'x^2 - a^2 = (x+a)(x-a)' },
      { name: '完全平方公式', latex: '(x \\pm a)^2 = x^2 \\pm 2ax + a^2' },
      { name: '立方和公式', latex: 'a^3 + b^3 = (a+b)(a^2-ab+b^2)' },
      { name: '立方差公式', latex: 'a^3 - b^3 = (a-b)(a^2+ab+b^2)' },
    ],
  };
  
  function displayRelatedFormulas(mode) {
    const formulasList = $('#formulasList');
    const formulaCard = $('#formulaCard');
    if (!formulasList || !formulaCard) return;
    
    const formulas = formulaDatabase[mode] || [];
    if (formulas.length === 0) {
      formulaCard.classList.add('hidden');
      return;
    }
    
    formulaCard.classList.remove('hidden');
    formulasList.innerHTML = '';
    
    formulas.forEach(formula => {
      const formulaEl = document.createElement('div');
      formulaEl.className = 'formula-item';
      formulaEl.innerHTML = `
        <div class="formula-name">${formula.name}</div>
        <div class="formula-expr"></div>
      `;
      
      const exprEl = formulaEl.querySelector('.formula-expr');
      renderKatex(exprEl, formula.latex, false);
      
      formulasList.appendChild(formulaEl);
    });
  }

  async function calculate() {
    const raw = dom.fnInput ? dom.fnInput.value.trim() : '';
    if (!raw) {
      showError('请输入函数表达式');
      return;
    }

    const expr = normalizeInput(raw);
    const order = dom.derivOrder ? parseInt(dom.derivOrder.value) : 1;
    const type = dom.integralType ? dom.integralType.value : 'indefinite';
    const lower = dom.lowerBound ? dom.lowerBound.value : '';
    const upper = dom.upperBound ? dom.upperBound.value : '';
    const point = currentMode === 'limit' ? (dom.limitPoint ? dom.limitPoint.value : '0') : (dom.seriesPoint ? dom.seriesPoint.value : '0');
    const direction = dom.limitDirection ? dom.limitDirection.value : 'both';
    const seriesOrder = parseInt(dom.seriesOrder ? dom.seriesOrder.value : 5);
    const target = dom.solveTarget ? dom.solveTarget.value : '0';

    // 尝试后端 API（直接调用，不预先检查健康状态）
    let backendResult = null;
    try {
      backendResult = await tryBackendCompute(raw, currentMode, {
        order, lower: type === 'definite' ? lower : null,
        upper: type === 'definite' ? upper : null,
        point, direction, seriesOrder, target
      });
    } catch (e) {
      console.warn('Backend computation failed:', e);
    }

    if (backendResult) {
      const formattedSteps = parseBackendSteps(backendResult, currentMode, {
        expr, order, type, lower, upper, point, direction, seriesOrder, target
      });

      lastResult = {
        expr,
        raw,
        mode: currentMode,
        result: backendResult.resultLatex,
        isBackendLatex: true,
        steps: formattedSteps,
        definiteValue: backendResult.numerical,
        solutions: backendResult.solutions,
        seriesCoefficients: backendResult.terms,
        graphExpr: backendResult.expression
      };

      if (dom.resultsSection) {
        dom.resultsSection.classList.remove('hidden');
        displayResults(lastResult);
        setTimeout(() => { drawGraph(); }, 100);
        dom.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      return;
    }

    // 后端不可用或失败，回退到 Algebrite
    try {
      const test = Algebrite.run(`simplify(${expr})`);
      if (!test || test.includes('undefined') || test.includes('nil')) {
        showError('无法解析该表达式，请检查输入');
        return;
      }

      const calcResult = generateDetailedSteps(expr, currentMode, order);
      
      lastResult = {
        expr,
        raw,
        mode: currentMode,
        ...calcResult
      };

      if (dom.resultsSection) {
        dom.resultsSection.classList.remove('hidden');
        displayResults(lastResult);
        
        setTimeout(() => {
          drawGraph();
        }, 100);
        
        dom.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    } catch (e) {
      console.error('Calculation error:', e);
      showError('计算出错: ' + e.message);
    }
  }

  // Graph drawing
  function drawGraph() {
    if (!dom.graphCanvas || !lastResult) return;
    
    const container = dom.graphCanvas.parentElement;
    if (!container) return;
    
    // 使用 getBoundingClientRect 获取实际渲染尺寸
    const rect = container.getBoundingClientRect();
    const canvasWidth = Math.floor(rect.width) || 600;
    const canvasHeight = Math.floor(rect.height) || 400;
    
    // 设置 canvas 的像素尺寸（这会清除之前的绘制）
    dom.graphCanvas.width = canvasWidth;
    dom.graphCanvas.height = canvasHeight;
    
    const ctx = dom.graphCanvas.getContext('2d');
    const width = dom.graphCanvas.width;
    const height = dom.graphCanvas.height;
    
    if (width === 0 || height === 0) return;
    
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, width, height);
    
    const xMin = dom.xMin ? parseFloat(dom.xMin.value) : -10;
    const xMax = dom.xMax ? parseFloat(dom.xMax.value) : 10;
    
    // 先采样原函数和结果函数，计算Y轴范围
    const samples = 400;
    const origSamples = [];
    const resultSamples = [];
    
    // 获取结果函数的表达式
    let resultExpr = null;
    if (lastResult.mode === 'derivative') {
      resultExpr = lastResult.graphExpr || (lastResult.isBackendLatex ? null : lastResult.result);
    } else if (lastResult.mode === 'integral') {
      resultExpr = lastResult.graphExpr || (lastResult.isBackendLatex ? null : lastResult.result);
    }
    
    // 预编译计算函数（避免每次采样都重新创建）
    const origFn = createEvalFunction(lastResult.expr);
    const resultFn = resultExpr ? createEvalFunction(resultExpr) : null;
    
    let yMin = Infinity, yMax = -Infinity;
    
    for (let i = 0; i <= samples; i++) {
      const x = xMin + (i / samples) * (xMax - xMin);
      
      let yOrig = NaN;
      if (origFn) {
        try { yOrig = origFn(x); } catch (e) {}
      }
      origSamples.push({ x, y: yOrig });
      if (isFinite(yOrig) && Math.abs(yOrig) < 1e6) {
        yMin = Math.min(yMin, yOrig);
        yMax = Math.max(yMax, yOrig);
      }
      
      if (resultFn) {
        let yResult = NaN;
        try { yResult = resultFn(x); } catch (e) {}
        resultSamples.push({ x, y: yResult });
        if (isFinite(yResult) && Math.abs(yResult) < 1e6) {
          yMin = Math.min(yMin, yResult);
          yMax = Math.max(yMax, yResult);
        }
      }
    }
    
    // 添加边距
    if (yMin === Infinity) { yMin = -10; yMax = 10; }
    const yRange = yMax - yMin || 1;
    yMin -= yRange * 0.1;
    yMax += yRange * 0.1;
    
    const scaleX = width / (xMax - xMin);
    const scaleY = height / (yMax - yMin);
    
    function toCanvasX(x) { return (x - xMin) * scaleX; }
    function toCanvasY(y) { return height - (y - yMin) * scaleY; }
    
    // 绘制网格
    ctx.strokeStyle = '#2a2a4a';
    ctx.lineWidth = 0.5;
    const xStep = Math.pow(10, Math.floor(Math.log10((xMax - xMin) / 5)));
    const yStep = Math.pow(10, Math.floor(Math.log10((yMax - yMin) / 5)));
    
    for (let x = Math.ceil(xMin / xStep) * xStep; x <= xMax; x += xStep) {
      const cx = toCanvasX(x);
      ctx.beginPath();
      ctx.moveTo(cx, 0);
      ctx.lineTo(cx, height);
      ctx.stroke();
    }
    for (let y = Math.ceil(yMin / yStep) * yStep; y <= yMax; y += yStep) {
      const cy = toCanvasY(y);
      ctx.beginPath();
      ctx.moveTo(0, cy);
      ctx.lineTo(width, cy);
      ctx.stroke();
    }
    
    // 绘制坐标轴
    ctx.strokeStyle = '#4a5568';
    ctx.lineWidth = 2;
    // X轴
    const axisY = toCanvasY(0);
    if (axisY >= 0 && axisY <= height) {
      ctx.beginPath();
      ctx.moveTo(0, axisY);
      ctx.lineTo(width, axisY);
      ctx.stroke();
    }
    // Y轴
    const axisX = toCanvasX(0);
    if (axisX >= 0 && axisX <= width) {
      ctx.beginPath();
      ctx.moveTo(axisX, 0);
      ctx.lineTo(axisX, height);
      ctx.stroke();
    }
    
    // 绘制刻度标签
    ctx.fillStyle = '#888';
    ctx.font = '11px sans-serif';
    for (let x = Math.ceil(xMin / xStep) * xStep; x <= xMax; x += xStep) {
      if (Math.abs(x) < xStep * 0.1) continue;
      const cx = toCanvasX(x);
      const labelY = Math.min(Math.max(axisY + 15, 15), height - 5);
      ctx.fillText(Number(x.toFixed(4)).toString(), cx - 10, labelY);
    }
    for (let y = Math.ceil(yMin / yStep) * yStep; y <= yMax; y += yStep) {
      if (Math.abs(y) < yStep * 0.1) continue;
      const cy = toCanvasY(y);
      const labelX = Math.min(Math.max(axisX + 5, 5), width - 30);
      ctx.fillText(Number(y.toFixed(4)).toString(), labelX, cy + 4);
    }
    
    // 绘制原函数
    if (dom.showOriginal && dom.showOriginal.checked) {
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 2;
      drawCurve(ctx, origSamples, toCanvasX, toCanvasY, height);
    }
    
    // 绘制结果函数
    if (resultExpr && dom.showResult && dom.showResult.checked) {
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 2;
      drawCurve(ctx, resultSamples, toCanvasX, toCanvasY, height);
    }
    
    // 绘制特殊点
    if (dom.showSpecialPoints && dom.showSpecialPoints.checked) {
      drawSpecialPoints(ctx, toCanvasX, toCanvasY);
    }
  }
  
  function drawCurve(ctx, samples, toCanvasX, toCanvasY, height) {
    ctx.beginPath();
    let drawing = false;
    for (let i = 0; i < samples.length; i++) {
      const { x, y } = samples[i];
      if (!isFinite(y)) {
        drawing = false;
        continue;
      }
      const cx = toCanvasX(x);
      const cy = toCanvasY(y);
      // 只在y值极大（渐近线）时断开
      if (Math.abs(y) > 1e6) {
        drawing = false;
        continue;
      }
      if (!drawing) {
        ctx.moveTo(cx, cy);
        drawing = true;
      } else {
        ctx.lineTo(cx, cy);
      }
    }
    ctx.stroke();
  }
  
  function drawSpecialPoints(ctx, toCanvasX, toCanvasY) {
    if (!lastResult || !lastResult.expr) return;
    
    const origFn = createEvalFunction(lastResult.expr);
    if (!origFn) return;
    
    const xMin = dom.xMin ? parseFloat(dom.xMin.value) : -10;
    const xMax = dom.xMax ? parseFloat(dom.xMax.value) : 10;
    
    const zeros = [];
    const extrema = [];
    let hasInfiniteZeros = false;
    let hasInfiniteExtrema = false;
    let zeroPeriod = null;
    let extPeriod = null;
    
    // 找零点
    ctx.fillStyle = '#ef4444';
    const zeroStep = 0.05;
    let zeroCount = 0;
    for (let x = xMin; x <= xMax; x += zeroStep) {
      let y1, y2;
      try { y1 = origFn(x); y2 = origFn(x + zeroStep); } catch (e) { continue; }
      if (isFinite(y1) && isFinite(y2) && y1 * y2 < 0) {
        let a = x, b = x + zeroStep;
        for (let i = 0; i < 30; i++) {
          const mid = (a + b) / 2;
          let fmid;
          try { fmid = origFn(mid); } catch (e) { break; }
          if (Math.abs(fmid) < 1e-10) { a = mid; break; }
          if (y1 * fmid < 0) b = mid; else a = mid;
        }
        const root = (a + b) / 2;
        const cx = toCanvasX(root);
        const cy = toCanvasY(0);
        ctx.beginPath();
        ctx.arc(cx, cy, 5, 0, Math.PI * 2);
        ctx.fill();
        zeros.push({ x: root, y: 0 });
        zeroCount++;
      }
    }
    
    // 检测零点是否周期性（超过6个零点且间距均匀）
    if (zeros.length >= 6) {
      const spacings = [];
      for (let i = 1; i < zeros.length; i++) {
        spacings.push(zeros[i].x - zeros[i-1].x);
      }
      const avgSpacing = spacings.reduce((a, b) => a + b, 0) / spacings.length;
      const isPeriodic = spacings.every(s => Math.abs(s - avgSpacing) / avgSpacing < 0.05);
      if (isPeriodic && avgSpacing > 0.1) {
        hasInfiniteZeros = true;
        zeroPeriod = avgSpacing;
      }
    }
    
    // 找极值点
    const derivFn = createEvalFunction(lastResult.result);
    if (derivFn && lastResult.mode === 'derivative') {
      ctx.fillStyle = '#f59e0b';
      let extCount = 0;
      for (let x = xMin; x <= xMax; x += zeroStep) {
        let d1, d2;
        try { d1 = derivFn(x); d2 = derivFn(x + zeroStep); } catch (e) { continue; }
        if (isFinite(d1) && isFinite(d2) && d1 * d2 < 0) {
          let a = x, b = x + zeroStep;
          for (let i = 0; i < 30; i++) {
            const mid = (a + b) / 2;
            let dmid;
            try { dmid = derivFn(mid); } catch (e) { break; }
            if (Math.abs(dmid) < 1e-10) { a = mid; break; }
            if (d1 * dmid < 0) b = mid; else a = mid;
          }
          const extX = (a + b) / 2;
          let extY;
          try { extY = origFn(extX); } catch (e) { continue; }
          if (isFinite(extY)) {
            const cx = toCanvasX(extX);
            const cy = toCanvasY(extY);
            ctx.beginPath();
            ctx.arc(cx, cy, 5, 0, Math.PI * 2);
            ctx.fill();
            extrema.push({ x: extX, y: extY });
            extCount++;
          }
        }
      }
      
      // 检测极值点是否周期性
      if (extrema.length >= 6) {
        const spacings = [];
        for (let i = 1; i < extrema.length; i++) {
          spacings.push(extrema[i].x - extrema[i-1].x);
        }
        const avgSpacing = spacings.reduce((a, b) => a + b, 0) / spacings.length;
        const isPeriodic = spacings.every(s => Math.abs(s - avgSpacing) / avgSpacing < 0.05);
        if (isPeriodic && avgSpacing > 0.1) {
          hasInfiniteExtrema = true;
          extPeriod = avgSpacing;
        }
      }
    }
    
    displaySpecialPoints(zeros, extrema, hasInfiniteZeros, zeroPeriod, hasInfiniteExtrema, extPeriod);
  }
  
  function displaySpecialPoints(zeros, extrema, hasInfiniteZeros, zeroPeriod, hasInfiniteExtrema, extPeriod) {
    const panel = dom.specialPointsPanel;
    if (!panel) return;
    
    let html = '';
    
    if (hasInfiniteZeros && zeroPeriod) {
      // 用通式表达周期性零点
      const periodStr = formatPeriod(zeroPeriod);
      const baseX = zeros[0].x;
      html += '<div class="special-points-title">零点 (f(x) = 0，无穷多个)</div>';
      html += '<div class="special-points-list">';
      html += `<div class="special-point-item"><span class="point-marker" style="background:#ef4444"></span> x = ${baseX.toFixed(4)} + n·${periodStr}，n ∈ ℤ</div>`;
      html += '</div>';
    } else if (zeros.length > 0) {
      html += '<div class="special-points-title">零点 (f(x) = 0)</div>';
      html += '<div class="special-points-list">';
      zeros.forEach((p, i) => {
        html += `<div class="special-point-item"><span class="point-marker" style="background:#ef4444"></span> x${zeros.length > 1 ? '_' + (i+1) : ''} = ${p.x.toFixed(4)}</div>`;
      });
      html += '</div>';
    }
    
    if (hasInfiniteExtrema && extPeriod) {
      const periodStr = formatPeriod(extPeriod);
      html += '<div class="special-points-title" style="margin-top:8px">极值点（无穷多个）</div>';
      html += '<div class="special-points-list">';
      // 区分极大值和极小值
      const maxima = extrema.filter((p, i) => i % 2 === 0);
      const minima = extrema.filter((p, i) => i % 2 === 1);
      if (maxima.length > 0) {
        html += `<div class="special-point-item"><span class="point-marker" style="background:#f59e0b"></span> 极大值: (${maxima[0].x.toFixed(4)} + n·${periodStr}, ${maxima[0].y.toFixed(4)})，n ∈ ℤ</div>`;
      }
      if (minima.length > 0) {
        html += `<div class="special-point-item"><span class="point-marker" style="background:#f59e0b"></span> 极小值: (${minima[0].x.toFixed(4)} + n·${periodStr}, ${minima[0].y.toFixed(4)})，n ∈ ℤ</div>`;
      }
      html += '</div>';
    } else if (extrema.length > 0) {
      html += '<div class="special-points-title" style="margin-top:8px">极值点</div>';
      html += '<div class="special-points-list">';
      extrema.forEach((p, i) => {
        const type = i > 0 && p.y < extrema[i-1].y ? '极小值' : '极大值';
        html += `<div class="special-point-item"><span class="point-marker" style="background:#f59e0b"></span> ${type}: (${p.x.toFixed(4)}, ${p.y.toFixed(4)})</div>`;
      });
      html += '</div>';
    }
    
    if (html) {
      panel.innerHTML = html;
      panel.classList.add('visible');
    } else {
      panel.classList.remove('visible');
    }
  }
  
  function formatPeriod(period) {
    // 尝试识别常见周期
    const pi = Math.PI;
    if (Math.abs(period - pi) < 0.01) return 'π';
    if (Math.abs(period - 2*pi) < 0.01) return '2π';
    if (Math.abs(period - pi/2) < 0.01) return 'π/2';
    if (Math.abs(period - pi/3) < 0.01) return 'π/3';
    if (Math.abs(period - 2*pi/3) < 0.01) return '2π/3';
    return period.toFixed(4);
  }

  // Event listeners
  if (dom.tabs) {
    dom.tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        dom.tabs.forEach((t) => t.classList.remove('active'));
        tab.classList.add('active');
        currentMode = tab.dataset.mode;
        toggleOptions();
      });
    });
  }

  if (dom.integralType) {
    dom.integralType.addEventListener('change', () => {
      if (dom.definiteOptions) {
        dom.definiteOptions.classList.toggle('hidden', dom.integralType.value === 'indefinite');
      }
    });
  }

  if (dom.calcBtn) {
    dom.calcBtn.addEventListener('click', calculate);
  }

  if (dom.fnInput) {
    dom.fnInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') calculate();
    });
    dom.fnInput.addEventListener('input', updatePreview);
  }

  if (dom.clearBtn) {
    dom.clearBtn.addEventListener('click', () => {
      if (dom.fnInput) dom.fnInput.value = '';
      if (dom.resultsSection) dom.resultsSection.classList.add('hidden');
      if (dom.previewExpr) dom.previewExpr.innerHTML = '';
      lastResult = null;
    });
  }

  if (dom.toastClose) {
    dom.toastClose.addEventListener('click', () => {
      dom.errorToast.classList.add('hidden');
    });
  }

  // Example buttons
  $$('.example-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      if (dom.fnInput && btn.dataset.fn) {
        dom.fnInput.value = btn.dataset.fn;
        updatePreview();
      }
    });
  });

  // Zoom buttons
  if (dom.zoomInBtn) {
    dom.zoomInBtn.addEventListener('click', () => {
      const xMinVal = parseFloat(dom.xMin.value) || -10;
      const xMaxVal = parseFloat(dom.xMax.value) || 10;
      const center = (xMinVal + xMaxVal) / 2;
      const range = (xMaxVal - xMinVal) * 0.75;
      dom.xMin.value = (center - range).toFixed(2);
      dom.xMax.value = (center + range).toFixed(2);
      if (lastResult) drawGraph();
    });
  }
  if (dom.zoomOutBtn) {
    dom.zoomOutBtn.addEventListener('click', () => {
      const xMinVal = parseFloat(dom.xMin.value) || -10;
      const xMaxVal = parseFloat(dom.xMax.value) || 10;
      const center = (xMinVal + xMaxVal) / 2;
      const range = (xMaxVal - xMinVal) * 1.25;
      dom.xMin.value = (center - range).toFixed(2);
      dom.xMax.value = (center + range).toFixed(2);
      if (lastResult) drawGraph();
    });
  }
  if (dom.resetViewBtn) {
    dom.resetViewBtn.addEventListener('click', () => {
      dom.xMin.value = -10;
      dom.xMax.value = 10;
      if (lastResult) drawGraph();
    });
  }

  // Graph pan (drag to move)
  if (dom.graphCanvas) {
    let isDragging = false;
    let dragStartX = 0;
    let dragStartXMin = 0;
    let dragStartXMax = 0;

    dom.graphCanvas.addEventListener('mousedown', (e) => {
      isDragging = true;
      dragStartX = e.clientX;
      dragStartXMin = parseFloat(dom.xMin.value) || -10;
      dragStartXMax = parseFloat(dom.xMax.value) || 10;
      dom.graphCanvas.style.cursor = 'grabbing';
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const container = dom.graphCanvas.parentElement;
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const dx = e.clientX - dragStartX;
      const xRange = dragStartXMax - dragStartXMin;
      const shift = -(dx / rect.width) * xRange;
      dom.xMin.value = (dragStartXMin + shift).toFixed(2);
      dom.xMax.value = (dragStartXMax + shift).toFixed(2);
      if (lastResult) drawGraph();
    });

    window.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        dom.graphCanvas.style.cursor = 'crosshair';
      }
    });

    // Mouse wheel zoom
    dom.graphCanvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const xMinVal = parseFloat(dom.xMin.value) || -10;
      const xMaxVal = parseFloat(dom.xMax.value) || 10;
      const center = (xMinVal + xMaxVal) / 2;
      const range = xMaxVal - xMinVal;
      const factor = e.deltaY > 0 ? 1.1 : 0.9;
      const newRange = range * factor;
      dom.xMin.value = (center - newRange / 2).toFixed(2);
      dom.xMax.value = (center + newRange / 2).toFixed(2);
      if (lastResult) drawGraph();
    }, { passive: false });
  }

  // Symbol panel tabs
  $$('.symbol-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      $$('.symbol-tab').forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      currentSymbolPanel = tab.dataset.panel;
      renderSymbolGrid();
    });
  });

  // Initialize
  renderSymbolGrid();
  updatePreview();
  toggleOptions();

  // 检查后端状态
  async function updateBackendStatus() {
    const statusEl = document.getElementById('backendStatus');
    if (!statusEl) return;
    
    statusEl.className = 'backend-status checking';
    statusEl.textContent = '检测中...';
    
    const available = await checkBackend();
    
    if (available) {
      statusEl.className = 'backend-status connected';
      statusEl.textContent = 'SymPy 后端已连接';
    } else {
      statusEl.className = 'backend-status disconnected';
      statusEl.textContent = '本地模式 (Algebrite)';
    }
  }
  updateBackendStatus();

  // Canvas setup
  if (dom.graphCanvas) {
    const resizeCanvas = () => {
      const container = dom.graphCanvas.parentElement;
      if (container) {
        const rect = container.getBoundingClientRect();
        dom.graphCanvas.width = Math.floor(rect.width) || 600;
        dom.graphCanvas.height = Math.floor(rect.height) || 400;
        // 如果已经有结果，重新绘制
        if (lastResult) {
          drawGraph();
        }
      }
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
  }

  console.log('Calculator initialized successfully!');
})();
