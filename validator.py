import os
import pandas as pd
from extract_s8 import extract
from sanitiser import sanitise
from voluptuous import Schema, Required, All, Optional, Length, Url, Any, \
    MultipleInvalid, Match


"""
- DOC_ID
- CODED_DATA
    - NOTICE_DATA
    - CODIF_DATA
- CONTRACT
    - CONTRACTING_AUTHORITY
    - OBJECT
    - CONTRACT
"""

# Lookups
iso_country = pd.read_csv('/Volumes/WD/Lookups/ISO_COUNTRY.csv', dtype='str',
                      encoding='latin', na_values='')
cpvs = pd.read_csv('/Volumes/WD/Lookups/CPV.csv', dtype='str')
ma = pd.read_csv('/Volumes/WD/Lookups/MA_MAIN_ACTIVITY.csv', dtype='str')
td = pd.read_csv('/Volumes/WD/Lookups/TD_DOCUMENT_TYPE.csv', dtype='str')
nc = pd.read_csv('/Volumes/WD/Lookups/NC_CONTRACT_NATURE.csv', dtype='str')
aa = pd.read_csv('/Volumes/WD/Lookups/AA_AUTHORITY_TYPE.csv', dtype='str')
pr = pd.read_csv('/Volumes/WD/Lookups/PR_PROC.csv', dtype='str')
ty = pd.read_csv('/Volumes/WD/Lookups/TY_TYPE_BID.csv', dtype='str')
ac = pd.read_csv('/Volumes/WD/Lookups/AC_AWARD_CRIT.csv', dtype='str')
rp = pd.read_csv('/Volumes/WD/Lookups/RP_REGULATION.csv', dtype='str')

# Allowed Currencies
currencies = ['EUR', 'BGN', 'CHF', 'USD', 'HRK', 'CZK', 'DKK', 'HUF', 'SEK',
              'NOK', 'LTL', 'TRY', 'PLN', 'MKD', 'RON', 'JPY', 'ISK', 'SKK',
              'LVL', 'GBP', 'MTL', 'CYP', 'EEK']

# Sub Schemas
value = Schema({
    Required('CURRENCY'): All(str, Any(*currencies)),
    Optional('VALUE'): All(float),
    Optional('HIGH_VALUE'): All(float),
    Optional('LOW_VALUE'): All(float),
    Optional('VAT_PRCT'): All(float)
})

contract_value = Schema({
    Optional('COST'): All(value),
    Optional('ESTIMATE'): All(value)
})


contractor = Schema({
    Optional('OFFICIALNAME'): All(str),
    Optional('COUNTRY'): All(str, Length(2), Any(*iso_country.Code)),
    Optional('ADDRESS'): All(str),
    Optional('TOWN'): All(str),
    Optional('POSTAL_CODE'): All(str)
})

nuts = Match('^(' + '|'.join(iso_country.Code) + ')')

cpv = Match('^(' + '|'.join(cpvs.CODE) + ')')

# Document Schema
schema = Schema({
    Required('DOC_ID'): All(str),
    Required('CODED_DATA'): All({
        Required('NOTICE_DATA'): All({
            Required('NO_DOC_OJS'): All(str),
            Optional('ORIGINAL_NUTS'): All([nuts]),  # NUTS codes must begin
                                                     # with valid country code
            Optional('ORIGINAL_CPV'): All([cpv]),  # CPV codes must begin
                                                   # with valid CPV code
            Required('ISO_COUNTRY'): All(str, Length(2),
                                         Any(*iso_country.Code)),
            Optional('IA_URL_GENERAL'): All(str),
            Optional('REF_NOTICE'): All([str]),
            Optional('VALUES_LIST'): All({
                Optional('GLOBAL_VALUE'): All(value),
                Optional('CONTRACTS_VALUE'): All([value])
            })
        }),
        Required('CODIF_DATA'): All({  # need to validate codes options
            Required('TD_DOCUMENT_TYPE'): All(str, Any(*td.CODE)),
            Required('AA_AUTHORITY_TYPE'): All(str, Any(*aa.CODE)),
            Required('NC_CONTRACT_NATURE'): All(str, Any(*nc.CODE)),
            Required('PR_PROC'): All(str, Any(*pr.CODE)),
            Required('RP_REGULATION'): All(str, Any(*rp.CODE)),
            Required('TY_TYPE_BID'): All(str, Any(*ty.CODE)),
            Required('AC_AWARD_CRIT'): All(str, Any(*ac.CODE)),
            Optional('MA_MAIN_ACTIVITIES'): All([Any(*ma.CODE)])
        })
    }),
    Required('CONTRACT'): All({
        Required('OTH_NOT'): All(Any('YES', 'NO')),
        Optional('CONTRACTING_AUTHORITY'): All(str),
        Optional('CONTRACT_OBJECT'): All({
            Optional('NUTS'): All([nuts]),
            Optional('NUTS_EXTRA'): All(str),
            Optional('CPV_MAIN'): All(cpv),
            Optional('CONTRACT_COVERED_GPA'): All(str, Any('YES', 'NO')),
            Optional('CONCLUSION_FRAMEWORK_AGREEMENT'): All(
                str, Any('YES', 'NO')),
            Optional('CONTRACTS_DPS'): All(str, Any('YES', 'NO')),
            Optional('CPV_MAIN'): All(str),
            Optional('CONTRACT_VALUE'): All(contract_value)
        }),
        Optional('AWARDS_OF_CONTRACT'): All([{
            Optional('CONTRACTOR'): All(contractor),
            Optional('CONTRACT_VALUE'): All(contract_value),
        }])
    })
})

if __name__ == "__main__":

    os.chdir('/Volumes/WD/S8')
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
            DIR = os.path.join(os.getcwd(), Y + '-' + M)
            # List xml files
            files = os.listdir(DIR)
            for f in files:
                # Extract data from xml file
                file_path = os.path.join(DIR, f)
                data = extract(file_path)
                sanitise(data)
                try:
                    schema(data)
                except MultipleInvalid as e:
                    collection.append(data)
                    print(str(e) + ' ---- file: ' + file_path)
