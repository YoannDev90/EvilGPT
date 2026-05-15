"""_summary_."""

import ast
import math
from typing import Any, Dict

from pint import UnitRegistry

from utils.logger import get_logger

logger = get_logger()

UREG = UnitRegistry()

ALLOWED_FUNCS: Dict[str, Any] = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "pow": pow,
    "floor": math.floor,
    "ceil": math.ceil,
}

ALLOWED_CONSTS: Dict[str, Any] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv)
ALLOWED_UNARYOPS = (ast.UAdd, ast.USub)


def _safe_eval(node: ast.AST) -> float:
    """_summary_.

    Parameters
    ----------
    node : ast.AST
        _description_

    Returns
    -------
    float
        _description_

    Raises
    ------
    ValueError
        _description_
    ValueError
        _description_
    ValueError
        _description_
    ValueError
        _description_
    ValueError
        _description_
    ValueError
        _description_
    ValueError
        _description_
    """
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError("Only numeric constants are allowed")

    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, ALLOWED_BINOPS):
            raise ValueError("Operator not allowed")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left**right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.FloorDiv):
            return left // right

    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, ALLOWED_UNARYOPS):
            raise ValueError("Unary operator not allowed")
        value = _safe_eval(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +value
        return -value

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct function calls are allowed")
        func_name = node.func.id
        if func_name not in ALLOWED_FUNCS:
            raise ValueError(f"Function not allowed: {func_name}")
        args = [_safe_eval(arg) for arg in node.args]
        return float(ALLOWED_FUNCS[func_name](*args))

    if isinstance(node, ast.Name):
        if node.id in ALLOWED_CONSTS:
            return float(ALLOWED_CONSTS[node.id])
        raise ValueError(f"Unknown symbol: {node.id}")

    raise ValueError("Expression contains unsupported syntax")


def _try_eval_units(expression: str) -> str:
    """_summary_.

    Parameters
    ----------
    expression : str
        _description_

    Returns
    -------
    str
        _description_

    Raises
    ------
    ValueError
        _description_
    """
    expr = expression.strip()

    for sep in (" to ", " in "):
        if sep in expr:
            left, right = expr.split(sep, 1)
            quantity = UREG.parse_expression(left.strip())
            converted = quantity.to(right.strip())
            return f"{converted:~P}"

    if any(ch.isalpha() for ch in expr):
        value = UREG.parse_expression(expr)
        return f"{value:~P}"

    raise ValueError("Not a unit expression")


async def safe_eval_math(expression: str, precision: int = 10) -> str:
    """Safely evaluate math expression, with optional unit conversion support.

    Parameters
    ----------
    expression : str
        _description_
    precision : int
        _description_ (Default value = 10)

    Returns
    -------
    str
        _description_
    """
    try:
        precision = max(1, min(int(precision), 16))
        expr = expression.strip()
        if not expr:
            return "Error: expression is empty"

        try:
            unit_result = _try_eval_units(expr)
            return unit_result
        except Exception:
            pass

        parsed = ast.parse(expr, mode="eval")
        result = _safe_eval(parsed)

        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return f"{result:.{precision}g}"
    except Exception as e:
        logger.error(f"safe_eval_math failed: {e}")
        return f"Error: {str(e)}"
