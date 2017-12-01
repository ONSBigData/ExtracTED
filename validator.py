import os
import re
import pandas as pd
from extractor import extract
from voluptuous import (Schema, Required, All, Optional, Length, Any,
                        MultipleInvalid, Match, Coerce)

# Lookups
iso_country = pd.read_csv('./Lookups/ISO_COUNTRY.csv', dtype='str',
                          encoding='latin', keep_default_na=False)
cpv = pd.read_csv('./Lookups/CPV.csv', dtype='str')
ma = pd.read_csv('./Lookups/MA_MAIN_ACTIVITY.csv', dtype='str')
td = pd.read_csv('./Lookups/TD_DOCUMENT_TYPE.csv', dtype='str')
nc = pd.read_csv('./Lookups/NC_CONTRACT_NATURE.csv', dtype='str')
aa = pd.read_csv('./Lookups/AA_AUTHORITY_TYPE.csv', dtype='str')
pr = pd.read_csv('./Lookups/PR_PROC.csv', dtype='str')
ty = pd.read_csv('./Lookups/TY_TYPE_BID.csv', dtype='str')
ac = pd.read_csv('./Lookups/AC_AWARD_CRIT.csv', dtype='str')
rp = pd.read_csv('./Lookups/RP_REGULATION.csv', dtype='str')

# Allowed Currencies
currencies = ['EUR', 'BGN', 'CHF', 'USD', 'HRK', 'CZK', 'DKK', 'HUF', 'SEK',
              'NOK', 'LTL', 'TRY', 'PLN', 'MKD', 'RON', 'JPY', 'ISK', 'SKK',
              'LVL', 'GBP', 'MTL', 'CYP', 'EEK']


def number(s):
    n = re.sub(r'\s', '', s.replace(',', '.').replace('%', ''))
    return float(n)


def concatenate(lst):
    return ' '.join(lst)


def flat(lst):
    return lst[0]

# Sub Schemas
value = Schema({
    Optional('CURRENCY'): All(str, Any(*currencies)),
    Optional(str): Any([], All(Coerce(flat), Coerce(number)),
                       All(Coerce(flat), str))  # Let it pass
})


contract_value = Schema({
    Optional(str): value,
    Optional('NUMBER_OF_YEARS'): Any([], All(Coerce(flat), Coerce(number)),
                                     All(Coerce(flat), str)),  # Let it pass
    Optional('NUMBER_OF_MONTHS'): Any([], All(Coerce(flat), Coerce(number)),
                                      All(Coerce(flat), str))  # Let it pass
})


contractor = Schema({
    Optional(str): Any([], All(Coerce(flat), str)),
    Optional('COUNTRY'): Any([], All(Coerce(flat), str, Length(2),
                                     Any(*iso_country.Code)))
})

match_nuts = Match('^(' + '|'.join(iso_country.Code) + ')')

match_cpv = Match('^(' + '|'.join(cpv.CODE) + ')')


# Document Schema
schema = Schema({
    Required('DOC_ID'): str,
    Required('CODED_DATA'): {
        Required('NOTICE_DATA'): {
            Required('NO_DOC_OJS'): All(Coerce(flat), str),
            Required('ORIGINAL_NUTS'): [All(str, match_nuts)],
            Required('ORIGINAL_CPV'): [All(str, match_cpv)],
            Required('ISO_COUNTRY'): All(Coerce(flat), str, Length(2),
                                         Any(*iso_country.Code)),
            Required('IA_URL_GENERAL'): Any([], All(Coerce(flat), str)),
            Required('REF_NOTICE'): [str],
            Required('VALUES_LIST'): {
                Optional('GLOBAL_VALUE'): value,
                Optional('CONTRACTS_VALUE'): [value]
            }
        },
        Required('CODIF_DATA'): {
            Required('DS_DATE_DISPATCH'): All(Coerce(flat), str),
            Required('TD_DOCUMENT_TYPE'): All(Coerce(flat), str,
                                              Any(*td.CODE)),
            Required('AA_AUTHORITY_TYPE'): All(Coerce(flat), str,
                                               Any(*aa.CODE)),
            Required('NC_CONTRACT_NATURE'): All(Coerce(flat), str,
                                                Any(*nc.CODE)),
            Required('PR_PROC'): All(Coerce(flat), str, Any(*pr.CODE)),
            Required('RP_REGULATION'): All(Coerce(flat), str, Any(*rp.CODE)),
            Required('TY_TYPE_BID'): All(Coerce(flat), str, Any(*ty.CODE)),
            Required('AC_AWARD_CRIT'): All(Coerce(flat), str, Any(*ac.CODE)),
            Required('MA_MAIN_ACTIVITIES'): [All(str, Any(*ma.CODE))]
        }
    },
    Required('CONTRACT'): {
        Required('OTH_NOT'): All(Coerce(flat), str, Any('YES', 'NO')),
        Optional('CONTRACTING_AUTHORITY'): All(Coerce(flat), str),
        Optional('CONTRACT_OBJECT'): {
            Optional('NUTS'): [All(str, match_nuts)],
            Optional('NUTS_EXTRA'): All(Coerce(concatenate), str),
            Optional('CPV_MAIN'): Any([], All(Coerce(flat), str, match_cpv)),
            Optional('CONTRACT_VALUE'): contract_value,
            Optional(str): Any([], All(Coerce(flat), str, Any('YES', 'NO'))),
        },
        Optional('AWARDS_OF_CONTRACT'): [{
            Optional('CONTRACTOR'): contractor,
            Optional('CONTRACT_VALUE'): contract_value,
        }]
    }
})


def prune(node):
    if isinstance(node, list):
        for n in node:
            prune(n)
    elif isinstance(node, dict):
        for k in list(node.keys()):
            if node[k]:
                prune(node[k])
            else:
                del node[k]

if __name__ == "__main__":

    Y = '2013'
    M = '01'

    years = ['2013', '2014', '2015', '2016']
    months = ['01', '02', '03', '04', '05', '06', '07', '08',
              '09', '10', '11', '12']

    collection = []
    for Y in years:
        print(Y)
        for M in months:
            print(M)
            # Folder containing xml files
            DIR = os.path.join('/Volumes/WD/S8', Y + '-' + M)
            # List xml files
            files = os.listdir(DIR)
            for f in files:
                # Extract data from xml file
                file_path = os.path.join(DIR, f)
                data = extract(file_path)
                try:
                    data = schema(data)
                except MultipleInvalid as e:
                    print(str(e) + ' ---- file: ' + file_path)

                prune(data)
                collection.append(data)
