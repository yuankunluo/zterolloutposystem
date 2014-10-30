__author__ = 'yuluo'

import app_po.polistReader as por
import recordReader as sapReader
import datetime
import pickle
from collections import Counter
import tools.fileWriter as fileWriter

def getAllDataAndWriteToFileDict():
    """

    :return:
    """


    # first read data from xls
    # the po objects from zte d
    zte_PORecords = por.goThroughPolistDirectory(path='input/po_polist/', output=False)
    # the sap po from zte po
    sap_PORecords = sapReader.getAllSapPoFromZTEPOInPath(path ='input/po_zte_to_sap/')
    # the delivery records from sap
    sap_DNRecords = sapReader.getAllSapDeleiveryRecordInPath(path='input/po_deliver_records/')
    # get bmidrecords
    bm_STRecors = sapReader.getAllBMStatusRecordInPath(path='input/po_bmstatus/')
    # get order-bmid record
    orbm_Records = sapReader.getAllSapOrderBmidInPath(path = 'input/po_oder_bmid/')



    # output the problem po


    fileDict = {
        "zte_PORecords": zte_PORecords,
        "sap_PORecords":sap_PORecords,
        "sap_DNRecords": sap_DNRecords,
        "bm_STRecors": bm_STRecors,
        "orbm_Records": orbm_Records
    }


    now = __getNowAsString()
    with open("input/raw/fileDict_" + now + '.data','wb') as f:
        pickle.dump(fileDict, f)

    print("Stored raw data")

    return fileDict


def loadRawData(path):
    fileDict = None
    with open(path, 'rb') as f:
        fileDict = pickle.load(f)
    return fileDict


def checkZTEPowithSAPLieferRecordAndOutput(fileDict):
    """

    :param fileDict:
    :return:
    """
    zte_PORecords = fileDict["zte_PORecords"]
    sap_DNRecords = fileDict["sap_DNRecords"]
    sap_PORecords = fileDict["sap_PORecords"]
    # orbm_Records = fileDict["orbm_Records"]



    # step1: delete sap_dn with delection indicator
    sap_DNRecords = [sapdn for sapdn in sap_DNRecords if sapdn.Deletion_Indicator is None]

    # step2: add sappo to ztepo
    zte_PORecords = addSPAPotoZtePo(sap_PORecords, zte_PORecords)

    # step3: compare ztepo with sappo
    # count = 0
    # for ztepo in zte_PORecords:
    #     if ztepo.SAP_PO_Nr is None:
    #         continue
    #     mcode = (ztepo.Material_Code, ztepo.Qty)
    #     sap_mcodes = [(spn.Material, spn.Order_Quantity) for spn in sap_DNRecords
    #                   if spn.Purchasing_Document == ztepo.SAP_PO_Nr]
    #     ztepo.SAP_RECORDS = unicode(__mixListofTupleofMaterialCode(sap_mcodes))
    #     if mcode in sap_mcodes:
    #         ztepo.Same_In_SAP = True
    #         continue
    #     else:
    #         ztepo.Same_In_SAP = False


    

    now = __getNowAsString()

    try:
        fileWriter.outputObjectsToFile(zte_PORecords, "PO_With_Problem_" + now , 'output/po_problem/')
        print("Output file in output/po_problem")
    except Exception:
        print("Problem with output")
    return zte_PORecords

def __mixListofTupleofMaterialCode(listoftuple):
    result = []
    materials = [x[0] for x in listoftuple]
    materials = set(materials)
    mDict = {}
    for mc in materials:
        qty_for_mc = [int(x[1]) for x in listoftuple if x[0] == mc]
        sum_qty = sum(qty_for_mc)
        result.append((mc, unicode(sum_qty)))




def __getNowAsString():
    now = datetime.datetime.now()
    now = now.strftime("%Y%m%d_%H%M%S")
    return now


