__author__ = 'yuluo'
import tools.fileReader as fileReader
import tools.fileWriter as fileWriter
import pickle
import datetime
import os
import re
import copy
from tools.fileReader import ExcelRowObject

class Record(object):

    def __eq__(self, other):
        if self.__dict__ == other.__dict__:
            return True
        else:
            return False

class DeliveryRecord(Record):
    pass

class SAPPORecord(Record):
    pass


class BMStatusRecord(Record):

    def __eq__(self, other):
        attlist = [u'BAUMASSNAHME_ID', u'BS_FE',u'IST92']
        if self.BAUMASSNAHME_ID == other.BAUMASSNAHME_ID and self.BS_FE == other.BS_FE and self.IST92 == other.IST92:
            return True
        else:
            return False
    pass


class SAPReferencePORecord(Record):
    pass

class OrderBmidRecord(Record):

    def __eq__(self, other):
        if self.__dict__ == other.__dict__:
            return True
        else:
            return False

class ZTEPoRecord(Record):
    pass


class BMStatus2(Record):
    pass



def __getAllSapReferencesPoFromZTEPOInPath(path = 'input/po_ztematerial_to_sappo_zztepolist/'):
    """
    Using all material code from ztepo to get all sappo

    :param path:
    :return:
    """
    rows = fileReader.getAllRowObjectInPath(fileReader.getTheNewestFileLocationInPath(path))
    sappoObjects = []

    attrs = [u'Reference_PO_Number',u'Material',u'Item_of_PO',u'Order',u'Material_Description',u'PurchNo']

    for drRow in rows:
        sapPO = SAPReferencePORecord()
        sapPO = initWithAttrsToNone(sapPO, attrs)
        for k, v in drRow.__dict__.items():
            if k in sapPO.__dict__:
                sapPO.__dict__[k] = fileReader.clearUnicode(v)
        sappoObjects.append(sapPO)
    sappoObjects = __deleteDuplicate(sappoObjects)
    return sappoObjects


def get1_AllSappoRecordInPath(path = 'input/po_ztematerial_to_sappo_zztepolist/' , output=True):
    """
    Using material code to ge all sappo information

    :param path:
    :param output:
    :return:
    """
    attrs = [
        u'Doc_Date',
        u'Item_of_PO',
        u'Material',
        u'Material_Description',
        u'PO_Quantity',
        u'Plant',
        u'PurchNo',
        u'Reference_PO_Number',
    ]
    sapopo_list = []
    rowObjs = fileReader.getAllRowObjectInPath(path)

    missCount = 0
    # cover rows as bmboject
    for row in rowObjs:
        sappo = SAPPORecord()
        sappo = initWithAttrsToNone(sappo, attrs)
        for k, v in row.__dict__.items():
            if k in attrs:
                sappo.__dict__[k] = fileReader.clearUnicode(v)
                sappo.SAP_POSource = row.Source
        if sappo.PurchNo and sappo.Material and sappo.Item_of_PO:
            sapopo_list.append(sappo)
        else:
            missCount += 1
    if output:
        fileWriter.outputObjectsToFile(sapopo_list,'Raw_1_SAP_POLIST','output/dn_maker/')
        storeRawData(sapopo_list,'Raw_1_SAP_POLIST')
    print("SAP PO rate", len(sapopo_list), len(rowObjs), "Information Miss",missCount)
    return sapopo_list



def get2_AllSapDeleiveryRecordInPath(path='input/po_vendor_to_sapdn_me2l/', output=True):
    """
    Reads the sap output using ME2L, with vendor nr: 5043096
    Change to account_view and layout, to put all header in table.

    *** Please delete the second Item column in excel ***

    :param path:

    :return:
    """

    attrs = [
        u'Deletion_Indicator',
        u'Document_Date',
        u'Document_item',
        u'Goods_recipient',
        u'Material',
        u'Order',
        u'Order_Price_Unit',
        u'Order_Quantity',
        u'Order_Unit',
        u'Purchasing_Document',
        u'Purchasing_Info_Rec',
        u'Still_to_be_delivered_qty',
        u'Short_Text',
        u'Goods_recipient',
        u'Item',
    ]



    drObjects = []
    drRows = fileReader.getAllRowObjectInBook(fileReader.getTheNewestFileLocationInPath(path))
    missing = []
    missingCount = 0
    # cover rows as bmboject
    for drRow in drRows:
        drobj = DeliveryRecord()
        drobj = initWithAttrsToNone(drobj, attrs)
        for k, v in drRow.__dict__.items():
            if k in attrs:
                drobj.__dict__[k] = fileReader.clearUnicode(v)
        if drobj.Purchasing_Document and drobj.Material and drobj.Order and drobj.Still_to_be_delivered_qty:
            drobj.SAP_Source = drRow.Source
            drObjects.append(drobj)
        else:
            missing.append(drobj)
            missingCount += 1

    if output:
        fileWriter.outputObjectsToFile(drObjects,'Raw_2_SAP_DN','output/dn_maker/')
        if len(missing) != 0:
            fileWriter.outputObjectsToFile(missing,'Raw_2_SAP_DN_Missing','output/error/')
        storeRawData(drObjects,'Raw_2_SAP_DN')
    print("SAP DN Rate: ", len(drObjects), len(drRows), 'Missing: ', missingCount )
    return drObjects


