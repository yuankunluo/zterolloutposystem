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
import copy



class ExcelRowObject(object):

    pass




# ----------------- book & sheet read methode --------------------------
def __readAllHeadersFromBook(book):
    """

    :param book: a book object
    :return: a list of headers
    """
    sheets = readAllSheetsFromBook(book)
    header_list = []
    for sheet in sheets:
        try:
            HEADER = [clearHeader(unicode(c.value)) for c in sheet.row(0)]
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
    sheets = readAllSheetsFromBook(book)
    for sheet in sheets:
        if sheet.nrows == 0 or sheet.ncols == 0:
            continue
        header = ''.join([unicode(c.value) for c in sheet.row(0)])
        # must have something in header
        if len(header) > 2:
            result.append(sheet)
    return result




def readAllWorkbookInBook(path):
    """
    Read all file from path

    :param path: the path
    :param recursive: token if recursively read files
    :return: all books objects
    """
    if path is None:
        return None
    # print("__readAllBookFilesInBook", path)
    book = open_workbook(path)
    book.source = path
    reg_f = '\.xls$|\.xlsx$'
    fnlist = re.split('[/\\\]', path)
    file = re.sub(reg_f,'',fnlist[-1])
    book.filename = file

    return book



def readAllBookFilesInPath(path, recursive = False):
    """
    Read all file from path

    :param path: the path
    :param recursive: token if recursively read files
    :return: all books objects
    """

    bookCount = 0
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
                    if re.match(reg, fname.lower(), re.IGNORECASE):
                        book_path = path + '/' + fname
                        try:
                            book = open_workbook(book_path)
                            bookCount += 1
                            # print("Open Workbook", fname)
                            book.source = book_path
                            reg_f = '\.xls$|\.xlsx$'
                            fname = re.sub(reg_f,'',fname)
                            book.filename = cleanString(fname)
                            for s in book.sheets():
                                s.source = book.source
                            books.append(book)
                        except Exception:
                            print("Error: reading xlsx file", book_path)
                            continue
            # print("Read %d excels files"%(bookCount))
            return books
        else:
            print('Error: %s is not path!'%(path))
            return []
    else:
        books = []
        for root, dirname, files in os.walk(path, topdown=False):
            if len(dirname) == 0:
                #print("Find %d files in dir %s"%(len(files), str(root)))
                for file in files:
                    reg = '[^~].*\.xls$|[^~].*\.xlsx$'
                    if re.match(reg, file.lower(), re.IGNORECASE):
                        book_path = root +'/' + file
                        #print(book_path)
                        try:
                            book = open_workbook(book_path)
                            bookCount += 1
                            # print("Open Workbook", file)
                            book.source = book_path
                            reg_f = '\.xls$|\.xlsx$'
                            file = re.sub(reg_f,'',file)
                            book.filename = cleanString(file)
                            books.append(book)
                        except Exception:
                            print("Error reading xls file", book_path)
                            continue

        print("Read %d excels files"%(bookCount))
        return books


def readAllSheetsFromBook(book):
    """

    :param book: the Workbook instance
    :return: a list of sheets
    """

    fileNameRegx='^.*\.(xls|xlsx)$'
    sheets = []
    if book is None:
        return []
    for s_index in range(len(book.sheets())):
        s = book.sheet_by_index(s_index) # geht sheet using index
        s.index = s_index
        s.hiddenlist = []
        # give sheet object two additonal attribute
        s.source = book.source
        s.filename = book.filename
        s.hiddenlist = findHiddenRowlistFromSheet(s)
        sheets.append(s)

    return sheets


def findHiddenRowlistFromSheet(origin_sheet):
    """
    Get the hidden row index in one list, then return

    :param origin_sheet: the sheet that will be analysis
    :return: a list of integers, indicates the hidden row index
    """

    reg_xls = '.*(xls)$'
    reg_xlsx = '.*(xlsx)$'
    hiddenlist = []

    if re.match(reg_xls, origin_sheet.source, re.IGNORECASE):
        try:
            xbook = open_workbook(origin_sheet.source, formatting_info=True)
            sheet = xbook.sheet_by_index(origin_sheet.index)
            rowinfokeys = sheet.rowinfo_map.keys()
            for rowx in rowinfokeys:
                rowinfo = sheet.rowinfo_map[rowx]
                if rowinfo.hidden == 1:
                    hiddenlist.append(rowx)
        except Exception:
            print("Error Reading xls file", origin_sheet.source)
    if re.match(reg_xlsx, origin_sheet.source, re.IGNORECASE):
        try:
            xbook = xlr.Workbook(origin_sheet.source)
            xsheet = xbook[origin_sheet.index + 1] # using id to get sheet
            xhidden_list = xsheet.getHiddenRowIndex()
            if len(xhidden_list) > 0:
                hiddenlist = xhidden_list
        except Exception:
            print("Error Reading xlsx file", origin_sheet.source)
    # if len(hiddenlist) != 0:
        # print("Find %d hiddenlist in sheet %s : %s"%(len(hiddenlist), origin_sheet.source, origin_sheet.name))
    return hiddenlist



