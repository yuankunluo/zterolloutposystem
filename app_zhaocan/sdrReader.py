__author__ = 'yuluo'
import tools.fileReader as fReader
import tools.fileWriter as fWriter
from app_dnmaker.recordReader import Record
import re


class SdrRecord(Record):
    pass




def readRncRecords():
    v3 = readRncV3Record()
    v4 = readRncV4Record()


def readRncV3Record(path='input/zhaocan/RNC_V3/'):

    books = fReader.readAllBookFilesInPath(path)

    print("Read books count", len(books))

    sheets_dict = {}
    usefule_sheetname = ['ManagedElement', 'RU', 'Equipment']


    read_sheet_count = 0
    for book in books:
        for sheet in book.sheets():
            if sheet.name in usefule_sheetname:
                if sheet.name not in sheets_dict:
                    sheets_dict[sheet.name] = []
                sheets_dict[sheet.name].append(sheet)
                read_sheet_count += 1

    print("Read sheets", read_sheet_count)

    attrs = ['Pri_Key', 'BSFE', 'HW_TYPE']

    # build bsfe_dict


    sdnr_pri_dict = {}
    for sheet in sheets_dict['ManagedElement']:
        for rowx in range(5, sheet.nrows):
            pre_key = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'D'))
            bsfe = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'E'))
            hw_type = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'H'))
            d = {
                'Pri_Key': pre_key,
                'BSFE': bsfe,
                'HW_TYPE': hw_type,
                'BPK':[],
                'RU':[],
                'Source':None,
            }
            sdnR = SdrRecord(d,'Pri_Key')
            sdnR.Source = sheet.source
            if sdnR.Pri_Key not in sdnr_pri_dict:
                sdnr_pri_dict[sdnR.Pri_Key] = sdnR
            else:
                print(sdnR.Pri_Key, "Double")


    # get fs cc npk
    for sheet in sheets_dict['Equipment']:
        for rowx in range(5, sheet.nrows):
            cc = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'F'))
            fs = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'H'))
            pre_key = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'D'))
            if pre_key in sdnr_pri_dict:
                sdnr = sdnr_pri_dict[pre_key]
                sdnr.CC = cc
                sdnr.FS = fs
            for colx in range(7, sheet.ncols):
                bpk_reg = '.*(bpk).*'
                cell_value = fReader.clearUnicode(sheet.cell(rowx, colx))
                if re.match(bpk_reg, cell_value, re.IGNORECASE):
                    sdnr.BPK.append(cell_value)


    for sheet in sheets_dict['RU']:
        for rowx in range(5, sheet.nrows):
            pre_key = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'D'))
            if pre_key in sdnr_pri_dict:
                sdnr = sdnr_pri_dict[pre_key]
                ru = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'G'))
                sdnr.RU.append(ru)


    # prepare to output
    sdnr_list = []
    for pre_key, sdnr in sdnr_pri_dict.items():
        ru_qty = len(sdnr.RU)
        bpk_qty = len(sdnr.BPK)
        sdnr.RU_QTY = ru_qty
        sdnr.BPK_QTY = bpk_qty
        sdnr_list.append(sdnr)

    fWriter.outputObjectsListToFile(sdnr_list, 'All_RNC_V3','output/zhaocan/')
    return sdnr_pri_dict


def readRncV4Record(path='input/zhaocan/RNC_V4/'):

    books = fReader.readAllBookFilesInPath(path)

    print("Read books count", len(books))

    sheets_dict = {}
    usefule_sheetname = ['ManagedElement', 'RU', 'Equipment']


    read_sheet_count = 0
    for book in books:
        for sheet in book.sheets():
            if sheet.name in usefule_sheetname:
                if sheet.name not in sheets_dict:
                    sheets_dict[sheet.name] = []
                sheets_dict[sheet.name].append(sheet)
                read_sheet_count += 1

    print("Read sheets", read_sheet_count)

    attrs = ['Pri_Key', 'BSFE', 'HW_TYPE']

    # build bsfe_dict


    sdnr_pri_dict = {}
    for sheet in sheets_dict['ManagedElement']:
        for rowx in range(5, sheet.nrows):
            pre_key = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'D'))
            bsfe = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'J'))
            hw_type = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'G'))
            d = {
                'Pri_Key': pre_key,
                'BSFE': bsfe,
                'HW_TYPE': hw_type,
                'BPK':[],
                'RU':[],
                'Source':None,
            }
            sdnR = SdrRecord(d,'Pri_Key')
            sdnR.Source = sheet.source
            if sdnR.Pri_Key not in sdnr_pri_dict:
                sdnr_pri_dict[sdnR.Pri_Key] = sdnR
            else:
                print(sdnR.Pri_Key, "Double")


    # get fs cc npk
    for sheet in sheets_dict['Equipment']:
        for rowx in range(5, sheet.nrows):
            cc = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'E'))
            fs = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'G'))
            pre_key = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'D'))
            if pre_key in sdnr_pri_dict:
                sdnr = sdnr_pri_dict[pre_key]
                sdnr.CC = cc
                sdnr.FS = fs
            for colx in range(7, sheet.ncols):
                bpk_reg = '.*(bpk).*'
                cell_value = fReader.clearUnicode(sheet.cell(rowx, colx))
                if re.match(bpk_reg, cell_value, re.IGNORECASE):
                    sdnr.BPK.append(cell_value)


    for sheet in sheets_dict['RU']:
        for rowx in range(5, sheet.nrows):
            pre_key = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'D'))
            if pre_key in sdnr_pri_dict:
                sdnr = sdnr_pri_dict[pre_key]
                ru = fReader.clearUnicode(fReader.getCellValueByName(sheet, str(rowx+1), 'F'))
                sdnr.RU.append(ru)


    # prepare to output
    sdnr_list = []
    for pre_key, sdnr in sdnr_pri_dict.items():
        ru_qty = len(sdnr.RU)
        bpk_qty = len(sdnr.BPK)
        sdnr.RU_QTY = ru_qty
        sdnr.BPK_QTY = bpk_qty
        sdnr_list.append(sdnr)

    fWriter.outputObjectsListToFile(sdnr_list, 'All_RNC_V4','output/zhaocan/')
    return sdnr_pri_dict

