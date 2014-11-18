__author__ = 'yuluo'
from tools import fileReader, fileWriter
import datetime
import os
import re
from time import gmtime, strftime
import app_dnmaker.recordReader as recordReader

import logging
import copy

log = logging.getLogger(__name__)



# ------------------ POLIST Model ------------------------------

class ZTEPORecord():
    """
    Present the PO record from ZTE Deutschland
    """
    pass





# ----------- Gothrough -----------------------------------------

def goThroughPolistDirectory(path = 'input/po_ztepolist/',
                             outputfile='ALL_ZTE_PO_List',
                             outputpath='output/zte_polist/',
                             output=True):
    """

    The dirctory name of the files that stored xlmx files

    """
    # read rowobj from path

    rowObjs = fileReader.getAllRowObjectInBook(fileReader.getTheNewestFileLocationInPath(path))
    poObjes = []
    wrongPos = []
    for robj in rowObjs:
        coverresult = __readPoRecordFromRowobje(robj)
        if coverresult:
            poObjes.extend(coverresult[0])
            wrongPos.extend(coverresult[1])
    hidden = [poObj for poObj in poObjes if poObj.Hidden]
    poObjes = [poObj for poObj in poObjes if poObj is not None and not poObj.Hidden]

    ztemcodes = [(poObj.ZTE_Material, poObj.ZTE_Product_Description) for poObj in poObjes
                if re.match('^5\d+', poObj.ZTE_Material)
                ]
    ztemcodes = list(set(ztemcodes))


    if output:
        fileWriter.outputObjectsToFile(poObjes,
                                       outputfile + fileWriter.getNowAsString(),
                                       outputpath)
        recordReader.storeRawData(poObjes,'Raw_ZTEPOLIST')
        if len(wrongPos) != 0:
            fileWriter.outputObjectsToFile(wrongPos, 'Unvalid-po', 'output/error/')
        if len(hidden)!= 0:
            fileWriter.outputObjectsToFile(hidden, 'Hidden-po', 'output/error/')
        fileWriter.outputListOfTupleToFile(ztemcodes,'zte_mcodes','output/zte_mcodes')
        print("Statistic %d PO Records in File %s" % (len(poObjes), outputfile))

    print("[Trans Rate]",len(poObjes), len(rowObjs),'Diff', len(poObjes)-len(rowObjs),
            "Hidden", len(hidden), "Unvalid",len(wrongPos))

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
     'ZTE_Delivery_Date':'Delivery_DateDDMMYY$|Delivery_DateDDMMYY$|Delivery_Date$',
     'ZTE_Product_Description': 'Description$|Product_Description$|Product_Description$',
     'ZTE_Item_Code':'Item_Code$|Item_Code$',
     'ZTE_Material':'Material_Code$|Materialnr$|PRODUCT_CODE$|Product Code$|Product_Code$',
     'ZTE_PO_Amount': 'PO_Amount_Euro$|PO_AmountEuro$',
     'ZTE_PO_Date': 'PO_Date$|PO_DateDDMMYY$',
     'ZTE_Qty': 'Qty$',
     'ZTE_Site_ID':'Site_ID$|Site_ID$',
     'ZTE_Origin_Mcode':'Origin_Mcode',
     'ZTE_Origin_Qty':'ZTE_Origin_Qty',
     'ZTE_Remark':'Remark$',
     'ZTE_Contract_No':'ZTE_Contract_No$',
     'ZTE_CM_No':'CM_No$',
     'ZTE_CM_Date':'CM_Date$$',
     'Hidden':'Hidden$',
    }

    poObj = ZTEPORecord()
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
    if poObj.ZTE_PO_Nr and poObj.ZTE_Material and poObj.ZTE_Site_ID and poObj.ZTE_Qty:
        if re.match('([0-9]+.*)', poObj.ZTE_Site_ID):
            poObj.Origin_Mcode = poObj.ZTE_Material
            reg_splt_m = '[^0-9]+'
            mc_list = re.split(reg_splt_m, poObj.ZTE_Material)
            qty_list = re.split(reg_splt_m, poObj.ZTE_Qty)
            # compare mclist and qty_list
            mq_tuples = __rematchMclistAndQtylist(mc_list, qty_list)
            for mq_t in mq_tuples:
                reg_mc = '([0-9]{5,})'
                if mq_t[0] and re.match(reg_mc, mq_t[0]):
                    newztepo = ZTEPORecord()
                    for k, v in poObj.__dict__.items():
                        if k in regx_header.keys():
                            newztepo.__dict__[k] = v
                    newztepo.ZTE_Origin_Mcode = poObj.ZTE_Material
                    newztepo.ZTE_Origin_Qty = poObj.ZTE_Qty
                    newztepo.ZTE_POSource = poObj.Source
                    newztepo.ZTE_Project = poObj.Sheetname
                    newztepo.ZTE_Material = mq_t[0]
                    newztepo.ZTE_Qty = mq_t[1]
                    result.append(newztepo)
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

