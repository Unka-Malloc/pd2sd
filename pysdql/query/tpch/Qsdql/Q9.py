from pysdql.query.tpch.const import (LINEITEM_TYPE, ORDERS_TYPE, NATION_TYPE, SUPPLIER_TYPE, PART_TYPE,
                                     PARTSUPP_TYPE)

from pysdql.extlib.sdqlpy.sdql_lib import *


@sdql_compile({"li": LINEITEM_TYPE, "ord": ORDERS_TYPE, "na": NATION_TYPE, "su": SUPPLIER_TYPE, "pa": PART_TYPE,
               "ps": PARTSUPP_TYPE})
def query(li, ord, na, su, pa, ps):

    # Insert
    green = "green"
    nation_part = na.sum(lambda x_nation: {x_nation[0].n_nationkey: record({"n_name": x_nation[0].n_name})})
    
    nation_supplier = su.sum(lambda x_supplier: ({x_supplier[0].s_suppkey: record({"n_name": nation_part[x_supplier[0].s_nationkey].n_name})}) if (nation_part[x_supplier[0].s_nationkey] != None) else (None))
    
    part_part = pa.sum(lambda x_part: ({x_part[0].p_partkey: True}) if (firstIndex(x_part[0].p_name, green) != ((-1) * (1))) else (None))
    
    nation_supplier_part_partsupp = ps.sum(lambda x_partsupp: (({record({"ps_suppkey": x_partsupp[0].ps_suppkey, "ps_partkey": x_partsupp[0].ps_partkey}): record({"n_name": nation_supplier[x_partsupp[0].ps_suppkey].n_name, "ps_partkey": x_partsupp[0].ps_partkey, "ps_suppkey": x_partsupp[0].ps_suppkey, "ps_supplycost": x_partsupp[0].ps_supplycost})}) if (nation_supplier[x_partsupp[0].ps_suppkey] != None) else (None)) if (part_part[x_partsupp[0].ps_partkey] != None) else (None))
    
    orders_part = ord.sum(lambda x_orders: {x_orders[0].o_orderkey: record({"o_orderdate": x_orders[0].o_orderdate})})
    
    nation_supplier_part_partsupp_orders_lineitem = li.sum(lambda x_lineitem: (({record({"nation": nation_supplier_part_partsupp[record({"l_suppkey": x_lineitem[0].l_suppkey, "l_partkey": x_lineitem[0].l_partkey})].n_name, "o_year": extractYear(orders_part[x_lineitem[0].l_orderkey].o_orderdate)}): record({"sum_profit": ((((x_lineitem[0].l_extendedprice) * (((1.0) - (x_lineitem[0].l_discount))))) - (((nation_supplier_part_partsupp[record({"l_suppkey": x_lineitem[0].l_suppkey, "l_partkey": x_lineitem[0].l_partkey})].ps_supplycost) * (x_lineitem[0].l_quantity))))})}) if (nation_supplier_part_partsupp[record({"l_suppkey": x_lineitem[0].l_suppkey, "l_partkey": x_lineitem[0].l_partkey})] != None) else (None)) if (orders_part[x_lineitem[0].l_orderkey] != None) else (None))
    
    results = nation_supplier_part_partsupp_orders_lineitem.sum(lambda x_nation_supplier_part_partsupp_orders_lineitem: {record({"nation": x_nation_supplier_part_partsupp_orders_lineitem[0].nation, "o_year": x_nation_supplier_part_partsupp_orders_lineitem[0].o_year, "sum_profit": x_nation_supplier_part_partsupp_orders_lineitem[1].sum_profit}): True})
    
    # Complete

    return results
