from pysdql.core.dtypes import OldColOpExpr, ColOpExpr
from pysdql.core.dtypes.AggrExpr import AggrExpr
from pysdql.core.dtypes.AggrFiltCond import AggrFiltCond
from pysdql.core.dtypes.AggrFrame import AggrFrame
from pysdql.core.dtypes.CalcExpr import CalcExpr
from pysdql.core.dtypes.ColApplyExpr import ColApplyExpr
from pysdql.core.dtypes.ColProjExpr import ColProjExpr
from pysdql.core.dtypes.CondExpr import CondExpr
from pysdql.core.dtypes.ColExtExpr import ColExtExpr
from pysdql.core.dtypes.FlexIR import FlexIR
from pysdql.core.dtypes.GroupbyAggrExpr import GroupbyAggrExpr
from pysdql.core.dtypes.GroupbyAggrFrame import GroupbyAggrFrame
from pysdql.core.dtypes.IterForm import IterForm
from pysdql.core.dtypes.JointFrame import JointFrame
from pysdql.core.dtypes.JoinPartFrame import JoinPartFrame
from pysdql.core.dtypes.JoinProbeFrame import JoinProbeFrame
from pysdql.core.dtypes.MergeExpr import MergeExpr
from pysdql.core.dtypes.OpExpr import OpExpr
from pysdql.core.dtypes.NewColOpExpr import NewColOpExpr
from pysdql.core.dtypes.IsInExpr import IsInExpr
from pysdql.core.dtypes.SDQLInspector import SDQLInspector
from pysdql.core.dtypes.sdql_ir import *

from pysdql.core.dtypes.EnumUtil import LastIterFunc, OptGoal, MergeType, OpRetType
from pysdql.core.util.df_retriever import Retriever
from pysdql.core.util.flex_check import is_cond, map_name_to_dataset
from pysdql.extlib.sdqlpy.sdql_lib import sr_dict


