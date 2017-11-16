"""
deltalab Database creation script v1.0, Updated July 28, 2017

Copyright (C) 2017, Tatonetti Lab
Tal Lorberbaum <tal.lorberbaum@columbia.edu>
Nicholas P. Tatonetti <nick.tatonetti@columbia.edu>
Julie Prost <jap2277@columbia.edu>
All rights reserved.

This script is released under a CC BY-NC-SA 4.0 license.
For full license details see LICENSE.txt or go to:
http://creativecommons.org/licenses/by-nc-sa/4.0/

------------------------------------------------------------------------
Creates deltalab Database by connecting to OMOP Common Data Model and a
local database of lab tests results.

"""


import MySQLdb
from collections import defaultdict
import numpy as np
import random
import operator
import csv
import urllib2
import json
import ipdb

from tqdm import tqdm

# Define table names
CONFIG_FILE = "~/.my.cnf"             # log-in credentials for database
OMOP_CDM_DB = "clinical_gm"             # local OMOP CDM MySQL database
DRUG_ERA    = "dili_drug_era"             # local OMOP CDM DRUG_ERA table
CONCEPT     = "clinical_cumc_v5.concept"             # local OMOP CDM CONCEPT table
PERSON      = "dili_person"             # local OMOP CDM PERSON table
MEASUREMENT = "dili_measurements"             #local OMOP CDM MEASUREMENT table

'''
#############################################################################
For dili, we know the drugs and the labs.

These have been loaded into EBDB, they should be the first three AEs in the list.

It should also be noted how we determined upper and lower limits of normal:
UPPER: The ULN values from the Columbia DILI phenotyping algorithm document
LOWER: The most prevalent 'range_high' (erroneously populated - the column should be named 'range_low') 
  value in clinical_cumc.measurement. Refer to EBDB.adverse_event_to_lab_test for more details.

Labs: 
3006923	Alanine aminotransferase serum/plasma	1742-6
3024128	Total Bilirubin serum/plasma	1975-2
3035995	Alkaline phosphatase serum/plasma	6768-6

Drugs:
[everything in clinical_gm.dili_drugs]

Note that we have to remove minimum limit on drug frequency
#############################################################################
'''


# Get ADVERSE_EVENT_OF_INTEREST and corresponding data through the nsides API
def nsides_api(service, method, args = None):
    """
    Simple python API to access the NSIDES services and data.

    service   string, that can be one of three values: aeolus, sider, or omop
    method    string, for a list of methods see http://nsideseb-env.us-east-1.elasticbeanstalk.com
    args      dictionary, method parameters see http://nsideseb-env.us-east-1.elasticbeanstalk.com
    """
    NSIDES_API_URL = 'https://www.nsides.io/api/v1/'

    base_url = NSIDES_API_URL + 'query?service=%s&meta=%s' % (service, method)
    url = base_url
    if not args is None:
        url = base_url + '&' + '&'.join(['%s=%s' % (k,v) for k,v in args.items()])

    response = urllib2.urlopen(url).read()
    data = json.loads(response)
    return data

data = nsides_api('lab', 'ae_to_lab')

ae2loinc = dict()
loinc2limitval = dict()
aelist = list()

for r in data['results']:
    ae2loinc[r['adverse_event']] = r['loinc']
    loinc2limitval[r['loinc']] = (r['limit_value_low'], r['limit_value_high'])
    aelist.append(r['adverse_event'])

aelist = sorted(set(aelist))

ADVERSE_EVENT_OF_INTEREST = aelist[0] #any adverse event from aelist

# ae2loinc = {
#     u'Alanine aminotransferase serum/plasma': u'1742-6',
#     u'Total Bilirubin serum/plasma': u'1975-2',
#     u'Alkaline phosphatase serum/plasma': u'6768-6'
# }

# aelist = [
#     u'Alanine aminotransferase serum/plasma',
#     u'Total Bilirubin serum/plasma',
#     u'Alkaline phosphatase serum/plasma'
# ]

# Creation of the database
print "Creating delta Database for %s ..." %ADVERSE_EVENT_OF_INTEREST

# Connect to MySQL database
print "Connecting to database"
con = MySQLdb.connect(read_default_file = CONFIG_FILE, db = OMOP_CDM_DB)
cur = con.cursor()

