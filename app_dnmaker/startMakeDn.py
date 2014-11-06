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




def stepOne_addingBMIDtoSapdn(sapdns, orbmids, output=False):
    """
    Combine bmid to delievery record

    :param sapdns:
    :param orbmids:
    :return:
    """
    result = []
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
            result.append(sapdn)
        if len(orbm_list) == 0:
            # no bmid for this order
            print("Error: no BMID for order", sapdn.Order, orbm_list)
        if len(orbm_list) > 1:
            # one-to-more relation
            print("Warning: One-to-More Order to Bmid",sapdn.Order, orbm_list)
            for orbm_tup in orbm_list:
                newSapdn = copy.deepcopy(sapdn)
                newSapdn.Equipment = orbm_tup[0]
                newSapdn.NotesID = orbm_tup[1]
                result.append(newSapdn)

    print("Adding BMID to SAP", len(sapdns), len(result))

    if output:
        fileWriter.outputObjectsToFile(result,
                                       'Step1_result_' + fileWriter.getNowAsString(),
                                       'output/dn_maker/')

    return result


def stepTwo_addBMstatusToSapdn(sapdns, bmstatus, output=False):
    """

    :param sapdns:
    :param bmstatus:
    :return:
    """
    result = []
    for sapdn in sapdns:
        bmstatus_list = [bm for bm in bmstatus if bm.BAUMASSNAHME_ID == sapdn.NotesID
                         and bm.BS_FE == sapdn.Equipment]
        bmstatus_list = list(set(bmstatus_list))

        if len(bmstatus_list) != 0:
            bmObj = bmstatus_list[0]
            for k, v in bmObj.__dict__.items():
                sapdn.__dict__[k] = v
        if len(bmstatus_list) == 0:
            print("Error: No BMstatus for this sapdn", sapdn.Order,sapdn.NotesID)
        if len(bmstatus_list) > 1:
            elist = [(bm.BAUMASSNAHME_ID, bm.BS_FE) for bm in bmstatus_list]
            print("Error: Find more BMstatus for this sapdn", sapdn.Order,sapdn.NotesID,
                  elist)

    if output:
        fileWriter.outputObjectsToFile(result,
                                       'Step2_result_' + fileWriter.getNowAsString(),
                                       'output/dn_maker/')

    return result

if __name__ == '__main__':
    getAllDataAndWriteToFileDict()












