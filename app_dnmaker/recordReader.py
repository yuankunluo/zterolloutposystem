__author__ = 'yuluo'
import tools.fileReader as fileReader
import tools.fileWriter as fileWriter
import pickle
import datetime
import os
import re


class DeliveryRecord(object):
    pass


class BMStatusRecord(object):
    pass

class SAPReferencePORecord(object):
    pass

class OrderBmidRecord(object):
    pass

class ZTEPoRecord(object):
    pass



def getAllSapReferencesPoFromZTEPOInPath(path = 'input/po_zte_to_sap/'):
    rows = fileReader.getAllRowObjectInPath(path)
    sappoObjects = []

    for drRow in rows:
        sapPO = SAPReferencePORecord()
        for k, v in drRow.__dict__.items():
            sapPO.__dict__[k] = fileReader.clearUnicode(v)
        sappoObjects.append(sapPO)

    return sappoObjects


def getAllMixedZtePowithSapPoFromPath(ztepopath='input/po_newest_polist',
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
    ref_Pos = getAllSapReferencesPoFromZTEPOInPath()
    ref_list = list(set([(ref.Reference_PO_Number, ref.PurchNo) for ref in ref_Pos]))

    # add on sappo to ztepo
    for zpo in ztePos:
        if not zpo.SAP_PO_Nr:
            refs = [ref.PurchNo for ref in ref_Pos if ref.Reference_PO_Number == zpo.ZTE_PO_Nr]
            refs = set(refs)
            if len(refs) == 1:
                zpo.SAP_PO_Nr = refs.pop()
            elif len(refs) == 0:
                print("Error: find more or none SAP po for reference", zpo.ZTE_PO_Nr, refs)
            else:
                pass
    # get useful  zte po
    cleanZpos = [po for po in ztePos if po.ZTE_PO_Nr is not None
            and po.Material_Code is not None
            and po.Qty is not None
            and po.Site_ID is not None
            and po.SAP_PO_Nr is not None]

    count2 = len(cleanZpos)

    # output error po
    errorpos = []
    for zpo in ztePos:
        if zpo not in cleanZpos:
            errorpos.append(zpo)
    fileWriter.outputObjectsToFile(errorpos,'Problem_ZTEPO','output/error/')

    if output:
        storeRawData(ztePos, 'zte_pos')
    print("ZTE Po list ok rate", count2, count)
    return cleanZpos



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
        sapPO = initWithAttrsToNone(sapPO, attris)
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
        drobj = initWithAttrsToNone(drobj, attrs)
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
        bmObj = initWithAttrsToNone(bmObj, attris)
        for k, v in rowObj.__dict__.items():
            if k in attris:
                bmObj.__dict__[k] = fileReader.clearUnicode(v)
        bmObjects.append(bmObj)

    if output:
        storeRawData(bmObjects,'bm_status')

    return bmObjects




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





