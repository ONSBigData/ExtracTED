import os
from lxml import etree
import pandas as pd

NMSP = {'ted': 'http://publications.europa.eu/TED_schema/Export'}


def get_total_value(xml):
    """
    Get TOTAL_VALUE of the contract
    :param xml:
    :return: dictionary:
        - CURRENCY: currency of the contract

        - VALUE: value, if SINGLE_VALUE
            or
        - LOW, HIGH: lower and higher range values, if RANGE_VALUE
    """
    if xml.xpath("name(*) = 'SINGLE_VALUE'"):
        currency, value = xml.xpath(".//ted:VALUE/@CURRENCY | "
                                    ".//ted:VALUE/text()",
                                    namespaces=NMSP)
        return {'CURRENCY': currency,
                'VALUE': value}
    else:
        assert (xml.xpath("name(*) = 'RANGE_VALUE'"))
        low_currency, low_value = xml.xpath(".//ted:VALUE[1]/@CURRENCY | "
                                            ".//ted:VALUE[1]/text()",
                                            namespaces=NMSP)
        high_currency, high_value = xml.xpath(".//ted:VALUE[2]/@CURRENCY | "
                                              ".//ted:VALUE[2]/text()",
                                              namespaces=NMSP)
        assert(low_currency == high_currency)  # Assert equal currencies
        return {'CURRENCY': low_currency,
                'LOW': low_value,
                'HIGH': high_value}


def get_notice(xml):
    """
    Get NOTICE_DATA Information: some general information related to the
    notice, or information which is extracted from the notice
    :param xml:
    :return: dictionary:
        - NO_DOC_OJS: Notice number in TED
        - [ORIGINAL_NUTS]: Region code(s) of the place of performance
                           or delivery
                           A 2-5 digits code of the “Nomenclature of
                           Territorial Units for Statistics”
        - [ORIGINAL_CPV]: Product or service 8 digits code(s) of the
                          Common Procurement Vocabulary
        - ISO_COUNTRY: 2-characters ISO code of the country where the
                       contracting body is located
        - VALUES_LIST: Estimated total value(s) or total final value(s)
                       of the procurement
        - IA_URL_GENERAL: Main internet address (URL) of the contracting body
        - [REF_NOTICE]: Reference notice number in TED.
                      Referencing a previous publication
                      (prior information, corrigendum, ...)
    """

    obj = dict()

    for item in ['ORIGINAL_NUTS', 'ORIGINAL_CPV']:
        obj[item] = xml.xpath("ted:*[local-name() = $name]/@CODE",
                              namespaces=NMSP,
                              name=item)  # 0 or multiple elements

    obj['NO_DOC_OJS'] = xml.xpath("ted:NO_DOC_OJS/text()",
                                  namespaces=NMSP)[0]  # Compulsory, only one

    obj['ISO_COUNTRY'] = xml.xpath("ted:ISO_COUNTRY/@VALUE",
                                   namespaces=NMSP)[0]  # Compulsory, only one

    url = xml.xpath("ted:IA_URL_GENERAL/text()", namespaces=NMSP)
    if url:
        assert(len(url) == 1)
        obj['IA_URL_GENERAL'] = url[0]
    else:
        obj['IA_URL_GENERAL'] = None

    obj['REF_NOTICE'] = xml.xpath("ted:REF_NOTICE/ted:NO_DOC_OJS/text()",
                                  namespaces=NMSP)  # 0 or multiple elements

    values = xml.xpath("ted:VALUES_LIST", namespaces=NMSP)

    if values:
        assert(len(values) == 1)

        global_val = values[0].xpath(".//ted:VALUES[@TYPE = 'GLOBAL']",
                                     namespaces=NMSP)
        obj['GLOBAL_VALUE'] = {}
        if global_val:
            assert(len(global_val) == 1)  # Can be only one
            obj['GLOBAL_VALUE'] = get_total_value(global_val[0])

        obj['CONTRACT_VALUE'] = []
        contract_val = values[0].xpath(".//ted:VALUES[@TYPE = 'CONTRACT']",
                                    namespaces=NMSP)
        for c_val in contract_val:  # Can be multiple
            obj['CONTRACT_VALUE'].append(get_total_value(c_val))

    return obj


