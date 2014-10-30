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

    #regexs for sheetname
    re_nonsheetnames = r'.*([Ss]torno|[cC]ancelled).*|Sheet1|cancelled|Equipment.*Storno|Testbed|SW|OSS'
    # regx
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