def mixFile(fileDict):

    zte_PORecords = fileDict["zte_PORecords"]
    sap_PORecords = fileDict["sap_PORecords"]
    sap_DNRecords = fileDict["sap_DNRecords"]
    bm_STRecors = fileDict["bm_STRecors"]
    orbm_Records = fileDict["orbm_Records"]

    result = []
    # step0: using sappo records to fill the ztepo record
    zte_PORecords = addSPAPotoZtePo(sap_PORecords, zte_PORecords)
    # step1:
    # delete all sap_dnRedords with Delection_Indictor
    # delete all order that has still to be delivery
    sap_DNRecords  = deleteAlreadyDeliverydFromSPDnRecord(sap_DNRecords)
    # step2: adding site id to SAP_DN
    sap_DNRecords  = addSiteIDTOSPDnRecordFromOrderBmRecord(sap_DNRecords, orbm_Records)
    # step3: add neid/BMID to sapdn_record
    sap_DNRecords = addBMIDToSapDNFromOrderBmid(sap_DNRecords, orbm_Records)
    # # step4: add bmid status to dn_record
    sap_DNRecords = addBMIDStatusToSapDNRecordFromBMStatus(sap_DNRecords, bm_STRecors)
    # step5: combain ztepo with dn_record
    for sap_dn in sap_DNRecords:
        if sap_dn.NotesID and sap_dn.Purchasing_Document and sap_dn.Material:
            sap_dn.Unique_SPM = '-'.join([sap_dn.Equipment, sap_dn.Purchasing_Document, sap_dn.Material])
            ztepos = [zpo for zpo in zte_PORecords if zpo.Unique_SPM == sap_dn.Unique_SPM]
            ztepos = list(set(ztepos))
            if len(ztepos) == 1:
                print("OK Step5: Match SAPDN with ZTEPO")
                zpo = ztepos[0]
                for k, v in sap_dn.__dict__.items():
                    zpo.__dict__[k] = v
                result.append(zpo)

    return result



def deleteAlreadyDeliverydFromSPDnRecord(sap_DNRecords):
    """
    Delete all SAP DN Record, which was deleted or has nothing to delivery

    :param sap_DNRecords: SPA DN Records
    :return: the modified DN Records
    """
    count1 = len(sap_DNRecords)
    ddns = [sdn for sdn in sap_DNRecords if sdn.Deletion_Indicator == 'L']
    for ddn in ddns:
        sap_DNRecords.remove(ddn)
    count2 = len(sap_DNRecords)
    sap_DNRecords = [sdn for sdn in sap_DNRecords if int(sdn.Still_to_be_delivered_qty) != 0]
    print("Delete sap_DNRecords processing: ", count1, count2, len(sap_DNRecords))
    return sap_DNRecords


def addSiteIDTOSPDnRecordFromOrderBmRecord(sap_DNRecords, orbm_Records):
    """
    Adding SiteID (BSFE/ Equipment) to SPA_DN Record

    :param sap_DNRecords:  the SAP DN record
    :param orbm_Records: the order-bmid record
    :return: the modified SAP DN Record
    """
    # step2: add site id to dn_record
    for sap_dn in sap_DNRecords:
        if sap_dn.Order:
            site_ids = [orbm.Equipment for orbm in orbm_Records if orbm.Order == sap_dn.Order]
            site_ids = list(set(site_ids))
            if len(site_ids) == 1:
                sap_dn.Equipment = site_ids[0]
            else:
                sap_dn.Equipment = None
                print("Error Step1: find more site_id for order", sap_dn.Order, site_ids)
    return sap_DNRecords


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


def addBMIDToSapDNFromOrderBmid(sap_DNRecords, orbm_Records):
    """

    :param sap_DNRecords:
    :param orbm_Records:
    :return:
    """
    for sap_dn in sap_DNRecords:
        if sap_dn.Equipment and sap_dn.Order: # if this dn has site_id
            NotesIDs = [orbm.NotesID for orbm in orbm_Records if orbm.Order == sap_dn.Order
                        and orbm.Equipment == sap_dn.Equipment]
            NotesIDs = list(set(NotesIDs))
            if len(NotesIDs) == 1: # make sure has only on site_id
                sap_dn.NotesID = NotesIDs[0]
            else:
                sap_dn.NotesID = None
                print("Error Step3: find zero or more NotesID for order", sap_dn.Order, sap_dn.Equipment, NotesIDs)


def addBMIDStatusToSapDNRecordFromBMStatus(sap_DNRecords, bm_STRecors):
    for sap_dn in sap_DNRecords:
        if sap_dn.NotesID and sap_dn.Equipment: # if has bmid
            bms = [bm for bm in bm_STRecors if bm.BAUMASSNAHME_ID == sap_dn.NotesID
                   and bm.BS_FE == sap_dn.Equipment and bm.IST92 is not None]
            bms = list(set(bms))
            if len(bms) == 1: #only one record
                bm = bms[0]
                sap_dn.IST92 = bm.IST92
                sap_dn.STRASSE = bm.STRASSE
                sap_dn.PLZ = bm.PLZ
                sap_dn.PRICING = bm.PRICING
                sap_dn.GEMEINDE_NAME = bm.GEMEINDE_NAME
                print("OK Step4: Find bmid status for sap_dn %bmid", sap_dn.NotesID, sap_dn.Equipment, len(bms))
            else:
                sap_dn.IST92 = None
                sap_dn.STRASSE = None
                sap_dn.PLZ = None
                sap_dn.PRICING = None
                sap_dn.GEMEINDE_NAME = None
                print("Error Step4:: find zero or more BMID Recorf for NotesID", sap_dn.NotesID,'Equipment', sap_dn.Equipment, len(bms))



if __name__ == '__main__':
    getAllDataAndWriteToFileDict()