class Optimizer:
    def __init__(self, opt_on, opt_goal=None):
        self.opt_on = opt_on
        self.opt_goal = opt_goal

        self.cond_info = {
            'cond_if': ConstantExpr(True),
            'cond_then': ConstantExpr(None),
            'cond_else': ConstantExpr(None)
        }

        self.cond_status = False

        self.col_ins = {

        }

        self.col_proj = []

        self.sum_info = {
            'sum_el': opt_on.iter_el.sdql_ir,
            'sum_on': opt_on.var_expr,
            'sum_op': ConstantExpr(None),
        }

        self.agg_dict_info = {
            'aggr_dict': None,
            'cond_if': ConstantExpr(None),
            'cond_then': ConstantExpr(None),
            'cond_else': ConstantExpr(None),

            'sum_el': opt_on.iter_el.sdql_ir,
            'sum_on': opt_on.var_expr,
            'sum_op': ConstantExpr(None),
        }

        self.vname_groupby_agg = f'{opt_on.name}_groupby_agg'
        self.var_groupby_agg = VarExpr(self.vname_groupby_agg)

        self.vname_groupby_agg_concat = f'{opt_on.name}_groupby_agg_concat'
        self.var_groupby_agg_concat = VarExpr(self.vname_groupby_agg_concat)

        self.groupby_aggr_info = {
            'groupby_cols': [],
            'aggr_dict': {},

            'aggr_keys': RecConsExpr([]),
            'aggr_vals': RecConsExpr([]),

            'aggr_var': self.var_groupby_agg,
            'aggr_el': opt_on.iter_el.sdql_ir,
            'aggr_on': opt_on.var_expr,
            'aggr_op': ConstantExpr(None),

            'let_var': self.var_groupby_agg_concat,
            'let_val': ConstantExpr(None),
            'let_next': ConstantExpr(None),
        }

        self.last_merge_info = {
            'merge_left': None,
            'merge_right': None,
            'merge_how': 'inner',
            'merge_left_on': ConstantExpr(None),
            'merge_right_on': ConstantExpr(None)
        }

        self.merge_left_info = {
            'merge_left_on': '',

            'merge_left_sum_el': opt_on.iter_el.sdql_ir,
            'merge_left_sum_on': opt_on.var_expr,
            'merge_left_sum_op': ConstantExpr(None),

            'merge_left_let_var': self.opt_on.var_part,
            'merge_left_let_val': ConstantExpr(None),
            'merge_left_let_next': ConstantExpr(None)
        }

        self.merge_right_info = {
            'merge_right_on': '',

            'merge_right_sum_el': opt_on.iter_el.sdql_ir,
            'merge_right_sum_on': opt_on.var_expr,
            'merge_right_sum_op': ConstantExpr(None),

            'merge_right_let_val': ConstantExpr(None),
            'merge_right_let_next': ConstantExpr(None)
        }

        self.merge_join_frame_info = {
            'partition_side': None,
            'probe_side': None,
        }

        self.join_partition_info = {
            'partition_key': None,
        }

        self.join_probe_info = {
            'probe_key': None,
        }

        self.joint_info = {
            'partition_side': None,
            'partition_key': None,

            'probe_side': None,
            'probe_key': None,

            'how': None,
            'joint_cond': None
        }

        self.is_join_partition_side = False
        self.is_join_probe_side = False
        self.is_joint = self.opt_on.is_joint

        self.status = {
            'conditional': False,
            'column_insertion': False,
            'column_projection': False
        }

        self.isin_op = None
        self.has_isin = False

        self.vname_having = f'{self.opt_on.name}_having'
        self.var_having = VarExpr(self.vname_having)
        self.opt_on.add_context_variable(self.vname_having, self.var_having)

    @property
    def has_cond(self):
        for op_expr in self.opt_on.operations:
            if op_expr.op_type == CondExpr:
                return True
        return False

    def get_cond_after_groupby_agg(self):
        groupby_agg_located = False
        for op_expr in self.opt_on.operations:
            if op_expr.op_type == GroupbyAggrExpr:
                groupby_agg_located = True
            if op_expr.op_type == CondExpr:
                if groupby_agg_located:
                    return op_expr.op
        return None

    @property
    def has_col_ins(self):
        return self.status['column_insertion']

    @property
    def has_col_proj(self):
        return self.status['column_projection']

    def add_cond(self, cond):
        if self.cond_info['cond_if']:
            self.cond_info['cond_if'] = MulExpr(self.cond_info['cond_if'], cond)
        else:
            self.cond_info['cond_if'] = cond

        self.status['conditional'] = True

    def add_col_ins(self, col_name, col_expr):
        self.col_ins[col_name] = col_expr

        self.status['column_insertion'] = True

    def add_col_proj(self, rec_tuple):
        self.col_proj.append(rec_tuple)

        self.status['column_projection'] = True

    def get_cond_ir(self):
        return self.cond_info['cond_if']

    def get_col_ins_ir(self, col_name: str):
        return self.col_ins[col_name]

    def get_col_proj_ir(self, merge_type: MergeType) -> RecConsExpr:
        if merge_type == MergeType.NONE:
            return RecConsExpr(self.col_proj)
        if merge_type == MergeType.PARTITION:
            if self.col_proj:
                return RecConsExpr(self.col_proj)
            else:
                left_on = self.last_merge_info['left_on']
                return RecConsExpr([(left_on,
                                     self.opt_on.key_access(left_on))])
        if merge_type == MergeType.PROBE:
            if self.col_proj:
                return RecConsExpr(self.col_proj)
            else:
                right_on = self.last_merge_info['right_on']
                return RecConsExpr([(right_on,
                                     self.opt_on.iter_el.key)])
                # right_on = self.merge_info['right_on']
                # return RecConsExpr([(right_on,
                #                      self.opt_on.key_access(right_on))])

    @property
    def cond_stmt(self):
        return IfExpr(condExpr=self.cond_info['cond_if'],
                      thenBodyExpr=self.cond_info['cond_then'],
                      elseBodyExpr=self.cond_info['cond_else'])

    @property
    def sum_stmt(self):
        return SumExpr(varExpr=self.sum_info['sum_el'],
                       dictExpr=self.sum_info['sum_on'],
                       bodyExpr=self.sum_info['sum_op'])

    @property
    def let_stmt(self):
        return LetExpr(varExpr=self.groupby_aggr_info['let_var'],
                       valExpr=self.groupby_aggr_info['let_val'],
                       bodyExpr=self.groupby_aggr_info['let_next'])

    def set_groupby_aggr_key_part(self, on, cols):
        if len(cols) == 1:
            self.groupby_aggr_info['aggr_keys'] = on.key_access(cols[0])
        else:
            self.groupby_aggr_info['aggr_keys'] = RecConsExpr([(i, on.key_access(i)) for i in cols])

    def set_groupby_aggr_val_part(self, aggr_dict):
        rec_list = []

        if self.col_ins:
            for k in aggr_dict.keys():
                v = aggr_dict[k]
                if v.name in self.col_ins.keys():
                    col_expr = self.col_ins[v.name].sdql_ir
                else:
                    col_expr = v

                rec_list.append((k, col_expr))
        else:
            for k in aggr_dict.keys():
                rec_list.append((k, aggr_dict[k]))

        self.groupby_aggr_info['aggr_vals'] = RecConsExpr(rec_list)

    def set_groupby_aggr_aggr_op(self):
        self.groupby_aggr_info['aggr_op'] = DicConsExpr([(self.groupby_aggr_info['aggr_keys'],
                                                          self.groupby_aggr_info['aggr_vals'])])

    def set_groupby_aggr_let_val(self):
        if self.has_cond:

            # cond_after_groupby_agg = self.get_cond_after_groupby_agg()
            # if cond_after_groupby_agg:
            #     vname_groupby_agg_el = f'x_{self.vname_groupby_agg}'
            #     var_groupby_agg_el = VarExpr(vname_groupby_agg_el)
            #     self.opt_on.add_context_variable(vname_groupby_agg_el, var_groupby_agg_el)
            #     vname_having = f'having_{self.opt_on.name}'
            #     var_having = VarExpr(vname_having)
            #     self.opt_on.add_context_variable(vname_having, var_having)
            #     next_op = LetExpr(var_having,
            #                       SumExpr(varExpr=var_groupby_agg_el,
            #                               dictExpr=self.var_groupby_agg,
            #                               bodyExpr=IfExpr(condExpr=cond_after_groupby_agg.replace(
            #                                   PairAccessExpr(var_groupby_agg_el, 1)),
            #                                   thenBodyExpr=DicConsExpr(
            #                                       [(PairAccessExpr(var_groupby_agg_el, 0),
            #                                         ConstantExpr(True))]),
            #                                   elseBodyExpr=EmptyDicConsExpr())),
            #                       ConstantExpr(True))

            if self.get_cond_after_groupby_agg():
                self.groupby_aggr_info['let_val'] = SumExpr(varExpr=self.groupby_aggr_info['aggr_el'],
                                                            dictExpr=self.groupby_aggr_info['aggr_on'],
                                                            bodyExpr=self.groupby_aggr_info['aggr_op'])
            else:
                self.groupby_aggr_info['let_val'] = SumExpr(varExpr=self.groupby_aggr_info['aggr_el'],
                                                            dictExpr=self.groupby_aggr_info['aggr_on'],
                                                            bodyExpr=IfExpr(condExpr=self.cond_info['cond_if'],
                                                                            thenBodyExpr=self.cond_info['cond_then'],
                                                                            elseBodyExpr=self.cond_info['cond_else']))
        else:
            self.groupby_aggr_info['let_val'] = SumExpr(varExpr=self.groupby_aggr_info['aggr_el'],
                                                        dictExpr=self.groupby_aggr_info['aggr_on'],
                                                        bodyExpr=self.groupby_aggr_info['aggr_op'])

    def get_groupby_aggr_stmt(self, next_op=None):
        self.opt_on.add_context_variable(self.vname_groupby_agg, self.var_groupby_agg)
        self.opt_on.add_context_variable(self.vname_groupby_agg_concat, self.var_groupby_agg_concat)

        if next_op is None:
            return LetExpr(varExpr=self.groupby_aggr_info['aggr_var'],
                           valExpr=self.groupby_aggr_info['let_val'],
                           bodyExpr=self.groupby_aggr_info['let_next'])
        else:
            return LetExpr(varExpr=self.groupby_aggr_info['aggr_var'],
                           valExpr=self.groupby_aggr_info['let_val'],
                           bodyExpr=next_op)

    def get_groupby_agg_having_stmt(self, next_op=None):
        if next_op is None:
            next_op = ConstantExpr(True)

        cond_after_groupby_agg = self.get_cond_after_groupby_agg()
        if cond_after_groupby_agg:
            vname_groupby_agg_el = f'x_{self.vname_groupby_agg}'
            var_groupby_agg_el = VarExpr(vname_groupby_agg_el)
            self.opt_on.add_context_variable(vname_groupby_agg_el, var_groupby_agg_el)
            vname_having = f'{self.opt_on.name}_having'
            var_having = VarExpr(vname_having)
            self.opt_on.add_context_variable(vname_having, var_having)
            having_op = LetExpr(var_having,
                                SumExpr(varExpr=var_groupby_agg_el,
                                        dictExpr=self.var_groupby_agg,
                                        bodyExpr=IfExpr(condExpr=cond_after_groupby_agg.replace(
                                            PairAccessExpr(var_groupby_agg_el, 1)),
                                            thenBodyExpr=DicConsExpr(
                                                [(PairAccessExpr(var_groupby_agg_el, 0),
                                                  ConstantExpr(True))]),
                                            elseBodyExpr=EmptyDicConsExpr()),
                                        isAssignmentSum=True),
                                next_op)
            return self.get_groupby_aggr_stmt(having_op)
        else:
            raise NotImplementedError

    @property
    def groupby_aggr_stmt(self) -> LetExpr:
        return self.get_groupby_aggr_stmt()

    def input(self, op_expr: OpExpr):
        if op_expr.op_type == CondExpr:

            self.add_cond(op_expr.op.sdql_ir)
            self.cond_info['cond_if'] = op_expr.op.sdql_ir

            if self.is_joint:
                self.joint_info['joint_cond'] = op_expr.op

            self.cond_status = True
        if op_expr.op_type == AggrExpr:
            if op_expr.ret_type == OpRetType.DICT:
                self.agg_dict_info['aggr_dict'] = op_expr.op.aggr_op
                self.agg_dict_info['cond_if'] = self.cond_info['cond_if']
                self.agg_dict_info['cond_then'] = op_expr.op.aggr_op
                self.agg_dict_info['cond_else'] = op_expr.op.aggr_else
            else:
                self.cond_info['cond_then'] = op_expr.op.aggr_op
                self.cond_info['cond_else'] = op_expr.op.aggr_else
                self.sum_info['sum_op'] = self.cond_stmt
        if op_expr.op_type == NewColOpExpr:
            self.add_col_ins(col_name=op_expr.op.col_var,
                             col_expr=op_expr.op.col_expr)

            self.col_ins[op_expr.op.col_var] = op_expr.op.col_expr
        if op_expr.op_type == GroupbyAggrExpr:
            groupby_from = op_expr.op.groupby_from
            groupby_cols = op_expr.op.groupby_cols
            aggr_dict = op_expr.op.aggr_dict

            self.groupby_aggr_info['groupby_cols'] = groupby_cols
            self.groupby_aggr_info['aggr_dict'] = aggr_dict

            self.set_groupby_aggr_key_part(groupby_from, groupby_cols)
            self.set_groupby_aggr_val_part(aggr_dict)

            self.set_groupby_aggr_aggr_op()

            if self.has_isin:
                ref_var = self.isin_op.get_ref_var()
                probe_field = self.isin_op.get_probe_field()
                self.cond_info['cond_then'] = IfExpr(condExpr=CompareExpr(compareType=CompareSymbol.NE,
                                                                          leftExpr=DicLookupExpr(ref_var,
                                                                                                 self.opt_on.key_access(
                                                                                                     probe_field)),
                                                                          rightExpr=ConstantExpr(None)),
                                                     thenBodyExpr=self.groupby_aggr_info['aggr_op'],
                                                     elseBodyExpr=EmptyDicConsExpr())
            else:
                self.cond_info['cond_then'] = self.groupby_aggr_info['aggr_op']
            self.cond_info['cond_else'] = EmptyDicConsExpr()

            self.set_groupby_aggr_let_val()

            vname_concat = f'x_{self.opt_on.name}_groupby_agg'
            var_concat = VarExpr(vname_concat)
            self.opt_on.add_context_variable(vname_concat, var_concat)
            sum_concat = SumExpr(varExpr=var_concat,
                                 dictExpr=self.groupby_aggr_info['aggr_var'],
                                 bodyExpr=DicConsExpr([(ConcatExpr(PairAccessExpr(var_concat, 0),
                                                                   PairAccessExpr(var_concat, 1)),
                                                        ConstantExpr(True))]),
                                 isAssignmentSum=True)

            vname_out = 'out'
            var_out = VarExpr(vname_out)
            self.opt_on.add_context_variable(vname_out, var_out)
            self.groupby_aggr_info['let_next'] = LetExpr(varExpr=var_out,
                                                         valExpr=sum_concat,
                                                         bodyExpr=ConstantExpr(True))

        if op_expr.op_type == ColProjExpr:
            for col in op_expr.op.proj_cols:
                self.add_col_proj((col,
                                   op_expr.op.proj_on.key_access(col)))

        if op_expr.op_type == MergeExpr:
            # detect(self) -> partition side
            if op_expr.op.left.name == self.opt_on.name:
                self.is_join_partition_side = True

                self.join_partition_info['partition_key'] = op_expr.op.left_on
            # detect(self) -> probe side
            elif op_expr.op.right.name == self.opt_on.name:
                self.is_join_probe_side = True

                self.join_probe_info['probe_key'] = op_expr.op.right_on
            else:
                if self.is_joint:
                    self.joint_info['partition_side'] = op_expr.op.left
                    self.joint_info['partition_key'] = op_expr.op.left_on
                    self.joint_info['probe_side'] = op_expr.op.right
                    self.joint_info['probe_key'] = op_expr.op.right_on
                    self.joint_info['how'] = op_expr.op.how
                else:
                    raise ValueError(str(op_expr))

        if op_expr.op_type == IsInExpr:
            self.isin_op = op_expr.op

            self.has_isin = True

        if op_expr.op_type == ColExtExpr:
            self.cond_info['cond_if'] = op_expr.op

    @property
    def partition_frame(self):
        frame = JoinPartFrame(iter_on=self.opt_on,
                              col_proj=self.col_proj)

        frame.add_key(self.join_partition_info['partition_key'])
        if type(self.cond_info['cond_if']) != ConstantExpr:
            frame.add_cond(self.cond_info['cond_if'])

        return frame

    @property
    def probe_frame(self):
        if not self.is_join_probe_side:
            raise ValueError()

        frame = JoinProbeFrame(self.opt_on)

        frame.add_key(self.join_probe_info['probe_key'])
        frame.add_cond(self.cond_info['cond_if'])
        frame.add_col_proj(self.col_proj)

        # print(self.join_probe_info['probe_key'])
        # print(self.cond_info['cond_if'])
        # print(self.col_proj)

        return frame

    @property
    def joint_frame(self):
        partition_frame = self.joint_info['partition_side'].get_partition_frame()
        probe_frame = self.joint_info['probe_side'].get_probe_frame()

        # define aggr_dict
        if self.last_func == LastIterFunc.GroupbyAgg:
            aggr_dict = self.groupby_aggr_info['aggr_dict']
        elif self.last_func == LastIterFunc.Agg:
            aggr_dict = self.agg_dict_info['aggr_dict']
        else:
            aggr_dict = None

        # define groupby_cols
        if self.groupby_aggr_info['groupby_cols']:
            groupby_cols = self.groupby_aggr_info['groupby_cols']
        else:
            groupby_cols = None

        # define joint_cond
        if self.joint_info['joint_cond']:
            joint_cond = self.joint_info['joint_cond']
        else:
            joint_cond = None

        # print(self.opt_on.name)
        # print(self.col_proj)

        tmp_joint_frame = JointFrame(partition=partition_frame,
                                     probe=probe_frame,
                                     joint=self.opt_on,
                                     col_ins=self.col_ins,
                                     col_proj=self.col_proj,
                                     groupby_cols=groupby_cols,
                                     aggr_dict=aggr_dict,
                                     joint_cond=joint_cond)

        if self.col_proj != tmp_joint_frame.col_proj:
            raise ValueError(f'Column Projection Not Applied to {self.opt_on.name}')

        return tmp_joint_frame

    @property
    def aggr_frame(self):
        return AggrFrame(self.opt_on)

    @property
    def retriever(self) -> Retriever:
        return self.opt_on.get_retriever()

    @property
    def last_func(self):
        return self.retriever.find_last_iter(as_enum=True)

    @property
    def output(self) -> LetExpr:
        if self.last_func == LastIterFunc.Agg:
            op_expr = self.retriever.find_aggr(body_only=False)
            if op_expr.op.aggr_on.name != self.opt_on.name:
                for k in op_expr.op.aggr_on.context_constant.keys():
                    self.opt_on.context_constant[k] = op_expr.op.aggr_on.context_constant[k]

                if op_expr.op.aggr_on.is_joint:
                    return op_expr.op.aggr_on.joint_frame.sdql_ir
                else:
                    return AggrFrame(op_expr.op.aggr_on).sdql_ir
                # return SDQLInspector.rename_last_binding(AggrFrame(op_expr.op.aggr_on).sdql_ir,
                #                                          self.opt_on.name)

            if op_expr.ret_type == OpRetType.DICT:
                # Q19
                if self.is_joint:
                    return self.joint_frame.sdql_ir
                # Q6
                # Q6_1
                return AggrFrame(self.opt_on).sdql_ir
            if op_expr.ret_type == OpRetType.FLOAT:
                # Q6_2
                return AggrFrame(self.opt_on).sdql_ir

            raise NotImplementedError
        elif self.last_func == LastIterFunc.GroupbyAgg:
            if self.is_joint:
                # Q3
                # Q16
                return self.joint_frame.sdql_ir
            # if self.get_cond_after_groupby_agg():
            #     return self.get_groupby_agg_having_stmt()

            # Q1
            # Q4
            return GroupbyAggrFrame(self.opt_on).sdql_ir
        elif self.last_func == LastIterFunc.Joint:
            # Q15
            # Q20
            return self.joint_frame.sdql_ir
        elif self.last_func == LastIterFunc.Calc:
            # Q14
            op_expr = self.retriever.find_last_iter(body_only=False)

            if op_expr.op.on.name != self.opt_on.name:
                for k in op_expr.op.on.context_constant.keys():
                    self.opt_on.context_constant[k] = op_expr.op.on.context_constant[k]

                # print(op_expr.op.on.operations)

                return op_expr.op.on.joint_frame.sdql_ir

            if self.is_joint:
                return self.joint_frame.sdql_ir
        else:
            last_op = self.retriever.find_last_iter()
            print('Unknown Last Operation:', type(last_op), last_op)
            raise NotImplementedError

    def fill_context_unopt(self, last_rename=''):
        hash_join = True

        tmp_vn_on = map_name_to_dataset(self.opt_on.name)
        tmp_el_on = 'x'
        tmp_vn_nx = f'v{self.opt_on.unopt_count}'

        for op_expr in self.opt_on.operations:
            if self.opt_on.unopt_count != 0:
                tmp_vn_on = f'v{self.opt_on.unopt_count - 1}'
                tmp_vn_nx = f'v{self.opt_on.unopt_count}'

            op_body = op_expr.op

            if isinstance(op_body, ColProjExpr):
                continue
            elif is_cond(op_body):
                tmp_it = IterForm(tmp_vn_on, tmp_el_on)

                if any([(i not in self.opt_on.cols_out)
                        & (i not in self.retriever.find_cols_used('groupby_aggr'))
                        for i in self.retriever.find_cols(op_body)]):
                    col_mapper = {}
                    col_relations = {}

                    for i in self.retriever.find_cols(op_body, as_expr=True):
                        if i.field not in self.opt_on.columns:
                            col_mapper[i.field] = VarExpr('prev_aggregation')

                            if i.relation.name not in col_relations.keys():
                                col_relations[i.relation.name] = i.relation.get_opt().get_unopt_sdqlir()
                        else:
                            col_mapper[i.field] = PairAccessExpr(VarExpr(tmp_el_on), 0)

                    for k in col_relations:
                        self.opt_on.context_unopt.append(
                            SDQLInspector.rename_last_binding(col_relations[k], 'prev_aggregation', with_res=False, keep_the=-3)
                        )

                    tmp_it.iter_cond.append(op_body.replace(rec=None, inplace=False, mapper=col_mapper))
                else:
                    tmp_it.iter_cond.append(op_body)

                self.opt_on.context_unopt.append(
                    LetExpr(varExpr=VarExpr(tmp_vn_nx),
                            valExpr=tmp_it.sdql_ir,
                            bodyExpr=ConstantExpr(True))
                )
            elif isinstance(op_body, AggrFiltCond):
                tmp_calc_value = 'tmp_calc_value'

                tmp_it = IterForm(tmp_vn_on, tmp_el_on)

                tmp_pairs = op_body.get_in_pairs()

                tmp_it.iter_op = SDQLInspector.replace_access(tmp_pairs[1].sdql_ir,
                                                                     PairAccessExpr(VarExpr(tmp_el_on), 0))

                self.opt_on.context_unopt.append(
                    LetExpr(varExpr=VarExpr(tmp_calc_value),
                            valExpr=tmp_it.sdql_ir,
                            bodyExpr=ConstantExpr(True))
                )

                tmp_it_2 = IterForm(tmp_vn_on, tmp_el_on)

                tmp_aggr_value = SDQLInspector.replace_access(tmp_pairs[2].sdql_ir,
                                                              PairAccessExpr(VarExpr(tmp_el_on), 0))

                tmp_it_2.iter_cond.append(CompareExpr(tmp_pairs[0],
                                                      VarExpr(tmp_calc_value),
                                                      tmp_aggr_value))

                self.opt_on.context_unopt.append(
                    LetExpr(varExpr=VarExpr(tmp_vn_nx),
                            valExpr=tmp_it_2.sdql_ir,
                            bodyExpr=ConstantExpr(True))
                )
            elif isinstance(op_body, (OldColOpExpr, NewColOpExpr)):
                tmp_it = IterForm(tmp_vn_on, tmp_el_on)

                tmp_it.iter_op = op_body

                self.opt_on.context_unopt.append(
                    LetExpr(varExpr=VarExpr(tmp_vn_nx),
                            valExpr=tmp_it.sdql_ir,
                            bodyExpr=ConstantExpr(True))
                )
            elif isinstance(op_body, IsInExpr):
                part_name = map_name_to_dataset(op_body.part_on.name)
                probe_name = map_name_to_dataset(op_body.probe_on.name)
                isin_build_name = f'{op_body.probe_on.name}_{op_body.part_on.name}_isin_build'

                if hash_join:
                    if op_body.part_on.unopt_count == 0:
                        tmp_it_1 = IterForm(part_name, tmp_el_on)

                        tmp_it_1.iter_op = DicConsExpr(
                            [(RecAccessExpr(PairAccessExpr(VarExpr(tmp_el_on), 0), op_body.col_part.field),
                              ConstantExpr(True))])

                        self.opt_on.context_unopt.append(
                            LetExpr(varExpr=VarExpr(isin_build_name),
                                    valExpr=tmp_it_1.sdql_ir,
                                    bodyExpr=ConstantExpr(True))
                        )
                    else:
                        tmp_it_1 = IterForm(isin_build_name, tmp_el_on)

                        tmp_it_1.iter_op = DicConsExpr(
                            [(RecAccessExpr(PairAccessExpr(VarExpr(tmp_el_on), 0), op_body.col_part.field),
                              ConstantExpr(True))])

                        self.opt_on.context_unopt.append(
                            LetExpr(varExpr=VarExpr(isin_build_name),
                                    valExpr=tmp_it_1.sdql_ir,
                                    bodyExpr=ConstantExpr(True))
                        )

                    tmp_it_2 = IterForm(probe_name, tmp_el_on)

                    cond_symbol = CompareSymbol.EQ if op_body.isinvert else CompareSymbol.NE

                    tmp_it_2.iter_op = IfExpr(CompareExpr(cond_symbol,
                                                          DicLookupExpr(VarExpr(isin_build_name),
                                                                        RecAccessExpr(PairAccessExpr(VarExpr(tmp_el_on),
                                                                                                     0),
                                                                                      op_body.col_probe.field)
                                                                        ),
                                                          ConstantExpr(None)),
                                              DicConsExpr([(PairAccessExpr(VarExpr(tmp_el_on), 0),
                                                            PairAccessExpr(VarExpr(tmp_el_on), 1))]),
                                              ConstantExpr(None))
                    self.opt_on.context_unopt.append(
                        LetExpr(varExpr=VarExpr(tmp_vn_nx),
                                valExpr=tmp_it_2.sdql_ir,
                                bodyExpr=ConstantExpr(True))
                    )
                else:
                    tmp_it = IterForm(probe_name, tmp_el_on)
                    tmp_it.iter_op = SumExpr(VarExpr('y'),
                                             VarExpr(part_name),
                                             IfExpr(CompareExpr(CompareSymbol.NE,
                                                                PairAccessExpr(VarExpr('y'), 0),
                                                                ConstantExpr(None)),
                                                    IfExpr(CompareExpr(CompareSymbol.EQ,
                                                                       RecAccessExpr(PairAccessExpr(
                                                                           VarExpr(tmp_el_on),
                                                                           0),
                                                                           op_body.col_probe.field),
                                                                       RecAccessExpr(PairAccessExpr(
                                                                           VarExpr('y'), 0),
                                                                           op_body.col_part.field)),
                                                           DicConsExpr([(PairAccessExpr(VarExpr(tmp_el_on), 0),
                                                                         ConstantExpr(True))]),
                                                           ConstantExpr(None)),
                                                    ConstantExpr(None))
                                             )

                    self.opt_on.context_unopt.append(
                        LetExpr(varExpr=VarExpr(tmp_vn_nx),
                                valExpr=tmp_it.sdql_ir,
                                bodyExpr=ConstantExpr(True))
                    )
            elif isinstance(op_body, MergeExpr):
                if self.opt_on.name == op_body.joint.name:
                    if hash_join:
                        tmp_it = IterForm(f'{self.opt_on.name}_part', tmp_el_on)

                        if isinstance(op_body.left_on, str):
                            tmp_it.iter_op = DicConsExpr([(RecAccessExpr(PairAccessExpr(VarExpr(tmp_el_on), 0),
                                                                         str(op_body.left_on)),
                                                           sr_dict({PairAccessExpr(VarExpr(tmp_el_on), 0):
                                                                        PairAccessExpr(VarExpr(tmp_el_on), 1)}))])
                        elif isinstance(op_body.left_on, list):
                            tmp_it.iter_op = DicConsExpr([(RecConsExpr([(c,
                                                                         RecAccessExpr(
                                                                             PairAccessExpr(VarExpr(tmp_el_on), 0),
                                                                             c))
                                                                        for c in op_body.left_on]),
                                                           sr_dict({PairAccessExpr(VarExpr(tmp_el_on), 0):
                                                                        PairAccessExpr(VarExpr(tmp_el_on), 1)}))])

                        self.opt_on.context_unopt.append(
                            LetExpr(varExpr=VarExpr('build_side'),
                                    valExpr=tmp_it.sdql_ir,
                                    bodyExpr=ConstantExpr(True))
                        )

                        tmp_it = IterForm(f'{self.opt_on.name}_probe', tmp_el_on)

                        if isinstance(op_body.right_on, str):
                            tmp_it.iter_cond.append(CompareExpr(CompareSymbol.NE,
                                                                DicLookupExpr(VarExpr('build_side'),
                                                                              RecAccessExpr(
                                                                                  PairAccessExpr(VarExpr(tmp_el_on), 0),
                                                                                  op_body.right_on)),
                                                                ConstantExpr(None)))

                            tmp_it.iter_op = DicConsExpr([(SumExpr(VarExpr('y'), DicLookupExpr(VarExpr('build_side'),
                                                                                               RecAccessExpr(
                                                                                                   PairAccessExpr(
                                                                                                       VarExpr(
                                                                                                           tmp_el_on),
                                                                                                       0),
                                                                                                   op_body.right_on)),
                                                                   ConcatExpr(PairAccessExpr(VarExpr(tmp_el_on), 0),
                                                                              PairAccessExpr(VarExpr('y'), 0))
                                                                   ),
                                                           ConstantExpr(True))])
                        elif isinstance(op_body.right_on, list):
                            tmp_it.iter_cond.append(CompareExpr(CompareSymbol.NE,
                                                                DicLookupExpr(VarExpr('build_side'),
                                                                              RecConsExpr([(c,
                                                                                            RecAccessExpr(
                                                                                                PairAccessExpr(
                                                                                                    VarExpr(tmp_el_on),
                                                                                                    0),
                                                                                                c))
                                                                                           for c in op_body.right_on])),
                                                                ConstantExpr(None)))

                            tmp_it.iter_op = DicConsExpr([(SumExpr(VarExpr('y'), DicLookupExpr(VarExpr('build_side'),
                                                                                               RecConsExpr([(c,
                                                                                                             RecAccessExpr(
                                                                                                                 PairAccessExpr(
                                                                                                                     VarExpr(
                                                                                                                         tmp_el_on),
                                                                                                                     0),
                                                                                                                 c))
                                                                                                            for c in
                                                                                                            op_body.right_on])),
                                                                   ConcatExpr(PairAccessExpr(VarExpr(tmp_el_on), 0),
                                                                              PairAccessExpr(VarExpr('y'), 0))
                                                                   ),
                                                           ConstantExpr(True))])

                        self.opt_on.context_unopt.append(
                            LetExpr(varExpr=VarExpr(tmp_vn_nx),
                                    valExpr=tmp_it.sdql_ir,
                                    bodyExpr=ConstantExpr(True))
                        )
                    else:
                        tmp_it = IterForm('v0_probe', tmp_el_on)

                        tmp_it.iter_op = DicConsExpr([(SumExpr(VarExpr('y'),
                                                               VarExpr('v0_part'),
                                                               IfExpr(CompareExpr(CompareSymbol.NE,
                                                                                  PairAccessExpr(VarExpr('y'), 0),
                                                                                  ConstantExpr(None)),
                                                                      IfExpr(CompareExpr(CompareSymbol.EQ,
                                                                                         RecAccessExpr(
                                                                                             PairAccessExpr(
                                                                                                 VarExpr(tmp_el_on),
                                                                                                 0),
                                                                                             op_body.right_on),
                                                                                         RecAccessExpr(
                                                                                             PairAccessExpr(
                                                                                                 VarExpr('y'), 0),
                                                                                             op_body.left_on)),
                                                                             ConcatExpr(
                                                                                 PairAccessExpr(VarExpr(tmp_el_on), 0),
                                                                                 PairAccessExpr(VarExpr('y'), 0)),
                                                                             ConstantExpr(None)),
                                                                      ConstantExpr(None))
                                                               ),
                                                       ConstantExpr(True))])

                        self.opt_on.context_unopt.append(
                            LetExpr(varExpr=VarExpr(tmp_vn_nx),
                                    valExpr=tmp_it.sdql_ir,
                                    bodyExpr=ConstantExpr(True))
                        )
            elif isinstance(op_body, AggrExpr):
                if len(list(op_body.aggr_op.keys())) == 1:
                    if list(op_body.aggr_op.keys())[0] in self.retriever.findall_cols_for_calc():
                        continue

                    if list(op_body.aggr_op.keys())[0] == 'sum_agg':
                        continue

                aggr_dict = op_body.aggr_op

                tmp_it_1 = IterForm(tmp_vn_on, tmp_el_on)

                rec_list = []
                for k in aggr_dict.keys():
                    v = aggr_dict[k]
                    if isinstance(v, FlexIR):
                        if v.replaceable:
                            rec_list.append((k, aggr_dict[k].replace(PairAccessExpr(VarExpr(tmp_el_on), 0))))
                        else:
                            rec_list.append((k, aggr_dict[k].sdql_ir))
                    elif isinstance(v, RecAccessExpr):
                        rec_list.append((k, RecAccessExpr(PairAccessExpr(VarExpr(tmp_el_on), 0),
                                                          v.name)))
                    else:
                        rec_list.append((k, aggr_dict[k]))

                tmp_it_1.iter_op = RecConsExpr(rec_list)

                self.opt_on.context_unopt.append(
                    LetExpr(varExpr=VarExpr(tmp_vn_nx),
                            valExpr=tmp_it_1.sdql_ir,
                            bodyExpr=ConstantExpr(True))
                )

                self.opt_on.unopt_count += 1

                tmp_vn_on_2 = f'v{self.opt_on.unopt_count - 1}'
                tmp_vn_nx = f'v{self.opt_on.unopt_count}'

                tmp_it_2 = IterForm(tmp_vn_on_2, tmp_el_on)

                tmp_it_2.iter_op = DicConsExpr([(VarExpr(tmp_vn_on_2), ConstantExpr(True))])

                self.opt_on.context_unopt.append(
                    LetExpr(varExpr=VarExpr(tmp_vn_nx),
                            valExpr=tmp_it_2.sdql_ir,
                            bodyExpr=ConstantExpr(True))
                )
            elif isinstance(op_body, GroupbyAggrExpr):
                has_mean = False

                groupby_cols = op_body.groupby_cols
                aggr_dict = op_body.aggr_dict

                tmp_it_1 = IterForm(tmp_vn_on, tmp_el_on)

                key_rec_list = []
                for c in groupby_cols:
                    key_rec_list.append((c, RecAccessExpr(PairAccessExpr(VarExpr(tmp_el_on), 0),
                                                          c)))

                val_rec_list = []
                for k in aggr_dict.keys():
                    if k.endswith('_sum_for_mean') or k.endswith('_count_for_mean'):
                        has_mean = True
                    v = aggr_dict[k]
                    if isinstance(v, FlexIR):
                        if v.replaceable:
                            val_rec_list.append((k, aggr_dict[k].replace(PairAccessExpr(VarExpr(tmp_el_on), 0))))
                        else:
                            val_rec_list.append((k, aggr_dict[k].sdql_ir))
                    elif isinstance(v, RecAccessExpr):
                        val_rec_list.append((k, RecAccessExpr(PairAccessExpr(VarExpr(tmp_el_on), 0),
                                                              v.name)))
                    else:
                        val_rec_list.append((k, aggr_dict[k]))

                tmp_it_1.iter_op = DicConsExpr([(RecConsExpr(key_rec_list), RecConsExpr(val_rec_list))])

                self.opt_on.context_unopt.append(
                    LetExpr(varExpr=VarExpr(tmp_vn_nx),
                            valExpr=tmp_it_1.sdql_ir,
                            bodyExpr=ConstantExpr(True))
                )

                self.opt_on.unopt_count += 1

                tmp_vn_on_2 = f'v{self.opt_on.unopt_count - 1}'
                tmp_vn_nx = f'v{self.opt_on.unopt_count}'

                tmp_it_2 = IterForm(tmp_vn_on_2, tmp_el_on)

                if has_mean:
                    rec_list_2 = []

                    for i in groupby_cols:
                        rec_list_2.append((i, RecAccessExpr(PairAccessExpr(VarExpr(tmp_el_on), 0), i)))

                    origin_dict = op_body.origin_dict
                    for j in origin_dict.keys():
                        if origin_dict[j][1] == 'mean':
                            rec_list_2.append((j, DivExpr(RecAccessExpr(PairAccessExpr(VarExpr(tmp_el_on), 1),
                                                                        f'{j}_sum_for_mean'),
                                                          RecAccessExpr(PairAccessExpr(VarExpr(tmp_el_on), 1),
                                                                        f'{j}_count_for_mean'))))
                        else:
                            rec_list_2.append((j, RecAccessExpr(PairAccessExpr(VarExpr(tmp_el_on), 1), j)))

                    tmp_it_2.iter_op = DicConsExpr([(RecConsExpr(rec_list_2),
                                                     ConstantExpr(True))])
                else:
                    tmp_it_2.iter_op = DicConsExpr([(ConcatExpr(PairAccessExpr(VarExpr(tmp_el_on), 0),
                                                            PairAccessExpr(VarExpr(tmp_el_on), 1)),
                                                 ConstantExpr(True))])

                self.opt_on.context_unopt.append(
                    LetExpr(varExpr=VarExpr(tmp_vn_nx),
                            valExpr=tmp_it_2.sdql_ir,
                            bodyExpr=ConstantExpr(True))
                )
            elif isinstance(op_body, CalcExpr):
                tmp_it = IterForm(tmp_vn_on, tmp_el_on)

                tmp_it.iter_op = RecConsExpr([(i,
                              RecAccessExpr(PairAccessExpr(VarExpr(tmp_el_on), 0), i))
                             for i in SDQLInspector.find_cols(op_body.sdql_ir)])

                self.opt_on.context_unopt.append(
                    LetExpr(varExpr=VarExpr(tmp_vn_nx),
                            valExpr=tmp_it.sdql_ir,
                            bodyExpr=ConstantExpr(True))
                )

                self.opt_on.unopt_count += 1

                tmp_vn_on_2 = f'v{self.opt_on.unopt_count - 1}'
                tmp_vn_nx = f'v{self.opt_on.unopt_count}'

                self.opt_on.context_unopt.append(
                    LetExpr(varExpr=VarExpr(tmp_vn_nx),
                            valExpr=SDQLInspector.replace_access(op_body.sdql_ir, VarExpr(tmp_vn_on_2)),
                            bodyExpr=ConstantExpr(True))
                )
            else:
                tmp_it = IterForm(tmp_vn_on, tmp_el_on)

                tmp_it.iter_op = op_body

                self.opt_on.context_unopt.append(
                    LetExpr(varExpr=VarExpr(tmp_vn_nx),
                            valExpr=tmp_it.sdql_ir,
                            bodyExpr=ConstantExpr(True))
                )

            self.opt_on.unopt_count += 1

        if last_rename:
            if self.opt_on.unopt_count != 0:
                self.opt_on.context_unopt.append(
                    LetExpr(varExpr=VarExpr(last_rename),
                            valExpr=VarExpr(SDQLInspector.get_last_binding_name(self.opt_on.context_unopt)),
                            bodyExpr=ConstantExpr(True))
                )
            else:
                self.opt_on.context_unopt.append(
                    LetExpr(varExpr=VarExpr(last_rename),
                            valExpr=VarExpr(map_name_to_dataset(self.opt_on.name)),
                            bodyExpr=ConstantExpr(True))
                )

    def get_unopt_sdqlir(self):
        self.fill_context_unopt()

        self.opt_on.context_unopt.append(
            LetExpr(varExpr=VarExpr('results'),
                    valExpr=VarExpr(f'v{self.opt_on.unopt_count - 1}'),
                    bodyExpr=ConstantExpr(True))
        )

        return SDQLInspector.concat_bindings(self.opt_on.context_unopt, drop_dup=False)
