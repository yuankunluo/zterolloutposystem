__author__ = 'yuluo'
from tools import fileReader, fileWriter
import datetime
import os
import re
from time import gmtime, strftime
import app_dnmaker.recordReader as rReader

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

def goThroughPolistDirectory(path = 'input/po_polist/',
                             outputfile='ALL_ZTE_PO_List',
                             outputpath='output/polist/',
                             output=True):
    """

    The dirctory name of the files that stored xlmx files

    """
    # read rowobj from path

    rowObjs = fileReader.getAllRowObjectInPath(path)
    poObjes = []
    wrongPos = []
    for robj in rowObjs:
        coverresult = __readPoRecordFromRowobje(robj)
        if coverresult:
            poObjes.extend(coverresult[0])
            wrongPos.extend(coverresult[1])
    hidden = [poObj for poObj in poObjes if poObj.Hidden]
    poObjes = [poObj for poObj in poObjes if poObj is not None and not poObj.Hidden]

    ztemcodes = [(poObj.ZTE_Material, poObj.Product_Description) for poObj in poObjes
                if re.match('^5\d+', poObj.ZTE_Material)
                ]
    ztemcodes = list(set(ztemcodes))


    if output:
        fileWriter.outputObjectsToFile(poObjes,
                                       outputfile + fileWriter.getNowAsString(),
                                       outputpath)
        fileWriter.outputObjectsToFile(wrongPos, 'Unvalid-po', 'output/error/')
        fileWriter.outputObjectsToFile(hidden, 'Hidden-po', 'output/error/')
        fileWriter.outputListOfTupleToFile(ztemcodes,'zte_mcodes','output/zte_mcodes')
        print("Statistic %d PO Records in File %s"%(len(poObjes), outputfile))
    print("[Trans Rate]",len(poObjes), len(rowObjs), len(poObjes)-len(rowObjs))
    return poObjes



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
     'ZTE_PO_Nr':'2510$|PO$|PO_Nr$|PO$|PO_No$',
     'Delivery_Date':'Delivery_DateDDMMYY$|Delivery_DateDDMMYY$|Delivery_Date$',
     'Product_Description': 'Description$|Product_Description$|Product_Description$',
     'Item_Code':'Item_Code$|Item_Code$',
     'ZTE_Material':'Material_Code$|Materialnr$|PRODUCT_CODE$|Product Code$|Product_Code$',
     'PO_Amount': 'PO_Amount_Euro$|PO_AmountEuro$',
     'PO_Date': 'PO_Date$|PO_DateDDMMYY$',
     'Qty': 'Qty$',
     'Site_ID':'Site_ID$|Site_ID$',
     'SAP_PO_Nr':'SAP_PONR',
     'Origin_Mcode':'Origin_Mcode',
     'Remark':'Remark$',
     'ZTE_Contract_No':'ZTE_Contract_No$',
     'CM_No':'CM_No$',
     'CM_Date':'CM_Date$$',
     'Hidden':'Hidden$',
     'SAP_Material':'^Material$',
    }

    poObj = PORecord()
    # initial po object
    for k, v in regx_header.items():
        poObj.__dict__[k] = None

    poObj.Sheetname = rowObj.Sheetname
    poObj.Source = rowObj.Source
    poObj.Filename = rowObj.Filename
    poObj.Rowindex = rowObj.Rowindex


    # trans rowObj into poObj
    for k, v in regx_header.items():
        objkeys = rowObj.__dict__.keys()
        for objk in objkeys:
            if re.match(v, objk, re.IGNORECASE):
                if k in ['Buyer','Delivery_Address','Product_Description']:
                    poObj.__dict__[k] = fileReader.cleanString(rowObj.__dict__[objk])
                else:
                    poObj.__dict__[k] = fileReader.clearUnicode(rowObj.__dict__[objk])


    result = []
    wrongpo = []
    if poObj.ZTE_PO_Nr and poObj.ZTE_Material and poObj.Site_ID and poObj.Qty:
        poObj.Origin_Mcode = poObj.ZTE_Material
        reg_splt_m = '[^0-9]+'
        mc_list = re.split(reg_splt_m, poObj.ZTE_Material)
        qty_list = re.split(reg_splt_m, poObj.Qty)
        # compare mclist and qty_list
        mq_tuples = __rematchMclistAndQtylist(mc_list, qty_list)
        for mq_t in mq_tuples:
            reg_mc = '([0-9]{5,})'
            if mq_t[0] and re.match(reg_mc, mq_t[0]):
                newpoObj = copy.deepcopy(poObj)
                newpoObj.ZTE_Material = mq_t[0]
                newpoObj.Qty = mq_t[1]
                result.append(newpoObj)
    else:
        wrongpo.append(poObj)
    return (result, wrongpo)


def __rematchMclistAndQtylist(mc_list, qty_list):
    """

    :param mc_list:
    :param qty_list:
    :return:
    """
    if len(mc_list) != len(qty_list):
        # print("Length of mcodes and qty not match", mc_list, qty_list)
        if len(mc_list) > len(qty_list):
            for i in range(len(mc_list)):
                try:
                    qty_list[i]
                except IndexError:
                    qty_list.insert(i,qty_list[-1])
        if len(mc_list) < len(qty_list):
            for i in range(len(qty_list)):
                try:
                    mc_list[i]
                except IndexError:
                    mc_list.insert(i,mc_list[-1])
    return zip(mc_list, qty_list)

