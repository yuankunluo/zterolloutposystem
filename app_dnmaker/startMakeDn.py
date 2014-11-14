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



def step1_MixSapPOandZTEPO(sappos = None, ztepos= None):
    """

    :param sappos:
    :param ztepos:
    :return:
    """
    # first load data if data was not given
    if sappos == None:
        sappos = recordReader.loadRawData('output/raw/Raw_1_SAP_POLIST.raw')
    if ztepos == None:
        ztepos = recordReader.loadRawData('output/raw/Raw_0_ZTEPOLIST.raw')

    # clean all ztepo with cm, only need the zpos without cm
    ztepos = [zpo for zpo in ztepos if zpo.ZTE_CM_No]
    print("ZPO has not CM:", len(ztepos))
    # 1 make two dict, one for sappo without ref, one for sappo with ref
    sappo_without_ref = {}
    sappo_with_ref = {}
    # add sappo to these dict
    saprefCount = 0
    sapnorefCount = 0
    for sappo in sappos:
        # check if this sappo has ref
        if sappo.Reference_PO_Number:
            # add it to refdict
            if sappo.Reference_PO_Number not in sappo_with_ref:
                sappo_with_ref[sappo.Reference_PO_Number] = set()
            sappo_with_ref[sappo.Reference_PO_Number].add(sappo)
            saprefCount += 1
        else:
            # add it to noref dict
            if sappo.PurchNo not in sappo_without_ref:
                sappo_without_ref[sappo.PurchNo] = set()
            sappo_without_ref[sappo.PurchNo].add(sappo)
            sapnorefCount += 1
    print("Step1: Refcout", saprefCount, "No ref: ", sapnorefCount,
          "Total record ", len(sappos), "Diff: ", len(sappos) - (sapnorefCount + saprefCount))

    # 2 combine ztepo with sappo
    normalMatch = []
    normalDisMatch = []
    refMatch = []
    refDisMatch = []
    nosapMatch = []
    for zpo in ztepos:
        # if this zpo has ztepor
        if zpo.ZTE_PO_Nr:
            # first check if this zponr is a refnr
            if zpo.ZTE_PO_Nr in sappo_with_ref:
                sappolist = list(sappo_with_ref[zpo.ZTE_PO_Nr])
                for sappo in sappolist:
                    # check math
                    if (sappo.Reference_PO_Number == zpo.ZTE_PO_Nr
                        and sappo.Material == zpo.ZTE_Material
                        # and sappo.PO_Quantity == zpo.ZTE_Qty
                    ):
                        newZPO = copy.deepcopy(zpo)
                        for k, v in sappo.__dict__.items():
                            newZPO.__dict__[k] = v
                        refMatch.append(newZPO)
                    else:
                        refDisMatch.append(zpo)
                continue
            # check if it is a normal sappo
            if zpo.ZTE_PO_Nr in sappo_without_ref:
                # do compare if this zpo record is right
                sappolist = list(sappo_without_ref[zpo.ZTE_PO_Nr])
                # compare item for item
                for sappo in sappolist:
                    # if every thing match
                    if (zpo.ZTE_PO_Nr == sappo.PurchNo
                        and zpo.ZTE_Material == sappo.Material
                        # and zpo.ZTE_Qty == sappo.PO_Quantity
                    ):
                        newZPO = copy.deepcopy(zpo)
                        # copy the information in sappo into zpo
                        for k, v in sappo.__dict__.items():
                            newZPO.__dict__[k] = v
                        normalMatch.append(newZPO)
                    else:
                        normalDisMatch.append(zpo)
                continue
            else:
                nosapMatch.append(zpo)


    print("Step1: Match rate:",
          "Normalmatch", len(normalMatch), "Normaldismatch",len(normalDisMatch),
          "Refmatch", len(refMatch), "Refdismatch", len(refDisMatch),
    )

    normalMatch.extend(refMatch)
    normalDisMatch.extend(refDisMatch)
    print("Step1: Total match rate", len(normalMatch), len(sappos),
          "Total dismatch rate", len(normalDisMatch), len(sappos)
    )
    fileWriter.outputObjectsToFile(ztepos, 'STEP1_ZPO_WITHOUT_CM','output/dn_maker/')
    fileWriter.outputObjectsToFile(normalMatch, 'Step1_ZPO_SAP_Match','output/dn_maker/')
    fileWriter.outputObjectsToFile(normalDisMatch, 'Step1_ZPO_SAP_Dismatch','output/error/')
    fileWriter.outputObjectsToFile(nosapMatch, 'Step1_ZPO_without_SAPPO','output/error/')






if __name__ == '__main__':
    getAllDataAndWriteToFileDict()