# Get drug names
print "Getting commonly prescribed drugs:",
min_num_pts = 1

drug2name = dict()
drugname2concept_id = dict()

# # GET DILI COHORT PATIENTS
# SQL = '''
# SELECT DISTINCT MRN as person_id
# from clinical_gm.dili_phenotype;
# '''
# cur.execute(SQL)
# dili_pts = [x[0] for x in cur.fetchall()]

SQL = '''select * from
        (select drug_concept_id, concept_name as drug, count(distinct person_id) as num_pts
        from {DRUG_ERA} de
        join {CONCEPT} c on (c.concept_id = de.drug_concept_id)
        where concept_name not like '%%vaccine%%'
        group by drug_concept_id
        order by num_pts desc) d

        where num_pts > {min_num_pts}
        limit 20;'''.format(DRUG_ERA=DRUG_ERA, CONCEPT=CONCEPT, min_num_pts=min_num_pts)
cur.execute(SQL)
results = cur.fetchall()

for concept_id, drugname, num_pts in results:
    concept_id = int(concept_id)
    drugname = drugname.lower()
    drug2name[concept_id] = drugname
    drugname2concept_id[drugname] = concept_id
print len(drug2name), "drugs selected"

# Get demographic information for patients on top drugs
print "Getting demographic information for patients on top drugs:",
pt2sex = dict()
pt2race = dict()
pt2bday = dict()

SQL = '''
select distinct person_source_value, gender_source_value, race_source_value,
convert(concat(cast(year_of_birth as CHAR), '-', cast(month_of_birth as CHAR), '-', cast(day_of_birth as CHAR)), date) as bday
from {DRUG_ERA} de
join {PERSON} p using (person_id)
where drug_concept_id in {selected_drugs}
and gender_source_value in ('M','F')
and datediff(drug_era_start_date, convert(concat(cast(year_of_birth as CHAR), '-', cast(month_of_birth as CHAR), '-', cast(day_of_birth as CHAR)), date))/365.25 >= 18
and datediff(drug_era_start_date, convert(concat(cast(year_of_birth as CHAR), '-', cast(month_of_birth as CHAR), '-', cast(day_of_birth as CHAR)), date))/365.25 <= 89;'''.format( DRUG_ERA=DRUG_ERA, PERSON=PERSON, selected_drugs=str(tuple(drug2name.keys())) )
print ""
print SQL
print ""
cur.execute(SQL)
results = cur.fetchall()


for person_id, sex, race, bday in results:
    pt2sex[person_id] = sex
    if race not in ('W', 'B'):
        race = 'O'
    pt2race[person_id] = race
    pt2bday[person_id] = bday

print len(pt2sex), "patients found"

'''
print "filtering for patients in DILI cohort...",
pt2sex = [pt for pt in pt2sex if int(pt[0]) in dili_pts]
for k, v in tqdm(pt2sex.iteritems()):
    if int(k) in dili_pts:
        pt2sex_new[k] = v
print " found {0}".format(len(pt2sex))
'''

# Get all Rx for all patients on top drugs
print "Getting prescriptions for patients on top drugs (this may take a while)"
pt2era = defaultdict(dict)

for drug_concept_id in tqdm(drug2name.keys()):
    SQL = '''
select person_id, drug_era_start_date, drug_era_end_date
from {DRUG_ERA} de
join {PERSON} p using (person_id)
where drug_concept_id = {drug_concept_id}
and gender_source_value in ('M','F')
and datediff(drug_era_start_date, convert(concat(cast(year_of_birth as CHAR), '-', cast(month_of_birth as CHAR), '-', cast(day_of_birth as CHAR)), date))/365.25 >= 18
and datediff(drug_era_start_date, convert(concat(cast(year_of_birth as CHAR), '-', cast(month_of_birth as CHAR), '-', cast(day_of_birth as CHAR)), date))/365.25 <= 89;'''.format( DRUG_ERA=DRUG_ERA, PERSON=PERSON, drug_concept_id=drug_concept_id)
    #print ""
    #print SQL
    #print ""

    num_results = cur.execute(SQL)

    for i in range(num_results):
        person_id, start_date, end_date = cur.fetchone()

        if drug_concept_id not in pt2era[person_id]:
            pt2era[person_id][drug_concept_id] = []

        pt2era[person_id][drug_concept_id].append((start_date, end_date))

