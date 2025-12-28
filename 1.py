#!/usr/bin/env python3
"""
Simple safe calculator.

Usage:
  - Interactive REPL:        python calculator.py
  - Single expression:       python calculator.py "2 + 3 * (4 - 1)"
  - Or:                     python calculator.py 2 + 3 \* 4

Supports: +, -, *, /, //, %, ** and parentheses. Accepts integers and floats.
"""
import ast
import operator as op
import sys

# Allowed binary operators mapping
_BIN_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}

# Allowed unary operators mapping
_UNARY_OPS = {
    ast.UAdd: lambda x: x,
    ast.USub: op.neg,
}

def _eval(node):
    """Recursively evaluate an AST node representing a math expression."""
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant):  # Python 3.8+
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value!r}")
    if isinstance(node, ast.Num):  # older versions
        return node.n
    if isinstance(node, ast.BinOp):
        left = _eval(node.left)
        right = _eval(node.right)
        op_type = type(node.op)
        if op_type in _BIN_OPS:
            try:
                return _BIN_OPS[op_type](left, right)
            except Exception as e:
                raise ValueError(f"Error computing {left} {op_type.__name__} {right}: {e}")
        raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
    if isinstance(node, ast.UnaryOp):
        operand = _eval(node.operand)
        op_type = type(node.op)
        if op_type in _UNARY_OPS:
            return _UNARY_OPS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
    if isinstance(node, ast.Call):
        raise ValueError("Function calls are not allowed")
    if isinstance(node, ast.Name):
        raise ValueError("Names/variables are not allowed")
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")

def evaluate_expr(expr: str):
    """Parse and evaluate a mathematical expression string safely."""
    try:
        parsed = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Syntax error in expression: {e}") from e
    # Walk AST to ensure it only contains allowed nodes
    for node in ast.walk(parsed):
        if isinstance(node, ast.BinOp) and type(node.op) not in _BIN_OPS:
            raise ValueError(f"Disallowed operator: {type(node.op).__name__}")
        if isinstance(node, ast.UnaryOp) and type(node.op) not in _UNARY_OPS:
            raise ValueError(f"Disallowed unary operator: {type(node.op).__name__}")
        # Allowed node types: Expression, BinOp, UnaryOp, Constant/Num, Load, operators, Expr
        allowed = (
            ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Num,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
            ast.UAdd, ast.USub, ast.Load, ast.Expr, ast.Subscript, ast.Tuple, ast.List
        )
        # We purposely exclude Name, Call, Attribute, Lambda, etc.
        if not isinstance(node, allowed):
            # But allow container nodes produced by parsing numbers/parentheses
            # Reject things explicitly we don't want
            if isinstance(node, (ast.Call, ast.Name, ast.Attribute, ast.Lambda, ast.Dict, ast.Set, ast.ListComp, ast.GeneratorExp)):
                raise ValueError(f"Disallowed expression component: {type(node).__name__}")
            # Some nodes like Module/Interactive are okay at specific positions; ignore Module here
    return _eval(parsed)

def repl():
    print("Simple calculator. Type 'exit' or 'quit' or Ctrl-C to leave.")
    while True:
        try:
            expr = input("calc> ").strip()
            if not expr:
                continue
            if expr.lower() in ("exit", "quit", "q"):
                print("Goodbye.")
                break
            try:
                result = evaluate_expr(expr)
                print(result)
            except ValueError as e:
                print("Error:", e)
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

def main():
    if len(sys.argv) > 1:
        expr = " ".join(sys.argv[1:])
        try:
            print(evaluate_expr(expr))
        except ValueError as e:
            print("Error:", e)
            sys.exit(1)
    else:
        repl()

if __name__ == "__main__":
    main()
