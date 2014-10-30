__author__ = 'yuluo'
from app_core import settings
from tools import fileReader, fileWriter
import datetime
import os
import re
from time import gmtime, strftime

import logging
import copy

log = logging.getLogger(__name__)



# ------------------ POLIST Model ------------------------------

class PORecord():
    """
    Present the PO record from ZTE Deutschland
    """
    pass




# ----------- Gothrough -----------------------------------------

def goThroughPolistDirectory(path = 'input/polist/', outputfile = 'ALL_ZTE_PO_List', outputpath='output/polist/', output = True):
    """

    The dirctory name of the files that stored xlmx files

    """
    # read rowobj from path

    rowObjs = fileReader.getAllRowObjectInPath(path)
    poObjes = []
    for robj in rowObjs:
        coverresult = __readPoRecordFromRowobje(robj)
        if coverresult:
            poObjes.extend(coverresult)
    poObjes = [poObj for poObj in poObjes if poObj is not  None]
    if output:
        fileWriter.outputPOList(poObjes, outputfile, outputpath)
        print("[OK]Output %d PO Records in File %s"%(len(poObjes), outputfile))
    print("[Trans Rate]",len(poObjes), len(rowObjs), len(poObjes)-len(rowObjs))
    return poObjes

def writePosIntoPoList(pos, filename):
    """
    Write all pos into one book
    :param pos:  all pos
    :param filename: file name to store
    :return: None
    """
    pass

def isPolistSheetOk(sheet):
    """
    determine if this sheet ok
    :param sheet: the sheet
    :return: boolean
    """
    header = [(unicode(h.value)).lower() for h in sheet.row(0)]
    header_s = ' '.join(header)
    header_regx = r's/n|po|po#|site_id|site id|buyer|supplier|po date|sn'
    macher = re.findall(header_regx, header_s)
    if macher is not None:
        if len(macher) > 4:
            try:
                print('Sheet %s in file %s is ok'%(sheet.name, sheet.source))
            except:
                pass
            return True
    else:
        return False


