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


def go():
    sapdns = recordReader.get0_AllSapDeleiveryRecordInPath()
    mixedzpo = recordReader.get1_AllMixedZtePowithSapPoFromPath()
    orbmid = recordReader.get2_AllOrderBmidInPath()
    bmstatus = recordReader.get3_AllBMStatusRecordInPath()

    print("Enter compare")
    result1 = step1_addingBMIDtoSapdn(sapdns, orbmid)
    result2 = step2_addBMstatusToSapdn(result1, bmstatus)
    result3 = step3_FilterOnlyZTEPO(result2, mixedzpo)

    return result3

def step1_addingBMIDtoSapdn(sapdns, orbmids, output=True):
    """
    Combine bmid to delievery record

    :param sapdns:
    :param orbmids:
    :return:
    """
    result = []
    error = []
    orbmid_dict = {}
    for orbm in orbmids:
        if orbm.Order not in orbmid_dict:
            orbmid_dict[orbm.Order] = set()
            orbmid_dict[orbm.Order].add((orbm.Equipment, orbm.NotesID))
        else:
            orbmid_dict[orbm.Order].add((orbm.Equipment, orbm.NotesID))

    for sapdn in sapdns:
        if sapdn.Order:
            if sapdn.Order in orbmid_dict:
                s_t = orbmid_dict[sapdn.Order]
                bm_tup = list(s_t)[0]
                sapdn.Equipment = bm_tup[0]
                sapdn.NotesID = bm_tup[1]
                result.append(sapdn)
            else:
                error.append(sapdn)

    # nomatch = []
    # matchCount = 0
    # nonmatchCount = 0
    # doubleMatchCount = 0
    # for sapdn in sapdns:
    #     # initial
    #     sapdn.Equipment = None
    #     sapdn.NotesID = None
    #
    #     orbm_list = [(orbm.Equipment, orbm.NotesID) for orbm in orbmids if
    #                  orbm.Order == sapdn.Order and orbm.Equipment and orbm.NotesID]
    #     orbm_list = list(set(orbm_list))
    #
    #     if len(orbm_list) == 1:
    #         # one-to-one
    #         sapdn.Equipment = orbm_list[0][0]
    #         sapdn.NotesID = orbm_list[0][1]
    #         matchCount += 1
    #         result.append(sapdn)
    #     if len(orbm_list) == 0:
    #         # no bmid for this order
    #         #print("Error: no BMID for order", sapdn.Order, orbm_list)
    #         nomatch.append(sapdn)
    #         nonmatchCount += 1
    #     if len(orbm_list) > 1:
    #         # one-to-more relation
    #         print("Warning: One-to-More Order to Bmid",sapdn.Order, orbm_list)
    #         for orbm_tup in orbm_list:
    #             newSapdn = copy.deepcopy(sapdn)
    #             newSapdn.Equipment = orbm_tup[0]
    #             newSapdn.NotesID = orbm_tup[1]
    #             result.append(newSapdn)
    #             doubleMatchCount += 1
    # print("Stat:", 'Match',matchCount, 'Doublematch', doubleMatchCount, 'Nonmatch', nonmatchCount)
    # print("Adding BMID to SAP rate",len(result), len(sapdns))
    #
    if output:
        fileWriter.outputObjectsToFile(result,
                                       'Step1_result_' + fileWriter.getNowAsString('%Y%m%d'),
                                       'output/dn_maker/')
        # recordReader.__storeRawData(result,"Result_1_SAPDN_with_BMID")
        fileWriter.outputObjectsToFile(error,
                                       'Step1_result_sapdn_without_bmid' + fileWriter.getNowAsString('%Y%m%d'),
                                       'output/error/')
        # recordReader.__storeRawData(error,"Result_1_SAPDN_without_BMID")

    print("Find bmid for order", len(result), "No find",len(error), 'ALL', len(sapdns))
    return result


