Firmware Exploration
====================

.. code:: python

    from __future__ import unicode_literals
    from __future__ import print_function
    


.. _firmware-exploration:

The page is structured as a collection of tables and forms (which contain tables):

.. digraph:: firmware_asp

   HTML -> Head
   HTML -> Body
   table_1 [label="Table: Navigation Header"]
   table_2 [label="Table: Logo, Title"]
   table_4 [label="Table: Select New Firmware"]
   table_5 [label="Table: Submit New Firmware"]
   form_2 [label="Table: Upload NVRAM"]
   form_3 [label="Table: Submit Upload"]
   tr_1 [label="Bootloader Version"]
   tr_2 [label="OS Version"]
   tr_3 [label="Driver Version"]
   Body -> table_1
   Body -> table_2
   Body -> form_1
   Body -> form_2
   Body -> form_3
   form_1 -> table_0
   table_0 -> tr_1
   table_0 -> tr_2
   table_0 -> tr_3
   form_1 -> table_4
   form_1 -> table_5
   
Looking at the graph it appears that ``table_0`` is the one we are interested here. This is what the html for that table looks like:

.. highlight:: html
.. include:: firmware_table.html
   :code: html


I had originally hoped to do this as a grammar, but it turns out to be kind of hard and I am apparently losing the AP so this will be brute-force BeautifulSoup:

.. highlight:: python


.. code:: python

    # python standard library
    import re
    
    # third-party
    from bs4 import BeautifulSoup



First, we can get the form directly because it has a unique ``action`` attribute:


.. code:: python

    soup = BeautifulSoup(open('firmware_asp.html'))
    
    # find_all returns a list, but since we specified the attrs, we know it has what we want
    form = soup('form', attrs={'action': 'upgrade.cgi'})[0]



``form`` is a BeautfulSoup ``tag`` so it can be searched for the table. There are two ways I thought of to do this. One is to use the fact that we know that the table we want is the first:


.. code:: python

    table = form('table')[0]



But that seems to be wrong, somehow, so I prefer to discover it:


.. code:: python

    for table in form('table'):
        if any(['Version' in tag.next for tag in table('th')]):
            break



Unfortunately, looking at the table-data, you can see that there is no really nice way to discover information. You either need to used the indices or assume the form of the versions will not change. At this point I will just give up and use the indices.


.. code:: python

    data = table('td')
    extractor = re.compile('\s*<[/]*td>')
    for index in range(1,6,2):
        print(extractor.sub('', str(data[index])))

.. code::

    CFE 5.10.128.2
    Linux  5.70.63.1
    5.60.134
    



Since that was so convoluted I will do it again in one piece using indices:


.. code:: python

    version_identifier = {1:'Bootloader', 3:'OS', 5:'Driver'}
    data = soup('form', attrs={'action': 'upgrade.cgi'})[0]('table')[0]('td')
    for index in range(1,6,2):
        output = "{0}: {1}".format(version_identifier[index],
                                   extractor.sub('', str(data[index])))
        print(output)

.. code::

    Bootloader: CFE 5.10.128.2
    OS: Linux  5.70.63.1
    Driver: 5.60.134
    


