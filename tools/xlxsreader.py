# -*- coding: utf-8 -*-
""" Small footprint xlsx reader """

from __future__ import unicode_literals

__author__="Ståle Undheim <staale@staale.org>"

import re
import zipfile

try:
    from xml.etree import cElementTree as ET
except:
    import cElementTree as ET

class DomZip(object):
    """ Excel xlsx files are zip files containing xml documents.
    This class handles parsing those xml documents into dom objects

    """

    def __init__(self, filename):
        """ Open up the xlsx document.
        Arguments::

            filename -- can be a filepath or a file-like object

        """

        self.ziphandle = None
        self.ziphandle = zipfile.ZipFile(filename, 'r')

    def __getitem__(self, key):
        """ Get a domtree from a document in the zip file
        Arguments::

            key -- path inside the zip file (xml document)

        """

        return ET.fromstring(self.ziphandle.read(key))

    def __del__(self):
        """Close the zip file when finished"""

        if self.ziphandle:
            self.ziphandle.close()

class Workbook(object):
    """Main class that contains sheets organized by name or by id.
    Id being the order number of the sheet starting from 1

    """
    def __init__(self, filename):
        self.__sheetsById = {}
        self.__sheetsByName = {}
        self.filename = filename
        self.domzip = DomZip(filename)
        try : # Not all xlsx documents contain Shared Strings
            self.sharedStrings = SharedStrings(
                self.domzip["xl/sharedStrings.xml"])
        except KeyError :
            self.sharedStrings = None

        # Extract the last modification date; based upon an answer at:
        #  http://superuser.com/questions/195548/excel-2007-modify-creation-date-statistics
        self.dcterms_modified = None
        modified_date_elements = self.domzip["docProps/core.xml"].findtext("{http://purl.org/dc/terms/}modified")
        if modified_date_elements:
            self.dcterms_modified = modified_date_elements

        self.styleSheet = self.domzip["xl/styles.xml"]
        self.cellStyles = (self.styleSheet.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}cellXfs'))
        self.numFmts = {}
        if self.styleSheet.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}numFmts') is not None:
            self.numFmts = dict((x.get('numFmtId'), x.get('formatCode')) for x in self.styleSheet.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}numFmts'))

        workbookDoc = self.domzip["xl/workbook.xml"]
        sheets = workbookDoc.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheets")

        self.numSheets = len(sheets)
        id = 1
        for sheetNode in sheets:
            name = sheetNode.get("name")
            sheet = Sheet(self, id, name)
            self.__sheetsById[id] = sheet
            self.__sheetsByName[name] = sheet
            assert sheet.name in self.__sheetsByName
            id += 1

    def keys(self):
        return self.__sheetsByName.keys()

    def close(self):
        self.domzip.__del__()

    def __len__(self):
        return len(self.__sheetsByName)

    def __iter__(self):
        for sheet in self.__sheetsByName.values():
            yield sheet

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.__sheetsById[key]
        else:
            return self.__sheetsByName[key]

    def __contains__(self, key):
        if isinstance(key, int):
            return key in self.__sheetsById
        else:
            return key in self.__sheetsByName

class SharedStrings(list):

    def __init__(self, sharedStringsDom):
        nodes = [x for x in sharedStringsDom]
        self.extend([self._convertText(node) for node in nodes])

    @staticmethod
    def _convertText(siNode):
        '''
        Convert 'SharedStringItem' node to text.

        Not only simple text node, also `RichTextRun` nodes.
        See http://msdn.microsoft.com/en-us/library/office/gg278314(v=office.15).aspx.
        '''
        firstNode = siNode[0]
        if firstNode.tag == '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t':
            return firstNode.text
        elif firstNode.tag == '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}r':
            # RichTextRun
            text = ''.join([tNode.text or '' for tNode in siNode.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')])
            return text or None
        raise Exception('Unknow tag.', firstNode.tag)

class Sheet(object):

    def __init__(self, workbook, id, name):
        self.workbook = workbook
        self.id = id
        self.name = name
        self.loaded = False
        self.addrPattern = re.compile("([a-zA-Z]*)(\d*)")
        self.__cells = {}
        self.__cols = None
        self.__rows = None
        self.rowslist = []

        sheetDoc = self.workbook.domzip["xl/worksheets/sheet%d.xml" % self.id]
        sheetData = sheetDoc.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheetData")

        for rowNode in sheetData:
            attrs = rowNode.attrib
            #print(attrs)
            row = Row()
            for k, v in attrs.items():
                row.__dict__[k] = v
            self.rowslist.append(row)


    def rowsIter(self):
        sheetDoc = self.workbook.domzip["xl/worksheets/sheet%d.xml" % self.id]
        sheetData = sheetDoc.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheetData")
        # @type sheetData Element
        for rowNode in sheetData:
            attrs = rowNode.attrib
            row = Row()
            for k, v in attrs.items():
                row.__dict__[k] = v
            self.rowslist.append(row)
            rowNum = int(rowNode.get("r"))
            rowCells = []
            yield rowNum, rowCells

    def __load(self):
        rows = {}
        columns = {}
        for rowNum, row in self.rowsIter():
            rows[rowNum] = row

            for cell in row:
                colNum = cell.column
                if not colNum in columns:
                    columns[colNum] = []
                self.__cells[cell.id] = cell
                columns[colNum].append(cell)
        self.__rows = rows
        self.__cols = columns
        self.loaded=True

    def rows(self):
        if not self.loaded:
            self.__load()
        return self.__rows

    def cols(self):
        if not self.loaded:
            self.__load()
        return self.__cols

    def getHiddenRowIndex(self):
        hiddenlist = []
        for row in self.rowslist:
            if 'hidden' in row.__dict__.keys():
                if row.hidden == '1':
                    hiddenlist.append(int(row.r) -1)
        return hiddenlist


class Row(object):

    def __init__(self):
        pass

