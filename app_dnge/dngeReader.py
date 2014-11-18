__author__ = 'yuluo'

import re
import copy

import tools.fileReader as fileReader
import datetime
import tools.fileWriter as fileWriter


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

    pass

# -------------------------


def goThroughDirectory(path , weekly = False, yearNr = None,
                       weekNr = None, date = None, weekDayNr = None,  recursive = True,
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

    for s in sheets:
        try:
            dng = DNGE(s.filename)
            head = readDngeHeader(s)
            contents = readDngeContent(s)
            print("Read %d records from sheet: %s"%(len(contents), s.filename))
            dng.header = head
            dng.contents = contents
            dngs.append(dng)
        except Exception:
            print("Error reading Sheet", s.filename, s.sheetname)



    # prepare for writing
    dng_records = __prepareFoWriting(dngs)

    if date:
        date = unicode(date)
        dng_records = [dng for dng in dng_records if re.match('.*'+date+'.*', dng.Date)]
    if weekNr and yearNr and weekDayNr:
        dng_records = [dng for dng in dng_records if dng.Weeknr == weekNr and dng.Yearnr == yearNr and dng.Weekdaynr == weekDayNr]
    if weekNr and yearNr:
        dng_records = [dng for dng in dng_records if dng.Weeknr == weekNr and dng.Yearnr == yearNr]
    if weekNr:
        dng_records = [dng for dng in dng_records if dng.Weeknr == weekNr]


    if output:
        # writing file
        fileWriter.outputDngeReport(dng_records, weekly)
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
            dngr = DNGERecord()
            dngr.__dict__ = dngc.__dict__
            for k, v in head.__dict__.items():
                dngr.__dict__[k] = v
            reg_neid = r'(1[0-9].{6})'

            # test if content has neid field
            if 'neid' in dngc.__dict__.keys(): # has neid
                neid = fileReader.clearUnicode(dngc.neid)
                if neid:
                    #print('neid', neid)
                    if re.match(reg_neid, neid):
                        dngr.SITE_ID = neid
            else: # if has not neid, then match remark
                if 'remark' in dngc.__dict__.keys():
                    ma = re.match(reg_neid, unicode(dngc.remark))
                    if ma:
                        if dngr.SITE_ID != ma.group(0):
                            dngr.SITE_ID = ma.group(0)
            dng_records.append(dngr)

    # # cover number to integer
    for dng in dng_records:
        for k, v in dng.__dict__.items():
            if k not in ['Yearnr','Weeknr','Weekdaynr','Date','SITE_ID',]:
                if isinstance(v, unicode) or isinstance(v, str):
                    value = fileReader.cleanString(v)
                    dng.__dict__[k] = value
                    continue

    return dng_records



def readDngeHeader(sheet):
    """
    Read sheet's header

    :param sheet: the sheet
    :return: the sheet's reader
    """

    Header = DNGEHeader()
    locations = {
        'DN_NO': ['G1','H1','I1','J1'],
        'Applicant': ['C3'],
        'Consignee': ['C4'],
        'Carry_Mode': ['C5'],
        'Original_Warehouse': ['C6'],
        'Project_Name': ['E2'],
        'Staff_ID': ['E3'],
        'Required_date_of_Arrival': ['E4'],
        'Contract_NO': ['G2'],
        'Phone_NO1': ['G3','J3'],
        'Phone_NO2': ['G4','J4'],
        'Carrier': ['G5'],
        'SITE_ID': ['G6','H6','I6','J6'],
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
        value_list = [v for v in value_list if v is not None]
        # get the string of value
        try:
            value = ''.join(value_list)
            # put the k as parities
        except Exception:
            print("Error", k, value_list)
        Header.__dict__[k] = value

    Header.Yearnr, Header.Weeknr, Header.Weekdaynr , Header.Date = __getDngeYearNrWeekNrWeekdayDatestringFromSheet(sheet)
    Header.Source = sheet.source
    Header.Filename = sheet.filename
    return Header



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
        reg_attention = r'attention.*all the information with mark'
        # test if get the bottom (attention)
        if re.match(reg_attention, r_string):
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
        if sheet.nrows > 1:
            clear_sheets.append(sheet)
    return clear_sheets
