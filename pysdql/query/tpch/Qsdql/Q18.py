from pysdql.query.tpch.const import (LINEITEM_TYPE, CUSTOMER_TYPE, ORDERS_TYPE)

from pysdql.extlib.sdqlpy.sdql_lib import *


@sdql_compile({"li": LINEITEM_TYPE, "cu": CUSTOMER_TYPE, "ord": ORDERS_TYPE})
def query(li, cu, ord):

    # Insert
    customer_orders_index = cu.sum(lambda x: {record({"c_custkey": x[0].c_custkey, "c_name": x[0].c_name}): True})
    
    lineitem_0 = li.sum(lambda x: {record({"l_orderkey": x[0].l_orderkey}): record({"sum_quantity": x[0].l_quantity})})
    
    lineitem_1 = lineitem_0.sum(lambda x: {x[0].concat(x[1]): True})
    
    lineitem_2 = lineitem_1.sum(lambda x: ({x[0]: x[1]}) if (x[0].sum_quantity > 300) else (None))
    
    lineitem_3 = lineitem_2.sum(lambda x: {record({"l_orderkey": x[0].l_orderkey}): True})
    
    lineitem_orders_isin_build_index = lineitem_3.sum(lambda x: {x[0].l_orderkey: True})
    
    customer_orders_probe = ord.sum(lambda x: ({x[0]: x[1]}) if (lineitem_orders_isin_build_index[x[0].o_orderkey] != None) else (None))
    
    customer_orders_build_nest_dict = customer_orders_index.sum(lambda x: {x[0].c_custkey: sr_dict({x[0]: x[1]})})
    
    customer_orders_0 = customer_orders_probe.sum(lambda x: (customer_orders_build_nest_dict[x[0].o_custkey].sum(lambda y: {x[0].concat(y[0]): True})
    ) if (customer_orders_build_nest_dict[x[0].o_custkey] != None) else (None))
    
    customer_orders_lineitem_index = customer_orders_0.sum(lambda x: {record({"c_name": x[0].c_name, "c_custkey": x[0].c_custkey, "o_orderkey": x[0].o_orderkey, "o_orderdate": x[0].o_orderdate, "o_totalprice": x[0].o_totalprice}): True})
    
    customer_orders_lineitem_build_nest_dict = customer_orders_lineitem_index.sum(lambda x: {x[0].o_orderkey: sr_dict({x[0]: x[1]})})
    
    customer_orders_lineitem_0 = li.sum(lambda x: (customer_orders_lineitem_build_nest_dict[x[0].l_orderkey].sum(lambda y: {x[0].concat(y[0]): True})
    ) if (customer_orders_lineitem_build_nest_dict[x[0].l_orderkey] != None) else (None))
    
    customer_orders_lineitem_1 = customer_orders_lineitem_0.sum(lambda x: {record({"c_name": x[0].c_name, "c_custkey": x[0].c_custkey, "o_orderkey": x[0].o_orderkey, "o_orderdate": x[0].o_orderdate, "o_totalprice": x[0].o_totalprice}): record({"sum_quantity": x[0].l_quantity})})
    
    results = customer_orders_lineitem_1.sum(lambda x: {x[0].concat(x[1]): True})
    
    # Complete

    return results
