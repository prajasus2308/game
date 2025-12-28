#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request, session
import random, math, ast, operator as op

# --- Safe evaluator (same as above, included here for completeness) ---
_BIN_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.FloorDiv: op.floordiv, ast.Mod: op.mod,
    ast.Pow: op.pow,
}
_UNARY_OPS = {ast.UAdd: lambda x: x, ast.USub: op.neg}

def _eval(node):
    if isinstance(node, ast.Expression): return _eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)): return node.value
        raise ValueError(f"Unsupported constant: {node.value!r}")
    if isinstance(node, ast.Num): return node.n
    if isinstance(node, ast.BinOp):
        left = _eval(node.left); right = _eval(node.right)
        op_type = type(node.op)
        if op_type in _BIN_OPS:
            try: return _BIN_OPS[op_type](left, right)
            except Exception as e: raise ValueError(f"Error computing {left} {op_type.__name__} {right}: {e}")
        raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
    if isinstance(node, ast.UnaryOp):
        operand = _eval(node.operand); op_type = type(node.op)
        if op_type in _UNARY_OPS: return _UNARY_OPS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
    if isinstance(node, (ast.Call, ast.Name)):
        raise ValueError("Function calls or names are not allowed")
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")

def evaluate_expr(expr: str):
    parsed = ast.parse(expr, mode="eval")
    for node in ast.walk(parsed):
        if isinstance(node, ast.BinOp) and type(node.op) not in _BIN_OPS:
            raise ValueError(f"Disallowed operator: {type(node.op).__name__}")
        if isinstance(node, ast.UnaryOp) and type(node.op) not in _UNARY_OPS:
            raise ValueError(f"Disallowed unary operator: {type(node.op).__name__}")
        allowed = (
            ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Num,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
            ast.UAdd, ast.USub, ast.Load, ast.Expr, ast.Subscript, ast.Tuple, ast.List
        )
        if not isinstance(node, allowed):
            if isinstance(node, (ast.Call, ast.Name, ast.Attribute, ast.Lambda, ast.Dict, ast.Set, ast.ListComp, ast.GeneratorExp)):
                raise ValueError(f"Disallowed expression component: {type(node).__name__}")
    return _eval(parsed)

# --- Expression generator ---
OPS = ['+', '-', '*', '/', '//', '%', '**']
import random
def generate_number():
    n = random.randint(0, 20)
    if random.random() < 0.15: n = -n
    return str(n)

def generate_expr(max_ops=2):
    parts = [generate_number()]
    ops_count = random.randint(0, max_ops)
    for _ in range(ops_count):
        op_sym = random.choices(OPS, weights=[3,3,3,2,1,1,1])[0]
        if op_sym == '**':
            right = str(random.randint(0, 4))
        else:
            right = generate_number()
            if op_sym in ('/', '//', '%') and right in ('0', '-0'):
                right = '1'
        if random.random() < 0.25:
            left = "(" + parts.pop() + " " + op_sym + " " + right + ")"
            parts.append(left)
        else:
            parts.append(op_sym); parts.append(right)
    return " ".join(parts)

# --- Flask app ---
from flask import Flask
app = Flask(__name__)
app.secret_key = "dev-secret-key-replace-in-prod"

@app.route("/")
def index():
    # ensure session keys
    session.setdefault("score", 0)
    session.setdefault("rounds", 0)
    return render_template("index.html")

@app.route("/expr", methods=["GET"])
def expr():
    # produce a valid expression
    for _ in range(30):
        e = generate_expr(max_ops=2)
        try:
            evaluate_expr(e)
            session['expr'] = e
            return jsonify(expr=e, score=session.get("score",0), rounds=session.get("rounds",0))
        except Exception:
            continue
    # fallback
    session['expr'] = "1 + 1"
    return jsonify(expr="1 + 1", score=session.get("score",0), rounds=session.get("rounds",0))

@app.route("/check", methods=["POST"])
def check():
    data = request.get_json() or {}
    answer = data.get("answer", "").strip()
    expr_in_session = session.get("expr")
    if not expr_in_session:
        return jsonify(error="No active expression. Reload."), 400
    try:
        real = evaluate_expr(expr_in_session)
    except Exception as e:
        return jsonify(error=f"Server evaluation error: {e}"), 500
    # parse answer
    try:
        if '.' in answer or 'e' in answer.lower():
            user_val = float(answer)
        else:
            user_val = int(answer)
    except Exception:
        try:
            user_val = float(answer)
        except Exception:
            return jsonify(correct=False, real=str(real), feedback="Couldn't parse your answer."), 200
    # compare
    if isinstance(real, int) and isinstance(user_val, int):
        correct = (real == user_val)
    else:
        try:
            correct = math.isclose(float(real), float(user_val), rel_tol=1e-9, abs_tol=1e-9)
        except Exception:
            correct = False
    if correct:
        session['score'] = session.get('score',0) + 1
        feedback = f"Correct! {expr_in_session} = {real}"
    else:
        feedback = f"Wrong. {expr_in_session} = {real} (you answered {user_val})"
    session['rounds'] = session.get('rounds',0) + 1
    return jsonify(correct=correct, real=str(real), feedback=feedback, score=session.get('score',0), rounds=session.get('rounds',0))

@app.route("/reset", methods=["POST"])
def reset():
    session['score'] = 0
    session['rounds'] = 0
    session.pop('expr', None)
    return jsonify(ok=True)

if __name__ == "__main__":
    app.run(debug=True)
