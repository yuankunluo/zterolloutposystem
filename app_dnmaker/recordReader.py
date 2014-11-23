__author__ = 'yuluo'
import tools.fileReader as fileReader
import tools.fileWriter as fileWriter
import app_po.polistReader as polistReader
import pickle
import datetime
import os
import re
import copy
from tools.fileReader import ExcelRowObject

class Record(object):



    def __key(self):
        values = ""
        for k, v in self.__dict__.items():
            if v:
                values += v

        return values

    def __str__(self):
        values = ""
        for k, v in self.__dict__.items():
            values += str(k) + ":" + str(v) + '\n'
        return values


    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def __cmp__(self, other):
        if hash(self) > hash(other):
            return 1
        if hash(self) < hash(other):
            return -1
        if hash(self) == hash(other):
            return 0

    def __init__(self, attriList, prefix=None):
        for a in attriList:
            if prefix:
                self.__dict__[prefix+"_"+a] = None
            else:
                self.__dict__[a] = None

    def add_newAttrs(self, newAttrDict):
        for k, v in newAttrDict.items():
            if k not in self.__dict__:
                self.__setattr__(k, v)


class DeliveryRecord(Record):
    pass

class SAPPORecord(Record):
    pass


class BMStatusRecord(Record):

    pass


class SAPReferencePORecord(Record):
    pass

class OrderBmidRecord(Record):
    pass

class ZTEPoRecord(Record):
    pass


class BMStatus2(Record):
    pass


class PurchaseRequisitionRecord(Record):
    pass



# ------------------------------ load record


def get_ALLZteposInPath():
    """

    :return:
    """
    polist = polistReader.goThroughPolistDirectory()
    zpo_att = ['ZTE_Qty','ZTE_Origin_Mcode','ZTE_PO_Nr',
               'ZTE_Contract_No','ZTE_Material','ZTE_CM_Date',
               'ZTE_Project','ZTE_Site_ID',
               'ZTE_CM_No','ZTE_PO_Amount','rowindex']

    po_set = set()

    for zpo in polist:
        zpoObj = ZTEPoRecord(zpo_att)
        for k, v in zpo.__dict__.items():
            if k in zpo_att:
                zpoObj.__dict__[k] = fileReader.clearUnicode(v)
        po_set.add(zpoObj)

    print("ZPO non rate", len(po_set), len(polist))


    storeRawData(po_set, "Raw_ZTEPO","output/raw/")
    fileWriter.outputObjectsListToFile(po_set,'Raw_ZTEPO','output/dn_maker/')
    return po_set



def get_AllSappoInPath(path='input/po_ztematerial_to_sappo_zztepolist/' , output=True):
    """
    Using material code to ge all sappo information

    :param path:
    :param output:
    :return:
    """
    attrs = [
        u'Item_of_PO',
        u'Material',
        u'Material_Description',
        u'PO_Quantity',
        u'PurchNo',
        u'Reference_PO_Number',
    ]
    sapopo_set = set()
    rowObjs = fileReader.getAllRowObjectInPath(path)
    missing_set = set()

    # cover rows as bmboject
    for row in rowObjs:
        sappo = SAPPORecord(attrs)
        for k, v in row.__dict__.items():
            if k in attrs:
                sappo.__setattr__(k,fileReader.clearUnicode(v))
        if sappo.PurchNo and sappo.Material and sappo.Item_of_PO:
            sapopo_set.add(sappo)
        else:
            missing_set.add(sappo)



    # output
    if output:
        fileWriter.outputObjectsListToFile(sapopo_set,'Raw_SAPPO','output/dn_maker/')
        if len(missing_set) != 0:
            fileWriter.outputObjectsListToFile(list(missing_set),"Raw_SAPPPO_missing",'output/error/')
        storeRawData(sapopo_set,'Raw_SAPPO')
    print("SAP PO rate", len(sapopo_set), len(rowObjs), "Information Miss",len(missing_set))
    return sapopo_set



def get_AllSapdnInPath(path='input/po_vendor_to_sapdn_me2l/', output=True):
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
        u'Goods_recipient',
        u'Material',
        u'Order',
        u'Order_Quantity',
        u'Purchasing_Document',
        u'Still_to_be_delivered_qty',
        u'Short_Text',
        u'Item',
    ]



    drObjects_set = set()
    drRows = fileReader.getAllRowObjectInBook(fileReader.getTheNewestFileLocationInPath(path))
    missing_set = set()
    # cover rows as bmboject
    for drRow in drRows:
        drobj = DeliveryRecord(attrs)
        for k, v in drRow.__dict__.items():
            if k in attrs:
                drobj.__setattr__(k,fileReader.clearUnicode(v))
        # test if all infomation for sapdn are ok
        if drobj.Purchasing_Document and drobj.Material and drobj.Order and drobj.Still_to_be_delivered_qty:
            drObjects_set.add(drobj)
        else:
            missing_set.add(drobj)

    if output:
        fileWriter.outputObjectsListToFile(drObjects_set,'Raw_SAPDN','output/dn_maker/')
        if len(missing_set) != 0:
            fileWriter.outputObjectsListToFile(missing_set,'Raw_SAPDN_Missing','output/error/')

        storeRawData(drObjects_set,'Raw_SAP_DN')

    print("SAP DN Rate: ", len(drObjects_set), len(drRows),
          'Missing: ', len(missing_set))
    return drObjects_set


