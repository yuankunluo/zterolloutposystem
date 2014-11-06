__author__ = 'yuluo'

import app_po.polistReader as poReader
import recordReader as recordReader
import datetime
import pickle
from collections import Counter
import tools.fileWriter as fileWriter
import copy

def getAllDataAndWriteToFileDict():
    """

    :return:
    """
    pass




def step1_addingBMIDtoSapdn(sapdns, orbmids, output=True):
    """
    Combine bmid to delievery record

    :param sapdns:
    :param orbmids:
    :return:
    """
    result = []
    matchCount = 0
    nonmatchCount = 0
    doubleMatchCount = 0
    for sapdn in sapdns:
        # initial
        sapdn.Equipment = None
        sapdn.NotesID = None

        orbm_list = [(orbm.Equipment, orbm.NotesID) for orbm in orbmids if
                     orbm.Order == sapdn.Order and orbm.Equipment and orbm.NotesID]
        orbm_list = list(set(orbm_list))

        if len(orbm_list) == 1:
            # one-to-one
            sapdn.Equipment = orbm_list[0][0]
            sapdn.NotesID = orbm_list[0][1]
            matchCount += 1
            result.append(sapdn)
        if len(orbm_list) == 0:
            # no bmid for this order
            #print("Error: no BMID for order", sapdn.Order, orbm_list)
            nonmatchCount += 1
        if len(orbm_list) > 1:
            # one-to-more relation
            print("Warning: One-to-More Order to Bmid",sapdn.Order, orbm_list)
            for orbm_tup in orbm_list:
                newSapdn = copy.deepcopy(sapdn)
                newSapdn.Equipment = orbm_tup[0]
                newSapdn.NotesID = orbm_tup[1]
                result.append(newSapdn)
                doubleMatchCount += 1
    print("Stat:", 'Match',matchCount, 'Doublematch', doubleMatchCount, 'Nonmatch', nonmatchCount)
    print("Adding BMID to SAP rate",len(result), len(sapdns))

    if output:
        fileWriter.outputObjectsToFile(result,
                                       'Step1_result_' + fileWriter.getNowAsString(),
                                       'output/dn_maker/')
        recordReader.storeRawData(result,"Result_1_SAPDN_with_BMID")
    return result


def step2_addBMstatusToSapdn(result1, bmstatus, output=True):
    """

    :param result1:
    :param bmstatus:
    :return:
    """
    result = []
    matchCount = 0
    noMatchCount = 0
    doubleCount = 0
    for sapdn in result1:
        bmstatus_list = [bm for bm in bmstatus if bm.BAUMASSNAHME_ID == sapdn.NotesID
                         and bm.BS_FE == sapdn.Equipment and bm.IST92]
        bmstatus_list = list(set(bmstatus_list))

        if len(bmstatus_list) != 0:
            bmObj = bmstatus_list[0]
            for k, v in bmObj.__dict__.items():
                sapdn.__dict__[k] = v
            matchCount += 1
            result.append(sapdn)
        if len(bmstatus_list) == 0:
            # print("Error: No BMstatus for this sapdn", sapdn.Order,sapdn.NotesID)
            noMatchCount += 1
        if len(bmstatus_list) > 1:
            elist = [(bm.BAUMASSNAHME_ID, bm.BS_FE) for bm in bmstatus_list]
            print("Error: Find more BMstatus for this sapdn", sapdn.Order,sapdn.NotesID,
                  elist)
            doubleCount += 1

    print("Stat Match:", 'Match',matchCount, 'Doublematch', doubleCount, 'Nonmatch', noMatchCount)
    countALL = len(result)
    result = [r for r in result if r.IST92]
    count92 = len(result)
    print("Stat IST92 rate", count92, countALL)
    if output:
        fileWriter.outputObjectsToFile(result,
                                       'Step2_result_' + fileWriter.getNowAsString(),
                                       'output/dn_maker/')
        recordReader.storeRawData(result,"Result_2_SAPDN_with_BMID_BMSTATUS")

    return result

def step3_FilterOnlyZTEPO(result2, ztepos, output=True):
    """

    :param result2:
    :param ztepos:
    :return:
    """
    result = []

    # create unique_pm for ztepos
    for ztepo in ztepos:
        if ztepo.SAP_PO_Nr and ztepo.Material_Code:
            ztepo.Unique_PM = '-'.join([ztepo.SAP_PO_Nr,ztepo.Material_Code])
        else:
            ztepo.Unique_PM = None

    noMatchSAPDN = []
    doubleSAPDN = []
    matchCount = 0
    noMatchCount = 0
    doubleCount = 0
    for sapdn in result2:
        # make sure these two data is not none
        if sapdn.Purchasing_Document and sapdn.Material:
            Unique_PM = '-'.join([sapdn.Purchasing_Document, sapdn.Material])
            zpo_list = [zpo for zpo in ztepos if zpo.Unique_PM and zpo.Unique_PM == Unique_PM]
            zpo_list = list(set(zpo_list))
            # one to one
            if len(zpo_list) == 1:
                zpo = zpo_list[0]
                for k, v in zpo.__dict__.items():
                    sapdn.__dict__[k] = v
                result.append(sapdn)
                matchCount += 1
            if len(zpo_list) == 0:
                noMatchCount += 1
                noMatchSAPDN.append(sapdn)
            if len(zpo_list) > 1:
                for zpo in zpo_list:
                    newSapDN = copy.deepcopy(sapdn)
                    for k, v in zpo.__dict__.items():
                        newSapDN.__dict__[k] = v
                    doubleSAPDN.append(newSapDN)
                    doubleCount += 1

    print("Stat Match:", 'Match',matchCount, 'Doublematch', doubleCount, 'Nonmatch', noMatchCount)

    if output:
        fileWriter.outputObjectsToFile(result,
                                       'Step3_result_' + fileWriter.getNowAsString(),
                                       'output/dn_maker/')
        fileWriter.outputObjectsToFile(noMatchSAPDN,
                                       'Step3_nomatch' + fileWriter.getNowAsString(),
                                       'output/dn_maker/')
        fileWriter.outputObjectsToFile(doubleSAPDN,
                                       'Step3_morematch' + fileWriter.getNowAsString(),
                                       'output/dn_maker/')
        recordReader.storeRawData(result,"Result_3_SAPDN_with_BMID_BMSTATUS_ZTEPO")

    return result


if __name__ == '__main__':
    getAllDataAndWriteToFileDict()