print len(pt2era), "patients on selected drugs"

# Confirm drug exposures aren't completely encapsulated by another exposure to same drug
print "Removing redundant drug exposures"
for person_id in tqdm(pt2era.keys()):
    for drug_concept_id in pt2era[person_id]:
        if len(pt2era[person_id][drug_concept_id]) > 1:
            prev_start = ''
            prev_end = ''

            for entry in sorted(pt2era[person_id][drug_concept_id]):
                if prev_start != '' and entry[0] > prev_start and entry[1] <= prev_end:
                    pt2era[person_id][drug_concept_id].remove(entry)

                prev_start = entry[0]
                prev_end = entry[1]

# Get the lab test necessary to study the ADVERSE_EVENT_OF_INTEREST
loinc_code = ae2loinc[ADVERSE_EVENT_OF_INTEREST]
limit_value_low = int(loinc2limitval[loinc_code][0])
limit_value_high = int(loinc2limitval[loinc_code][1])

print "Getting all lab tests results"
pt2labtest = defaultdict(list)

# Get all lab tests for this specific adverse event
SQL = '''select p.person_id, date(measurement_date), value_as_number, gender_source_value
    from {MEASUREMENT} m
    join {PERSON} p on (m.person_id = p.person_id)
    join {CONCEPT} c on (c.concept_id = m.measurement_concept_id)
    where c.concept_code = '{loinc_code}'
    and (value_as_number >= {limit_value_low} and value_as_number <= {limit_value_high})
    and p.person_id in (select distinct p.person_id
				from {PERSON}
				join {DRUG_ERA} using (person_id));'''.format(MEASUREMENT=MEASUREMENT, PERSON=PERSON, CONCEPT=CONCEPT, loinc_code=loinc_code, limit_value_low=limit_value_low, limit_value_high=limit_value_high, DRUG_ERA=DRUG_ERA)
print ""
print SQL
print ""

num_results = cur.execute(SQL)
results = cur.fetchall()

for person_id,testdate,testresult,sex in tqdm(results):
    if sex in ['M','F']:
        pt2labtest[person_id].append((testdate,int(testresult)))

#pt2labtest[patient_id]=sorted(pt2labtest[patient_id])

print len(pt2labtest), "patients with lab results"

# Group lab tests into eras
print "Grouping lab tests into eras"
pt2labtest_era = dict()

for pt in tqdm(pt2labtest.keys()):
    if pt == 0 or len(pt2labtest[pt]) == 1:
        continue

    pt2labtest_era[pt] = defaultdict(list)

    buffer_date = pt2labtest[pt][0][0]
    era_num = 1
    for (testdate,testresult) in pt2labtest[pt]:
        if (testdate-buffer_date).days <= 36:
            pt2labtest_era[pt][era_num].append((testdate,testresult))
            buffer_date = testdate
        else:
            buffer_date = testdate
            era_num += 1
            pt2labtest_era[pt][era_num] = [(testdate,testresult)]

# Calculate baseline for each patient (global median)
print "Calculating baseline %s labtest interval for each patient" %loinc_code
pt2baseline = dict()

pts = pt2sex.keys()
pts = [int(x) for x in pts]

for pt, era in tqdm(pt2labtest_era.iteritems()):
    if pt not in pts:
        continue

    labtest_arr = []
    for (testdate,testresult) in pt2labtest[pt]:
        labtest_arr.append(testresult)
    median_testresult = np.median(labtest_arr)
    pt2baseline[pt] = median_testresult

print len(pt2baseline), "baselines calculated"

# Get max(testdate,testresult) per era (including era of length 1)
print "Collecting max_testresult per %s labtest era" %loinc_code
pt2max_test_era = defaultdict(dict)


for pt, era in tqdm(pt2labtest_era.iteritems()):
    if pt not in pts:
        continue

    for era_num in era:
        if len(era[era_num]) == 1:
            (testdate,testresult) = era[era_num][0]
            pt2max_test_era[pt][era_num] = (testdate,testresult)
        else:
            max_testresult = 0
            max_testdate = ''
            for (testdate,testresult) in era[era_num]:
                if testresult > max_testresult:
                    max_testresult = testresult
                    max_testdate = testdate
            pt2max_test_era[pt][era_num] = (max_testdate,max_testresult)