def get_AllOrderBmidInPath(path='input/po_odernr_to_order_iw39/', output=True):

    attris = [u'Equipment',u'Order',u'NotesID']

    rows = fileReader.getAllRowObjectInPath(path)
    orbmid_set = set()
    miss_set = set()

    for row in rows:
        order = OrderBmidRecord(attris)
        for k, v in row.__dict__.items():
            if k in attris:
                order.__setattr__(k,fileReader.clearUnicode(v))
        if order.Equipment and order.NotesID and order.Order:
            orbmid_set.add(order)
        else:
            miss_set.add(order)



    print("SAP Orbmid rate", len(orbmid_set), len(rows))
    if output:
        fileWriter.outputObjectsListToFile(orbmid_set, "Raw_Orbmid",'output/dn_maker/')
        storeRawData(orbmid_set, "Raw_Orbmid")
        if len(miss_set) != 0:
            fileWriter.outputObjectsListToFile(miss_set,"Raw_Orbmid_missing",'output/error/')

    return orbmid_set



def get_AllBMStatusRecordInPath(bmprojectname, inputpath='input/po_bmstatus/',
                                outputfilename=None, outputpath = None):
    """
    Read bmstatus in path

    :param inputpath:
    :param output:
    :return:
    """


    rowObjList = []
    bm_sheets = []
    #get all sheets in path
    sheets = fileReader.getAllSheetsInPath(inputpath, recursive=True)
    attris = [u'BAUMASSNAHME_ID', u'BS_FE',u'IST92',u'IST21',
              u'IST26',u'IST82',u'IST100',
              u'STRASSE', u'PLZ',u'GEMEINDE_NAME', u'PRICING',u'NBNEU',
              u'BAUMASSNAHMEVORLAGE',u'BAUMASSNAHMETYP',u'BESCHREIBUNG',
    ]
    # test if this is a good bm status list
    for sheet in sheets:
        header = fileReader.getHeaderFromSheet(sheet)
        if __contains(attris, header):
            bm_sheets.append(sheet)
        else:
            print("Error: No BM_STATUS Header", sheet.name, sheet.filename)

    for bm_sheet in bm_sheets:
        rowObjs = fileReader.covertSheetRowIntoRowObjectFromSheet(bm_sheet)
        rowObjList.extend(rowObjs)

    # addint to list
    bm_set = set()
    for row in rowObjList:
        bmobj = BMStatusRecord(attris)
        for k, v in row.__dict__.items():
            if k in attris:
                bmobj.__setattr__(k,fileReader.clearUnicode(v))
        bmobj.BM_SOURCE = row.Source
        bm_set.add(bmobj)



    print("BM rate", len(bm_set), len(rowObjList))

    if not outputfilename:
        outputfilename = "Raw_Bmstatus"
    if not outputpath:
        outputpath = "output/dn_maker/"

    if bmprojectname:
        outputfilename = outputfilename+"_"+ bmprojectname



    fileWriter.outputObjectsListToFile(bm_set,outputfilename,outputpath)
    storeRawData(bm_set,outputfilename,'output/raw/')

    return bm_set



def get_AllPurchesingRequestionsInPath(path="input/po_vendor_to_purchaserequest_me5a/", output=True):
    """

    :param path:
    :return:
    """
    attris = [
            u'Deletion_Indicator',
            u'Delivery_Date',
            u'Item_of_Requisition',
            u'Material',
            u'Name_of_Vendor',
            u'Order',
            u'Purchase_Order',
            u'Purchase_Order_Date',
            u'Purchase_Order_Item',
            u'Purchase_Requisition',
    ]

    drRows = fileReader.getAllRowObjectInBook(fileReader.getTheNewestFileLocationInPath(path))

    pr_set = set()
    # cover rows as bmboject
    for row in drRows:
        prObj = PurchaseRequisitionRecord(attris)
        for k, v in row.__dict__.items():
            if k in attris:
                prObj.__setattr__(k,fileReader.clearUnicode(v))
        if prObj.Order and prObj.Material and prObj.Purchase_Order and prObj.Purchase_Requisition:
            pr_set.add(prObj)

    if output:
        fileWriter.outputObjectsListToFile(pr_set,'Raw_SAPPR','output/dn_maker/')

        storeRawData(pr_set,'Raw_SAP_PR')
    print("SAP DN Rate: ", len(pr_set), len(drRows))
    return pr_set










# ----------------------------------- help functions ----------------------

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

    with open(path + filename+ '.raw', 'wb') as f:
        pickle.dump(object, f)
    print("Store Objects in " +  path + filename +'.raw')





