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

    fileWriter.outputObjectsToFile(normalMatch, 'Step1_ZPO_SAP_Match','output/dn_maker/')
    fileWriter.outputObjectsToFile(normalDisMatch, 'Step1_ZPO_SAP_Dismatch','output/error/')
    fileWriter.outputObjectsToFile(nosapMatch, 'Step1_ZPO_without_SAPPO','output/error/')
    recordReader.storeRawData(normalMatch, 'Step1_ZPO_SAP_Match','output/raw/')

    return normalMatch

def step2_AddingSAPDNtoSappo(sappos = None, sapdns = None):
    """

    :param sappos:
    :param sapdns:
    :return:
    """
    # first load data if data was not given
    if sappos == None:
        sappos = recordReader.loadRawData('output/raw/Step1_ZPO_SAP_Match.raw')
    if sapdns == None:
        sapdns = recordReader.loadRawData('output/raw/Raw_2_SAP_DN.raw')



    # 1. build dict for sappos using po-m-item as key
    sapdns_dict = {}
    sapdn_dup_count = 0
    unvalid_sapdn_count = 0
    for sapdn in sapdns:
        if sapdn.Purchasing_Document and sapdn.Material and sapdn.Item:
            unique = (sapdn.Purchasing_Document, sapdn.Material, sapdn.Item)
            if unique not in sapdns_dict:
                sapdns_dict[unique] = set()
            else:
                sapdn_dup_count += 1
            sapdns_dict[unique].add(sapdn)
        else:
            unvalid_sapdn_count += 1

    # 2.build dict for sappo using po-m-item as key
    sappos_dict = {}
    sappo_dup_count = 0
    unvalid_sappo_count = 0
    for sappo in sappos:
        if sappo.PurchNo and sappo.Material and sappo.Item_of_PO:
            unique = (sappo.PurchNo , sappo.Material , sappo.Item_of_PO)
            if unique not in sappos_dict:
                sappos_dict[unique] = set()
            else:
                sappo_dup_count += 1
            sappos_dict[unique].add(sappo)
        else:
            unvalid_sappo_count += 1


    result = []

    morematchCount = 0
    nosapdnforthisappo = []
    for sappo_u, sappo_set in sappos_dict.items():
        if sappo_u in sapdns_dict:
            # if this sappo_u alos in sapdn_dict
            sapdn_set = sapdns_dict[sappo_u]
            sapdn_list = list(sapdn_set)
            if len(sapdn_list) == 1:
                sappo = sappos_dict[sappo_u].pop()
                for k, v in sapdn_list[0].__dict__.items():
                    sappo.__dict__[k] = v
                result.append(sappo)
            else:
                morematchCount += 1
        else:
            sapposlist = list(sappos_dict[sappo_u])
            nosapdnforthisappo.extend(sapposlist)


    print("Step2: Sappo and sapdn Match rate", len(result), len(sappos),
          "Morematch", morematchCount,
          "Nomatch", len(nosapdnforthisappo)
    )


    fileWriter.outputObjectsToFile(result, 'Step2_SAPPO_SAPDN_Match','output/dn_maker/')
    fileWriter.outputObjectsToFile(nosapdnforthisappo, 'Step1_ZPO_SAP_Dismatch','output/error/')
    recordReader.storeRawData(result,'Step2_SAPPO_SAPDN_Match')


    return result



def step3_AddingBMIDandBsfeToSAPPO(sappos = None, orderbmids = None):
    """

    :param sappos:
    :param orderbmids:
    :return:
    """
    # first load data if data was not given
    if sappos == None:
        sappos = recordReader.loadRawData('output/raw/Step2_SAPPO_SAPDN_Match.raw')
    if orderbmids == None:
        orderbmids = recordReader.loadRawData('output/raw/Raw_3_SAP_OrderBMID.raw')

    # 1. build order to bmid-sitid dict
    orderbmid_dict = {}
    order_dup_count = 0
    for order in orderbmids:
        if order.Order and order.NotesID and order.Equipment:
            if order.Order not in orderbmid_dict:
                orderbmid_dict[order.Order] = set()
            else:
                order_dup_count += 1
            orderbmid_dict[order.Order].add(order)

    # 2 add BMID and BSFE to sappos
    noOrders = []
    dupOrderCount = 0
    result = []
    for sappo in sappos:
        if sappo.Order and sappo.Order in orderbmid_dict:
            order_list = list(orderbmid_dict[sappo.Order])
            if len(order_list) == 1:
                orbmid = order_list.pop()
                for k, v in orbmid:
                    sappo.__dict__[k] = v
                result.append(sappo)
            else:
                dupOrderCount += 1
        else:
            noOrders.append(sappo)

    print("Step3: Sappo and Order Match rate", len(result), len(sappos),
          "Morematch", dupOrderCount,
          "Nomatch", len(noOrders)
    )


    fileWriter.outputObjectsToFile(result, 'Step3_SAPPO_Order_Match','output/dn_maker/')
    fileWriter.outputObjectsToFile(noOrders, 'Step3_SAPPO_noorder','output/error/')
    recordReader.storeRawData(result,'Step3_SAPPO_Order_Match')

    return result














if __name__ == '__main__':
    getAllDataAndWriteToFileDict()












