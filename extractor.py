import os
from lxml import etree

NMSP = {'ted': 'http://publications.europa.eu/TED_schema/Export'}


def get_total(xml):
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
        currency, *value = xml.xpath(".//ted:VALUE/@CURRENCY | "
                                     ".//ted:VALUE/text()",
                                     namespaces=NMSP)  # Value Might be missing

        return {'CURRENCY': currency,
                'VALUE': value}  # Might be missing
    else:
        low_currency, *low_value = xml.xpath(".//ted:VALUE[1]/@CURRENCY | "
                                             ".//ted:VALUE[1]/text()",
                                             namespaces=NMSP)
        high_currency, *high_value = xml.xpath(".//ted:VALUE[2]/@CURRENCY | "
                                               ".//ted:VALUE[2]/text()",
                                               namespaces=NMSP)
        # Values Might be missing

        return {'CURRENCY': low_currency,
                'LOW_VALUE': low_value,
                'HIGH_VALUE': high_value}


def get_notice(xml):
    """
    Get NOTICE_DATA Information: some general information related to the
    notice, or information which is extracted from the notice
    :param xml:
    :return: dictionary:
        - NO_DOC_OJS: Notice number in TED
        - ORIGINAL_NUTS: Region code(s) of the place of performance
                         or delivery
                         A 2-5 digits code of the “Nomenclature of
                         Territorial Units for Statistics”
        - ORIGINAL_CPV: Product or service 8 digits code(s) of the
                        Common Procurement Vocabulary
        - ISO_COUNTRY: 2-characters ISO code of the country where the
                       contracting body is located
        - VALUES_LIST: Estimated total value(s) or total final value(s)
                       of the procurement
        - IA_URL_GENERAL: Main internet address (URL) of the contracting body
        - REF_NOTICE: Reference notice number in TED.
                      Referencing a previous publication
                      (prior information, corrigendum, ...)
    """

    obj = dict()

    for item in ['ORIGINAL_NUTS', 'ORIGINAL_CPV']:
        obj[item] = xml.xpath("ted:*[local-name() = $name]/@CODE",
                              namespaces=NMSP,
                              name=item)  # 0 or more

    obj['NO_DOC_OJS'] = xml.xpath("ted:NO_DOC_OJS/text()",
                                  namespaces=NMSP)  # Compulsory, only one

    obj['ISO_COUNTRY'] = xml.xpath("ted:ISO_COUNTRY/@VALUE",
                                   namespaces=NMSP)  # Compulsory, only one

    obj['IA_URL_GENERAL'] = xml.xpath("ted:IA_URL_GENERAL/text()",
                                      namespaces=NMSP)  # Optional

    obj['REF_NOTICE'] = xml.xpath("ted:REF_NOTICE/ted:NO_DOC_OJS/text()",
                                  namespaces=NMSP)  # 0 or more

    values = xml.xpath("ted:VALUES_LIST", namespaces=NMSP)
    values_list = dict()

    if values:
        # Extract Total Final Value
        global_val = values[0].xpath(".//ted:VALUES[@TYPE = 'GLOBAL']",
                                     namespaces=NMSP)
        if global_val:
            values_list['GLOBAL_VALUE'] = get_total(global_val[0])

        # Extract individual sub-contracts values
        contract_val = values[0].xpath(".//ted:VALUES[@TYPE = 'CONTRACT']",
                                       namespaces=NMSP)
        if contract_val:
            values_list['CONTRACTS_VALUE'] = []
            for c_val in contract_val:  # 0 or more
                values_list['CONTRACTS_VALUE'].append(get_total(c_val))

    obj['VALUES_LIST'] = values_list

    return obj


