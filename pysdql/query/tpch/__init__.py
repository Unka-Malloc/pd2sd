import pprint
import time
import traceback

import pysdql.query.tpch.Qsdql

import pysdql.query.tpch.Qpandas

from pysdql.query.util import sdql_to_df, pandas_to_df, compare_dataframe

sep_line = '=' * 60

issue_info = {
    2: 'Not Implemented: Minimum promotion',
    9: 'Mismatch Answer: Incorrect n_name due to string addition (Example: PERUPERUPERUPERU)',
    12: 'Mismatch Answer: Incorrect l_shipmode due to string addition (Example: SHIPSHIPSHIP)',
    16: 'Weak: If a dict is empty, then dict[key] should be None instead of asserting an Exception'
}


def tpch_query(qindex=1, execution_mode=0, threads_count=1, verbose=True) -> bool:
    done = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]

    error_info = {}

    if isinstance(qindex, int):
        if qindex not in done:
            print(f'Query {qindex} has not been verified.')
            return False

        qindex = [qindex]

    if isinstance(qindex, (tuple, list)):
        check_dict = {}
        for q in qindex:
            if q not in done:
                print(f'Query {q} has not been verified.')
                return False

            print(f'>> Query {q} (Q{q}) <<')

            sdql_df = None
            pandas_df = None

            if verbose:
                print(f'>> SDQL <<')

            try:
                sdql_result = eval(f'pysdql.query.tpch.Qsdql.q{q}({execution_mode}, {threads_count})')
            except:
                check_dict[q] = '\033[31m Error \033[0m'

                if verbose:
                    print_error_text(q)
                else:
                    print(f'Query {q}: Error')

                traceback.print_exc()

                error_info[q] = traceback.format_exc()

                continue

            sdql_df = sdql_to_df(sdql_result)

            if verbose:
                print(sdql_result)

                print(f'>> Pandas <<')

            try:
                pandas_result = eval(f'pysdql.query.tpch.Qpandas.q{q}()')
            except:
                check_dict[q] = '\033[31m Error \033[0m'

                if verbose:
                    print_error_text(q)
                else:
                    print(f'Query {q}: Error')

                traceback.print_exc()

                error_info[q] = traceback.format_exc()

                continue

            pandas_df = pandas_to_df(pandas_result)

            if verbose:
                print(pandas_result)

            if compare_dataframe(sdql_df, pandas_df, verbose):
                check_dict[q] = '\033[32m Pass \033[0m'
                if verbose:
                    print_pass_text(q)
                else:
                    print(sep_line)
                    print(f'\033[32m Query {q}: Pass \033[0m')
                    print(sep_line)
            else:
                check_dict[q] = '\033[0m Fail \033[0m'
                if verbose:
                    print_fail_text(q)
                else:
                    print(sep_line)
                    print(f'\033[0m Query {q}: Fail \033[0m')
                    print(sep_line)
        else:
            if verbose:
                for k in error_info.keys():
                    print(f'>> Traceback Q{k} <<')
                    print()
                    print(error_info[k])
                    print(sep_line)

            for k in check_dict.keys():
                if k in issue_info.keys():
                    print(f'{k}: {check_dict[k]} (\033[31m {issue_info[k]} \033[0m)')
                else:
                    print(f'{k}: {check_dict[k]}')
            print(sep_line)

            for k in check_dict.keys():
                if 'Pass' not in check_dict[k]:
                    return False
            else:
                return True
    else:
        raise NotImplementedError

def print_pass_text(q):
    print(sep_line)
    print(f'''
    {art_map[q]}
    \033[32m
           ██████╗  █████╗ ███████╗███████╗
           ██╔══██╗██╔══██╗██╔════╝██╔════╝
           ██████╔╝███████║███████╗███████╗
           ██╔═══╝ ██╔══██║╚════██║╚════██║
           ██║     ██║  ██║███████║███████║
           ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝                                                                  
    \033[0m''')
    print(sep_line)


def print_fail_text(q):
    print(sep_line)
    print(f'''
    {art_map[q]}
             █████▒ ▄▄▄       ██▓ ██▓    
           ▓██   ▒ ▒████▄    ▓██▒▓██▒    
           ▒████ ░ ▒██  ▀█▄  ▒██▒▒██░    
           ░▓█▒  ░ ░██▄▄▄▄██ ░██░▒██░    
           ░▒█░     ▓█   ▓██▒░██░░██████▒
            ▒ ░     ▒▒   ▓▒█░░▓  ░ ▒░▓  ░
            ░        ▒   ▒▒ ░ ▒ ░░ ░ ▒  ░
            ░ ░      ░   ▒    ▒ ░  ░ ░   
                         ░  ░ ░      ░  ░
    ''')
    print(sep_line)

