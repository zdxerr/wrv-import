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

from lxml.etree import Element, SubElement, Comment, tostring


# create XML
root = Element('logFile')

test_description_attributes = {
    'file': "APV\SCALEXIO_FlexRay_Plugin\TC00001.LOG.txt",
    'name': "Default Configuration Test",
    'author': "ChristophSchniedermeier; rtitest; VM-User; Administrator",
    'changedate': "23.1.2013",
    'version': "1.00.00",
    'time': "23/01/2013 09:27:21.802",
    'descriptionValue': "",
}
SubElement(root, 'testDescription', test_description_attributes)
# another child with text
child = Element('child')
child.text = 'some text'
root.append(child)

# pretty string
s = tostring(root, pretty_print=True)
print s
