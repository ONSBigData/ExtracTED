import os
import re
from json import dumps, loads
import xmltodict
import pandas as pd

#### Auxilliary functions


def retrieve(xml, *args):
    if isinstance(xml, dict):
        val = xml.get(args[0], None)
        if val:
            yield from retrieve(val, *args[1:])
    elif isinstance(xml, list):
        for el in xml:
            yield from retrieve(el, *args)
    else:
        yield xml


def get_value(xml, *args):
    value = list(retrieve(xml, *args))
    if len(value) == 0:
        return None
    elif len(value) == 1:
        return value[0]
    else:
        return value

########################


def get_root(xml):
    """
    Get Root Information
    :param xml:
    :return: dictionary:
        - DOC_ID: Unique document number in TED. Format: nnnnnn-yyyy
    """

    doc_id = xml['@DOC_ID']

    return {'DOC_ID': doc_id}


def get_codif(xml):
    """
    Get CODIF_DATA Information: descriptive metadata related to the notice content
    :param xml:
    :return: dictionary:
        - TD_DOCUMENT_TYPE: Type of awarding authority
        - AA_AUTHORITY_TYPE: Type of document
        - NC_CONTRACT_NATURE: Nature of contract
        - PR_PROC: Type of procedure
        - RP_REGULATION: The regulation that applies to the procedure
        - TY_TYPE_BID: Type of bid
        - AC_AWARD_CRIT: Type of awarding criteria
        - MA_MAIN_ACTIVITIES: Main activity of the contracting body
        - DIRECTIVE: The Directive that applies to the notice
    """

    return {
        'TD_DOCUMENT_TYPE': get_value(xml, 'TD_DOCUMENT_TYPE', '@CODE'),
        'AA_AUTHORITY_TYPE': get_value(xml, 'AA_AUTHORITY_TYPE', '@CODE'),
        'NC_CONTRACT_NATURE': get_value(xml, 'NC_CONTRACT_NATURE', '@CODE'),
        'PR_PROC': get_value(xml, 'PR_PROC', '@CODE'),
        'RP_REGULATION': get_value(xml, 'RP_REGULATION', '@CODE'),
        'TY_TYPE_BID': get_value(xml, 'TY_TYPE_BID', '@CODE'),
        'AC_AWARD_CRIT': get_value(xml, 'AC_AWARD_CRIT', '@CODE'),
        'MA_MAIN_ACTIVITIES': get_value(xml, 'MA_MAIN_ACTIVITIES', '@CODE'),
        'DIRECTIVE': get_value(xml, 'DIRECTIVE', '@VALUE')
    }


def get_notice(xml):
    """
    Get NOTICE_DATA Information: some general information related to the notice,
    or information which is extracted from the notice
    :param xml:
    :return: dictionary:
        - NO_DOC_OJS: Notice number in TED
        - ORIGINAL_NUTS: Region code(s) of the place of performance or delivery
                         A 2-5 digits code of the “Nomenclature of Territorial Units for Statistics”
        - CURRENT_NUTS: n/a
        - ORIGINAL_CPV: Product or service 8 digits code(s) of the Common Procurement Vocabulary
        - CURRENT_CPV: n/a
        - ISO_COUNTRY: 2-characters ISO code of the country where the contracting body is located
        - VALUES_LIST: Estimated total value(s) or total final value(s) of the procurement
        - IA_URL_GENERAL: Main internet address (URL) of the contracting body
        - REF_NOTICE: Reference notice number in TED.
                      Referencing a previous publication (prior information, corrigendum, ...)
    """
    return {
        'NO_DOC_OJS': get_value(xml, 'NO_DOC_OJS'),
        'ORIGINAL_NUTS': get_value(xml, 'ORIGINAL_NUTS', '@CODE'),
        'CURRENT_NUTS': get_value(xml, 'CURRENT_NUTS', '@CODE'),
        'ORIGINAL_CPV': get_value(xml, 'ORIGINAL_CPV', '@CODE'),
        'CURRENT_CPV': get_value(xml, 'CURRENT_CPV', '@CODE'),
        'ISO_COUNTRY': get_value(xml, 'ISO_COUNTRY', '@VALUE'),
        'VALUES_LIST': get_value(xml, 'VALUES_LIST', '@VALUE'),
        'IA_URL_GENERAL': get_value(xml, 'IA_URL_GENERAL'),
        'REF_NOTICE': get_value(xml, 'REF_NOTICE', 'NO_DOC_OJS')
    }


def get_coded(xml):
    """
    Get CODED_DATA_SECTION Information
    :param xml:
    :return: dictionary
    """

    coded_data = dict()

    coded_data.update(get_codif(xml['CODIF_DATA']))
    coded_data.update(get_notice(xml['NOTICE_DATA']))

    return coded_data


def get_contract(xml):
    """
    Extract the contract, preferably the English version else French
    :param xml:
    :return: contract
    """

    forms = (*xml.values(),)[0]

    if isinstance(forms, list):
        langs = []
        for form in forms:
            langs.append(form['@LG'])

        for lang in ['EN', 'FR', 'DE']:  # if English not available, pick French, then German
            try:
                i = langs.index(lang)
                contract = forms[i]
                break
            except ValueError:
                continue
    else:
        contract = forms

    r = re.compile('^FD_')
    key = str(*filter(r.match, contract.keys()))

    return key, contract[key]


def extract(path):

    with open(path) as fd:
        doc = xmltodict.parse(fd.read())

    main = doc['TED_EXPORT']

    doc_id = main['@DOC_ID']
    coded_data = get_coded(main['CODED_DATA_SECTION'])

    contract = get_contract(main['FORM_SECTION'])

    return coded_data


def get_keys(path):
    with open(path) as fd:
        doc = xmltodict.parse(fd.read())

    key, contract = get_contract(doc['TED_EXPORT']['FORM_SECTION'])
    return key, len(contract.keys())


if __name__ == "__main__":

    # Folder containing xml files
    DIR = os.path.join(os.getcwd(), "2015-12")
    # List xml files
    files = os.listdir(DIR)

    keys = []
    collection = []
    for f in files:
        # Extract data from xml file
        #data = extract(os.path.join(DIR, f))
        #collection.append(data)
        keys.append((get_keys(os.path.join(DIR, f))))

    df = pd.DataFrame(collection)
    set(df.contract)


