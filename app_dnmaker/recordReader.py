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




class BMStatusRecord(Record):

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
    sappoObjects = deleteDuplicate(sappoObjects)
    return sappoObjects


def get1_AllMixedZtePowithSapPoFromPath(ztepopath='output/polist',
                                      referencepopath = 'input/po_zte_to_sap/', output=True):
    rows1 = fileReader.getAllRowObjectInBook(fileReader.getTheNewestFileLocationInPath(ztepopath))
    rows2 = fileReader.getAllRowObjectInBook(fileReader.getTheNewestFileLocationInPath(referencepopath))

    ztePos = []
    error = []
    refCount = []
    # # initialize ztePos
    # for row in rows1:
    #     ztePo = ZTEPoRecord()
    #     for k, v in row.__dict__.items():
    #         ztePo.__dict__[k] = fileReader.clearUnicode(v)
    #     ztePos.append(ztePo)
    # count = len(ztePos)
    # print("Read %d ZTEPO from polist"%(count))
    #
    # referenct_dict = {}
    # for ref in rows2:
    #     if ref.Reference_PO_Number:
    #         referenct_dict[ref.Reference_PO_Number] = set()
    #         if ref.Reference_PO_Number not in referenct_dict:
    #             referenct_dict[ref.Reference_PO_Number].add((
    #                 ref.Reference_PO_Number,ref.Order, ref.PurchNo
    #             ))
    #
    # for zpo in ztePos:
    #     if zpo.ZTE_PO_Nr and zpo.ZTE_PO_Nr in referenct_dict:
    #         ref_list = list(referenct_dict[zpo.ZTE_PO_Nr])
    #         if len(ref_list) == 1:
    #             ref_tup = ref_list[0]
    #             zpo.SAP_PO_Nr = ref_tup[2]
    #             refCount += 1
    #         else:
    #             error.extend(ref_list)
    #
    # cleanZpos = [po for po in ztePos
    #             if po.ZTE_PO_Nr
    #             and po.Material_Code
    #             and po.Qty
    #             and po.Site_ID
    #             and po.SAP_PO_Nr]
    #
    # for czpo in cleanZpos:
    #     czpo.Unique_ZTE_PM = '-'.join([czpo.SAP_PO_Nr, czpo.Material_Code])
    # if output:
    #     storeRawData(ztePos, 'Raw_1_ztepos_all')
    #     storeRawData(cleanZpos, 'Raw_1_ztepos_clean')
    #     storeRawData(error, 'Raw_1_ztepos_error')
    #     fileWriter.outputObjectsToFile(ztePos,'Raw_1_MIXedztepos_all_','output/raw/')
    #     fileWriter.outputObjectsToFile(cleanZpos,'Raw_1_MIXedztepos_clean','output/raw/')
    #     fileWriter.outputObjectsToFile(error,'Raw_1_MIXedztepos_error','output/error/')
    #
    # print("Mixed rate:", len(cleanZpos), len(ztePos), "error",len(error), 'Refrences', refCount)

    return cleanZpos




def get2_AllOrderBmidInPath(path = 'input/po_oder_bmid/', output = True):

    attris = [
             u'Equipment',
             u'Order',
             u'NotesID'
    ]

    rows = fileReader.getAllRowObjectInPath(path)
    orbmid = []
    dupCount = 0
    for drRow in rows:
        sapPO = OrderBmidRecord()
        sapPO = initWithAttrsToNone(sapPO, attris)
        for k, v in drRow.__dict__.items():
            if k in attris:
                sapPO.__dict__[k] = fileReader.clearUnicode(v)
        if sapPO not in orbmid:
            orbmid.append(sapPO)
        else:
            dupCount += 1

    if output:
        storeRawData(orbmid,'Raw_2_order_to_bmid')
        fileWriter.outputObjectsToFile(orbmid,'Raw_2_OrderBMID','output/raw/')
    print("ORBMID rate", len(orbmid), len(rows), 'Duplicate', dupCount)
    return orbmid



def get0_AllSapDeleiveryRecordInPath(path='input/po_deliver_records/', output=True):
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
        drobj.Unique_PM = '-'.join([drobj.Purchasing_Document, drobj.Material])
        drObjects.append(drobj)
    alldrObjects = [dn for dn in drObjects if dn.Deletion_Indicator == None
                # and int(dn.Still_to_be_delivered_qty) != 0
    ]
    drObjects = [dn for dn in drObjects if dn.Deletion_Indicator == None
                and int(dn.Still_to_be_delivered_qty) != 0
    ]
    #drObjects = deleteDuplicate(drObjects)
    if output:
        fileWriter.outputObjectsToFile(drObjects,'Raw_0_SAPDN_clean','output/raw/')
        storeRawData(drObjects, 'Raw_0_sap_dn_clean')
        fileWriter.outputObjectsToFile(alldrObjects,'Raw_0_SAPDN_all','output/raw/')
        storeRawData(alldrObjects, 'Raw_0_sap_dn_all')
    print("SAPDN clean (still to be del.) rate", len(drObjects), len(alldrObjects))
    return drObjects