def get_codif(xml):
    """
    Get CODIF_DATA Information: descriptive metadata related to
    the notice content
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
                             (multiple values)
    """
    obj = dict()

    for item in ['TD_DOCUMENT_TYPE', 'AA_AUTHORITY_TYPE', 'NC_CONTRACT_NATURE',
                 'PR_PROC', 'RP_REGULATION', 'TY_TYPE_BID', 'AC_AWARD_CRIT']:
        el = xml.xpath("ted:*[local-name() = $name]/@CODE",
                       namespaces=NMSP,
                       name=item)
        assert (len(el) == 1)
        obj[item] = el[0]  # Compulsory, contains only one element

    obj['MA_MAIN_ACTIVITIES'] = xml.xpath("ted:*[local-name() = "
                                          "'MA_MAIN_ACTIVITIES']/@CODE",
                                          namespaces=NMSP)  # multiple elements
    return obj


def get_coded(xml):
    """
    Get metadata of the contract
    :param xml:
    :return: dictionary with data from NOTICE_DATA and CODIF_DATA sections
    """

    obj = dict()
    obj.update(get_notice(xml.xpath("ted:CODED_DATA_SECTION/ted:NOTICE_DATA",
                                    namespaces=NMSP)[0]))
    obj.update(get_codif(xml.xpath("ted:CODED_DATA_SECTION/ted:CODIF_DATA",
                                   namespaces=NMSP)[0]))
    return obj


def get_authority(xml):

    obj = dict()

    obj['CA_OFFICIALNAME'] = xml.xpath("*/ted:CA_CE_CONCESSIONAIRE_PROFILE/"
                                       "ted:ORGANISATION/ted:OFFICIALNAME/"
                                       "text()",
                                       namespaces=NMSP)
    obj['TYPE_OF_CONTRACTING_AUTHORITY'] = \
        xml.xpath(".//ted:TYPE_OF_CONTRACTING_AUTHORITY/@VALUE",
                                           namespaces=NMSP)
    return obj


def get_cost(xml):

    currency = xml.attrib['CURRENCY']
    vat = xml.xpath(".//ted:VAT_PRCT/text()", namespaces=NMSP)

    if xml.xpath("boolean(./ted:VALUE_COST)", namespaces=NMSP):
        return {
            'CURRENCY': currency,
            'VALUE_COST': xml.xpath("./ted:VALUE_COST/text()",
                                    namespaces=NMSP),
            'VAT_PRCT': vat
        }
    if xml.xpath("boolean(./ted:RANGE_VALUE_COST)", namespaces=NMSP):
        return {
            'CURRENCY': currency,
            'LOW': xml.xpath("./ted:RANGE_VALUE_COST/LOW_VALUE/text()",
                             namespaces=NMSP),
            'HIGH': xml.xpath("./ted:RANGE_VALUE_COST/HIGH_VALUE/text()",
                              namespaces=NMSP),
            'VAT_PRCT': vat
        }


def get_contract_value(xml):

    obj = dict()

    if xml.xpath("boolean(./ted:COSTS_RANGE_AND_CURRENCY_WITH_VAT_RATE)",
                 namespaces=NMSP):
        obj['COST'] = get_cost(xml.xpath("./ted:COSTS_RANGE_AND_CURRENCY_WITH_VAT_RATE",
                                         namespaces=NMSP)[0])
    if xml.xpath("boolean(./ted:INITIAL_ESTIMATED_TOTAL_VALUE_CONTRACT)",
                 namespaces=NMSP):
        obj['ESTIMATE'] = get_cost(xml.xpath("./ted:INITIAL_ESTIMATED_TOTAL_VALUE_CONTRACT",
                                             namespaces=NMSP)[0])

    return obj