def covertSheetRowIntoRowObjectFromSheet(sheet, headerRowIndex= 0):
    """
    Covert sheet row into row object

    :param sheet: sheet object
    :return: a list of excel row object
    """
    result = []
    HEADER = [clearHeader(unicode(c.value)) for c in sheet.row(headerRowIndex)]
    hiddenCount = 0
    # delete empty header cell
    for rowx in range(headerRowIndex+1,sheet.nrows):
        if rowx in sheet.hiddenlist:
            hiddenCount += 1
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
                if rowx in sheet.hiddenlist:
                    rowObj.Hidden = True
                else:
                    rowObj.Hidden = False
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
            if rowx in sheet.hiddenlist:
                rowObj.Hidden = True
            else:
                rowObj.Hidden = False
            for h in HEADER:
                    rowObj.__dict__[h] = None
            try:
                for hx in range(len(HEADER)):
                    if len(unicode(sheet.cell(rowx, hx).value)) != 0:
                        rowObj.__dict__[HEADER[hx]] = sheet.cell(rowx, hx).value
            except Exception:
                pass
            result.append(rowObj)

    print("fileReader: CoverRowObject rate", len(result),sheet.nrows-1,
          'Hidden', hiddenCount, sheet.nrows-1 - hiddenCount ,
            sheet.name, sheet.source)
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
    if value == 42:
        return None
    value = unicode(value)
    if value == 'True':
        return True
    if value == 'False':
        return False
    if re.match('none|n.*a|n.*v|error', value, re.IGNORECASE):
        return None
    # replace number after .
    reg = r'\.0$'
    value = re.sub(reg,'',value)
    return value

def cleanString(value, replaceblank=False):
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
        print("Error: clearString()", value)
        return None
    # replace non alphbet letter
    reg = '[^a-zA-Z0-9_ ]'
    value = re.sub(reg,'', value)
    # replace ()
    value = re.sub('[()]','',value) # ()
    # split string using blank
    value = re.split('\s+', value)
    if replaceblank:
        return "".join(value)

    return ' '.join(value)



# ---------------- apis --------------------------------

def getAllRowObjectInPath(path, recursive = False):
    books = readAllBookFilesInPath(path, recursive)
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

    if path == None:
        return []
    # test if path is a non valid file
    reg_nofile = '.*[~$]+.*'
    if re.match(reg_nofile, path):
        return []
    book = readAllWorkbookInBook(path)
    sheets = __readAllSheetsWithHeaderInBook(book)
    rowObjs = []
    for s in sheets:
        rowObj = covertSheetRowIntoRowObjectFromSheet(s)
        rowObjs.extend(rowObj)
    # print("Read %d Rowobjects from %s"%(len(rowObjs), path))
    return rowObjs


def getAllHeadersFromBookInPath(path, recursive = False):
    """

    :param path:
    :param recursive:
    :return:
    """
    headers_list = []
    books = readAllBookFilesInPath(path, recursive)
    for b in books:
        header = __readAllHeadersFromBook(b)
        headers_list.extend(header)
    headers_list = set(headers_list)
    headers_list = list(headers_list)
    headers_list.sort()
    return headers_list


def getAllSheetsInPath(path, recursive = False):
    books = readAllBookFilesInPath(path, recursive)
    sheets = []
    for b in books:
        sheets.extend(readAllSheetsFromBook(b))
    return sheets

def getHeaderFromSheet(sheet):
    header = []
    if sheet.nrows != 0:
        header = [clearHeader(unicode(c.value)) for c in sheet.row(0)]
        return header
    else:
        return header


def clearHeader(value):
    string = cleanString(value)
    value = re.sub('\s+','_', string)
    return value



def test(dng):
    for d in dng:
        for k, v in d.__dict__.items():
            if not isinstance(v, unicode):
                print(k, v, type(v))


def getTheNewestFileLocationInPath(path, fileNameRegx='^.*\.(xls|xlsx)$',
                                   recursively = False):
    if path is None:
        return None

    filesList = []

    filelist = os.listdir(path)
    if len(filelist) == 0:
        print("No FILE in path:", path)
        return None

    if not recursively:
        for fn in os.listdir(path):
            fullpath = os.path.join(path, fn)
            if not os.path.isdir(fullpath):
                fTupe = (fn, fullpath)
                filesList.append(fTupe)
    else:
        for dirname,subdirs,files in os.walk(path):
            for fname in files:
                full_path = os.path.join(dirname, fname)
                fTupe = (fname, full_path)
                filesList.append(fTupe)

    for fTupe in filesList:
        fname = fTupe[0]
        if fname and not fname.startswith('.'):
            # print(fname)
            if fileNameRegx:
                if not re.match(fileNameRegx, fname, re.IGNORECASE):
                    print("File Extension no match", fname, fileNameRegx)
                    filesList.remove(fTupe)
                    continue
        else:
            filesList.remove(fTupe)

    max_mtime = 0
    max_file = None

    for fTupe in filesList:
        fullpath = fTupe[1]
        mtime = os.stat(fullpath).st_mtime
        if mtime > max_mtime:
            max_mtime = mtime
            max_file = fullpath

    return  max_file


def coverRowobjIntoObjWithHeader(rowObj, otherObj, regx_header):
    for k, v in regx_header.items():
        objkeys = rowObj.__dict__.keys()
        for objk in objkeys:
            if re.match(v, objk, re.IGNORECASE):
                otherObj.__dict__[k] = cleanString(rowObj.__dict__[objk])
    return otherObj