def __get_AllBM2StatusRecordInPath(path='input/po_bmstatus2/', output=True):
    rowObjes = fileReader.getAllRowObjectInPath(path)
    bm2List = []
    att_regx = {
         'BAUMASSNAHME_ID':'BAUMASSNAHME_ID$',
         'BS_FE':'BS_FE$|Site_ID$',
         'ZTE_PO':'HW_PO$|PO$',
         'IST92':'IST92$',
        'PRICING':'PRICING$',
        'Source':'Source',
    }

    for rowobj in rowObjes:
        bmStu2 = BMStatus2()
        bmStu2 = initWithAttrsToNone(bmStu2, att_regx.keys())
        bmStu2 = fileReader.coverRowobjIntoObjWithHeader(rowobj,bmStu2,att_regx)
        if bmStu2.ZTE_PO and bmStu2.BAUMASSNAHME_ID and bmStu2.PRICING:
            bm2List.append(bmStu2)

    if output:
        storeRawData(bm2List, 'Raw_3_bmstatus2')
        fileWriter.outputObjectsToFile(bm2List, 'RAW_3_bmstatus2','output/raw/')
    return bm2List



def get3_AllBMStatusRecordInPath(path='input/po_bmstatus/', output=True):

    bmObjects = []

    rowObjList = []
    bm_sheets = []
    #get all sheets in path
    sheets = fileReader.getAllSheetsInPath(path, recursive=True)
    # test header
    test_header = [u'BAUMASSNAHME_ID', u'BS_FE', u'GEMEINDE_NAME',u'IST92', u'PLZ',u'STRASSE']
    # test if this is a good bm status list
    for sheet in sheets:
        header = fileReader.getHeaderFromSheet(sheet)
        if __contains(test_header, header):
            bm_sheets.append(sheet)
        else:
            print("Error"
                  ": No BM_STATUS Header", sheet.name, sheet.filename,
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
    bmstatus2 = __get_AllBM2StatusRecordInPath()
    bmstatus_dict = {}
    for bm2 in bmstatus2:
        if bm2.BAUMASSNAHME_ID not in bmstatus_dict:
            bmstatus_dict[bm2.BAUMASSNAHME_ID] = set()
            bmstatus_dict[bm2.BAUMASSNAHME_ID].add((bm2.BAUMASSNAHME_ID, bm2.IST92))
        else:
            bmstatus_dict[bm2.BAUMASSNAHME_ID].add((bm2.BAUMASSNAHME_ID, bm2.IST92))

    addonCount = 0
    for bm in bmObjects:
        if not bm.IST92:
            if bm.BAUMASSNAHME_ID in bmstatus_dict:
                bm2_set = bmstatus_dict[bm.BAUMASSNAHME_ID]
                bm2_list = list(bm2_set)
                bm2_list = [bm2_tuple for bm2_tuple in bm2_list if bm2_tuple[1] != None]
                if len(bm2_list) != 0:
                    bm.IST02 = bm2_list[0][1]
                    addonCount += 1

    result = deleteDuplicate(bmObjects)
    bm92 = [bm for bm in bmObjects if bm.IST92]

    if output:
        fileWriter.outputObjectsToFile(result,'RAW_3_BMSTATUS_all','output/raw/')
        storeRawData(result,'Raw_3_bm_status_all')
        fileWriter.outputObjectsToFile(bm92,'RAW_3_BMSTATUS_ist92','output/raw/')
        storeRawData(bm92,'Raw_3_bm_status_ist92')
    print("BM STATUS IST 92 Rate:", len(bm92), len(result), 'Addon', addonCount)
    return bm92




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
        with open(path + filename+ '.raw', 'wb') as f:
            pickle.dump(object, f)
        print("Store Objects in " +  path + filename +'.raw')
    except Exception:
        print(Exception.message)
        print("Error:storeRawData," + path + filename + '.raw')


def deleteDuplicate(objectsList):
    result = []
    for obj in objectsList:
        if obj not in result:
            result.append(obj)
        # else:
        #     print(obj.__dict__)
    print("Duplicate Rate:", len(objectsList)- len(result), len(objectsList))
    return result