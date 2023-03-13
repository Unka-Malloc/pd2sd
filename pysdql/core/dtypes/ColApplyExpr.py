from pysdql.core.dtypes.SDQLInspector import SDQLInspector
from pysdql.core.dtypes.sdql_ir import IfExpr


class ColApplyExpr:
    def __init__(self, apply_op, apply_cond=None, apply_else=None, more_cond=None):
        self.apply_op = apply_op

        self.apply_cond = apply_cond
        self.apply_else = apply_else

        self.more_cond = more_cond if more_cond else []

    def replace(self, rec, inplace=False, mapper=None):
        if rec:
            if inplace:
                raise NotImplementedError
            else:
                self.apply_op = SDQLInspector.replace_access(self.apply_op, rec)
        else:
            if mapper:
                new_mapper = {}

                for k in mapper.keys():
                    if isinstance(k, (tuple, )):
                        for el in k:
                            new_mapper[el] = mapper[k]
                    else:
                        new_mapper[k] = mapper[k]

                self.apply_cond = SDQLInspector.replace_field(sdql_obj=self.apply_cond,
                                                              inplace=inplace,
                                                              mapper=new_mapper)

                self.apply_op = SDQLInspector.replace_field(sdql_obj=self.apply_op,
                                                              inplace=inplace,
                                                              mapper=new_mapper)

        return self.sdql_ir



    @property
    def sdql_ir(self):
        if self.apply_cond:
            result = IfExpr(self.apply_cond,
                          self.apply_op,
                          self.apply_else)
        else:
            result = self.apply_op

        if self.more_cond:
            for cond in self.more_cond:
                result = IfExpr(cond,
                                result,
                                self.apply_else)

        return result

    def __repr__(self):
        return str(self.sdql_ir)