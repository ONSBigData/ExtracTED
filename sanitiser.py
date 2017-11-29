import os
import re
from extract_s8 import extract


def check_compulsory(obj, key):

    assert obj[key]
    if isinstance(obj[key], list):
        obj[key] = obj[key][0]


def check_optional_list(obj, key):

    assert isinstance(obj[key], list)
    if not obj[key]:
        obj.pop(key)


def check_optional_one(obj, key):

    assert isinstance(obj[key], list)
    if obj[key]:
        obj[key] = obj[key][0]
    else:
        obj.pop(key)


def to_number(value):

    try:
        return float(
        re.sub(r'\s', '', value.replace(',', '.').replace('%', ''))
    )
    except ValueError:
        print("Problem in converting value to numbeer : %s" % value)
        return ''




def check_value(obj):

    # Check if it is SINGLE or RANGE value
    if 'VALUE' in obj:
        check_optional_one(obj, 'VALUE')

    if 'LOW_VALUE' in obj:
        check_optional_one(obj, 'LOW_VALUE')

    if 'HIGH_VALUE' in obj:
        check_optional_one(obj, 'HIGH_VALUE')

    # Check CURRENCY is there
    check_compulsory(obj, 'CURRENCY')

    # Check OPTIONAL VAT_PRCT if there
    if 'VAT_PRCT' in obj:
        check_optional_one(obj, 'VAT_PRCT')

    # Convert to float
    for item in ['VALUE', 'LOW_VALUE', 'HIGH_VALUE', 'VAT_PRCT']:
        if item in obj:
            obj[item] = to_number(obj[item])


def test_value_float(obj):
    for item in ['VALUE', 'HIGH_VALUE', 'LOW_VALUE', 'VAT_PRCT']:
        if (item in obj) & ~isinstance(obj.get(item, 'NaN'), float):
            obj.pop(item)


def test_value(obj):
    assert (
        ('CURRENCY' in obj) &
        ((('LOW_VALUE' in obj) | ('HIGH_VALUE' in obj)) | ('VALUE' in obj))
    )


def check_notice_value(obj):

    assert isinstance(obj['VALUES_LIST'], dict)

    if obj['VALUES_LIST']:
        values_list = obj['VALUES_LIST']

        if values_list.get('GLOBAL_VALUE', {}):
            check_value(values_list['GLOBAL_VALUE'])
            try:
                test_value_float(values_list['GLOBAL_VALUE'])
                test_value(values_list['GLOBAL_VALUE'])
            except AssertionError:
                values_list.pop('GLOBAL_VALUE')

        if values_list.get('CONTRACTS_VALUE', []):
            for idx, contract_value in enumerate(values_list['CONTRACTS_VALUE']):
                check_value(contract_value)
                try:
                    test_value_float(contract_value)
                    test_value(contract_value)
                except AssertionError:
                    del values_list['CONTRACTS_VALUE'][idx]

            try:
                assert values_list['CONTRACTS_VALUE']
            except AssertionError:
                values_list.pop('CONTRACTS_VALUE')

    if not obj['VALUES_LIST']:
        obj.pop('VALUES_LIST')


def check_contract_value(obj):
    assert isinstance(obj['CONTRACT_VALUE'], dict)

    if obj['CONTRACT_VALUE']:
        values_list = obj['CONTRACT_VALUE']

        if values_list.get('COST', {}):
            check_value(values_list['COST'])
            try:
                test_value_float(values_list['COST'])
                test_value(values_list['COST'])
            except AssertionError:
                values_list.pop('COST')

        if values_list.get('ESTIMATE', {}):
            check_value(values_list['ESTIMATE'])
            try:
                test_value_float(values_list['ESTIMATE'])
                test_value(values_list['ESTIMATE'])
            except AssertionError:
                values_list.pop('ESTIMATE')

    if not obj['CONTRACT_VALUE']:
        obj.pop('CONTRACT_VALUE')


def sanitise(doc):
    """
    Main function to sanitise data from document object
    :param doc: dictionary with main sections:
        - DOC_ID
        - CODED_DATA
            - NOTICE_DATA
            - CODIF_DATA
        - CONTRACT
            - CONTRACTING_AUTHORITY
            - CONTRACT_OBJECT
            - AWARDS_OF_CONTRACT
    """

    # Step 1: Check DOC_ID
    check_compulsory(doc, 'DOC_ID')

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