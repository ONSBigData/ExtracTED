# ExtracTED
## Overview

[TED (Tenders Electronic Daily)](http://ted.europa.eu/TED/main/HomePage.do) is the online version of the 'Supplement to the Official Journal' of the EU, dedicated to European public procurement.

TED provides free access to public procurement notices from contracting authorities based in the European Union and in the European Economic Area (also if they provide services in any other country).

TED website currently offers bulk downloads of XML packages dating back to 1993, which can be found on the FTP ftp://ted.europa.eu/ accessible with generic credentials (guest/guest).

This repo contains scrips to extract and parse TED **Contract award** notices, i.e. the results of the procurement procedure.
The scripts have been fully tested to extract all Contract award notices for 2014, 2015 and 2016.
Documents are extracted as Python dictionaries which can be saved in a MongoDB database for easy retrieval, or further normalised to be converted in CSVs.

## Example of TED **Contract award** notice

The image below show an example of document as shown on the TED website.

![](2016-OJS253-466898-en.pdf)

## Example of extracted dictionary

An example of cleaned document:
```
{
  'DOC_ID': '466898-2016',
  'CODED_DATA': {
    'NOTICE_DATA': {
      'IA_URL_GENERAL': 'www.ekz.ch',
      'ISO_COUNTRY': 'CH',
      'NO_DOC_OJS': '2016/S 253-466898',
      'ORIGINAL_CPV': ['79970000'],
      'REF_NOTICE': ['2016/S 172-310484']
      },
    'CODIF_DATA': {
      'AA_AUTHORITY_TYPE': '4',
      'AC_AWARD_CRIT': 'Z',
      'DS_DATE_DISPATCH': '20161230',
      'MA_MAIN_ACTIVITIES': ['Z'],
      'NC_CONTRACT_NATURE': '4',
      'PR_PROC': '2',
      'RP_REGULATION': '7',
      'TD_DOCUMENT_TYPE': '7',
      'TY_TYPE_BID': '9'
      }
    },
 'CONTRACT': {
   'OTH_NOT': 'NO',
   'CONTRACTING_AUTHORITY': 'Elektrizitätswerke des Kantons Zürich',
   'CONTRACT_OBJECT': {
     'CONCLUSION_FRAMEWORK_AGREEMENT': 'NO',
     'CONTRACTS_DPS': 'NO',
     'CONTRACT_COVERED_GPA': 'YES',
     'CPV_MAIN': '79970000'
     }
   },
   'AWARDS_OF_CONTRACT': [
    {
      'CONTRACTOR': {
         'ADDRESS': 'Mühlebachstraße 52',
         'COUNTRY': 'CH',
         'OFFICIALNAME': 'Linkgroup AG',
         'POSTAL_CODE': '8008',
         'TOWN': 'Zürich'
         },
      'CONTRACT_VALUE': {
        'COST': {
          'CURRENCY': 'CHF',
          'VALUE': 700000.0
          }
        }
    }
   ]
}

```

Fields and description of the extracted data

Field  |   Data type  | Description
------------- | ------------- | -------------
DOC_ID  | String 	| Unique document number in TED.

### 2. CODED_DATA section
The CODED_DATA section is divided in 2 groups of data.
- NOTICE_DATA contains data related to the notice
- CODIF_DATA contains the META data (codification) related to the notice.

#### 2.1 NOTICE_DATA section
Field  |   Data type  | Description
------------- | ------------- | -------------
NO_DOC_OJS  | String  | Notice number in TED
ORIGINAL_NUTS  | List(String) 	| Region code(s) of the place of performance or delivery. A 2-5 digits code of the *Nomenclature of Territorial Units for Statistics*. Lookup values for first two digits: [ISO_COUNTRY.csv](Lookups/ISO_COUNTRY.csv)
ORIGINAL_CPV  | List(String)  | Product or service 8 digits code(s) of the *Common Procurement Vocabulary*. Lookup values for first two digits: [CPV.csv](Lookups/CPV.csv)
ISO_COUNTRY  | String 	| 2-characters ISO code of the country where the contracting body is located. Lookup values: [ISO_COUNTRY.csv](Lookups/ISO_COUNTRY.csv)
IA_URL_GENERAL  | String  | Main internet address (URL) of the contracting body
REF_NOTICE  | List(String) 	| Reference notice number in TED. Referencing a previous publication (prior information, corrigendum, ...)
VALUES_LIST  | Total Value  | Estimated total value(s) or total final value of the procurement

##### 2.1.1 VALUES_LIST sub-section
VALUES_LIST can be composed of the following fields:

Field  |   Data type  | Description
------------- | ------------- | -------------
GLOBAL_VALUE  | Value  | Value. Can be single or range value. Can have VAT percentage
CONTRACTS_VALUE  | List(Value)  | List of Values. Each value can be single or range value. Can have VAT percentage

###### 2.1.1.1 VALUE
Each value can be single or range value and can have VAT percentage

When is single:

Field  |   Data type  | Description
------------- | ------------- | -------------
CURRENCY  | String  | Currency of the value
VALUE  | Float  | Value
VAT_PRCT  | Int  | Vat percentage

When is range:

Field  |   Data type  | Description
------------- | ------------- | -------------
CURRENCY  | String  | Currency of the value
LOW_VALUE  | Float  | Lower value of the range
HIGH_VALUE  | Float  | Higher value of the range
VAT_PRCT  | Int  | Vat percentage



#### 2.2 CODIF_DATA section
Field  |   Data type  | Description
------------- | ------------- | -------------
DS_DATE_DISPATCH  | String  | Date of dispatch of the notice. Format: yyyymmdd
TD_DOCUMENT_TYPE  | String 	| Type of document. Lookup values: [TD_DOCUMENT_TYPE.csv](Lookups/TD_DOCUMENT_TYPE.csv)
AA_AUTHORITY_TYPE  | String  | Type of awarding authority. Lookup values: [AA_AUTHORITY_TYPE.csv](Lookups/AA_AUTHORITY_TYPE.csv)
NC_CONTRACT_NATURE  | String 	| Nature of contract. Lookup values: [NC_CONTRACT_NATURE.csv](Lookups/NC_CONTRACT_NATURE.csv)
PR_PROC  | String  | Type of procedure. Lookup values: [PR_PROC.csv](Lookups/PR_PROC.csv)
RP_REGULATION  | String	| The regulation that applies to the procedure. Lookup values: [RP_REGULATION.csv](Lookups/RP_REGULATION.csv)
TY_TYPE_BID  | String  | Type of bid. Lookup values: [TY_TYPE_BID.csv](Lookups/TY_TYPE_BID.csv)
AC_AWARD_CRIT  | String  | Type of awarding criteria. Lookup values: [AC_AWARD_CRIT.csv](Lookups/AC_AWARD_CRIT.csv)
MA_MAIN_ACTIVITIES  | List(String)  | Main activity of the contracting body. Lookup values: [MA_MAIN_ACTIVITIES.csv](Lookups/MA_MAIN_ACTIVITIES.csv)

### 3. CONTRACT section

The CONTRACT section contains the notice itself, in the XML format.
In the original XML file this section can be available in different translations, up to 24 when is fully translated.
If available, the English translation of the contract is preferred. Otherwise, French and German becomes second and third choice respectively.
When any of this translation is not present, the first available is picked.

#### 3.1 OTH_NOT section

Field  |   Data type  | Description
------------- | ------------- | -------------
OTH_NOT  | String  | Indicate whether the notice follow a standard structure (then *OTH_NOT* = *NO*) or structure is open to allow the publication of any other notice which is not following a standard form, aka non-structured notice (then *OTH_NOT* = *YES*). Only when *OTH_NOT* = *NO*, the fields CONTRACTING_AUTHORITY, CONTRACT_OBJECT and AWARDS_OF_CONTRACT are extracted

#### 3.2 CONTRACTING_AUTHORITY section

Field  |   Data type  | Description
------------- | ------------- | -------------
CONTRACTING_AUTHORITY  | String  | Name of Contracting Authority

#### 3.3 CONTRACT_OBJECT section
Object of the contract.

Field  |   Data type  | Description
------------- | ------------- | -------------
NUTS  | List(String)  | Region code(s) of the place of performance or delivery. A 2-5 digits code of the *Nomenclature of Territorial Units for Statistics*. Lookup values for first two digits: [ISO_COUNTRY.csv](Lookups/ISO_COUNTRY.csv)
NUTS_EXTRA  | String  | Additional extracted comments on the place of performance or delivery
CPV_MAIN  | String  | Main Product or service 8 digits code of the *Common Procurement Vocabulary*. Lookup values for first two digits: [CPV.csv](Lookups/CPV.csv)
CONTRACT_COVERED_GPA  | String  | *YES* or *NO* if contract is covered by GPA (Government Procurement Agreement)
CONCLUSION_FRAMEWORK_AGREEMENT  | String  | *YES* or *NO* if contract is part of a Framework Agreement
CONTRACTS_DPS  | String  | *YES* or *NO* if contract is subject to a Dynamic Purchasing System
CONTRACT_VALUE  | Contract Value  | Total value. Should correspond to the sum of individual contractor's contract values. See below

##### 3.3.1 CONTRACT_VALUE sub-section

Each contract value can be composed of the following fields:

Field  |   Data type  | Description
------------- | ------------- | -------------
COST  | Value  | Value. Can be single or range value. Can have VAT percentage
ESTIMATE  | Value  | Value. Can be single or range value. Can have VAT percentage
NUMBER_OF_YEARS  | Int  | Address (Street Name) of Contractor
NUMBER_OF_MONTHS  | Int  | Town of Contractor

**Value Data Type:**

Fields are same as mentioned above. See [Section 2.1.1.1](#2.1.1.1-VALUE)

#### 3.4 AWARDS_OF_CONTRACT section
List of awards.

Each award can contain the following sub-sections:
- CONTRACTOR: General Information about successful bidder
- CONTRACT_VALUE: Contract value associated with contractor.

#####  3.4.1 CONTRACTOR sub-section

Field  |   Data type  | Description
------------- | ------------- | -------------
OFFICIALNAME  | String  | Name of Contractor
COUNTRY  | String  | Country of Contractor
ADDRESS  | String  | Address (Street Name) of Contractor
TOWN  | String  | Town of Contractor
POSTAL_CODE  | String  | Postal Code of Contractor

#####  3.4.2 CONTRACT_VALUE sub-section
Fields are same as mentioned above. See [Section 3.3.1](#3.3.1-CONTRACT-VALUE-sub-section)

## How do I use it?

### Requirements/Pre-requisites

Python modules required:
* lxml
* voluptuous
* pandas

Optional:
* pymongo

Python version: 3.6
Database: MongoDB, local mode

### How to run the project locally
Example of how to convert a document

```python
file_path = '454322_2015.xml'  # Contract Award notice downloaded from tED website

# Extract the raw data
from extractor import extract
raw = extract(file_path)

# Validate the raw data
from validator import validate
data = validate(raw)

# Prune the data: remove empty fields
from validator import prune
prune(data)
```

### Project Structure
Repository structure:

    .
    ├── Lookups
    │   └── AA_AUTHORITY_TYPE.csv
    │   └── AC_AWARD_CRIT.csv
    │   └── CPV.csv
    │   └── ISO_COUNTRY.csv
    │   └── MA_MAIN_ACTIVITY.csv
    │   └── NC_CONTRACT_NATURE.csv
    │   └── PR_PROC.csv
    │   └── RP_REGULATION.csv
    │   └── TD_DOCUMENT_TYPE.csv
    │   └── TY_TYPE_BID.csv
    ├── extractor.py
    └── validator.py
    └── mongo_import.py


 * ``Lookups``: folder containing various lookup files
 * ``extractor.py``: script to extract raw data from the contract award notices
 * ``validator.py``: scripts to validate the raw data and prune the dictionary (i.e. remove the empty fileds)
 * ``mongo_import.py``: script to upload the data in a MongoDB database

## Contributors

[Alessandra Sozzi](https://github.com/AlessandraSozzi), working for the [Office for National Statistics Big Data project](https://www.ons.gov.uk/aboutus/whatwedo/programmesandprojects/theonsbigdataproject)

## LICENSE

Released under the [MIT License](LICENSE.txt).