# Collect drug exposures leading up to max(testdate,testresult)
print "Collecting drug exposures leading up to max_testresult date in test era"
pt2testdb = dict()

for pt in tqdm(pt2max_test_era):
    pt2testdb[pt] = defaultdict(list)

    pre_test = pt2baseline[pt]

    for era_num in sorted(pt2max_test_era[pt].keys()):
        (post_test_date, post_test) = pt2max_test_era[pt][era_num]

        # Find drug exposures leading up to ECG date
        # drug_start_date-----post_ECG-------drug_end_date
        # drug_start_date---drug_end_date---36d---post_ECG
        for drug_concept_id in pt2era[pt]:
            for (drug_start_date, drug_end_date) in pt2era[pt][drug_concept_id]:
                if (post_test_date >= drug_start_date) and (post_test_date-drug_end_date).days <= 36:
                    pt2testdb[pt][era_num,post_test_date,pre_test,post_test].append( (drug_concept_id,drug_start_date,drug_end_date))

## JDR: THIS IS FINE TO KEEP, ALTHOUGH UNNECESSARY
# Calculate median drug effect to assign swap frequency
print "Binning drugs by effect (median delta)"
drug2deltas = defaultdict(list) # all deltas for a drug
drug2change = dict() # median delta per drug

for person_id, tests in tqdm(pt2testdb.iteritems()):
    if len(tests) == 0:
        continue
    for pt_era_orig,post_test_date,pre_test,post_test in tests:
        for (drug_concept_id, drug_start_date,drug_end_date) in tests[pt_era_orig,post_test_date,pre_test,post_test]:
            drug2deltas[drug_concept_id].append(post_test-pre_test)

drug_changes = []
for drug_concept_id in sorted(drug2deltas.keys()):
    drug2change[drug_concept_id] = np.median(drug2deltas[drug_concept_id])
    drug_changes.append(np.median(drug2deltas[drug_concept_id]))

# Bin drugs by effect (median deltaQTc)
num_bins = 10
bins = np.linspace(min(drug_changes), max(drug_changes), num_bins)
bin_ind = np.digitize(drug_changes, bins)

bin2drugs = defaultdict(list)
drug2bin = dict()

for bin_ind_, drug in zip(bin_ind,sorted(drug2change.keys())):
    bin2drugs[bin_ind_].append(drug)
    drug2bin[drug] = bin_ind_
    #print "%2d" %bin_ind_, '\t', "%15s" %drug2name[drug][0:15],'\t', "%.1f" %drug2change[drug],'\t', len(drug2deltas[drug])

# JDR: WE SHOULD COMPLETELY DISREGARD ALL SWAPPING PROCEDURES
'''
# Calculate swap frequency such that drugs with a greater effect get swapped less frequently
print "Calculating swap frequencies"
keys = [10-i for i in range(10)]
vals = np.logspace(np.log10(0.001/100), np.log10(1./100), 10)
bin2swap_freq = dict(zip(keys,vals))
# print bin2swap_freq

# Calculate number of swapped labtest eras per drug
drug2num_swap = dict()
for bin_ind_ in sorted(bin2drugs.keys()):
    #print bin_ind_,'-> %s%%' %str(bin2swap_freq[bin_ind_]*100)
    for drug in bin2drugs[bin_ind_]:
        drug2num_swap[drug] = int(round(bin2swap_freq[bin_ind_]*len(drug2deltas[drug])))
        #print '\t%20s' %drug2name[drug][:20], '\t', len(drug2deltas[drug]), '\t%d' %round(bin2swap_freq[bin_ind_]*len(drug2deltas[drug]))

# Define eras to swap
print "Defining candidate labtest eras for drug swap"
pt_list_swap = [pt for pt in pt2testdb.keys() if len(pt2testdb[pt]) != 0]
'''

eras_to_remove = dict()
eras_to_add = dict()

