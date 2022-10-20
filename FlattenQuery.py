from pysdql.core.dtypes.sdql_ir import VarExpr, LetExpr, ConstantExpr, JoinPartitionBuilder, DicConsExpr, RecConsExpr, \
    JoinProbeBuilder, SumBuilder, ConcatExpr, IfExpr


def q3():
    building = VarExpr("building")
    customer_indexed = VarExpr("customer_indexed")
    order_probed = VarExpr("order_probed")
    lineitem_probed = VarExpr("lineitem_probed")
    results = VarExpr("results")

    li = VarExpr("db->li_dataset")
    cu = VarExpr("db->cu_dataset")
    ord = VarExpr("db->ord_dataset")

    q3 = LetExpr(building, ConstantExpr("BUILDING"),
                 LetExpr(customer_indexed,
                         JoinPartitionBuilder(cu, "c_custkey", lambda p: (p.c_mktsegment == building), []),
                         LetExpr(order_probed, JoinProbeBuilder(customer_indexed, ord, "o_custkey",
                                                                lambda p: (p.o_orderdate < ConstantExpr(19950315)),
                                                                lambda indexedDictValue, probeDictKey: DicConsExpr([(
                                                                    probeDictKey.o_orderkey,
                                                                    RecConsExpr(
                                                                        [(
                                                                            "o_orderdate",
                                                                            probeDictKey.o_orderdate),
                                                                            (
                                                                                "o_shippriority",
                                                                                probeDictKey.o_shippriority)]))]),
                                                                True), LetExpr(lineitem_probed,
                                                                               JoinProbeBuilder(order_probed, li,
                                                                                                "l_orderkey",
                                                                                                lambda p: (
                                                                                                        p.l_shipdate > ConstantExpr(
                                                                                                    19950315)),
                                                                                                lambda indexedDictValue,
                                                                                                       probeDictKey: DicConsExpr(
                                                                                                    [(RecConsExpr([(
                                                                                                        "l_orderkey",
                                                                                                        probeDictKey.l_orderkey),
                                                                                                        (
                                                                                                            "o_orderdate",
                                                                                                            indexedDictValue.o_orderdate),
                                                                                                        (
                                                                                                            "o_shippriority",
                                                                                                            indexedDictValue.o_shippriority)]),
                                                                                                      RecConsExpr([(
                                                                                                          "revenue",
                                                                                                          (
                                                                                                                  probeDictKey.l_extendedprice * (
                                                                                                                  ConstantExpr(
                                                                                                                      1.0) - probeDictKey.l_discount)))]))])),
                                                                               LetExpr(results, SumBuilder(
                                                                                   lambda p: DicConsExpr(
                                                                                       [(ConcatExpr(p[0],
                                                                                                    p[1]),
                                                                                         ConstantExpr(
                                                                                             True))]),
                                                                                   lineitem_probed, True),
                                                                                       LetExpr(VarExpr("out"), results,
                                                                                               ConstantExpr(True)))))))

    print(q3)

    '''
    LetExpr(building, ConstantExpr("BUILDING"), LetExpr(customer_indexed, SumExpr(v1, db->cu_dataset, IfExpr(CompareExpr(CompareSymbol.EQ, RecAccessExpr(PairAccessExpr(v1, 0), 'c_mktsegment'), building), DicConsExpr([(RecAccessExpr(PairAccessExpr(v1, 0), 'c_custkey'), RecConsExpr([('c_custkey', RecAccessExpr(PairAccessExpr(v1, 0), 'c_custkey'))]))]), EmptyDicConsExpr()), True), LetExpr(order_probed, LetExpr(v3, customer_indexed, SumExpr(v4, db->ord_dataset, IfExpr(CompareExpr(CompareSymbol.LT, RecAccessExpr(PairAccessExpr(v4, 0), 'o_orderdate'), ConstantExpr(19950315)), IfExpr(CompareExpr(CompareSymbol.NE, DicLookupExpr(v3, RecAccessExpr(PairAccessExpr(v4, 0), 'o_custkey')), ConstantExpr(None)), DicConsExpr([(RecAccessExpr(PairAccessExpr(v4, 0), 'o_orderkey'), RecConsExpr([('o_orderdate', RecAccessExpr(PairAccessExpr(v4, 0), 'o_orderdate')), ('o_shippriority', RecAccessExpr(PairAccessExpr(v4, 0), 'o_shippriority'))]))]), EmptyDicConsExpr()), EmptyDicConsExpr()), True)), LetExpr(lineitem_probed, LetExpr(v6, order_probed, SumExpr(v7, db->li_dataset, IfExpr(CompareExpr(CompareSymbol.GT, RecAccessExpr(PairAccessExpr(v7, 0), 'l_shipdate'), ConstantExpr(19950315)), IfExpr(CompareExpr(CompareSymbol.NE, DicLookupExpr(v6, RecAccessExpr(PairAccessExpr(v7, 0), 'l_orderkey')), ConstantExpr(None)), DicConsExpr([(RecConsExpr([('l_orderkey', RecAccessExpr(PairAccessExpr(v7, 0), 'l_orderkey')), ('o_orderdate', RecAccessExpr(DicLookupExpr(v6, RecAccessExpr(PairAccessExpr(v7, 0), 'l_orderkey')), 'o_orderdate')), ('o_shippriority', RecAccessExpr(DicLookupExpr(v6, RecAccessExpr(PairAccessExpr(v7, 0), 'l_orderkey')), 'o_shippriority'))]), RecConsExpr([('revenue', MulExpr(RecAccessExpr(PairAccessExpr(v7, 0), 'l_extendedprice'), SubExpr(ConstantExpr(1.0), RecAccessExpr(PairAccessExpr(v7, 0), 'l_discount'))))]))]), EmptyDicConsExpr()), EmptyDicConsExpr()), False)), LetExpr(results, SumExpr(v9, lineitem_probed, DicConsExpr([(ConcatExpr(PairAccessExpr(v9, 0), PairAccessExpr(v9, 1)), ConstantExpr(True))]), True), LetExpr(out, results, ConstantExpr(True)))))))
    '''


def q6():
    results = VarExpr("results")

    li = VarExpr("db->li_dataset")

    q6 = LetExpr(results, SumBuilder(lambda p: IfExpr((((p[0].l_shipdate >= ConstantExpr(19940101))) * (
        (p[0].l_shipdate < ConstantExpr(19950101))) * ((p[0].l_discount >= ConstantExpr(0.05))) * (
                                                           (p[0].l_discount <= ConstantExpr(0.07))) * (
                                                           (p[0].l_quantity < ConstantExpr(24.0)))),
                                                      (p[0].l_extendedprice * p[0].l_discount), ConstantExpr(0.0)),
                                     li, ), LetExpr(VarExpr("out"), results, ConstantExpr(True)))

    print(q6)


if __name__ == '__main__':
    # q3()
    q6()
