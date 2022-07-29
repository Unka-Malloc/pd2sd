"""
select
	sum(l_extendedprice* (1 - l_discount)) as revenue
from
	lineitem,
	part
where
	(
		p_partkey = l_partkey
		and p_brand = ':1'
		and p_container in ('SM CASE', 'SM BOX', 'SM PACK', 'SM PKG')
		and l_quantity >= :4 and l_quantity <= :4 + 10
		and p_size between 1 and 5
		and l_shipmode in ('AIR', 'AIR REG')
		and l_shipinstruct = 'DELIVER IN PERSON'
	)
	or
	(
		p_partkey = l_partkey
		and p_brand = ':2'
		and p_container in ('MED BAG', 'MED BOX', 'MED PKG', 'MED PACK')
		and l_quantity >= :5 and l_quantity <= :5 + 10
		and p_size between 1 and 10
		and l_shipmode in ('AIR', 'AIR REG')
		and l_shipinstruct = 'DELIVER IN PERSON'
	)
	or
	(
		p_partkey = l_partkey
		and p_brand = ':3'
		and p_container in ('LG CASE', 'LG BOX', 'LG PACK', 'LG PKG')
		and l_quantity >= :6 and l_quantity <= :6 + 10
		and p_size between 1 and 15
		and l_shipmode in ('AIR', 'AIR REG')
		and l_shipinstruct = 'DELIVER IN PERSON'
	)
"""
import pysdql

if __name__ == '__main__':
    var1 = 'Brand#54'
    var2 = 'Brand#22'
    var3 = 'Brand#33'
    var4 = 1
    var4_1 = var4 + 10
    var5 = 18
    var5_1 = var5 + 10
    var6 = 26
    var6_1 = var6 + 10

    lineitem = pysdql.read_tbl(path=r'T:/UG4-Proj/datasets/lineitem.tbl', names=pysdql.LINEITEM_COLS)
    part = pysdql.read_tbl(path=r'T:/UG4-Proj/datasets/part.tbl', names=pysdql.PART_COLS)

    r = lineitem.merge(part, on=(lineitem['l_partkey'] == part['p_partkey']))

    r = r[((r['p_brand'] == var1)
           & (r['p_container'].isin(['SM CASE', 'SM BOX', 'SM PACK', 'SM PKG']))
           & (r['p_size'] >= 1) & (r['p_size'] <= 5)
           & (r['l_quantity'] >= var4)
           & (r['l_quantity'] <= var4_1)
           & (r['l_shipmode'].isin(['AIR', 'AIR REG']))
           & (r['l_shipinstruct'] == 'DELIVER IN PERSON')
           )
          | ((r['p_brand'] == var2)
             & (r['p_container'].isin(['MED BAG', 'MED BOX', 'MED PKG', 'MED PACK']))
             & (r['p_size'] >= 1) & (r['p_size'] <= 10)
             & (r['l_quantity'] >= var5) & (r['l_quantity'] <= var5_1)
             & (r['l_shipmode'].isin(['AIR', 'AIR REG']))
             & (r['l_shipinstruct'] == 'DELIVER IN PERSON')
             )
          | ((r['p_brand'] == var3)
             & (r['p_container'].isin(['LG CASE', 'LG BOX', 'LG PACK', 'LG PKG']))
             & (r['p_size'] >= 1) & (r['p_size'] <= 15)
             & (r['l_quantity'] >= var6)
             & (r['l_quantity'] <= var6_1)
             & (r['l_shipmode'].isin(['AIR', 'AIR REG']))
             & (r['l_shipinstruct'] == 'DELIVER IN PERSON'))]

    r = r.agg(revenue=((r['l_extendedprice'] * (1 - r['l_discount'])), 'sum'))

    pysdql.db_driver(db_path=r'T:/sdql', name='tpch-19').run(r).export().to()