# JDR: THIS IS MORE SWAPPING STUFF
'''
for swap_drug in tqdm(drug2num_swap.keys()):
    random.shuffle(pt_list_swap)
    num_swap = drug2num_swap[swap_drug]

    pt_w_drug_to_remove = set() # (person_id, pt_era_orig) containing given drug: candidates for removing exposure
    pt_wo_drug_to_add   = set() # (person_id, pt_era_orig) not containing given drug: candidates for adding exposure

    # Collect list of pt_eras that contain/ don't contain drug
    for person_id in pt_list_swap:
        for pt_era_orig,post_test_date,pre_test,post_test in pt2testdb[person_id]:
            for (drug_concept_id, drug_start_date,drug_end_date) in pt2testdb[person_id][pt_era_orig,post_test_date,pre_test,post_test]:
                if drug_concept_id == swap_drug:
                    pt_w_drug_to_remove.add((person_id, pt_era_orig))
            # Same drug can be present multiple times in same era;
            # collect all instances in set first then if not found, assign as removal candidate
            if (person_id, pt_era_orig) not in pt_w_drug_to_remove:
                pt_wo_drug_to_add.add((person_id, pt_era_orig))

    # Confirm add/ remove sets are distinct
    if len( pt_w_drug_to_remove & pt_wo_drug_to_add ) > 1:
        print "Overlap found for",drug2name[swap_drug], person_id, pt_era_orig

    # Randomly choose `num_swap` eras to swap without replacement
    pt_w_drug_to_remove_arr = np.array(list(pt_w_drug_to_remove))
    idx = np.random.choice(len(pt_w_drug_to_remove_arr), size=num_swap, replace=False) # http://stackoverflow.com/a/23446047
    eras_to_remove[swap_drug] = list(map(tuple, pt_w_drug_to_remove_arr[idx])) # http://stackoverflow.com/a/10016379

    pt_wo_drug_to_add_arr = np.array(list( pt_wo_drug_to_add ))
    idx = np.random.choice(len(pt_wo_drug_to_add_arr), size=num_swap, replace=False)
    eras_to_add[swap_drug] = list(map(tuple, pt_wo_drug_to_add_arr[idx]))

# Build swapped QTDb dictionary
print "Swapping drugs"
pt2testdb_swap = dict()

for person_id in tqdm(pt2testdb.keys()):
    pt2testdb_swap[person_id] = defaultdict(list)
    for pt_era_orig,post_test_date,pre_test,post_test in pt2testdb[person_id]:
        for (drug_concept_id, drug_start_date,drug_end_date) in pt2testdb[person_id][pt_era_orig,post_test_date,pre_test,post_test]:
            # Check if drug should be removed from era
            if (person_id, pt_era_orig) in eras_to_remove[drug_concept_id]:
                continue
            # Otherwise add as normal
            else:
                pt2testdb_swap[person_id][pt_era_orig,post_test_date,pre_test,post_test].append((drug_concept_id, drug_start_date,drug_end_date))

        # Check if era should add any drugs
        for drug in eras_to_add.keys():
            if (person_id, pt_era_orig) in eras_to_add[drug]:
                pt2testdb_swap[person_id][pt_era_orig,post_test_date,pre_test,post_test].append((drug, "swap","swap"))
'''

# Function for randomly adjusting age +/- 0-5 years
def shuffle_age(test_date,bday,prev_age=None):
    age = int((test_date-bday).days/365.25)

    operators = [operator.add, operator.sub]
    random_operator = random.choice(operators)

    age_shift = random.randint(0,5)

    shuffled_age = random_operator(age, age_shift)

    if shuffled_age < 18:
        shuffled_age = 18
    if shuffled_age > 89:
        shuffled_age = 89

    if prev_age is not None:
        if shuffled_age < prev_age:
            shuffled_age = prev_age

    return shuffled_age

# Save drugs to csv
print "Done! Saving %s database to csv" %loinc_code
outf = open('%s_db_Drug.csv'%loinc_code, 'w')
writer = csv.writer(outf)
writer.writerow(['drug_concept_id', 'drug'])
for drugname in sorted(drugname2concept_id.keys()):
    concept_id = drugname2concept_id[drugname]
    writer.writerow([concept_id, drugname])
outf.close()

