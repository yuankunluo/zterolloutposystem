__author__ = 'yuluo'
import app_core.settings as setting

"""
Read data from xlxs
@author: yuankunluo
"""
from xlrd import open_workbook
from xlwt import Workbook, Worksheet
import os
import re
import datetime
from collections import OrderedDict
import xlxsreader as xlr




class ExcelRowObject(object):

    pass




# ----------------- book & sheet read methode --------------------------
def __readAllHeadersFromBook(book):
    """

    :param book: a book object
    :return: a list of headers
    """
    sheets = __readAllSheetsFromBook(book)
    header_list = []
    for sheet in sheets:
        try:
            HEADER = [cleanString(unicode(c.value)) for c in sheet.row(0)]
            header_list.extend(HEADER)
        except Exception:
            print("[Error]:No Header \nin nsheet %s \nin boook %s \nsource %s"%(sheet.name, sheet.filename, sheet.source))
    header_set = set(header_list)
    header_list = list(header_set)
    header_list.sort()
    return header_list


def __readAllSheetsWithHeaderInBook(book):
    """
    Get all sheets (has header) from a specific book.
    The first row must be header

    :param bookFile: a excel file
    :return: a list of sheets
    """
    result = []
    sheets = __readAllSheetsFromBook(book)
    for sheet in sheets:
        if sheet.nrows == 0 or sheet.ncols == 0:
            continue
        header = ''.join([unicode(c.value) for c in sheet.row(0)])
        # must have something in header
        if len(header) > 2:
            result.append(sheet)
    return result




def __readAllBookFilesInBook(path):
    """
    Read all file from path

    :param path: the path
    :param recursive: token if recursively read files
    :return: all books objects
    """
    book = open_workbook(path)
    book.source = path
    reg_f = '\.xls$|\.xlsx$'
    fnlist = re.split('[/\\\]', path)
    file = re.sub(reg_f,'',fnlist[-1])
    book.filename = file

    return book



def __readAllBookFilesInPath(path, recursive = False):
    """
    Read all file from path

    :param path: the path
    :param recursive: token if recursively read files
    :return: all books objects
    """

    if not recursive:
        reg = '.*\.xls$|.*\.xlsx$'
        books = []
        if os.path.isdir(path):
            files = os.listdir(path)
            for fname in files:
                if fname.startswith('~'):
                    continue
                elif fname.startswith('.'):
                    continue
                else:
                    if re.match(reg, fname):
                        book_path = path + '/' + fname
                        book = open_workbook(book_path)
                        book.source = book_path
                        reg_f = '\.xls$|\.xlsx$'
                        fname = re.sub(reg_f,'',fname)
                        book.filename = fname
                        for s in book.sheets():
                            s.source = book.source
                        books.append(book)
            return books
        else:
            print('%s is not path!'%(path))
            return []
    else:
        books = []
        for root, dirname, files in os.walk(path, topdown=False):
            if len(dirname) == 0:
                #print("Find %d files in dir %s"%(len(files), str(root)))
                for file in files:
                    reg = '[^~].*\.xls$|[^~].*\.xlsx$'
                    if re.match(reg, file):
                        book_path = root +'/' + file
                        #print(book_path)
                        book = open_workbook(book_path)
                        book.source = book_path
                        reg_f = '\.xls$|\.xlsx$'
                        file = re.sub(reg_f,'',file)
                        book.filename = file
                        books.append(book)
        return books


def __readAllSheetsFromBook(book):
    """

    :param book: the Workbook instance
    :return: a list of sheets
    """
    sheets = []

    for s_index in range(len(book.sheets())):
        s = book.sheet_by_index(s_index) # geht sheet using index
        s.index = s_index
        s.hiddenlist = []
        # give sheet object two additonal attribute
        s.source = book.source
        s.filename = book.filename
        try:
            s.hiddenlist = getXlsHiddenRowlistFromSheet(s)
        except Exception:
            print("Error", "getHiddenRowList", s.name, s.source)
        sheets.append(s)

    return sheets


