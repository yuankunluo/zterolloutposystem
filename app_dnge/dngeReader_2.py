__author__ = 'yuluo'

import re
import copy

import tools.fileReader as fileReader
import datetime
import tools.fileWriter as fileWriter
from app_dnmaker.recordReader import Record

class OutputDNGE(Record):
    pass

class DNGE(object):
    """
    Represent a DNGE
    """
    def __init__(self, filename):
        self.header = None
        self.contents = None
        self.name = filename

    def __repr__(self):
        return self.name


class DNGERecord(object):
    """
    Present a DNGERecord ROW ITEM
    """
    pass

class DNGEHeader(object):

    pass

class DNGEContentRecord(object):

    def __init__(self, attrlist):
        for k in attrlist:
            self.__dict__[k] = None


HEADER = [
        u'DN_NO',
        u'ZTE_HW_PO',
        u'BMID',
        u'NEID',
        u'Applicant',
        u'Consignee',
        u'Destination_Address',
        u'Region',
        u'MR_receiving_date',
        u'MR_process_to_Compass_date',
        u'Compass_Outbound_Date',
        u'Required_date_of_Arrival',
        u'Site_equipment_description',
        u'Position',
        u'PackageNo',
        u'BomNo',
        u'DetailDescription',
        u'QTY',
        u'UNIT',
        u'Remark',
        u'POD_date',
        u'Reason_for_NON-process_MR',
        u'Email_Applican',
        u'Phone_Consignee',
        u'Original_Warehouse',
        u'Source',
        u'Phone_Applicant',
        u'Date',
        u'Yearnr',
        u'Weeknr',
        u'Carry_Mode',
        u'Filename',
        u'Weekdaynr',
        u'Contract_NO',
    ]


# -------------------------


def goThroughDirectory(path , outputname="DNGE_REPORT_", weekly = False, recursive = True,
                       output = True):
    """

    :param path:
    :param weekly:
    :param weekNr:
    :param recursive:
    :return:
    """

    dngs = []


    sheets = fileReader.getAllSheetsInPath(path, recursive)

    sheets = __getRidoffEmptySheet(sheets)

    print("Read %d sheets"%(len(sheets)))

    for s in sheets:
        try:
            dng = DNGE(s.filename)
            head = readDngeHeader(s)
            # print(head.__dict__)
            contents = readDngeContent2(s)
            # print("Read %d records from sheet: %s"%(len(contents), s.filename))
            dng.header = head
            dng.contents = contents
            dngs.append(dng)
        except Exception:
            print("Error reading Sheet", s.filename, s.sheetname)

    # prepare for writing
    dng_records = __prepareFoWriting(dngs)

    if output:
        # writing file
        fileWriter.outputObjectsListToFile(dng_records, 'DO', 'output/dnge/', timeformatStr="%Y%m%d_%H%M", header=HEADER);
    return dng_records


def __prepareFoWriting(dngs):
    """

    :param dngs:
    :return:
    """

    dng_records = []
    for dng in dngs:
        head = dng.header
        for dngc in dng.contents:
            outputRecord = OutputDNGE(HEADER, 'BMID',)
            for k, v in head.__dict__.items():
                outputRecord.__dict__[k] = v
            for k, v in dngc.__dict__.items():
                outputRecord.__dict__[k] = v

            dng_records.append(outputRecord)

    print("Total: %d DNGE Records readed"%(len(dng_records)))
    return dng_records



def readDngeHeader(sheet):
    """
    Read sheet's header

    :param sheet: the sheet
    :return: the sheet's reader
    """

    Header = DNGEHeader()
    locations = {
        'DN_NO': ['G1'],

        'Applicant': ['C3'],
        'Consignee': ['C4'],
        'Carry_Mode': ['C5'],
        'Original_Warehouse': ['C6'],

        'ZTE_HW_PO': ['E2'],
        'Email_Applican': ['E3'],
        'Required_date_of_Arrival': ['E4'],
        'NEID': ['E5'],
        'BMID': ['E6'],


        'Contract_NO': ['G2'],
        'Phone_Applicant': ['G3','J3'],
        'Phone_Consignee': ['G4','J4'],

        'Destination_Address': ['C7'],
        'Region': ['J7'],
    }

    for k in locations.keys():
        # value = None
        # value_list = [fileReader.getCellValueByLocation(sheet, lo) for lo in locations[k]]
        # print(value_list)
        #
        # value_list = [v for v in value_list if v is not None]
        # value = ''.join([fileReader.clearUnicode(x) for x in value_list if x is not None])
        #
        # print(value)
        #
        # Header.__dict__[k] = value # put the k as parities
        value = None
        value_list = [fileReader.getCellValueByLocation(sheet, lo) for lo in locations[k]]
        value_list = [fileReader.clearUnicode(v) for v in value_list]
        value_list = [fileReader.cleanString(v) for v in value_list if v is not None]
        # get the string of value
        try:
            value = ''.join(value_list)
            # put the k as parities
        except Exception:
            print("Error", k, value_list)
        Header.__dict__[k] = value

    # double checking
    Header.NEID = Header.NEID[:8]

    Header.Yearnr, Header.Weeknr, Header.Weekdaynr , Header.Date = __getDngeYearNrWeekNrWeekdayDatestringFromSheet(sheet)
    Header.Source = sheet.source
    Header.Filename = sheet.filename
    return Header


