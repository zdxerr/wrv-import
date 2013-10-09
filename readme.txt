
SQS-Import
==========

This module provides basic functions to import test results in various formats
into the SQS database that is used by the Web-Result-Viewer.

Currently supported test engine results are *CRTITA* and *RTITE*.


Responsible
-----------
ChristophS


Requirements
------------
- Python 2.7
- [pymssql](http://pymssql.sourceforge.net/) 
    is required for database access
- [scipy](http://www.scipy.org/) 
    is required to import results from RTITE
- [dateutil](http://labix.org/python-dateutil)
    is required to parse dates from CRTITA


Usage
-----

1. Open the `sqs_importer.py` and edit the line with your login informations.

        LOGIN = ('hostname', 'username', 'password', 'database')

2. Run the import from the command line

        python sqs_import.py -l "MEIN TEST LABEL" "E:\test"

    This will import all test result files in `E:\test`.

        python sqs_import.py -n "E:\test"

    This will list all all test result files in `E:\test`.

         python sqs_import.py -c

    Will **clear** your database of **all** entries. So be careful!

3. Have fun!




