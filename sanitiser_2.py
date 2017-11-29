import os
import re
from extractor import extract

value_keys = ['VALUE',
              'LOW_VALUE',
              'HIGH_VALUE',
              'VAT_PRCT']
paths_single = (
    (['CODED_DATA', 'CODIF_DATA'], ['AA_AUTHORITY_TYPE',
                                    'AC_AWARD_CRIT',
                                    'NC_CONTRACT_NATURE',
                                    'PR_PROC',
                                    'RP_REGULATION',
                                    'TD_DOCUMENT_TYPE',
                                    'TY_TYPE_BID']),
    (['CODED_DATA', 'NOTICE_DATA'], ['IA_URL_GENERAL',
                                     'ISO_COUNTRY',
                                     'NO_DOC_OJS']),
    (['CODED_DATA', 'NOTICE_DATA', 'VALUES_LIST', 'GLOBAL_VALUE'], value_keys),
    (['CONTRACT'],  ['OTH_NOT',
                     'CONTRACTING_AUTHORITY']),
    (['CONTRACT', 'CONTRACT_OBJECT'], ['CONCLUSION_FRAMEWORK_AGREEMENT',
                                       'CONTRACTS_DPS',
                                       'CONTRACT_COVERED_GPA',
                                       'CPV_MAIN']),
    (['CONTRACT', 'CONTRACT_OBJECT', 'CONTRACT_VALUE', 'COST'], value_keys),
    (['CONTRACT', 'CONTRACT_OBJECT', 'CONTRACT_VALUE', 'ESTIMATE'], value_keys)
)


def flat(funct, value, key, empty):
    if isinstance(funct(value, key, empty), list) & \
            len(funct(value, key, empty)) == 1:
        value[key] = value[key][0]

def reduce(funct, iterable, key, initialiser=None, empty=dict()):

    it = iter(iterable)
    if initialiser is None:
        value = next(it)
    else:
        value = initialiser
    for element in it:

        value = funct(value, element, empty)

    if isinstance(funct(value, key, empty), list) & \
            len(funct(value, key, empty)) == 1:
        value[key] = value[key][0]

    return


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


for path, keys in paths_single:
    for key in keys:
        reduce(dict.get, path, key, data)


def sanitise(doc):
    """
    Main function to sanitise data from document object
    :param doc: dictionary with main sections:
        - DOC_ID
        - YEAR
        - MONTH
        - XML_FILE
        - CODED_DATA
            - NOTICE_DATA
            - CODIF_DATA
        - CONTRACT
            - CONTRACTING_AUTHORITY
            - CONTRACT_OBJECT
            - AWARDS_OF_CONTRACT
    """



    # Step 2: Sanitise CODED_DATA
    assert doc['CODED_DATA']
    coded = doc['CODED_DATA']

    # Step 2.1: Sanitise NOTICE_DATA
    assert coded['NOTICE_DATA']
    notice = coded['NOTICE_DATA']

    # Step 2.1.1: Sanitise fields with compulsory single value
    for item in ['NO_DOC_OJS', 'ISO_COUNTRY']:
        check_compulsory(notice, item)

    # Step 2.1.2: Sanitise fields with optional lists values
    for item in ['ORIGINAL_CPV', 'ORIGINAL_NUTS', 'REF_NOTICE']:
        check_optional_list(notice, item)

    # Step 2.1.3: Sanitise fields with optional single value
    check_optional_one(notice, 'IA_URL_GENERAL')

    # Step 2.1.4: Sanitise NOTICE_DATA VALUES_LIST field
    check_notice_value(notice)

    # Step 2.2: Sanitise CODIF_DATA
    assert coded['CODIF_DATA']
    codif = coded['CODIF_DATA']

    # Step 2.2.1: Sanitise fields with compulsory single value
    for item in ['TD_DOCUMENT_TYPE', 'AA_AUTHORITY_TYPE', 'NC_CONTRACT_NATURE',
                 'PR_PROC', 'RP_REGULATION', 'TY_TYPE_BID', 'AC_AWARD_CRIT']:
        check_compulsory(codif, item)

    # Step 2.2.2: Sanitise fields with optional single value
    check_optional_list(codif, 'MA_MAIN_ACTIVITIES')

    # Step 3: Sanitise CONTRACT
    assert doc['CONTRACT']
    contract = doc['CONTRACT']

    # Step 3.1: Sanitise 'OTH_NOT' compulsory single value
    check_compulsory(contract, 'OTH_NOT')

    if contract['OTH_NOT'] == 'YES':
        # Early return
        return

    # Step 3.2: Sanitise CONTRACTING_AUTHORITY
    check_compulsory(contract, 'CONTRACTING_AUTHORITY')

    # Step 3.3: Sanitise CONTRACT_OBJECT
    assert contract['CONTRACT_OBJECT']
    contract_object = contract['CONTRACT_OBJECT']

    # Step 3.3.1: Sanitise fields with optional single value
    for item in ['CPV_MAIN', 'CONTRACTS_DPS', 'CONTRACT_COVERED_GPA',
                 'CONCLUSION_FRAMEWORK_AGREEMENT']:
        check_optional_one(contract_object, item)

    # Step 3.3.2: Sanitise fields with optional list value
    check_optional_list(contract_object, 'NUTS')
    check_optional_list(contract_object, 'NUTS_EXTRA')

    # Step 3.3.3: Compose NUTS_EXTRA as single string
    if 'NUTS_EXTRA' in contract_object:
        contract_object['NUTS_EXTRA'] = ' '.join(contract_object['NUTS_EXTRA'])

    # Step 3.3.4: Sanitise CONTRACT_OBJECT VALUE
    if 'CONTRACT_VALUE' in contract_object:
        check_contract_value(contract_object)

    # Step 3.4: Sanitise AWARDS_OF_CONTRACT
    assert contract['AWARDS_OF_CONTRACT']
    awards = contract['AWARDS_OF_CONTRACT']

    for award in awards:

        # Step 3.4.1: Sanitise CONTRACTOR
        if 'CONTRACTOR' in award:
            for item in ['ADDRESS', 'COUNTRY', 'OFFICIALNAME', 'POSTAL_CODE',
                         'TOWN']:
                check_optional_one(award['CONTRACTOR'], item)

        # Step 3.4.2: Sanitise VALUE
        if 'CONTRACT_VALUE' in award:
            check_contract_value(award)

    return


if __name__ == "__main__":

    os.chdir('/Volumes/WD/S8')
    years = ['2013']

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
                collection.append(data)