# Save Db to csv
outf_dem = open('%s_db_Patient.csv'%loinc_code,'w')
writer_dem = csv.writer(outf_dem)
writer_dem.writerow(['pt_id_era', 'pt_id', 'era', 'age', 'sex', 'race', 'num_drugs', 'pre_test', 'post_test', 'delta_test'])

outf_drug = open('%s_db_Patient2Drug.csv'%loinc_code,'w')
writer_drug = csv.writer(outf_drug)
writer_drug.writerow(['pt_id_era', 'drug_concept_id'])

outf_anon = open('%s_db.csv'%loinc_code,'w')
writer_anon = csv.writer(outf_anon)
writer_anon.writerow(['pt_id_era', 'pt_id', 'era', 'age', 'sex', 'race', 'num_drugs', 'drug_concept_id', 'drug_name', 'pre_test_high', 'post_test_high', 'delta_test'])

#pt_list = [pt for pt in pt2testdb_swap.keys() if len(pt2testdb_swap[pt]) != 0]
pt_list = [pt for pt in pt2testdb.keys() if len(pt2testdb[pt]) != 0]


for i, person_id in tqdm(enumerate(pt_list), total=len(pt_list)):
    pt_era = 0
    for pt_era_orig, post_test_date, pre_test, post_test in pt2testdb[person_id]:
        pt_era += 1
        pt_age = pt2bday[str(person_id)]
        drug_set = set()
        for (drug_concept_id, drug_start_date, drug_end_date) in pt2testdb[person_id][pt_era_orig,post_test_date,pre_test,post_test]:
            drug_set.add(drug_concept_id)
        num_drugs = len(drug_set)

        writer_dem.writerow(['%d_%d'%(person_id,pt_era),
                             person_id,
                             pt_era,
                             pt_age,
                             pt2sex[str(person_id)],
                             pt2race[str(person_id)],
                             num_drugs,
                             pre_test,
                             post_test,
                             pre_test-post_test])

        for drug_concept_id in drug_set:
            writer_drug.writerow(['%d_%d'%(person_id,pt_era),
                                  drug_concept_id])
            writer_anon.writerow(['%d_%d'%(person_id,pt_era),
                                  person_id,
                                  pt_era,
                                  pt_age,
                                  pt2sex[str(person_id)],
                                  pt2race[str(person_id)],
                                  num_drugs,
                                  drug_concept_id,
                                  drug2name[drug_concept_id],
                                  pre_test,
                                  post_test,
                                  post_test-pre_test])
                                  
                    

# #random.shuffle(pt_list)
# for i,person_id in tqdm(enumerate(pt_list), total=len(pt_list)):
#     pt_era = 0
#     #prev_age = None
#     for pt_era_orig,post_test_date,pre_test,post_test in pt2testdb[person_id]:
#         pt_era += 1
#         #pt_age = shuffle_age(post_test_date, pt2bday[person_id], prev_age)
#         pt_age = pt2bday[str(person_id)]

#         #prev_age = pt_age

#         drug_set = set()
#         for (drug_concept_id, drug_start_date,drug_end_date) in pt2testdb[person_id][pt_era_orig,post_test_date,pre_test,post_test]:
#             drug_set.add(drug_concept_id)

#         num_drugs = len(drug_set)

#         # pre_test_high = 0
#         # post_test_high = 0
#         # if pre_test >= range_high:
#         #     pre_test_high = 1
#         # if post_test >= range_high:
#         #     post_test_high = 1

#         writer_dem.writerow(['%d_%d' %(i+1,pt_era), i+1, pt_era, pt_age, pt2sex[person_id], pt2race[person_id], num_drugs, pre_test_high, post_test_high, post_test-pre_test])

#         for drug_concept_id in drug_set:
#             writer_drug.writerow(['%d_%d' %(i+1,pt_era), drug_concept_id])

#             writer_anon.writerow(['%d_%d' %(i+1,pt_era), i+1, pt_era, pt_age, pt2sex[person_id], pt2race[person_id], num_drugs,
#                                   drug_concept_id, drug2name[drug_concept_id],
#                                   pre_test_high, post_test_high, post_test-pre_test])
        

outf_dem.close()
outf_drug.close()
outf_anon.close()

cur.close()
con.close()
