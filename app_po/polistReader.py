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

def goThroughPolistDirectory(path = 'input/po_polist/', outputfile = 'ALL_ZTE_PO_List',
                             outputpath='output/polist/', output = True, updateWithSAPPO = False):
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
    poObjes = [poObj for poObj in poObjes if poObj is not None]


    if updateWithSAPPO:
        poObjesNoSAP = [po for po in poObjes if po.SAP_PO_Nr is None]
        fileWriter.outputPOList(poObjesNoSAP, filename="Temp_"+outputfile,
                                path='output/polist_temp/', perProject=False)

        print("\nZTE_POlist without SAP PO was already stored as excel file in output/polist_temp/!\n"
              "Please use it as reference source and do Query ZZTE_PO_LIST in sap,\n"
              "Store the result in input/po_zte_to_sap\n")

        # get user input
        user_input = raw_input("Enter [Yes] to continue, Enter No to Stop: ")

        if user_input.lower() == 'yes':
            print("Prepare to add sappo to ztepo... ")
            try:
                # adding sappo to ztepo
                sap_Record = rReader.__getAllSapReferencesPoFromZTEPOInPath()
                poObjes = addSPAPotoZtePo(sap_Record, poObjes)
            except Exception:
                print("ZTEPO to SAP po files are not usefull!")
                pass
    if output:
        fileWriter.outputPOList(poObjes, outputfile, outputpath, perProject=True)
        print("Statistic %d PO Records in File %s"%(len(poObjes), outputfile))
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
     'Site_ID':'Site_ID$',
     'SN':'SN$',
     'SAP_PO_Nr':'SAP_PONR',# Additional Parities
     'Origin_Mcode':'Origin_Mcode',
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
                if k in ['Buyer','Delivery_Address','Product_Description']:
                    poObj.__dict__[k] = fileReader.cleanString(rowObj.__dict__[objk])
                else:
                    poObj.__dict__[k] = fileReader.clearUnicode(rowObj.__dict__[objk])


    result = []
    if poObj.ZTE_PO_Nr and poObj.Material_Code and poObj.Site_ID and poObj.Qty:
        # if zte po is also the sap po
        if re.match('^3\d+$', poObj.ZTE_PO_Nr, re.IGNORECASE):
            poObj.SAP_PO_Nr = poObj.ZTE_PO_Nr
        poObj.Origin_Mcode = poObj.Material_Code
        reg_splt_m = '[^0-9]+'
        mc_list = re.split(reg_splt_m, poObj.Material_Code, re.IGNORECASE)
        qty_list = re.split(reg_splt_m, poObj.Qty, re.IGNORECASE)
        # compare mclist and qty_list
        mq_tuples = __rematchMclistAndQtylist(mc_list, qty_list)
        for mq_t in mq_tuples:
            newpoObj = copy.deepcopy(poObj)
            newpoObj.Material_Code = mq_t[0]
            newpoObj.Qty = mq_t[1]
            result.append(newpoObj)
    return result


def __rematchMclistAndQtylist(mc_list, qty_list):
    """

    :param mc_list:
    :param qty_list:
    :return:
    """
    if len(mc_list) != len(qty_list):
        print("Length of mcodes and qty not match", mc_list, qty_list)
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

def addSPAPotoZtePo(sap_PORecords, zte_PORecords):
    """
    Find all matched SAP PO to ZTE po

    :param sap_PORecords: the SAP Po records
    :param zte_PORecords: the ZTE Po records
    :return: modified ZTE Po Records
    """
    for zte_po in zte_PORecords:
        if zte_po.SAP_PO_Nr is None: # this record must find it's sap po
            sap_nrs = [spo.PurchNo for spo in sap_PORecords if spo.Reference_PO_Number == zte_po.ZTE_PO_Nr]
            sap_nrs = list(set(sap_nrs))
            if len(sap_nrs) == 1:
                zte_po.SAP_PO_Nr = sap_nrs[0]
                print("Find sappo", zte_po.ZTE_PO_Nr, zte_po.SAP_PO_Nr)
        if zte_po.SAP_PO_Nr and zte_po.Site_ID and zte_po.Material_Code:
            zte_po.Unique_SPM = '-'.join([zte_po.Site_ID, zte_po.SAP_PO_Nr, zte_po.Material_Code])
            zte_po.Unique_PM = '-'.join([zte_po.SAP_PO_Nr, zte_po.Material_Code])
        else:
            zte_po.Unique_SPM = None
            zte_po.Unique_PM = None
    return zte_PORecords