def step2_addBMstatusToSapdn(result1, bmstatus, output=True):
    """

    :param result1:
    :param bmstatus:
    :return:
    """
    result = []
    error = []
    bm_dict = {}
    errorCount = 0
    for bm in bmstatus:
        if bm.BAUMASSNAHME_ID:
            if bm.BAUMASSNAHME_ID not in bm_dict:
                bm_dict[bm.BAUMASSNAHME_ID] = bm
    done_count = 0
    print("Enter comparation ...")
    for sapdn in result1:
        if sapdn.NotesID and sapdn.NotesID in bm_dict:
            bm = bm_dict[sapdn.NotesID]
            for k, v in bm.__dict__.items():
                sapdn.__dict__[k] = v
            result.append(sapdn)
            done_count += 1
        else:
            error.append(sapdn)
            errorCount += 1
        # print("Done:",done_count, len(result1))
    result92 = [sapdn for sapdn in result if sapdn.IST92]

    print("OK rate", len(result),len(result1),'IST',len(result92),'Error', len(error))
    if output:
        fileWriter.outputObjectsToFile(result,
                                       'Step2_result_all_' + fileWriter.getNowAsString('%Y%m%d'),
                                       'output/dn_maker/')
        fileWriter.outputObjectsToFile(result92,
                                       'Step2_result_92_' + fileWriter.getNowAsString('%Y%m%d'),
                                       'output/dn_maker/')
        fileWriter.outputObjectsToFile(error,
                                       'Step2_result_error_no_BMSTATUS_' + fileWriter.getNowAsString('%Y%m%d'),
                                       'output/error/')

        # recordReader.__storeRawData(result,"Result_2_SAPDN_with_BMID_BMSTATUS")
        # recordReader.__storeRawData(result92,"Result_2_SAPDN_with_BMID_BMSTATUS_92")
        # recordReader.__storeRawData(error,"Result_2_SAPDN_Without_BMSTATUS")
    return result

    # matchCount = 0
    # noMatchCount = 0
    # doubleCount = 0
    # done_count = 0
    # error = []
    # for sapdn in result1:
    #     bmstatus_list = [bm for bm in bmstatus if bm.BAUMASSNAHME_ID == sapdn.NotesID
    #                      and bm.BS_FE == sapdn.Equipment
    #                      # and bm.IST92
    #     ]
    #     bmstatus_list = list(set(bmstatus_list))
    #
    #     if len(bmstatus_list) != 0:
    #         bmObj = bmstatus_list[0]
    #         for k, v in bmObj.__dict__.items():
    #             sapdn.__dict__[k] = v
    #         matchCount += 1
    #         result.append(sapdn)
    #     if len(bmstatus_list) == 0:
    #         # print("Error: No BMstatus for this sapdn", sapdn.Order,sapdn.NotesID)
    #         noMatchCount += 1
    #     if len(bmstatus_list) > 1:
    #         elist = [(bm.BAUMASSNAHME_ID, bm.BS_FE) for bm in bmstatus_list]
    #         print("Error: Find more BMstatus for this sapdn", sapdn.Order,sapdn.NotesID,
    #               elist)
    #         doubleCount += 1
    #         error.append(sapdn, bmstatus_list)
    #     done_count += 1
    #     print("Done: ", done_count, len(sapdn))
    #
    # print("Stat Match:", 'Match',matchCount, 'Doublematch', doubleCount, 'Nonmatch', noMatchCount)
    # countALL = len(result)
    # result_92 = [r for r in result if r.IST92]
    # count92 = len(result_92)
    # print("Stat IST92 rate", count92, countALL)
    # if output:
    #     fileWriter.outputObjectsToFile(result,
    #                                    'Step2_result_all' + fileWriter.getNowAsString(),
    #                                    'output/dn_maker/')
    #     fileWriter.outputObjectsToFile(result_92,
    #                                    'Step2_result_92' + fileWriter.getNowAsString(),
    #                                    'output/dn_maker/')
    #     recordReader.storeRawData(result,"Result_2_SAPDN_with_BMID_BMSTATUS")
    #     recordReader.storeRawData(result,"Result_2_SAPDN_with_BMID_BMSTATUS_92")
    #     recordReader.storeRawData(error,"Result_2_SAPDN_with_BMID_BMSTATUS_MORE_BMSTATUS")
    # return result

