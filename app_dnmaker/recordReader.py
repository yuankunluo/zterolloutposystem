__author__ = 'yuluo'
import tools.fileReader as fileReader
import tools.fileWriter as fileWriter
import pickle
import datetime
import os
import re
import copy
from tools.fileReader import ExcelRowObject


class DeliveryRecord(ExcelRowObject):
    pass


class BMStatusRecord(ExcelRowObject):

    pass

class SAPReferencePORecord(ExcelRowObject):
    pass

class OrderBmidRecord(ExcelRowObject):
    pass

class ZTEPoRecord(ExcelRowObject):
    pass



def __getAllSapReferencesPoFromZTEPOInPath(path = 'input/po_zte_to_sap/'):
    rows = fileReader.getAllRowObjectInPath(path)
    sappoObjects = []

    attrs = [u'Reference_PO_Number',u'Material',u'Item_of_PO',u'Order',u'Material_Description',u'PurchNo']

    for drRow in rows:
        sapPO = SAPReferencePORecord()
        sapPO = initWithAttrsToNone(sapPO, attrs)
        for k, v in drRow.__dict__.items():
            if k in sapPO.__dict__:
                sapPO.__dict__[k] = fileReader.clearUnicode(v)
        sappoObjects.append(sapPO)

    return sappoObjects


def get1_AllMixedZtePowithSapPoFromPath(ztepopath='input/po_newest_polist',
                                      referencepopath = 'input/po_zte_to_sap/', output=False):
    rows = fileReader.getAllRowObjectInPath(ztepopath)
    ztePos = []
    # initialize ztePos
    for row in rows:
        ztePo = ZTEPoRecord()
        for k, v in row.__dict__.items():
            ztePo.__dict__[k] = fileReader.clearUnicode(v)
        ztePos.append(ztePo)
    count = len(ztePos)

    # get references po
    ref_Pos = __getAllSapReferencesPoFromZTEPOInPath()
    ref_list = list(set([(ref.Reference_PO_Number, ref.PurchNo) for ref in ref_Pos]))

    cleanZpos = []
    # add on sappo to ztepo
    for zpo in ztePos:
        if not zpo.SAP_PO_Nr:
            refs = [ref.PurchNo for ref in ref_Pos if ref.Reference_PO_Number == zpo.ZTE_PO_Nr]
            refs = set(refs)
            if len(refs) == 1:
                # only one found
                zpo.SAP_PO_Nr = refs.pop()
                cleanZpos.append(zpo)
            elif len(refs) == 0:
                # no one found
                print("Error: find none SAP po for reference", zpo.ZTE_PO_Nr, refs)
            else: # zte po and sap po not 1 one to one
                print("Warning: found one ZTE PO to more refs",zpo.ZTE_PO_Nr, refs)
                for ref in refs:
                    newZPO = copy.deepcopy(zpo)
                    newZPO.SAP_PO_Nr = ref
                    cleanZpos.append(newZPO)
    # get useful  zte po
    cleanZpos = [po for po in cleanZpos if po.ZTE_PO_Nr is not None
            and po.Material_Code is not None
            and po.Qty is not None
            and po.Site_ID is not None
            and po.SAP_PO_Nr is not None]

    count2 = len(cleanZpos)

    if output:
        storeRawData(ztePos, 'Raw_1_zte_pos')
    print("ZTE Po list ok rate", count2, count)
    return cleanZpos



def get2_AllSapOrderBmidInPath(path = 'input/po_oder_bmid/', output = False):

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
        sapPO = initWithAttrsToNone(sapPO, attris)
        for k, v in drRow.__dict__.items():
            if k in attris:
                sapPO.__dict__[k] = fileReader.clearUnicode(v)
        sappoObjects.append(sapPO)

    if output:
        storeRawData(sappoObjects,'Raw_2_order_to_bmid')

    result = deleteDuplicate(sappoObjects)

    return result



def get0_AllSapDeleiveryRecordInPath(path='input/po_deliver_records/', output=False):
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
        ]



    drObjects = []
    drRows = fileReader.getAllRowObjectInPath(path)
    print("Read rows",len(drRows))

    for drRow in drRows:
        drobj = DeliveryRecord()
        drobj = initWithAttrsToNone(drobj, attrs)
        for k, v in drRow.__dict__.items():
            if k in attrs:
                drobj.__dict__[k] = fileReader.clearUnicode(v)
        drObjects.append(drobj)

    drObjects = [dn for dn in drObjects if dn.Deletion_Indicator == None
                and int(dn.Still_to_be_delivered_qty) != 0]

    #drObjects = deleteDuplicate(drObjects)

    if output:
        storeRawData(drObjects, 'Raw_0_sap_dn')
    return drObjects


def get3_AllBMStatusRecordInPath(path='input/po_bmstatus/', output=False):

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
              u'STRASSE', u'PLZ',u'GEMEINDE_NAME', u'PRICING']

    for rowObj in rowObjList:
        bmObj = BMStatusRecord()
        bmObj = initWithAttrsToNone(bmObj, attris)
        for k, v in rowObj.__dict__.items():
            if k in attris:
                bmObj.__dict__[k] = fileReader.clearUnicode(v)
        bmObjects.append(bmObj)


    # delete all has no IST92
    # count = len(bmObjects)
    # bmObjects = [bms for bms in bmObjects if bms.IST92]
    # count2 = len(bmObjects)
    # print("BMstatus have IST92", count2, count)

    result = deleteDuplicate(bmObjects)

    if output:
        storeRawData(result,'Raw_3_bm_status')

    return result




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

def storeRawData(object, filename, path='input/raw/'):
    tims = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    try:
        with open(path + filename + "_" + tims + '.raw', 'wb') as f:
            pickle.dump(object, f)
        print("Store Objects in " +  path + filename + "_" + tims + '.raw')
    except Exception:
        print(Exception.message)
        print("Error:storeRawData," + path + filename + "_" + tims + '.raw')


def deleteDuplicate(objectsList):
    result = []
    for obj in objectsList:
        if obj not in objectsList:
            result.append(obj)
    print("Duplicate Rate:", len(objectsList)- len(result), len(objectsList))
    return result