def readDngeContent2(sheet):
    """

    :param sheet:
    :return:
    """

    if len(sheet.hiddenlist) != 0:
        print("***Find %d Hiddenrows"%(len(sheet.hiddenlist)), sheet.source)

    start_reg = ".*(Part.*2.*For.*ZTE).*$"
    stop_reg = ".*(attention.*all the information with mark).*$"

    content_list = []

    start_rowx = 0
    stop_rowx = 0

    # determin zte zone
    for rowx in range(8, sheet.nrows):
        cells = [fileReader.cleanString(fileReader.clearUnicode(c.value)) for c in sheet.row(rowx) if c.value]
        cells_str = "".join([x for x in cells if x])
        if re.match(start_reg, cells_str, re.IGNORECASE):
            #print("Find start string", rowx, cells_str)
            start_rowx = rowx
        if re.match(stop_reg, cells_str, re.IGNORECASE):
            #print("Find stop string", rowx, cells_str)
            stop_rowx = rowx

    header_row = [c.value for c in sheet.row(start_rowx+1)]
    header_row = [fileReader.cleanString(v, True) for v in header_row]
    #print("header_row", header_row)

    for rowx in range(start_rowx+2, stop_rowx):

        cells = [fileReader.cleanString(fileReader.clearUnicode(c.value)) for c in sheet.row(rowx) if c.value]
        cells_str = "".join([x for x in cells if x])

        if rowx in sheet.hiddenlist:
            continue
        if len(cells_str) < 20:
            continue
        #print(rowx, cells_str)
        content = DNGEContentRecord(header_row)

        for colx in range(len(header_row)):
            h = header_row[colx]
            #h = re.sub('[^a-zA-Z]', '', h)
            v = fileReader.clearUnicode(sheet.cell(rowx, colx).value)
            content.__dict__[h] = v
        content_list.append(content)

    return content_list




def readDngeContent(sheet):
    """
    Read the content of sheet
    :param sheet: sheet
    :return: a list contains all contents
    """
    # heade in row 8 index 7
    header = [unicode(c.value).lower() for c in sheet.row(7)]
    header = [re.sub('[^0-9a-zA-Z]+','',x) for x in header]
    # catch the index of qty
    unit_index = 0
    unit_reg = '.*unit'
    for i in range(len(header)):
        if re.match(unit_reg, header[i]):
            unit_index = i
    #print('Unit Index', unit_index, header[unit_index])
    result = []
    temp = []


    # from the row 8 , git ride of the fotter
    for rowx in range(8,sheet.nrows-8):
        if rowx in sheet.hiddenlist:
            #print('Hidden row found: Rowindex %d in Sheet %s of file %s'%(rowx, sheet.name, sheet.source))
            continue
        r_list = [unicode(x.value).lower() for x in sheet.row(rowx)]
        r_string = ''.join(r_list)
        reg_attention = r'.*(attention.*all the information with mark).*|.*(Approved by).*'
        # test if get the bottom (attention)
        if re.match(reg_attention, r_string, re.IGNORECASE):
            # if get the bottom of package list, then break out
            break
        # test if qty is zero
        elif len(r_list[unit_index-1]) == 0:
            continue
        # test if this row is empty
        elif len(r_string) < 30:
            continue
        else:
            row = [fileReader.clearUnicode(c.value) for c in sheet.row(rowx)]
            r = [(x,y) for (x,y) in zip(header, row)]
            r.append(('rowindex',rowx))
            temp.append(r)
    contents = []
    for t in temp:
        Content = DNGEContentRecord()
        for k, v in t:
            if len(k) > 1:
                Content.__dict__[k] = v
        contents.append(Content)
    return contents


def __getColumnNameByIndex(index):
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


def __getCellValueByName(sheet, rowname, colname):
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
    if len(colxname) == 1:
        colx = ord(colname[0]) - 65
    if len(colxname) == 2:
        first_l = colxname[0]
        second_l = colxname[1]
        colx = (ord(first_l) - 60) * 26 + (ord(second_l) - 65)
    return sheet.cell(rowx - 1, colx).value


def __getDngeYearNrWeekNrWeekdayDatestringFromSheet(sheet):
    """
    Get the dnge date from sheet
    :param sheet:
    :return:
    """
    reg_date = r'^DNGE(20\d\d)(\d\d)(\d\d).*$'
    match = re.match(reg_date, sheet.filename)
    if match:
        y_m_d = match.groups()
        d = datetime.date(int(y_m_d[0]), int(y_m_d[1]) ,int(y_m_d[2]))
        dt = ''.join(y_m_d)
        return d.isocalendar()[0],d.isocalendar()[1], d.isoweekday(), dt,
    else:
        #print('Not Match',sheet.filename)
        d =  datetime.date.today()
        dt = d.strftime('%Y%m%d')
        return d.isocalendar()[0],d.isocalendar()[1], d.isoweekday(), dt



def __getRidoffEmptySheet(sheets):
    """
    Delete the empty sheet or non delivery note sheet from sheets
    :param sheets: sheets that has been readed
    :return: a clean list of sheets
    """
    clear_sheets = []
    for sheet in sheets:
        # row1 = sheet.row(0)
        # row_string = ' '.join([unicode(c.value) for c in row1])
        # rex = '.*(DELIVERY NOTE GERMANY).*(DNGE\d+).*'
        # if re.match(rex, row_string, re.IGNORECASE):
        #     clear_sheets.append(sheet)
        if sheet.nrows > 10 and sheet.ncols in [10, 12]:
            clear_sheets.append(sheet)
    return clear_sheets