def get3_AllOrderBmidInPath(path='input/po_odernr_to_order_iw39/', output = True):

    attris = [
             u'Equipment',
             u'Order',
             u'NotesID'
    ]

    rows = fileReader.getAllRowObjectInPath(path)
    orbmids = []
    missing = []
    missingCount = 0
    duplicatCount = 0
    for drRow in rows:
        order = OrderBmidRecord()
        order = initWithAttrsToNone(order, attris)
        order.Order_Source = drRow.Source
        for k, v in drRow.__dict__.items():
            if k in attris:
                order.__dict__[k] = fileReader.clearUnicode(v)
        if order.Equipment and order.Order and order.NotesID:
            if order not in orbmids:
                orbmids.append(order)
            else:
                duplicatCount += 1
        else:
            missing.append(order)
            missingCount += 1

    if output:
        fileWriter.outputObjectsToFile(orbmids,'Raw_3_SAP_OrderBMID','output/dn_maker/')
        if len(missing) != 0 :
            fileWriter.outputObjectsToFile(missing,'Raw_3_SAP_OrderBMID_Missing','output/error/')
        storeRawData(orbmids,'Raw_3_SAP_OrderBMID')
    print('Order Bmid Rate: ', len(orbmids), len(rows),
          'Missing: ', missingCount,
          'Duplicat', duplicatCount,
    )
    return orbmids



def get4_AllBMStatusRecordInPath(path='input/po_bmstatus/', output=True):

    bmObjects = []

    rowObjList = []

    bm_sheets = []
    #get all sheets in path
    sheets = fileReader.getAllSheetsInPath(path, recursive=True)
    test_header = [u'BAUMASSNAHME_ID', u'BS_FE', u'GEMEINDE_NAME',u'IST92', u'PLZ',u'STRASSE']
    # test if this is a good bm status list
    for sheet in sheets:
        header = fileReader.getHeaderFromSheet(sheet)
        if __contains(test_header, header):
            bm_sheets.append(sheet)
        else:
            print("Error: No BM_STATUS Header", sheet.name, sheet.filename)

    for bm_sheet in bm_sheets:
        rowObjs = fileReader.covertSheetRowIntoRowObjectFromSheet(bm_sheet)
        rowObjList.extend(rowObjs)

    attris = [u'BAUMASSNAHME_ID', u'BS_FE',u'IST92',
              u'STRASSE', u'PLZ',u'GEMEINDE_NAME', u'PRICING','NBNEU']

    bm_dict = {}
    conflict_bmstatus = []
    result = []


    updateCount = 0
    print("Enter covering Rowobejec into BMStatusObject")
    for rowObj in rowObjList:
        bmObj = BMStatusRecord()
        bmObj = initWithAttrsToNone(bmObj, attris)
        bmObj.BM_Source = rowObj.Source
        for k, v in rowObj.__dict__.items():
            if k in attris:
                bmObj.__dict__[k] = fileReader.clearUnicode(v)
        # get the tupe as key
        bm_tupe = (bmObj.BAUMASSNAHME_ID, bmObj.BS_FE)
        # test if this bm tupe already in dict
        if bm_tupe not in bm_dict:
            # not in bmdict, then add into it
            bm_dict[bm_tupe] = set()
            bm_dict[bm_tupe].add(bmObj)
        else:
            oldbm = bm_dict[bm_tupe].pop()
            # update only the IST is 92
            if bmObj.IST92 and not oldbm.IST92:
                bm_dict[bm_tupe].add(bmObj)
                updateCount += 1
            else:
                bm_dict[bm_tupe].add(oldbm)

    for k, bmset in bm_dict.items():
        result.extend(list(bmset))


    print("Update Count,", updateCount)
    if output:
        fileWriter.outputObjectsToFile(result,'RAW_4_BMSTATUS_all','output/dn_maker/')
        if len(conflict_bmstatus) != 0:
            fileWriter.outputObjectsToFile(conflict_bmstatus,'RAW_4_BMSTATUS_conflict','output/error/')
        storeRawData(result,'Raw_4_BMSTATUS_all')
    print("BM Status Rate: ",len(result), len(rowObjs), 'Conflict: ', len(conflict_bmstatus))
    return result









# ----------------------------------- help functions ----------------------

def initWithAttrsToNone(obj, attrisList):
    for k in attrisList:
        obj.__dict__[k] = None
    return obj

def __contains(small, big):
    smallset = set(small)
    bigset = set(big)
    return smallset.issubset(bigset)

def loadRawData(path):
    fileDict = None
    with open(path, 'rb') as f:

        fileDict = pickle.load(f)
    print("Load %d records"%(len(fileDict)))
    return fileDict

def storeRawData(object, filename, path='output/raw/'):
    try:
        with open(path + filename+ '.raw', 'wb') as f:
            pickle.dump(object, f)
        print("Store Objects in " +  path + filename +'.raw')
    except Exception:
        print(Exception.message)
        print("Error:storeRawData," + path + filename + '.raw')


def __deleteDuplicate(objectsList):
    result = []
    for obj in objectsList:
        if obj not in result:
            result.append(obj)
        # else:
        #     print(obj.__dict__)
    print("Duplicate Rate:", len(objectsList)- len(result), len(objectsList))
    return result

