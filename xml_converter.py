# -*- coding: utf-8 -*-
"""
Generating test butler result like xml-files.

The test result structure looks like:
    -logFile
        - testDescription
        - referenceLinks
        - entry
            - log
            - stepValue
        - statement
        - result
"""

from __future__ import with_statement

from datetime import datetime


try:
    # Python < 2.7
    from xml.etree.ElementTree import Element, SubElement, Comment, tostring
except:
    # Python >= 2.7
    from lxml.etree import Element, SubElement, Comment, tostring

# create XML
root = Element('logFile')

test_description_attributes = {
    'name': "This is just a test",
    'author': "ChristophS",
    'changedate': "23.1.2013",
    'version': "1.00.00",
    'time': "23/01/2013 09:27:21.802",
    'descriptionValue': "Hello Test",
}
SubElement(root, 'testDescription', test_description_attributes)

for i in range(10):
    entry_attributes = {
        'result': '-1',
        'id': '%s' % (i, ),
        'time': str(datetime.now())
    }
    entry = SubElement(root, 'entry', entry_attributes)

    log = SubElement(entry, 'log')
    log.text = "This is step %d!" % (i, )

    step_value = SubElement(entry, 'StepValue')
    step_value.text = "Nothing happened in this step!"

# string
s = tostring(root)
with open('test_case.LOG.xml', 'a') as f:
    f.write(s)
print s
