from numbers import Real
from typing import Mapping

from asd import ASD


# noinspection PyUnboundLocalVariable
class Calc(ASD):
    _ = (
        Code(stms=list[Stmt])
    )
    Stmt = (
            Assign(name=str, value=Expr)
            | Print(value=Expr)
    )
    Expr = (
            Binary(op=BinOp, left=Expr, right=Expr)
            | Unary(op=UnOp, value=Expr)
            | Number(value=Real)
            | Variable(name=str)
    )
    BinOp = Add() | Sub() | Mul() | Div()
    UnOp = Pos() | Neg()


globals().update({n: v for n, v in Calc.__dict__.items() if not n.startswith("_")})


def calculate(expr: Calc, variables: Mapping[str, Real] = None) -> Real:
    if variables is None:
        variables = {}
    match expr:
        case Code([*stmts]):
            value = None
            for stmt in stmts:
                assert isinstance(stmt, Stmt)
                value = calculate(stmt, variables)
            return value
        case Assign(name, value):
            variables[name] = calculate(value, variables)
        case Print(value):
            print(calculate(value, variables))
        case Number(value):
            return value
        case Variable(name):
            return variables[name]
        case Unary(Pos(), value):
            return +value
        case Unary(Neg(), value):
            return -value
        case Binary(Add(), left, right):
            return calculate(left, variables) + calculate(right, variables)
        case Binary(Sub(), left, right):
            return calculate(left, variables) - calculate(right, variables)
        case Binary(Mul(), left, right):
            return calculate(left, variables) * calculate(right, variables)
        case Binary(Div(), left, right):
            return calculate(left, variables) / calculate(right, variables)
        case _:
            raise ValueError(expr)


v = Code([Assign("x", Number(10)), Print(Binary(Div(), Variable("x"), Number(2)))])
print(v)
print(calculate(v))
