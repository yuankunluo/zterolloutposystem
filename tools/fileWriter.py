__author__ = 'luoyuankun'


from xlrd import open_workbook
from xlwt import Workbook, Worksheet
import os
import re
import datetime
import fileReader
from collections import OrderedDict
import pickle
from app_core.settings import  BASE_DIR
import copy

# ---------------- write -------------------------------------


def outputObjectsListToFile(objects, filename, path, timeformatStr = None, header = None):

    if type(objects) is not list:
        try:
            objects  = list(objects)
        except Exception:
            print("Can not cover objects into list")
            return

    if objects is None or len(objects) == 0:
        print("None object can not be wrote")
        return


    objects.sort()


    book = Workbook()
    sheet = book.add_sheet('Overview')
    if header == None:
        HEADER = []
        for obj in objects:
            HEADER.extend(obj.__dict__.keys())
        HEADER = set(HEADER)
        HEADER = list(HEADER)
        HEADER.sort()
    else:
        HEADER = header

    if 'Key_Attr' in HEADER:
        HEADER.remove('Key_Attr')

    rowindex = 0
    for colx in range(len(HEADER)):
        sheet.write(0, colx, HEADER[colx])
    for obj in objects:
        for colx in range(len(HEADER)):
            try:
                value = obj.__dict__[HEADER[colx]]
                if isinstance(value, list):
                    value = ";".join(value)
                sheet.write(rowindex+1, colx, obj.__dict__[HEADER[colx]])
            except Exception:
                continue
        rowindex += 1

    if timeformatStr:
        filename += "_" + getNowAsString(timeformatStr)

    book.save(path + filename + '.xls')
    print("OK: output",path + filename + '.xls' )


def outputObjectDictToFile(objectDict, filename, path, timeformatStr=None, header=None):

    if type(objectDict) != dict:
        print("Not a Dict, object can not be wrote")
        return

    if len(objectDict) == 0:
        print("Empty Dict, object can not be wrote")
        return

    book = Workbook()

    for k, v in objectDict.items():
        book = __writeObjectInoSheetOfBook(v, k, book, header)

    if timeformatStr:
        filename += "_" + getNowAsString(timeformatStr)

    book.save(path + filename + '.xls')
    print("OK: output",path + filename + '.xls' )




def __writeObjectInoSheetOfBook(objects ,sheetname , book, header=None):


    if type(objects) is not list:
        try:
            objects  = list(objects)
        except Exception:
            print("Can not cover objects into list")
            return book

    if objects is None or len(objects) == 0:
        print("None object can not be wrote")
        return book


    objects.sort()


    sheet = book.add_sheet(sheetname)
    if not header:
        HEADER = []
        for obj in objects:
            HEADER.extend(obj.__dict__.keys())
        HEADER = set(HEADER)
        HEADER = list(HEADER)
        if 'Key_Attr' in HEADER:
            HEADER.remove('Key_Attr')
        HEADER.sort()
    else:
        HEADER = header

    rowindex = 0
    for colx in range(len(HEADER)):
        sheet.write(0, colx, HEADER[colx])
    for obj in objects:
        for colx in range(len(HEADER)):
            try:
                sheet.write(rowindex+1, colx, obj.__dict__[HEADER[colx]])
            except Exception:
                continue
        rowindex += 1

    return book







def __writePoRecords(poRecorsList, filename='poRecordList', path = 'output'):
    filename = re.sub('\s','',filename)
    book = Workbook()
    sheet = book.add_sheet(unicode(filename))
    header = []






