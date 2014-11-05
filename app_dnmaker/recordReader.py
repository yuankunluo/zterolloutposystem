__author__ = 'yuluo'
import tools.fileReader as fileReader
import pickle
import datetime
import os
import re

class DeliveryRecord(object):
    pass


class BMStatusRecord(object):
    pass

class SAPPORecord(object):
    pass

class OrderBmidRecord(object):
    pass



def __getAllSapPoFromZTEPOInPath(path = 'input/po_zte_to_sap/'):
    rows = fileReader.getAllRowObjectInPath(path)
    sappoObjects = []

    for drRow in rows:
        sapPO = SAPPORecord()
        for k, v in drRow.__dict__.items():
            sapPO.__dict__[k] = fileReader.clearUnicode(v)
        sappoObjects.append(sapPO)

    return sappoObjects






def getAllSapOrderBmidInPath(path = 'input/po_oder_bmid/'):

    attris = [u'Purchase_order_number',
             u'Description',
             u'Equipment',
             u'Oberbaumassnahme',
             u'Order',
             u'User_Status',
             u'NotesID']

    rows = fileReader.getAllRowObjectInPath(path)
    sappoObjects = []

    for drRow in rows:
        sapPO = OrderBmidRecord()
        sapPO = initWithAttrs(sapPO, attris)
        for k, v in drRow.__dict__.items():
            if k in attris:
                sapPO.__dict__[k] = fileReader.clearUnicode(v)
        sappoObjects.append(sapPO)
    return sappoObjects



def getAllSapDeleiveryRecordInPath(path='input/po_deliver_records/', output=False):
    """
    Reads the sap output using ME2L, with vendor nr: 5043096
    Change to account_view and layout, to put all header in table.

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
        u'Unique_PO_MC'
        ]



    drObjects = []
    drRows = fileReader.getAllRowObjectInPath(path)

    for drRow in drRows:
        drobj = DeliveryRecord()
        drobj = initWithAttrs(drobj, attrs)
        for k, v in drRow.__dict__.items():
            if k in attrs:
                drobj.__dict__[k] = fileReader.clearUnicode(v)
        try:
            drobj.Unique_PO_MC = '-'.join([drobj.Purchasing_Document, drobj.Material])
        except Exception:
            print("Error: Unique_PO_MC", drobj.Purchasing_Document, drobj.Material)
        drObjects.append(drobj)

    count_all = len(drObjects)
    drObjects = [dn for dn in drObjects if dn.Deletion_Indicator == None]
    count_del = len(drObjects)
    drObjects = [dn for dn in drObjects if int(dn.Still_to_be_delivered_qty) != 0]
    print('All SAP_DN', count_all, ' To be delivery', len(drObjects))

    if output:
        storeRawData(drObjects, 'sap_dn')
    return drObjects


def getAllBMStatusRecordInPath(path='input/po_bmstatus/', output=False):

    bmObjects = []

    rowObjList = []
    bm_sheets = []
    #get all sheets in path
    sheets = fileReader.getAllSheetsInPath(path, recursive=True)
    # test header
    test_header = [u'BAUMASSNAHME_ID', u'BS_FE', u'GEMEINDE_NAME',u'IST1092', u'PLZ',u'STRASSE']
    # test if this is a good bm status list
    for sheet in sheets:
        header = fileReader.getHeaderFromSheet(sheet)
        # if __contains(test_header, header):
        #     bm_sheets.append(sheet)
        if len(header) >= 230:
            bm_sheets.append(sheet)
        else:
            print("Error: No BM_STATUS Header", sheet.name, sheet.filename,
                  'Header Length', len(header))

    for bm_sheet in bm_sheets:
        rowObjs = fileReader.covertSheetRowIntoRowObjectFromSheet(bm_sheet)
        rowObjList.extend(rowObjs)

    attris = [u'BAUMASSNAHME_ID', u'BS_FE',u'BS_STO',u'BS_FE',u'IST92',
              u'STRASSE', u'PLZ',u'GEMEINDE_NAME', u'PRICING','Unique_BM_BS']

    for rowObj in rowObjList:
        bmObj = BMStatusRecord()
        bmObj = initWithAttrs(bmObj, attris)
        for k, v in rowObj.__dict__.items():
            if k in attris:
                bmObj.__dict__[k] = fileReader.clearUnicode(v)
        bmObjects.append(bmObj)


    if output:
        storeRawData(bmObjects,'bm_status')

    return bmObjects




def initWithAttrs(obj, attrisList):
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
    return fileDict

def storeRawData(object, filename, path='input/raw/'):
    tims = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    try:
        with open(path + filename + "_" + tims + '.raw', 'wb') as f:
            pickle.dump(object, f)
        print("Store Objects in " +  path + filename + "_" + tims + '.raw')
    except Exception:
        print(Exception.message)
        print("Error:storeRawData," + path + filename + "_" + tims + '.raw')





