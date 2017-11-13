import os
import re
from lxml import etree
import pandas as pd

NMSP = {'ted': 'http://publications.europa.eu/TED_schema/Export'}


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
        values = values[0]
        values = values.xpath(".//ted:VALUE/ancestor::node()[2]/@TYPE | .//ted:VALUE/@CURRENCY | .//ted:VALUE/text()",
                              namespaces=NMSP)
    obj['VALUES_LIST'] = values

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


def get_contract(xml):

    form = xml.xpath('ted:FORM_SECTION', namespaces=NMSP)[0]

    if form.xpath('name(child::*/*)') == 'FD_OTH_NOT':
        return dict()

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

    # AWARD_OF_CONTRACT
    award = contract.xpath("*/ted:*[starts-with(local-name(), 'AWARD')]",
                           namespaces=NMSP)

    return

def extract(path):

    root = etree.parse(path).getroot()

    doc_id = root.get('DOC_ID', default=None)

    coded_data = get_coded(root)

    form = get_contract(root)

    return form


def get_el(path):
    root = etree.parse(path).getroot()
    vals = root.xpath('ted:CODED_DATA_SECTION/ted:NOTICE_DATA/ted:VALUES_LIST',
                            namespaces=NMSP)
    if not vals:
        return vals

    val = vals[0]
    t = val.xpath("name(.//ted:VALUE/ancestor::node()[1])", namespaces=NMSP)
    if t == 'RANGE_VALUE':
        print(path)
    return vals


if __name__ == "__main__":

    # Folder containing xml files
    DIR = os.path.join(os.getcwd(), "2015-12")
    # List xml files
    files = os.listdir(DIR)

    collection = []
    for f in files:
        # Extract data from xml file
        #data = extract(os.path.join(DIR, f))
        #print(data)
        get_el(os.path.join(DIR, f))
        collection.append(get_el(os.path.join(DIR, f)))