def get_codif(xml):
    """
    Get CODIF_DATA Information: descriptive metadata related to
    the notice content
    :param xml:
    :return: dictionary:
        - DS_DATE_DISPATCH: Date of dispatch of the notice. Format: yyyymmdd
        - TD_DOCUMENT_TYPE: Type of document
        - AA_AUTHORITY_TYPE: Type of awarding authority
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
                 'PR_PROC', 'RP_REGULATION', 'TY_TYPE_BID', 'AC_AWARD_CRIT',
                 'MA_MAIN_ACTIVITIES']:
        el = xml.xpath("ted:*[local-name() = $name]/@CODE",
                       namespaces=NMSP,
                       name=item)
        obj[item] = el  # All Compulsory, only one
                        #  MA_MAIN_ACTIVITIES can be 0 or more
    obj['DS_DATE_DISPATCH'] = xml.xpath(
        "ted:*[local-name() = 'DS_DATE_DISPATCH']/text()", namespaces=NMSP)

    return obj


def get_coded(xml):
    """
    Get metadata of the contract
    :param xml:
    :return: dictionary with data from NOTICE_DATA and CODIF_DATA sections
    """

    obj = dict()

    obj['NOTICE_DATA'] = get_notice(xml.xpath(
        "ted:CODED_DATA_SECTION/ted:NOTICE_DATA", namespaces=NMSP)[0])
    obj['CODIF_DATA'] = get_codif(xml.xpath(
        "ted:CODED_DATA_SECTION/ted:CODIF_DATA", namespaces=NMSP)[0])

    return obj


def get_cost(xml):
    """
    Get CURRENCY, VALUE (or LOW - HIGH values), VAT PERCENTAGE of the contract
    :param xml:
    :return: dictionary:
        - CURRENCY
        - VALUE ( or LOW_VALUE, HIGH_VALUE for range values)
        - VAT_PRCT
    """

    obj = dict()

    obj['CURRENCY'] = xml.attrib['CURRENCY']

    obj['VAT_PRCT'] = xml.xpath(".//ted:VAT_PRCT/text()", namespaces=NMSP)

    if xml.xpath("boolean(./ted:VALUE_COST)", namespaces=NMSP):

        obj['VALUE'] = xml.xpath("./ted:VALUE_COST/text()", namespaces=NMSP)

    if xml.xpath("boolean(./ted:RANGE_VALUE_COST)", namespaces=NMSP):

        obj['LOW_VALUE'] = xml.xpath("./ted:RANGE_VALUE_COST/ted:LOW_VALUE/text()",
                                   namespaces=NMSP)
        obj['HIGH_VALUE'] = xml.xpath("./ted:RANGE_VALUE_COST/ted:HIGH_VALUE/text()",
                                    namespaces=NMSP)

    return obj


def get_contract_value(xml):
    """
    Function to help extract the CONTRACT value
    :param xml:
    :return: dictionary with either the TOTAL FINAL VALUE of the contract
             or the INITIAL ESTIMATE
    """

    obj = dict()

    if xml.xpath("boolean(./ted:COSTS_RANGE_AND_CURRENCY_WITH_VAT_RATE)",
                 namespaces=NMSP):
        obj['COST'] = get_cost(xml.xpath(
            "./ted:COSTS_RANGE_AND_CURRENCY_WITH_VAT_RATE",
            namespaces=NMSP)[0])

    if xml.xpath("boolean(./ted:INITIAL_ESTIMATED_TOTAL_VALUE_CONTRACT)",
                 namespaces=NMSP):
        obj['ESTIMATE'] = get_cost(xml.xpath(
            "./ted:INITIAL_ESTIMATED_TOTAL_VALUE_CONTRACT",
            namespaces=NMSP)[0])
    if xml.xpath(
            "boolean(.//ted:NUMBER_OF_YEARS) or boolean(.//ted:NUMBER_YEARS)",
            namespaces=NMSP):
        obj['NUMBER_OF_YEARS'] = xml.xpath(
            ".//ted:NUMBER_OF_YEARS/text() | .//ted:NUMBER_YEARS/text()",
            namespaces=NMSP)
    if xml.xpath(
            "boolean(.//ted:NUMBER_OF_MONTHS) or boolean(.//ted:NUMBER_MONTHS)",
            namespaces=NMSP):
        obj['NUMBER_OF_MONTHS'] = xml.xpath(
            ".//ted:NUMBER_OF_MONTHS/text() | .//ted:NUMBER_MONTHS/text()",
            namespaces=NMSP)

    return obj


def get_object(xml):
    """
    Function to extract the OBJECT section of the xml
    :param xml:
    :return:
    """

    obj = dict()

    # Step 4.1: Extract OBJECT LOCATION, NUTS, MAIN_CPV
    obj['NUTS'] = xml.xpath(".//ted:NUTS/@CODE", namespaces=NMSP)  # 0 or more
    obj['NUTS_EXTRA'] = xml.xpath(".//ted:LOCATION/ted:P/text()",
                                  namespaces=NMSP)  # 0 or more
    obj['CPV_MAIN'] = xml.xpath(".//ted:CPV_MAIN/ted:CPV_CODE/@CODE",
                                namespaces=NMSP)  # 0 or 1

    # Step 4.2: Extract CONTRACT_COVERED_GPA, CONCLUSION_FRAMEWORK_AGREEMENT,
    # CONTRACTS_DPS
    obj['CONTRACT_COVERED_GPA'] = xml.xpath(
        ".//ted:CONTRACT_COVERED_GPA/@VALUE", namespaces=NMSP)  # 0 or 1

    obj['CONCLUSION_FRAMEWORK_AGREEMENT'] = ['YES'] if xml.xpath(
        "boolean(.//ted:CONCLUSION_FRAMEWORK_AGREEMENT)", namespaces=NMSP) \
        else ['NO'] # YES/NO

    obj['CONTRACTS_DPS'] = ['YES'] if xml.xpath(
        "boolean(.//ted:CONTRACTS_DPS)", namespaces=NMSP) \
        else ['NO']  # YES/NO

    # Step 4.3: Extract TOTAL_VALUE
    values = xml.xpath("ted:TOTAL_FINAL_VALUE", namespaces=NMSP)

    if values:
        obj['CONTRACT_VALUE'] = get_contract_value(values[0])

    if xml.xpath("boolean(./ted:COSTS_RANGE_AND_CURRENCY_WITH_VAT_RATE)",
                 namespaces=NMSP):
        obj['CONTRACT_VALUE'] = get_contract_value(xml)

    return obj


def get_award(xml):

    obj = dict()

    # Step 5.1: Extract CONTRACTOR DATA
    contractor = dict()
    contact_data = xml.xpath(
        ("./ted:ECONOMIC_OPERATOR_NAME_ADDRESS"
         "/ted:CONTACT_DATA_WITHOUT_RESPONSIBLE_NAME"
         "| ./ted:CONTACT_DATA_WITHOUT_RESPONSIBLE_NAME_CHP"),
        namespaces=NMSP)

    if contact_data:
        contact_data = contact_data[0]

        # Step 5.1.2: Extract CONTRACTOR NAME
        contractor['OFFICIALNAME'] = contact_data.xpath(
            ("./ted:ORGANISATION/ted:OFFICIALNAME/text() | "
             "./ted:ORGANISATION/text()"), namespaces=NMSP)

        # Step 5.1.2: Extract CONTRACTOR ADDRESS
        contractor['COUNTRY'] = contact_data.xpath("ted:COUNTRY/@VALUE",
                                                   namespaces=NMSP)
        contractor['ADDRESS'] = contact_data.xpath("ted:ADDRESS/text()",
                                                   namespaces=NMSP)
        contractor['TOWN'] = contact_data.xpath("ted:TOWN/text()",
                                                namespaces=NMSP)
        contractor['POSTAL_CODE'] = contact_data.xpath(
            "ted:POSTAL_CODE/text()", namespaces=NMSP)
        obj['CONTRACTOR'] = contractor

    # Step 5.2: Extract CONTRACTOR CONTRACT VALUE
    values = xml.xpath(
      ".//ted:CONTRACT_VALUE_INFORMATION | .//ted:INFORMATION_VALUE_CONTRACT",
      namespaces=NMSP)

    if values:
        obj['CONTRACT_VALUE'] = get_contract_value(values[0])

    return obj


def get_contract(xml):
    """
    Function to extract data from CONTRACT xml section
    :param xml:
    :return: dictionary of the main sections:
        - CONTRACTING_AUTHORITY
        - CONTRACT_OBJECT
        - AWARDS_OF_CONTRACT
    """

    obj = dict()

    form = xml.xpath('ted:FORM_SECTION', namespaces=NMSP)[0]

    # Step 1: Skip if it is a form with no structure. Too difficult to extract
    if form.xpath("name(*) = 'OTH_NOT'"):
        obj['OTH_NOT'] = ['YES']
        return obj
    obj['OTH_NOT'] = ['NO']

    # Step 2: Extract the contract award section. Prefer English, or French, or
    # German translation if there. Otherwise pick first language available.
    contract = form.xpath("*/*")[0]

    for ln in ['EN', 'FR', 'DE']:
        if form.xpath("*/@LG = $ln", ln=ln):
            contract = form.xpath("*[@LG = $ln]/*", ln=ln)[0]
            break

    # Step 3: Extract Contracting Authority: OFFICIALNAME
    authority = contract.xpath(
        ("ted:*[starts-with(local-name(), 'CONTRACTING') or "
         "starts-with(local-name(), 'CONTACTING') or "
         "starts-with(local-name(), 'AUTHORITY')]/"
         "ted:*[starts-with(local-name(), 'NAME')]//"
         "ted:ORGANISATION"), namespaces=NMSP)[0]
    obj['CONTRACTING_AUTHORITY'] = authority.xpath(  # Compulsory, only one
        "ted:OFFICIALNAME/text() | ./text()", namespaces=NMSP)

    # Step 4: Extract CONTRACT OBJECT information
    contract_object = contract.xpath(  # Compulsory, only one
            "ted:*[starts-with(local-name(), 'OBJECT')]", namespaces=NMSP)[0]
    obj['CONTRACT_OBJECT'] = get_object(contract_object)

    # Step 5: Extract AWARD_OF_CONTRACT section
    awards = contract.xpath(  # 0 or more
        "ted:*[starts-with(local-name(), 'AWARD')]", namespaces=NMSP)

    obj['AWARDS_OF_CONTRACT'] = []

    for award in awards:

        if award.xpath("boolean(./ted:AWARD_AND_CONTRACT_VALUE)",
                       namespaces=NMSP):

            for sub_award in award.xpath(
                    "ted:AWARD_AND_CONTRACT_VALUE",
                    namespaces=NMSP):
                obj['AWARDS_OF_CONTRACT'].append(get_award(sub_award))

        else:
            obj['AWARDS_OF_CONTRACT'].append(get_award(award))

    return obj


def extract(path):
    """
    Main function to extract data from xml file
    :param path:
    :return: dictionary of the main sections:
        - DOC_ID
        - CODED_DATA
            - NOTICE_DATA
            - CODIF_DATA
        - CONTRACT
            - CONTRACTING_AUTHORITY
            - CONTRACT_OBJECT
            - AWARDS_OF_CONTRACT
    """

    root = etree.parse(path).getroot()

    obj = dict()

    obj['DOC_ID'] = root.get('DOC_ID', default=None)

    obj['CODED_DATA'] = get_coded(root)

    obj['CONTRACT'] = get_contract(root)

    return obj


if __name__ == "__main__":

    os.chdir('/Volumes/WD/S8')

    years = ['2011', '2012', '2013', '2014', '2015', '2016']
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
                try:
                    data = extract(file_path)
                except Exception as e:
                    print(e)
