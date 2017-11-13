import os
from lxml import etree
import pandas as pd

NMSP = {'ted': 'http://publications.europa.eu/TED_schema/Export'}


def contract_item(xml):
    obj = dict()
    if xml.xpath("name(*) = 'SINGLE_VALUE'"):
        currency, value = xml.xpath(".//ted:VALUE/@CURRENCY | .//ted:VALUE/text()",
                                      namespaces=NMSP)
        return {'CURRENCY': currency,
                'VALUE': value}
    else:
        assert (xml.xpath("name(*) = 'RANGE_VALUE'"))
        low_currency, low_value = xml.xpath(".//ted:VALUE[1]/@CURRENCY | .//ted:VALUE[1]/text()",
                                            namespaces=NMSP)
        high_currency, high_value = xml.xpath(".//ted:VALUE[2]/@CURRENCY | .//ted:VALUE[2]/text()",
                                              namespaces=NMSP)

        return {'LOW':  {'CURRENCY': low_currency,
                         'VALUE': low_value},
                'HIGH': {'CURRENCY': high_currency,
                         'VALUE': high_value}}


def get_notice(xml):
    """
    Get NOTICE_DATA Information: some general information related to the notice,
    or information which is extracted from the notice
    :param xml:
    :return: dictionary:
        - NO_DOC_OJS: Notice number in TED
        - ORIGINAL_NUTS: Region code(s) of the place of performance or delivery
                         A 2-5 digits code of the “Nomenclature of Territorial Units for Statistics”
        - ORIGINAL_CPV: Product or service 8 digits code(s) of the Common Procurement Vocabulary
        - ISO_COUNTRY: 2-characters ISO code of the country where the contracting body is located
        - VALUES_LIST: Estimated total value(s) or total final value(s) of the procurement
        - IA_URL_GENERAL: Main internet address (URL) of the contracting body
        - REF_NOTICE: Reference notice number in TED.
                      Referencing a previous publication (prior information, corrigendum, ...)
    """

    obj = dict()

    for item in ['ORIGINAL_NUTS', 'ORIGINAL_CPV']:
        obj[item] = xml.xpath("ted:*[local-name() = $name]/@CODE",
                              namespaces=NMSP,
                              name=item)

    obj['NO_DOC_OJS'] = xml.xpath("ted:NO_DOC_OJS/text()",
                        namespaces=NMSP)

    obj['ISO_COUNTRY'] = xml.xpath("ted:ISO_COUNTRY/@VALUE",
                                  namespaces=NMSP)

    obj['IA_URL_GENERAL'] = xml.xpath("ted:IA_URL_GENERAL/text()",
                                  namespaces=NMSP)

    obj['REF_NOTICE'] = xml.xpath("ted:REF_NOTICE/ted:NO_DOC_OJS/text()",
                                      namespaces=NMSP)

    values = xml.xpath("ted:VALUES_LIST", namespaces=NMSP)

    if values:
        assert(len(values) == 1)

        global_val = values[0].xpath(".//ted:VALUES[@TYPE = 'GLOBAL']",
                                  namespaces=NMSP)
        if global_val:
            assert(len(global_val) == 1)
            obj['GLOBAL_VALUE'] = contract_item(global_val[0])

        obj['CONTRACT_VALUE'] = []
        contract_val = values[0].xpath(".//ted:VALUES[@TYPE = 'CONTRACT']",
                                    namespaces=NMSP)
        for c_val in contract_val:
            obj['CONTRACT_VALUE'].append(contract_item(c_val))

    return obj


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
    """
    obj = dict()

    for item in ['TD_DOCUMENT_TYPE', 'AA_AUTHORITY_TYPE', 'NC_CONTRACT_NATURE', 'PR_PROC',
                 'RP_REGULATION', 'TY_TYPE_BID', 'AC_AWARD_CRIT', 'MA_MAIN_ACTIVITIES' ]:
        obj[item] = xml.xpath("ted:*[local-name() = $name]/@CODE",
                              namespaces=NMSP,
                              name=item)
    return obj


def get_coded(xml):

    notice_data = get_notice(xml.xpath('ted:CODED_DATA_SECTION/ted:NOTICE_DATA',
                            namespaces=NMSP)[0])

    codif_data = get_codif(xml.xpath('ted:CODED_DATA_SECTION/ted:CODIF_DATA',
                           namespaces=NMSP)[0])

    codif_data.update(notice_data)

    return codif_data


def get_authority(xml):

    obj = dict()

    obj['OFFICIALNAME'] = xml.xpath("*/ted:CA_CE_CONCESSIONAIRE_PROFILE/ted:ORGANISATION/ted:OFFICIALNAME/text()",
                          namespaces=NMSP)
    obj['TYPE_OF_CONTRACTING_AUTHORITY'] = xml.xpath(".//ted:TYPE_OF_CONTRACTING_AUTHORITY/@VALUE",
                                           namespaces=NMSP)
    return obj


def get_object_value(xml):

    currency = xml.xpath("*/@CURRENCY")
    vat = xml.xpath(".//ted:VAT_PRCT/text()", namespaces=NMSP)

    if xml.xpath("boolean(.//ted:VALUE_COST)", namespaces=NMSP):
        return {
            'CURRENCY': currency,
            'VALUE_COST': xml.xpath(".//ted:VALUE_COST/text()", namespaces=NMSP),
            'VAT_PRCT': vat
        }
    elif xml.xpath("boolean(.//ted:RANGE_VALUE_COST)", namespaces=NMSP):
        return {
            'CURRENCY': currency,
            'LOW': xml.xpath(".//ted:RANGE_VALUE_COST/LOW_VALUE/text()", namespaces=NMSP),
            'HIGH': xml.xpath(".//ted:RANGE_VALUE_COST/HIGH_VALUE/text()", namespaces=NMSP),
            'VAT_PRCT': vat
        }
    else:
        return {}


def get_object(xml):

    obj = dict()

    obj['NUTS'] = xml.xpath(".//ted:NUTS/@CODE", namespaces=NMSP)

    obj['CPV_MAIN'] = xml.xpath(".//ted:CPV_MAIN/ted:CPV_CODE/@CODE", namespaces=NMSP)

    obj['CONTRACT_COVERED_GPA'] = xml.xpath(".//ted:CONTRACT_COVERED_GPA/@VALUE", namespaces=NMSP)

    framework = xml.xpath(".//ted:CONCLUSION_FRAMEWORK_AGREEMENT", namespaces=NMSP)
    if framework:
        obj['CONCLUSION_FRAMEWORK_AGREEMENT'] = True

    dps = xml.xpath(".//ted:CONTRACTS_DPS", namespaces=NMSP)
    if dps:
        obj['CONTRACTS_DPS'] = True

    values = xml.xpath(".//ted:TOTAL_FINAL_VALUE", namespaces=NMSP)

    if values:
        assert(len(values) == 1)
        obj['VALUES_LIST'] = get_object_value(values[0])

    return obj


def get_award(xml):

    obj = dict()
    obj['CONTRACTOR_COUNTRY'] = xml.xpath((".//ted:ECONOMIC_OPERATOR_NAME_ADDRESS/"
                                           "ted:CONTACT_DATA_WITHOUT_RESPONSIBLE_NAME/ted:COUNTRY/@VALUE"),
                                          namespaces=NMSP)
    obj['ADDRESS'] = " ".join(xml.xpath((".//ted:ECONOMIC_OPERATOR_NAME_ADDRESS/"
                                         "ted:CONTACT_DATA_WITHOUT_RESPONSIBLE_NAME//ted:ADDRESS/text() | "
                                         ".//ted:ECONOMIC_OPERATOR_NAME_ADDRESS/"
                                         "ted:CONTACT_DATA_WITHOUT_RESPONSIBLE_NAME//ted:TOWN/text()  | "
                                         ".//ted:ECONOMIC_OPERATOR_NAME_ADDRESS/"
                                         "ted:CONTACT_DATA_WITHOUT_RESPONSIBLE_NAME//ted:POSTAL_CODE/text()"),
                                        namespaces=NMSP))
    values = xml.xpath(".//ted:COSTS_RANGE_AND_CURRENCY_WITH_VAT_RATE",
                                   namespaces=NMSP)
    if values:
        obj['VALUES_LIST'] = get_award_value(values[0])
    return obj


def get_contract(xml):

    form = xml.xpath('ted:FORM_SECTION', namespaces=NMSP)[0]

    if form.xpath('name(child::*/*)') == 'FD_OTH_NOT':
        return {'OTH_NOT' : True}

    if len(form.xpath('*')) > 1:
        for lg in ['EN', 'FR', 'DE']:
            contract = form.xpath("ted:*[starts-with(local-name(), 'CONTRACT_') and @LG = $lg]",
                                  namespaces=NMSP,
                                  lg=lg)
            if contract:
                contract = contract[0]
                break
    else:
        contract = form.xpath("ted:*[starts-with(local-name(), 'CONTRACT_')]",
                              namespaces=NMSP)[0]



    # CONTRACTING_AUTHORITY
    ca = contract.xpath(("*/ted:*[starts-with(local-name(), 'CONTRACTING') "
                         "or  local-name() = 'AUTHORITY_CONTRACT_MOVE']"),
                        namespaces=NMSP)
    if len(ca) == 1:
        ca = get_authority(ca[0])

    # OBJECT
    object_c = contract.xpath("*/ted:*[starts-with(local-name(), 'OBJECT')]",
                         namespaces=NMSP)
    if len(object_c) == 1:
        object_c = get_object(object_c[0])

    # AWARD_OF_CONTRACT
    awards = []

    for award in contract.xpath("*/ted:*[starts-with(local-name(), 'AWARD')]",
                           namespaces=NMSP):
        awards.append(get_award(award))

    return object_c

def extract(path):

    root = etree.parse(path).getroot()

    doc_id = root.get('DOC_ID', default=None)

    coded_data = get_coded(root)

    form = get_contract(root)

    return form


def get_el(path):
    root = etree.parse(path).getroot()

    form = root.xpath('ted:FORM_SECTION', namespaces=NMSP)[0]

    if form.xpath('name(child::*/*)') == 'FD_OTH_NOT':
        return [{'OTH_NOT': True}]

    values = root.xpath('ted:CODED_DATA_SECTION/ted:NOTICE_DATA/ted:VALUES_LIST',
                            namespaces=NMSP)

    obj = dict()

    if values:
        assert(len(values) == 1)
        values = values[0]
        global_val = values.xpath(".//ted:VALUES[@TYPE = 'GLOBAL']",
                                  namespaces=NMSP)
        if global_val:
            assert(len(global_val) == 1)
            obj['GLOBAL'] = contract_item(global_val[0])

        obj['CONTRACT'] = []
        contract_val = values.xpath(".//ted:VALUES[@TYPE = 'CONTRACT']",
                                    namespaces=NMSP)
        for c_val in contract_val:
            obj['CONTRACT'].append(contract_item(c_val))



    return values


if __name__ == "__main__":

    # Folder containing xml files
    DIR = os.path.join(os.getcwd(), "2015-12")
    # List xml files
    files = os.listdir(DIR)

    keys = []
    collection = []
    for f in files:
        # Extract data from xml file
        #data = get_el(os.path.join(DIR, f))
        #print(data)
        data = extract(os.path.join(DIR, f))
        #if not c:
        #    break
        #keys.extend()
        collection.append(data)

        df = pd.DataFrame(collection)