def __readPoRecordFromRowobje(rowObj):
    """

    :param rowObj:
    :return:
    """

    result = []

    #regexs
    re_nonsheetnames = r'.*([Ss]torno|[cC]ancelled).*|Sheet1|cancelled|Equipment.*Storno|Testbed|SW|OSS'
    regx_header = {
     'ZTE_PO_Nr':'2510$|PO$|PO_Nr$',
     'Buyer':'Buyer$',
     'Confirm_Date':'Date_of_PO_ConfirmationDDMMYY$|PO_Confirmation_Date$',
     'Delivery_Address':'Delivery$|Delivery_Address$',
     'Delivery_Date':'Delivery_DateDDMMYY$',
     'Product_Description': 'Description$|Product_Description$',
     'Item_Code':'Item_Code$',
     'Material_Code':'Material_Code$|Materialnr$|PRODUCT_CODE$|Product Code',
     'PO_Amount': 'PO_Amount_Euro$',
     'PO_Date': 'PO_Date$|PO_DateDDMMYY$',
     'Qty': 'Qty$',
     'Remarks': 'Remarks$',
     'Site_ID':'Site_ID$',
     'SN':'SN$',
     'SAP_PO_Nr':'SAP_PONR',# Additional Parities
     'Unique_SPM':'Unique_SPM',
    }

    poObj = PORecord()
    # initial po object
    for k, v in regx_header.items():
        poObj.__dict__[k] = None

    poObj.Sheetname = rowObj.Sheetname
    poObj.Source = rowObj.Source
    poObj.Filename = rowObj.Filename
    poObj.Rowindex = rowObj.Rowindex

    # test if sheet are not needed to be read
    if re.match(re_nonsheetnames, rowObj.Sheetname, re.IGNORECASE):
        #print('Find nonsheet %s'%(rowObj.Sheetname))
        return None


    # trans rowObj into poObj
    for k, v in regx_header.items():
        objkeys = rowObj.__dict__.keys()
        for objk in objkeys:
            if re.match(v, objk, re.IGNORECASE):
                #print("Match:", k, objk, rowObj.__dict__[objk])
                if re.search('date', objk, re.IGNORECASE):
                    poObj.__dict__[k] = fileReader.clearUnicode(rowObj.__dict__[objk])
                else:
                    poObj.__dict__[k] = fileReader.clearUnicode(rowObj.__dict__[objk])


    split_reg = r'[^0-9a-zA-Z]'
    if poObj.ZTE_PO_Nr is not None:
        malist = None
        try:
            malist = re.split(split_reg, poObj.Material_Code, re.IGNORECASE)
        except Exception:
            malist = [poObj.Material_Code]
        for mc in malist:
            newPoObj = copy.deepcopy(poObj) # clone obj
            newPoObj.Material_Code = mc
            if newPoObj.ZTE_PO_Nr:
                reg_sappo = '3\d+'
                if re.match(reg_sappo, newPoObj.ZTE_PO_Nr):
                    newPoObj.SAP_PO_Nr = newPoObj.ZTE_PO_Nr
            result.append(newPoObj)
    return result

    #     ponr_reg = '^([0-9]{6,15})$'
    #     if re.match(ponr_reg, unicode(poObj.ZTE_PO_Nr)):
    #         if poObj.Material_Code:
    #             mcode_list = re.split(split_reg, poObj.Material_Code, re.IGNORECASE)
    #             for mc in mcode_list:
    #                 newPoObj = copy.deepcopy(poObj) # clone obj
    #                 newPoObj.Material_Code = mc
    #                 result.append(newPoObj)
    #         else:
    #             result.append(poObj)
    #     else:
    #         print("PO Nr doesn' match")
    #         print(poObj.ZTE_PO_Nr, poObj.Site_ID, poObj.Filename, poObj.Sheetname, poObj.Rowindex)
    #         print('-'*20)
    # else:
    #     print("Error Converting Po Object:" )
    #     print(poObj.ZTE_PO_Nr, poObj.Site_ID, poObj.Filename, poObj.Sheetname, poObj.Rowindex)
    #     print('-'*20)
    #     return None


    # count = 0
    # # the table header
    # header = [unicode(x.value).lower() for x in sheet.row(0)]
    # for rowx in range(1, sheet.nrows):
    #     po = PORecord()
    #     try:
    #         po.Source= re.sub(r'\s', '',sheet.source, re.IGNORECASE)
    #         po.Product_Line = re.sub(r'DE|\s', '',sheet.name, re.IGNORECASE)
    #     except Exception:
    #         pass
    #
    #     #project name
    #     m_proj = re.match(re_project, po.Source, re.IGNORECASE)
    #     if m_proj:
    #         po.Project_Name = m_proj.group(1)
    #     else:
    #         po.Project_Name = None
    #
    #     for k, reg in regx_header.items():
    #         for colx in range(len(header)):
    #             head = header[colx]
    #             if re.match(reg, head, re.IGNORECASE):
    #                 po.__dict__[k] = fileReader.clearUnicode(sheet.row(rowx)[colx].value)
    #

    #     # pos.append(po)
    #     count += 1
    #
    # try:
    #     print(len(pos), count,sheet.name, sheet.source)
    # except:
    #     pass
    # return pos


def storePos(poRecords):
    """
    Store pos, it's quick to pickle pos into one .dat file,
    then check this file every time to make sure if this po already in database,
    because access in db(disk) is too slow.
    :param pos: the pos
    :return: None
    """
    pass


def createZTEPOFromPoRecord(po):
    pass


def createZTEMatNrsFromPoRecord(po):
    """
    Using the Information to create po, split with ;
    :param po: the original po record from xls
    :return: a list contains unsaved ZTEMatNr
    """
    pass