def get_object(xml):

    obj = dict()

    obj['NUTS'] = xml.xpath(".//ted:NUTS/@CODE", namespaces=NMSP)

    obj['CPV_MAIN'] = xml.xpath(".//ted:CPV_MAIN/ted:CPV_CODE/@CODE",
                                namespaces=NMSP)

    obj['CONTRACT_COVERED_GPA'] = xml.xpath(".//ted:CONTRACT_COVERED_GPA/@VALUE",
                                            namespaces=NMSP)

    framework = xml.xpath(".//ted:CONCLUSION_FRAMEWORK_AGREEMENT",
                          namespaces=NMSP)
    if framework:
        obj['CONCLUSION_FRAMEWORK_AGREEMENT'] = True

    dps = xml.xpath(".//ted:CONTRACTS_DPS", namespaces=NMSP)
    if dps:
        obj['CONTRACTS_DPS'] = True

    values = xml.xpath(".//ted:TOTAL_FINAL_VALUE", namespaces=NMSP)

    if values:
        assert(len(values) == 1)
        obj['VALUES_LIST'] = get_contract_value(values[0])

    return obj


def get_award(xml):

    obj = dict()
    obj['CONTRACTOR_COUNTRY'] = xml.xpath((".//ted:ECONOMIC_OPERATOR_NAME_ADDRESS/"
                                           "ted:CONTACT_DATA_WITHOUT_RESPONSIBLE_NAME/"
                                           "ted:COUNTRY/@VALUE"),
                                          namespaces=NMSP)
    obj['ADDRESS'] = " ".join(xml.xpath((".//ted:ECONOMIC_OPERATOR_NAME_ADDRESS/"
                                         "ted:CONTACT_DATA_WITHOUT_RESPONSIBLE_NAME//"
                                         "ted:ADDRESS/text() | "
                                         ".//ted:ECONOMIC_OPERATOR_NAME_ADDRESS/"
                                         "ted:CONTACT_DATA_WITHOUT_RESPONSIBLE_NAME//"
                                         "ted:TOWN/text()  | "
                                         ".//ted:ECONOMIC_OPERATOR_NAME_ADDRESS/"
                                         "ted:CONTACT_DATA_WITHOUT_RESPONSIBLE_NAME//"
                                         "ted:POSTAL_CODE/text()"),
                                        namespaces=NMSP))
    values = xml.xpath(".//ted:CONTRACT_VALUE_INFORMATION",
                                   namespaces=NMSP)
    obj['VALUES_LIST'] = []
    if values:
        assert (len(values) == 1)
        obj['VALUES_LIST'].append(get_contract_value(values[0]))

    return obj


def get_contract(xml):

    obj = dict()

    form = xml.xpath('ted:FORM_SECTION', namespaces=NMSP)[0]

    if form.xpath('name(child::*/*)') == 'FD_OTH_NOT':
        obj['OTH_NOT'] = True
        return obj
    else:
        obj['OTH_NOT'] = False

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

    assert(len(ca) == 1)
    obj.update(get_authority(ca[0]))

    # OBJECT
    object_c = contract.xpath("*/ted:*[starts-with(local-name(), 'OBJECT')]",
                         namespaces=NMSP)
    if object_c:
        assert (len(object_c) == 1)
        obj['OBJECT'] = get_object(object_c[0])

    # AWARDS_OF_CONTRACT
    awards = []

    for award in contract.xpath("*/ted:*[starts-with(local-name(), 'AWARD')]",
                           namespaces=NMSP):
        awards.append(get_award(award))
    obj['AWARDS_OF_CONTRACT'] = awards

    return obj


def extract(path):

    root = etree.parse(path).getroot()

    obj = dict()

    obj['DOC_ID'] = root.get('DOC_ID', default=None)

    obj.update(get_coded(root))

    obj.update(get_contract(root))

    return obj


if __name__ == "__main__":

    # Folder containing xml files
    DIR = os.path.join(os.getcwd(), "2015-12")
    # List xml files
    files = os.listdir(DIR)

    collection = []
    for f in files:
        # Extract data from xml file
        file_path = os.path.join(DIR, f)
        data = extract(file_path)
        collection.append(data)

    df = pd.DataFrame(collection)