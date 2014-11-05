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


def outputObjectsToFile(objects, filename, path, header = None):
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
    book.save(path + filename + '.xls')





def __writePoRecords(poRecorsList, filename='poRecordList', path = 'output'):
    filename = re.sub('\s','',filename)
    book = Workbook()
    sheet = book.add_sheet(unicode(filename))
    header = []



def outputPOList(Objects, filename = 'POLIST', path='output', perProject = False):
    """
    Write Objects into xls

    :param Objects: A list of any class
    :param filename: the file name
    :return: None
    """
    print("Prepare to output Excel file.")

    Objects.sort(key=lambda x: x.ZTE_PO_Nr, reverse=False)

    tims = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    filename = re.sub('\s','',filename)
    book = Workbook()
    sheet = book.add_sheet(unicode(filename))
    header = Objects[0].__dict__.keys()
    header.sort()

    header = [
            #'Unique_SPM',
            'ZTE_PO_Nr',
            'SAP_PO_Nr',
            'Site_ID',
            # 'BMID',
            # 'PMR',
            'Material_Code',
            'Qty',
            'Sheetname',
            #'IST_92',
            'PO_Amount',
            'Confirm_Date',
            'PO_Date',
            #'DN_Done_Date','DN_Maker',
            # 'DN_Status','DN_Booker'
            'Product_Description',
            #'Credit_Memo_Amount','Credit_Memo',
            'Item_Code',
            #'Buyer','Supplier',
            'Delivery_Address','Delivery_Date',
            'Remarks',
            'Filename',
            'Source',
            'SN',
            'Rowindex',
            # 'SAP_Deleted',
    ]

    # try:
    #     header.remove('_state')
    #     header.remove('id')
    # except Exception:
    #     pass
    for hx in range(len(header)):
        sheet.write(0, hx, unicode(header[hx]))
    rowIndex = 1
    allPosList = []
    for poObj in Objects:
        # @todo
        split_reg = r'[^0-9a-zA-Z]'
        if poObj.Material_Code is not None: # this object has material code
            # try break material code
            poObj.Material_Code = re.sub('\s+',"",poObj.Material_Code) # delete all blank in mcode
            mcode_list = re.split(split_reg, poObj.Material_Code, re.IGNORECASE)
            # if len(mcode_list) > 1:
                #print("INFO","Find more mcode in one row", mcode_list)
            for mc in mcode_list:
                newPoObj = copy.deepcopy(poObj) # clone obj
                newPoObj.Material_Code = mc
                allPosList.append(newPoObj)
                for cx in range(len(header)):
                    try:
                        sheet.write(rowIndex, cx, unicode(newPoObj.__dict__[header[cx]]))
                    except:
                        continue
                rowIndex += 1
        else: # the object has no material code
            allPosList.append(poObj)
            for cx in range(len(header)):
                try:
                    sheet.write(rowIndex, cx, unicode(poObj.__dict__[header[cx]]))
                except:
                    continue
            rowIndex+=1
    book.save(path + filename + '_'+tims+ '.xls')

    # store the newest po list into input/po_newest_polist
    book.save('input/po_newest_polist' + 'All_ZTE_PO_LIST.xls')

    if perProject:
    # output per file
        filenamesList = [poObj.Filename for poObj in allPosList]
        filenamesList = set(filenamesList)
        filenamesList = list(filenamesList)
        for fn in filenamesList:
            # build book
            fn_clean = "ALL_Project_"+ re.sub('[^a-zA-Z]|DE|PO|[Ll]ist','',fn)
            #print(fn, fn_clean)
            book = Workbook()
            sheet = book.add_sheet(fn_clean[:25])
            poObjs = [poObj for poObj in allPosList if poObj.Filename == fn]
            # write header
            for hx in range(len(header)):
                sheet.write(0, hx, unicode(header[hx]))
            rowIndex = 1
            for po in poObjs:
                for cx in range(len(header)):
                    try:
                        sheet.write(rowIndex, cx, unicode(po.__dict__[header[cx]]))
                    except:
                        continue
                rowIndex+=1
            book.save(path + fn_clean+"_PO_List_"+tims + '.xls')
            print("Output Project PO book:", fn_clean+"_"+tims)




def outputDngeReport(dngRecords, weekly = False,  filename = 'DNGE_REPORT_', path='output/dnge/' ):
    """

    :param dngRecords:
    :param filename:
    :param path:
    :param weekly:
    :return:
    """
    # HEADER = dngRecords[0].__dict__.keys()
    HEADER = ['DN_NO', u'SITE_ID', u'bmid', 'Applicant' ,
              'Phone_NO2','Phone_NO1','Carrier','Consignee',
              'Original_Warehouse', u'no', u'packageno',
              'Required_date_of_Arrival',
              u'bomno', u'detaildescription', u'qty', u'unit',u'remark',
              'Destination_Address','Source',
              #'Yearnr', 'Weeknr','Weekdaynr','Date'
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



