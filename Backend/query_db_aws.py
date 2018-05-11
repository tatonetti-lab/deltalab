"""
deltalab Database - Query Database, Updated July 28, 2017

Copyright (C) 2017, Tatonetti Lab
Tal Lorberbaum <tal.lorberbaum@columbia.edu>
Victor Nwankwo <vtn2106@cumc.columbia.edu>
Nicholas P. Tatonetti <nick.tatonetti@columbia.edu>
Julie Prost <jap2277@columbia.edu>
All rights reserved.

This script is released under a CC BY-NC-SA 4.0 license.
For full license details see LICENSE.txt or go to:
http://creativecommons.org/licenses/by-nc-sa/4.0/

------------------------------------------------------------------------
deltalab Database script for querying database for one or more drugs.
"""

import pymysql

DATABASE = '' # name of the database created with create_Db_tables.sql

def query_db(drugs,cache=False):
    # Connect to the database
    conn = pymysql.connect(read_default_file='CONFIG_FILE',
                db=DATABASE,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor)
    cur = conn.cursor()

    table_suffix = ""

    if len(drugs) == 1:
        if drugs[0].startswith('('):
            drug_select = 'in'
        else:
            drug_select = '='

        SQL = '''select pm.pt_id_era, pm.pt_id, pm.age, pm.sex, pm.race, pm.num_drugs, pm.pre_test_high, pm.post_test_high, pm.delta_qt
from {DATABASE}.Patient{suffix} pm
join
    (select pt_id,
     max(delta_test) as max_delta
     from {DATABASE}.Patient{suffix} p
     join {DATABASE}.Patient2Drug{suffix} d1 using (pt_id_era)
     where d1.drug_concept_id {drug_select} {drugs0}\n'''.format(DATABASE=DATABASE, suffix=table_suffix, drug_select=drug_select, drugs0=drugs[0])


    else:
        SQL = '''select pm.pt_id_era, pm.pt_id, pm.age, pm.sex, pm.race, pm.num_drugs, pm.pre_test_high, pm.post_test_high, pm.delta_test
from labtestdb.Patient{suffix} pm
join
    (select pt_id,
     max(delta_test) as max_delta
     from {DATABASE}.Patient{suffix} p\n'''.format(suffix=table_suffix, DATABASE=DATABASE)

        for i in range(len(drugs)):
            SQL += '''     join {DATABASE}.Patient2Drug%s d%d using (pt_id_era)\n'''.format(DATABASE=DATABASE) %(table_suffix, (i+1))


        for i in range(len(drugs)):
            if i == 0:
                where_statement = 'where'
            else:
                where_statement = 'and'

            if drugs[i].startswith('('):
                drug_select = 'in'
            else:
                drug_select = '='

            SQL += '''     %s d%d.drug_concept_id %s %s\n''' %(where_statement, i+1, drug_select, drugs[i])

    delta_limit = 150
    SQL += '''     and abs(delta_test) <= %d\n''' %delta_limit

    SQL += '''     group by pt_id) m
on pm.pt_id = m.pt_id
and pm.delta_test = m.max_delta;'''

    print SQL
    cur.execute(SQL)
    results = cur.fetchall()
    delta_tests = []
    pt_ids_seen = set()

    for result in results:
        if result['pt_id'] in pt_ids_seen:
            continue
        pt_ids_seen.add(result['pt_id'])
        delta_tests.append({"delta": result['delta_test'], "age": result['age'], "sex": str(result['sex']),
                          "race": str(result['race']), "num_drugs": result['num_drugs'],
                          "pre_test_high": result['pre_test_high'], "post_test_high": result['post_test_high']})

    if cache == True:
        if drugs[-1].startswith('('):
            drug_select = 'in'
        else:
            drug_select = '='

        SQL = '''select pm.pt_id_era, pm.pt_id, pm.age, pm.sex, pm.race, pm.num_drugs, pm.pre_test_high, pm.post_test_high, pm.delta_test
from {DATABASE}.Patient{suffix} pm
join
    (select pt_id,
     max(delta_test) as max_delta
     from {DATABASE}.Patient{suffix} p
     join {DATABASE}.Patient2Drug{suffix} d1 using (pt_id_era)
     where d1.drug_concept_id {drug_select} {drugs0}\n'''.format(DATABASE=DATABASE, suffix=table_suffix, drug_select=drug_select, drugs0=drugs[-1])

        SQL += '''     and abs(delta_test) <= %d\n''' %delta_limit

        SQL += '''     group by pt_id) m
    on pm.pt_id = m.pt_id
    and pm.delta_test = m.max_delta;'''

        print "Caching:", SQL
        cur.execute(SQL)
        results = cur.fetchall()

        delta_tests_cache = []
        pt_ids_seen = set()

        for result in results:
            if result['pt_id'] in pt_ids_seen:
                continue
            pt_ids_seen.add(result['pt_id'])
            delta_tests_cache.append({"delta": result['delta_qt'], "age": result['age'], "sex": str(result['sex']),
                                    "race": str(result['race']), "num_drugs": result['num_drugs'],
                                    "pre_test_high": result['pre_test_high'], "post_test_high": result['post_test_high']})

    cur.close()
    conn.close()

    if cache != True:
        return delta_tests
    else:
        return delta_tests, delta_tests_cache
