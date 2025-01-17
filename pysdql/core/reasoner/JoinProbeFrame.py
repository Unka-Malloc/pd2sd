from pysdql.core.exprs.complex.GroupbyAggrExpr import GroupbyAggrExpr
from pysdql.core.exprs.advanced.BinCondExpr import BinCondExpr
from pysdql.core.exprs.advanced.ColOpIsinExpr import ColOpIsin
from pysdql.core.killer.Retriever import Retriever


class JoinProbeFrame:
    def __init__(self, iter_on):
        self.__probe_key = None
        self.__iter_cond = None
        self.__col_proj = None
        self.__iter_el = iter_on.iter_el.sdql_ir
        self.__iter_on = iter_on
        self.__iter_op = None
        self.__partition_frame = None
        self.__next_op = None

    def get_groupby_cols(self):
        for op_expr in self.probe_on.operations:
            if op_expr.op_type == GroupbyAggrExpr:
                return op_expr.op.groupby_cols
        else:
            raise ValueError()

    def get_aggr_dict(self):
        for op_expr in self.probe_on.operations:
            if op_expr.op_type == GroupbyAggrExpr:
                return op_expr.op.aggr_dict
        else:
            raise ValueError()

    def get_cond_after_groupby_agg(self):
        groupby_agg_located = False
        for op_expr in self.probe_on.operations:
            if op_expr.op_type == GroupbyAggrExpr:
                groupby_agg_located = True
            if op_expr.op_type == BinCondExpr:
                if groupby_agg_located:
                    return op_expr.op
        return None

    def has_isin(self):
        for op_expr in self.probe_on.operations:
            if op_expr.op_type == ColOpIsin:
                return True
        return False

    def find_isin(self):
        for op_expr in self.probe_on.operations:
            if op_expr.op_type == ColOpIsin:
                return op_expr.op
        return None

    @property
    def was_isin(self):
        for op_expr in self.probe_on.operations:
            if op_expr.op_type == ColOpIsin:
                return True
        return False

    def get_probe_col_proj(self):
        return self.__col_proj

    @property
    def probe_key(self):
        if isinstance(self.__probe_key, list) and len(self.__probe_key) == 1:
            return self.__probe_key[0]
        return self.__probe_key

    def get_probe_key(self):
        if isinstance(self.__probe_key, list) and len(self.__probe_key) == 1:
            return self.__probe_key[0]
        return self.__probe_key

    @property
    def probe_key_sdql_ir(self):
        return self.probe_on.key_access(self.probe_key)

    def get_probe_cond(self):
        return self.__iter_cond

    def get_probe_on(self):
        return self.__iter_on

    def get_probe_on_var(self):
        return self.__iter_on.var_expr

    @property
    def probe_on(self):
        return self.__iter_on

    @property
    def is_joint(self) -> bool:
        return self.probe_on.is_joint

    @property
    def retriever(self) -> Retriever:
        return self.probe_on.get_retriever()

    def add_key(self, val):
        self.__probe_key = val

    def add_partition(self, val):
        self.__partition_frame = val

    def add_cond(self, val):
        self.__iter_cond = val

    def add_col_proj(self, val):
        self.__col_proj = val

    def add_op(self, val):
        self.__iter_op = val

    def add_next(self, val):
        self.__next_op = val

    def __repr__(self):
        if self.probe_on.is_joint:
            joint_frame = self.probe_on.get_joint_frame()
            return str(joint_frame)

        return str(
            {
                'probe': 'frame',
                'probe_key': self.probe_key,
                'cond': self.__iter_cond,
                'cols': self.__col_proj
            }
        )