def getXlsHiddenRowlistFromSheet(origin_sheet):
    """
    Get the hidden row index in one list, then return

    :param origin_sheet: the sheet that will be analysis
    :return: a list of integers, indicates the hidden row index
    """

    reg_xls = '.*(xls$)'
    reg_xlsx = '.*(xlsx$)'
    hiddenlist = []

    if re.match(reg_xls, origin_sheet.source):
        xbook = open_workbook(origin_sheet.source, formatting_info=True)
        sheet = xbook.sheet_by_index(origin_sheet.index)
        rowinfokeys = sheet.rowinfo_map.keys()
        for rowx in rowinfokeys:
            rowinfo = sheet.rowinfo_map[rowx]
            if rowinfo.hidden == 1:
                hiddenlist.append(rowx)
    if re.match(reg_xlsx, origin_sheet.source):
        xbook = xlr.Workbook(origin_sheet.source)
        xsheet = xbook[origin_sheet.index + 1] # using id to get sheet
        xhidden_list = xsheet.getHiddenRowIndex()
        if len(xhidden_list) > 0:
            hiddenlist = xhidden_list
    return hiddenlist



def covertSheetRowIntoRowObjectFromSheet(sheet):
    """
    Covert sheet row into row object

    :param sheet: sheet object
    :return: a list of excel row object
    """
    result = []
    HEADER = [cleanString(unicode(c.value)) for c in sheet.row(0)]
    # delete empty header cell
    for rowx in range(1,sheet.nrows):
        # test this row's empty
        rowlist = [unicode(c.value) for c in sheet.row(rowx)]
        rowset = set(rowlist)
        if len(rowset) == 1:
            if ''.join(rowlist) == '':
                continue
            else:
                rowObj = ExcelRowObject()
                for h in HEADER:
                    rowObj.__dict__[h] = None
                rowObj.Source = sheet.source
                rowObj.Filename = sheet.filename
                rowObj.Sheetname = sheet.name
                rowObj.Rowindex = rowx
                try:
                    for hx in range(len(HEADER)):
                        if len(unicode(sheet.cell(rowx, hx).value)) != 0:
                            rowObj.__dict__[HEADER[hx]] = sheet.cell(rowx, hx).value
                except Exception:
                    pass
                result.append(rowObj)
        else:
            rowObj = ExcelRowObject()
            rowObj.Source = sheet.source
            rowObj.Filename = sheet.filename
            rowObj.Sheetname = sheet.name
            rowObj.Rowindex = rowx
            for h in HEADER:
                    rowObj.__dict__[h] = None
            try:
                for hx in range(len(HEADER)):
                    if len(unicode(sheet.cell(rowx, hx).value)) != 0:
                        rowObj.__dict__[HEADER[hx]] = sheet.cell(rowx, hx).value
            except Exception:
                pass
            result.append(rowObj)
    print("fileReader: CoverRowObject", sheet.nrows-1, len(result), sheet.name, sheet.source)
    return result





#--------------------------------------- help functions --------------------------------

def getCellValueByLocation(sheet, location='A1'):
    """
    Using the location like A1, B32 to retrieve the corresponding value of this cell.

    :param sheet: the OpenSheet Object
    :param location: A String to indicate the location of sheet
    :return: a unicode value
    """
    # the patter to macth
    try:
        reg = r'([A-Za-z]+)([0-9]+)'
        # match the location using pattern
        ma = re.match(reg, location)
        if ma and '' not in ma.groups():
            rowname = ma.group(2)
            colname = ma.group(1)
            return getCellValueByName(sheet, rowname, colname)
        else:
            print('The Location [%s] is not valid'%(unicode(location)))
    except Exception:
        print("Error", "getCellValueByLocation", sheet.name, location, sheet.source)



def getColumnIndexByName(columnName):
    """
    Get the column index by the given colun name

    :param columnName: A string like A, AK, AB
    :return: A integer index the column index
    """
    colxname = list(columnName)
    colx = 0
    if len(colxname) == 1:
        colx = ord(columnName[0]) - 65
    if len(colxname) == 2:
        first_l = colxname[0]
        second_l = colxname[1]
        colx = (ord(first_l) - 60) * 26 + (ord(second_l) - 65)
    return colx

def getColumnNameByIndex(index):
    """
    Using the giving index to get the column name
    :param index:  a integer
    :return: a string presents the column name
    """
    # get the first and second number
    if index < 26:
        return chr(index + 65)
    if index == 26 :
        return 'AA'
    f_nr = index / 26
    s_nr = index % 26
    # get the character
    f_ch = chr(f_nr-1 + 65)
    s_ch = chr(s_nr + 65)
    #print(f_ch+ s_ch)
    return f_ch+s_ch

