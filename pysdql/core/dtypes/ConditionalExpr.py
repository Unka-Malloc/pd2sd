from pysdql.core.dtypes.ConditionalUnit import CondUnit
from pysdql.core.dtypes.DictionaryExpr import DictExpr


class CondExpr:
    def __init__(self, conditions, then_case: DictExpr, else_case: DictExpr, new_iter=None):
        self.conditions = conditions
        self.then_case = then_case
        self.else_case = else_case
        self.new_iter = new_iter

    @property
    def one_branch(self):
        if self.else_case:
            return False
        else:
            return True

    @property
    def expr(self):
        if self.new_iter:
            c_str = self.conditions.new_expr(self.new_iter)
        else:
            c_str = self.conditions.expr
        return f'if ({c_str}) then {self.then_case} else {self.else_case}'

    def new_expr(self, new_str) -> str:
        return self.conditions.new_expr(new_str)

    def __repr__(self):
        return self.expr