def print_error_text(q):
    print(sep_line)
    print(f'''
    {art_map[q]}
    \033[31m
         ▓█████  ██▀███   ██▀███   ▒█████   ██▀███  
         ▓█   ▀ ▓██ ▒ ██▒▓██ ▒ ██▒▒██▒  ██▒▓██ ▒ ██▒
         ▒███   ▓██ ░▄█ ▒▓██ ░▄█ ▒▒██░  ██▒▓██ ░▄█ ▒
         ▒▓█  ▄ ▒██▀▀█▄  ▒██▀▀█▄  ▒██   ██░▒██▀▀█▄  
         ░▒████▒░██▓ ▒██▒░██▓ ▒██▒░ ████▓▒░░██▓ ▒██▒
         ░░ ▒░ ░░ ▒▓ ░▒▓░░ ▒▓ ░▒▓░░ ▒░▒░▒░ ░ ▒▓ ░▒▓░
          ░ ░  ░  ░▒ ░ ▒░  ░▒ ░ ▒░  ░ ▒ ▒░   ░▒ ░ ▒░
            ░     ░░   ░   ░░   ░ ░ ░ ░ ▒    ░░   ░ 
            ░  ░   ░        ░         ░ ░     ░                 
    \033[0m''')
    print(sep_line)


art_map = {
    1: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     ██╗
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ███║
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ╚██║
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝       ██║
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║        ██║
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═╝
    ''',
    2: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗    ██████╗ 
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ╚════██╗
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝      █████╔╝
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝      ██╔═══╝ 
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║       ███████╗
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝       ╚══════╝
    ''',
    3: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗    ██████╗ 
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ╚════██╗
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝      █████╔╝
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝       ╚═══██╗
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║       ██████╔╝
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝       ╚═════╝ 
    ''',
    4: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗    ██╗  ██╗
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ██║  ██║
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ███████║
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝      ╚════██║
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║            ██║
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝            ╚═╝

    ''',
    5: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗    ███████╗
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ██╔════╝
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ███████╗
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝      ╚════██║
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║       ███████║
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝       ╚══════╝
    ''',
    6: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     ██████╗ 
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ██╔════╝ 
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ███████╗ 
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝      ██╔═══██╗
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║       ╚██████╔╝
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═════╝ 
    ''',
    7: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗    ███████╗
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ╚════██║
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝        ██╔╝ 
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝        ██╔╝  
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║         ██║   
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝         ╚═╝   
''',
    8: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     █████╗ 
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ██╔══██╗
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ╚█████╔╝
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝      ██╔══██╗
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║       ╚█████╔╝
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚════╝ 
''',
    9: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     █████╗ 
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ██╔══██╗
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ╚██████║
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝       ╚═══██║
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║        █████╔╝
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚════╝ 
''',
    10: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     ██╗ ██████╗ 
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ███║██╔═████╗
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ╚██║██║██╔██║
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝       ██║████╔╝██║
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║        ██║╚██████╔╝
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═╝ ╚═════╝ 
''',
    11: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     ██╗ ██╗
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ███║███║
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ╚██║╚██║
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝       ██║ ██║
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║        ██║ ██║
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═╝ ╚═╝
''',
    12: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     ██╗██████╗ 
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ███║╚════██╗
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ╚██║ █████╔╝
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝       ██║██╔═══╝ 
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║        ██║███████╗
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═╝╚══════╝
''',
    13: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     ██╗██████╗ 
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ███║╚════██╗
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ╚██║ █████╔╝
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝       ██║ ╚═══██╗
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║        ██║██████╔╝
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═╝╚═════╝ 
''',
    14: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     ██╗██╗  ██╗
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ███║██║  ██║
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ╚██║███████║
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝       ██║╚════██║
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║        ██║     ██║
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═╝     ╚═╝
''',
    15: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     ██╗███████╗
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ███║██╔════╝
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ╚██║███████╗
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝       ██║╚════██║
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║        ██║███████║
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═╝╚══════╝
''',
    16: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     ██╗ ██████╗ 
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ███║██╔════╝ 
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ╚██║███████╗ 
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝       ██║██╔═══██╗
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║        ██║╚██████╔╝
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═╝ ╚═════╝ 
''',
    17: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     ██╗███████╗
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ███║╚════██║
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ╚██║   ██╔╝ 
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝       ██║  ██╔╝  
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║        ██║  ██║   
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═╝  ╚═╝   
''',
    18: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     ██╗ █████╗ 
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ███║██╔══██╗
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ╚██║╚█████╔╝
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝       ██║██╔══██╗
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║        ██║╚█████╔╝
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═╝ ╚════╝ 
''',
    19: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗     ██╗ █████╗ 
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ███║██╔══██╗
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝     ╚██║╚██████║
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝       ██║ ╚═══██║
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║        ██║ █████╔╝
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═╝ ╚════╝ 
''',
    20: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗    ██████╗  ██████╗ 
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ╚════██╗██╔═████╗
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝      █████╔╝██║██╔██║
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝      ██╔═══╝ ████╔╝██║
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║       ███████╗╚██████╔╝
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝       ╚══════╝ ╚═════╝ 
''',
    21: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗    ██████╗  ██╗
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ╚════██╗███║
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝      █████╔╝╚██║
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝      ██╔═══╝  ██║
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║       ███████╗ ██║
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝       ╚══════╝ ╚═╝
''',
    22: '''
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗    ██████╗ ██████╗ 
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ╚════██╗╚════██╗
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝      █████╔╝ █████╔╝
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝      ██╔═══╝ ██╔═══╝ 
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║       ███████╗███████╗
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝       ╚══════╝╚══════╝
''',
}
