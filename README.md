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

## Example of extracted dictionary
Fields, data types, and description of the scraped pages stored as MongoDB [documents](https://docs.mongodb.com/manual/core/document/).

Field  |   Data type  | Description
------------- | ------------- | -------------
\_id  | ObjectId 	| Unique Index automatically created by MongoDB for each document
company  | string  | Company Name. This field is part of the compound key for this collection
url  | string 	| The URL of the webpage. This field is part of the compound key for this collection
link_text  | string  | The link text, i.e. the text that was used to indicate the URL on the page where the link was found
content  | array 	| The textual content of the webpage extracted using the dragnet library
keywords  | array  | The list of unique keywords found either in the link text or in the link URL


An example of scraped page as stored in MongoDB:
```
{

}
```

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
Include instructions on how to run the project on a user's local machine. Be sure to reference the technologies they might have to download for the application to run.

1. Step 1

2. Step 2
	* Substep (a)
	* Substep (b)
3. Step 3

	```
	Your code here
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


 * ``Lookups``
 * ``extractor.py``
 * ``validator.py``
 * ``mongo_import.py``

## Contributors

[Alessandra Sozzi](https://github.com/AlessandraSozzi), working for the [Office for National Statistics Big Data project](https://www.ons.gov.uk/aboutus/whatwedo/programmesandprojects/theonsbigdataproject)

## LICENSE

Released under the [MIT License](LICENSE.txt).