def getCellValueByName(sheet, rowname, colname):
    """
    Return the row index and column index

    :param sheet: the sheet
    :param rowname: the row name - string
    :param colname: the column name - string
    :return: the cell value
    """
    rowx = int(rowname)
    colname = colname.upper()
    if isinstance(rowname, str):
        rowx = int(rowname)
    colxname = list(colname)
    # if the colxname just consists of one letter
    colx = 0
    if len(colxname) == 1:
        colx = ord(colname[0]) - 65
    if len(colxname) == 2:
        first_l = colxname[0]
        second_l = colxname[1]
        colx = (ord(first_l) - 60) * 26 + (ord(second_l) - 65)
    return sheet.cell(rowx - 1, colx).value



def clearUnicode(value):
    if value is None:
        return None
    if len(unicode(value)) == 0:
        return None
    value = unicode(value)
    # replace number after .
    reg = r'\.\d*'
    value = re.sub(reg,'',value)
    return value

def cleanString(value):
    """
    Clean the string, just keep the alphabet and number.

    :param value: value, maybe unicode
    :return: a string
    """
    if value is None:
        return None
    try:
        value = unicode(value)
    except Exception:
        pass
    value = re.sub('\s+','_', value) # blank
    value = re.sub('\_{2,}','_', value) # _
    value = re.sub('[()]','',value) # ()
    reg = '[^a-zA-Z0-9_]'
    value = re.sub(reg,'', value)
    return value



# ---------------- apis --------------------------------
def getAllRowObjectInPath(path, recursive = False):
    books = __readAllBookFilesInPath(path, recursive)
    sheets = []
    for b in books:
        s = __readAllSheetsWithHeaderInBook(b)
        sheets.extend(s)
    rowObjs = []
    for s in sheets:
        rowObj = covertSheetRowIntoRowObjectFromSheet(s)
        rowObjs.extend(rowObj)
    return rowObjs


def getAllRowObjectInBook(path):
    book = __readAllBookFilesInBook(path)
    sheets = __readAllSheetsWithHeaderInBook(book)
    rowObjs = []
    for s in sheets:
        rowObj = covertSheetRowIntoRowObjectFromSheet(s)
        rowObjs.extend(rowObj)
    return rowObjs


def getAllHeadersFromBookInPath(path, recursive = False):
    """

    :param path:
    :param recursive:
    :return:
    """
    headers_list = []
    books = __readAllBookFilesInPath(path, recursive)
    for b in books:
        header = __readAllHeadersFromBook(b)
        headers_list.extend(header)
    headers_list = set(headers_list)
    headers_list = list(headers_list)
    headers_list.sort()
    return headers_list


def getAllSheetsInPath(path, recursive = False):
    books = __readAllBookFilesInPath(path, recursive)
    sheets = []
    for b in books:
        sheets.extend(__readAllSheetsFromBook(b))
    return sheets

def getHeaderFromSheet(sheet):
    header = []
    if sheet.nrows != 0:
        header = [cleanString(unicode(c.value)) for c in sheet.row(0)]
        return header
    else:
        return header



def __readXMLInPath(path, recursive= False, theNewestOnly=False):

    if not recursive:
        reg = '.*\.xml$'
        books = []
        if os.path.isdir(path):
            files = os.listdir(path)
            for fname in files:
                if fname.startswith('~'):
                    continue
                elif fname.startswith('.'):
                    continue
                else:
                    if re.match(reg, fname):
                        book_path = path + '/' + fname
                        book = open_workbook(book_path)
                        book.source = book_path
                        reg_f = '\.xls$|\.xlsx$'
                        fname = re.sub(reg_f,'',fname)
                        book.filename = fname
                        for s in book.sheets():
                            s.source = book.source
                        books.append(book)
            return books
        else:
            print('%s is not path!'%(path))
            return []
    else:
        books = []
        for root, dirname, files in os.walk(path, topdown=False):
            if len(dirname) == 0:
                #print("Find %d files in dir %s"%(len(files), str(root)))
                for file in files:
                    reg = '[^~].*\.xls$|[^~].*\.xlsx$'
                    if re.match(reg, file):
                        book_path = root +'/' + file
                        #print(book_path)
                        book = open_workbook(book_path)
                        book.source = book_path
                        reg_f = '\.xls$|\.xlsx$'
                        file = re.sub(reg_f,'',file)
                        book.filename = file
                        books.append(book)
        return books