def step3_FilterOnlyZTEPO(result2, mixedZtepo, output=True):
    """

    :param result2:
    :param mixedZtepo:
    :param output:
    :return:
    """
    result = []
    # build sapdn dict
    sapdn_dict = {}
    error = []
    donecount = 0
    errorcount = 0
    doublematchcount = 0
    for sapdn in result2:
        if sapdn.Unique_PM:
            if sapdn.Unique_PM not in sapdn_dict:
                sapdn_dict[sapdn.Unique_PM] = [sapdn]
            else:
                sapdn_dict[sapdn.Unique_PM].append(sapdn)

    for zpo in mixedZtepo:
        if zpo.SAP_PO_Nr and zpo.SAP_Material:
            zpo.Unique_ZTE_PM = '-'.join([zpo.SAP_PO_Nr, zpo.SAP_Material])
        if zpo.Unique_ZTE_PM:
            if zpo.Unique_ZTE_PM in sapdn_dict:
                spnlist = sapdn_dict[zpo.Unique_ZTE_PM]
                if len(spnlist) == 1:
                    sapdn = spnlist[0]
                    for k, v in sapdn.__dict__.items():
                        zpo.__dict__[k] = v
                    zpo.__dict__['Position'] = unicode(1)
                    result.append(zpo)
                    donecount += 1
                else:
                    donecount += 1
                    ponr = 1
                    for sapdn in spnlist:
                        newZPO = copy.deepcopy(zpo)
                        for k, v in sapdn.__dict__.items():
                            newZPO.__dict__[k] = v
                        newZPO.__dict__['Position'] = unicode(ponr)
                        ponr += 1
            else:
                error.append(zpo)
                errorcount += 1

    result_DN = [zpo for zpo in result if zpo.IST92 and int(zpo.Still_to_be_delivered_qty) != 0]

    if output:
        fileWriter.outputObjectsToFile(result,
                                       'Step3_result_all_' + fileWriter.getNowAsString('%Y%m%d'),
                                       'output/dn_maker/')
        fileWriter.outputObjectsToFile(result_DN,
                                       'Step3_result_DN_' + fileWriter.getNowAsString('%Y%m%d'),
                                       'output/dn_maker/')
        fileWriter.outputObjectsToFile(error,
                                       'Step3_result_error_no_match_' + fileWriter.getNowAsString(),
                                       'output/error/')
        fileWriter.outputObjectsToFile(result2,
                                       'Step3_result_sapdn' + fileWriter.getNowAsString(),
                                       'output/raw/')
    print("Done,", donecount,"DN",len(result_DN) ,"Doublematch", doublematchcount, "Error",errorcount)

    # # create unique_pm for ztepos
    # for ztepo in ztepos:
    #     if ztepo.SAP_PO_Nr and ztepo.Material_Code:
    #         ztepo.Unique_PM = '-'.join([ztepo.SAP_PO_Nr,ztepo.Material_Code])
    #     else:
    #         ztepo.Unique_PM = None
    #
    # noMatchSAPDN = []
    # doubleSAPDN = []
    # matchCount = 0
    # noMatchCount = 0
    # doubleCount = 0
    # for sapdn in result2:
    #     # make sure these two data is not none
    #     if sapdn.Purchasing_Document and sapdn.Material:
    #         Unique_PM = '-'.join([sapdn.Purchasing_Document, sapdn.Material])
    #         zpo_list = [zpo for zpo in ztepos if zpo.Unique_PM and zpo.Unique_PM == Unique_PM]
    #         zpo_list = list(set(zpo_list))
    #         # one to one
    #         if len(zpo_list) == 1:
    #             zpo = zpo_list[0]
    #             for k, v in zpo.__dict__.items():
    #                 sapdn.__dict__[k] = v
    #             result.append(sapdn)
    #             matchCount += 1
    #         if len(zpo_list) == 0:
    #             noMatchCount += 1
    #             noMatchSAPDN.append(sapdn)
    #         if len(zpo_list) > 1:
    #             for zpo in zpo_list:
    #                 newSapDN = copy.deepcopy(sapdn)
    #                 for k, v in zpo.__dict__.items():
    #                     newSapDN.__dict__[k] = v
    #                 doubleSAPDN.append(newSapDN)
    #                 doubleCount += 1
    #
    # print("Stat Match:", 'Match',matchCount, 'Doublematch', doubleCount, 'Nonmatch', noMatchCount)
    #
    # if output:
    #     fileWriter.outputObjectsToFile(result,
    #                                    'Step3_result_' + fileWriter.getNowAsString(),
    #                                    'output/dn_maker/')
    #     fileWriter.outputObjectsToFile(noMatchSAPDN,
    #                                    'Step3_nomatch' + fileWriter.getNowAsString(),
    #                                    'output/dn_maker/')
    #     fileWriter.outputObjectsToFile(doubleSAPDN,
    #                                    'Step3_morematch' + fileWriter.getNowAsString(),
    #                                    'output/dn_maker/')
    #     recordReader.storeRawData(result,"Result_3_SAPDN_with_BMID_BMSTATUS_ZTEPO")

    return result






if __name__ == '__main__':
    getAllDataAndWriteToFileDict()












