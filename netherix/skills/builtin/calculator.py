"""Calculator skill: safe mathematical expression evaluation."""

from __future__ import annotations

import ast
import math
import operator
from typing import Any

from netherix.skills.base_skill import BaseSkill, SkillResult

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_FUNCS = {
    "abs": abs, "round": round,
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "pi": math.pi, "e": math.e,
    "ceil": math.ceil, "floor": math.floor,
}


def _safe_eval(expr: str) -> float:
    """Evaluate a math expression safely without exec/eval."""
    tree = ast.parse(expr, mode="eval")

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant: {node.value}")
        if isinstance(node, ast.BinOp):
            op = _SAFE_OPS.get(type(node.op))
            if not op:
                raise ValueError(f"Unsupported op: {type(node.op).__name__}")
            return op(_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            op = _SAFE_OPS.get(type(node.op))
            if not op:
                raise ValueError(f"Unsupported unary op: {type(node.op).__name__}")
            return op(_eval(node.operand))
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCS:
                fn = _SAFE_FUNCS[node.func.id]
                args = [_eval(a) for a in node.args]
                return fn(*args) if callable(fn) else fn
            raise ValueError(f"Unsupported function: {ast.dump(node.func)}")
        if isinstance(node, ast.Name) and node.id in _SAFE_FUNCS:
            val = _SAFE_FUNCS[node.id]
            if not callable(val):
                return val
        raise ValueError(f"Unsupported node: {type(node).__name__}")

    return _eval(tree)


class CalculatorSkill(BaseSkill):
    name = "calculator"
    description = "计算数学表达式，支持基本运算和常用数学函数（sin, cos, sqrt, log等）"
    parameters_schema = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式，例如: 2+3*4, sqrt(16), sin(pi/2)",
            },
        },
        "required": ["expression"],
    }

    async def execute(self, params: dict[str, Any]) -> SkillResult:
        expr = params.get("expression", "")
        try:
            result = _safe_eval(expr)
            return SkillResult(True, f"{expr} = {result}", {"result": result})
        except Exception as e:
            return SkillResult(False, f"计算失败: {e}")