def outputDngeReport(dngRecords, weekly = False,  filename = 'DNGE_REPORT_', path='output/dnge/' ):
    """

    :param dngRecords:
    :param filename:
    :param path:
    :param weekly:
    :return:
    """
    HEADER = dngRecords[0].__dict__.keys()

    HEADER = [

        'DN_NO',
        'SITE_ID',
        'BMID',

        'Applicant',
        'Phone_NO1',
        'Phone_NO2',
        'Carrier',
        'Consignee',

        'Original_Warehouse',
        'No',
        'PackageNo',
        'Required_date_of_Arrival',
        'BomNr',
        'Detail_Description',
        'QTY',
        'UNIT',
        'Volume',
        'Remark',
        'Destination_Address',




        #--------------------

        'Region',
        'Project_Name',



        # 'Weeknr',
        'Filename',
        # 'Source',
        # 'Yearnr',
        # 'Weekdaynr',
        # 'Date',
    ]



    if weekly: # output weekly report
        # get week nrs in dngRecords
        wnrs = [dng.Weeknr for dng in dngRecords]
        wnrs = set(wnrs)
        wnrs = list(wnrs)
        wnrs.sort()
        # build Weekly workbook
        book = Workbook()
        # write overview sheet
        first_week = wnrs[0]
        last_week = wnrs[-1]
        if first_week != last_week:
            sname = 'Week_' + '-'.join([str(first_week), str(last_week)])
        else:
            sname = 'Week_' + '_'.join([str(w) for w in wnrs])
        filename += sname
        if len(wnrs) > 1:
            sheet = book.add_sheet("Overview_Week_"+ sname )
            rowIndex = 0
            for hx in range(len(HEADER)):
                sheet.write(0, hx, str.capitalize(str(HEADER[hx])))
            for dngr in dngRecords:
                for hx in range(len(HEADER)):
                    try:
                        sheet.write(rowIndex+1, hx, dngr.__dict__[HEADER[hx]])
                    except Exception:
                        pass
                rowIndex += 1
        # write week sheet
        for wnr in wnrs:
            sheet = book.add_sheet("Week_" + str(wnr))
            rowIndex = 0
            # write header
            for hx in range(len(HEADER)):
                sheet.write(0, hx, str.capitalize(str(HEADER[hx])))
            dnrs = [dnr for dnr in dngRecords if dnr.Weeknr == wnr]
            for dng in dnrs:
                for hx in range(len(HEADER)):
                    try:
                        sheet.write(rowIndex+1, hx, dng.__dict__[HEADER[hx]])
                    except Exception:
                        pass
                rowIndex += 1

        book.save(path + filename + '.xls')
        print("Output Weekly Report %s in %s"%(filename, path))
    else:
        # build daily report
        dates = [dng.Date for dng in dngRecords]
        dates.sort()
        dates = set(dates)
        dates = list(dates)
        for date in dates:
            # for every date, build a new book
            book = Workbook()
            sheet = book.add_sheet("Daily_" + date + "_overview")
            rowIndex = 0
            # wirte header
            for hx in range(len(HEADER)):
                    sheet.write(0, hx, str.capitalize(str(HEADER[hx])))
            rowIndex += 1
            # select content for that day
            dailyRecord = [dng for dng in dngRecords if dng.Date == date]
            for dng in dailyRecord:
                for hx in range(len(HEADER)):
                    try:
                        sheet.write(rowIndex, hx, dng.__dict__[HEADER[hx]])
                    except Exception:
                        continue
                rowIndex += 1
            filename = 'DNGE_REPORT_Day_' + date
            book.save(path + filename + '.xls')
            print("Output Daily Report %s in %s"%(filename, path))


def outputDeliverRecord(result, outputfile = 'All_Delievery', outputpath='output/zhaocan/'):

    print("Prepare to output Excel file.")
    # build book and sheet
    book = Workbook()
    sheet = book.add_sheet("All_delivery_overview")
    maxProductCount = max([v.Count for k, v in result.items()])

    # write Header
    HEADER = ['BS_STO', 'BS_FE', 'Type','Count', 'Summer']
    Product_Header = []
    for i in range(maxProductCount):
        Product_Header.append('Site_Equipment')
        Product_Header.append('Qty')
    HEADER.extend(Product_Header)

    for colx in range(len(HEADER)):
        sheet.write(0, colx, HEADER[colx])

    print("Header Ok")
    # write product
    rowIndex = 1
    for bsfe, record in result.items():
        try:
            colx = 0
            for k in ['BS_STO', 'BS_FE', 'Type','Count', 'Summer']:
                sheet.write(rowIndex, colx, record.__dict__[k])
                colx += 1
            for p in record.Products:
                sheet.write(rowIndex, colx, p[0])
                colx += 1
                sheet.write(rowIndex, colx, p[1])
                colx += 1
            rowIndex += 1
        except Exception:
            continue

    book.save(outputpath + outputfile + '.xls')


def outputListOfTupleToFile(listofTuple, filename, path, header=None):

    book = Workbook()
    sheet = book.add_sheet(filename)
    if header:
        for colx in range(len(header)):
            sheet.write(0, colx, header[colx])
    for rowx in range(len(listofTuple)):
        tup = listofTuple[rowx]
        for colx in range(len(tup)):
            if header:
                writerowx = 1
            else:
                writerowx = 0
            sheet.write(rowx+writerowx, colx, tup[colx])
    book.save(path + '/' + filename +'.xls')
    print("Output tuple to file", path + filename)

def getNowAsString(formatStr = "%Y%m%d_%H%M"):
    tims = datetime.datetime.now().strftime(formatStr)
    return tims


