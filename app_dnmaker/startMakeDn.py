__author__ = 'yuluo'

import app_po.polistReader as poReader
import recordReader as recordReader
import datetime
import pickle
from collections import Counter
import tools.fileWriter as fileWriter
import copy
import re

def getAllData():
    sappos = recordReader.get_AllSappoInPath()
    sappns = recordReader.get_AllSapdnInPath()
    orbmids = recordReader.get_AllOrderBmidInPath()
    ztepos = poReader.goThroughPolistDirectory()
    bmstatus = recordReader.get_AllBMStatusRecordInPath()

    raw_dict = {}
    raw_dict['sappos'] = sappos
    raw_dict['sappns'] = sappns
    raw_dict['orbmids'] = orbmids
    raw_dict['ztepos'] = ztepos
    raw_dict['bmstatus'] = bmstatus
    recordReader.storeRawData(raw_dict,"Raw_data_dict",'output/raw/')
    return raw_dict


def doProductDN(raw_dict):
    """

    :param raw_dict:
    :return:
    """
    sappos = raw_dict['sappos']
    sappns =raw_dict['sappns']
    orbmids = raw_dict['orbmids']
    ztepos = raw_dict['ztepos']
    bmstatus = raw_dict['bmstatus']

    sappos = step1_MixSapPOandZTEPO(sappos, ztepos)
    sappos = step2_AddingSAPDNtoSappo(sappos, sappns)
    sappos = step3_AddingBMIDandBsfeToSAPPO(sappos, orbmids)
    sappos = step4_AddBmstatusToSappos(sappos, bmstatus)

    return sappos




def new_step1_AddOrbmidsToSapdns(orbmids = None, sapdns = None):
    """

    :param orbmids:
    :param sapdns:
    :return:
    """
    # build order dict
    orbmids_dict = {}
    order_dup = set()
    for orbmid in orbmids:
        if orbmid.Order:
            if orbmid.Order not in orbmids_dict:
                orbmids_dict[orbmid.Order] = set()
            else:
                order_dup.add(orbmid)
            orbmids_dict[orbmid.Order].add(orbmid)

    print("Orders count",len(orbmids_dict.keys()), len(orbmids))

    # do match
    matchCount = 0
    dupCount = 0
    nomatchCount = 0
    noOrderCount = 0
    new_attrs = [u'Equipment', u'NotesID']

    for sapdn in sapdns:
        # init the keys from orbmid
        for k in new_attrs:
            sapdn.__dict__[k] = None
        if sapdn.Order:
            if sapdn.Order in orbmids_dict:
                orbm_set = orbmids_dict[sapdn.Order]
                if len(orbm_set) == 1:
                    orbmid = list(orbm_set)[0]
                    for k, v in orbmid.__dict__.items():
                        if k in new_attrs:
                            sapdn.__dict__[k] = v
                    matchCount += 1
                if len(orbm_set) > 1:
                    dupCount += 1
                if len(orbm_set) == 0:
                    nomatchCount += 1
        else:
            noOrderCount += 1

    print("Step1: Match rate", matchCount, len(sapdns),
          "DupCount", dupCount, "Nomatch", nomatchCount,
          "No Order", noOrderCount
    )

    fileWriter.outputObjectsToFile(sapdns,"Step_1_Sapdns_with_BMID",'output/dn_maker/')
    return sapdns


def new_step2_addBmstatusToSapdns(bmstatus=None, sapdns = None):
    """

    :param bmstatus: all bm92
    :param sapdns:
    :return:
    """

    #build bm_dict
    bsfe_dict = {}
    bm_dict = {}
    unique_dict = {}
    for bm in bmstatus:
        if bm.BAUMASSNAHME_ID:
            if bm.BAUMASSNAHME_ID not in bm_dict:
                bm_dict[bm.BAUMASSNAHME_ID] = set()
            bm_dict[bm.BAUMASSNAHME_ID].add(bm)

        if bm.BS_FE:
            if bm.BS_FE not in bsfe_dict:
                bsfe_dict[bm.BS_FE] = set()
            bsfe_dict[bm.BS_FE].add(bm)

        if bm.BAUMASSNAHME_ID and bm.BS_FE:
            unique = (bm.BAUMASSNAHME_ID, bm.BS_FE)
            if unique not in unique_dict:
                unique_dict[unique] = set()
            unique_dict[unique].add(bm)

    print("bm_dict", len(bm_dict),
          "bsfe_dict", len(bsfe_dict),
          "unique_dict", len(unique_dict)
    )



    uniqueMatch = []
    uniqueMoreMatch = []
    bsfeOneMatch = []
    bsfeMoreMatch = []
    for sapdn in sapdns:
        # has unique
        if sapdn.NotesID and sapdn.Equipment:
            unique = (sapdn.NotesID, sapdn.Equipment)
            # if unique is the in bmid
            if unique in unique_dict:
                bm_set = unique_dict[unique]
                if len(bm_set) == 1:
                    bm = list(bm_set)[0]
                    for k, v in bm.__dict__.items():
                        sapdn.__dict__[k] = v
                    uniqueMatch.append(sapdn)
                    continue
                if len(bm_set) > 1:
                    uniqueMoreMatch.append(sapdn)
            else:
                if sapdn.Equipment in bsfe_dict:
                    bm_set = bsfe_dict[sapdn.Equipment]
                    if len(bm_set) == 1:
                        bm = list(bm_set)[0]
                        for k, v in bm.__dict__.items():
                            sapdn.__dict__[k] = v
                        bsfeOneMatch.append(sapdn)
                        continue
                    if len(bm_set) > 1:
                        bsfeMoreMatch.append(sapdn)

    match = []
    match.extend(uniqueMatch)
    match.extend(bsfeOneMatch)

    nomatch = []
    nomatch.extend(uniqueMoreMatch)
    nomatch.extend(bsfeMoreMatch)

    print("Step2 (BMID,BSFE) match",len(uniqueMatch),
          "(BMID,BSFE) more match", len(uniqueMoreMatch),
          "One BSFE match", len(bsfeOneMatch),
          "More BSFE match", len(bsfeMoreMatch),
          "Total match rate", len(match), len(bmstatus), len(sapdns),
          "Total dismatch rate", len(nomatch), len(sapdns)
    )

    fileWriter.outputObjectsToFile(sapdns,"Step2_SAPDN_WITH_BMSTATUS92", 'output/dn_maker/')

    return sapdns


def new_step3_MixZteposIntoSapdns(ztepos=None, sapdns=None):
    """

    :param ztepos:
    :param sapdns:
    :return:
    """
    















# --------------- old
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

    # ------------------- new
    # build dicts
    refpo_dict = {}
    sappo_dict = {}
    ref_count = 0
    noref_count = 0
    ref_dupCount = 0
    noref_dupcount = 0
    for sappo in sappos:
        if sappo.Reference_PO_Number and sappo.Material:
            key_PMQ = (sappo.Reference_PO_Number, sappo.Material)
            if key_PMQ not in refpo_dict:
                refpo_dict[key_PMQ] = set()
            else:
                ref_dupCount += 1
            refpo_dict[key_PMQ].add(sappo)
            ref_count += 1
            continue
        if sappo.Material and sappo.PurchNo:
            key_PMQ = (sappo.PurchNo, sappo.Material)
            if key_PMQ not in sappo_dict:
                sappo_dict[key_PMQ] = set()
            else:
                noref_dupcount += 1
            sappo_dict[key_PMQ].add(sappo)
            noref_count += 1
            continue

    print("Ref po ",ref_count, "Noref po ",noref_count,
          "Dup Count", ref_dupCount, noref_dupcount,
          "Total sappos ", len(sappos),
          "Diff", len(sappos) - ref_count - noref_count)



    result = []
    nomatchzpo = []
    for zpo in ztepos:
        if zpo.ZTE_PO_Nr and zpo.ZTE_Material:
            zpo_unique_PM = (zpo.ZTE_PO_Nr, zpo.ZTE_Material)
            # check if this zpo in sappo
            if zpo_unique_PM in sappo_dict:
                sappo_set = sappo_dict[zpo_unique_PM]
                sappo_list = list(sappo_set)
                for sappo in sappo_list:
                    for k, v in zpo.__dict__.items():
                        sappo.__dict__[k] = v
                    result.append(sappo)
            elif zpo_unique_PM in refpo_dict:
                sappo_set = refpo_dict[zpo_unique_PM]
                sappo_list = list(sappo_set)
                for sappo in sappo_list:
                    for k, v in zpo.__dict__.items():
                        sappo.__dict__[k] = v
                    result.append(sappo)
            else:
                nomatchzpo.append(zpo)

    print(len(result), len(sappos), len(nomatchzpo))


    fileWriter.outputObjectsToFile(result, 'Step1_ZPO_SAP_Match','output/dn_maker/')
    fileWriter.outputObjectsToFile(nomatchzpo, 'Step1_ZPO_SAP_Dismatch','output/error/')
    recordReader.storeRawData(result, 'Step1_ZPO_SAP_Match','output/raw/')
    fileWriter.outputObjectsToFile(sappos, 'Step1_mixed_ZPO','output/dn_maker/')







    # # ------------------- old
    # print("ZPO has not CM:", len(ztepos))
    # # 1 make two dict, one for sappo without ref, one for sappo with ref
    # sappo_without_ref = {}
    # sappo_with_ref = {}
    # # add sappo to these dict
    # saprefCount = 0
    # sapnorefCount = 0
    # for sappo in sappos:
    #     # check if this sappo has ref
    #     if sappo.Reference_PO_Number:
    #         # add it to refdict
    #         if sappo.Reference_PO_Number not in sappo_with_ref:
    #             sappo_with_ref[sappo.Reference_PO_Number] = set()
    #         sappo_with_ref[sappo.Reference_PO_Number].add(sappo)
    #         saprefCount += 1
    #     else:
    #         # add it to noref dict
    #         if sappo.PurchNo not in sappo_without_ref:
    #             sappo_without_ref[sappo.PurchNo] = set()
    #         sappo_without_ref[sappo.PurchNo].add(sappo)
    #         sapnorefCount += 1
    # print("Step1: Refcout", saprefCount, "No ref: ", sapnorefCount,
    #       "Total record ", len(sappos), "Diff: ", len(sappos) - (sapnorefCount + saprefCount))
    #
    # # 2 combine ztepo with sappo
    # normalMatch = []
    # normalDisMatch = []
    # refMatch = []
    # refDisMatch = []
    # nosapMatch = []
    # for zpo in ztepos:
    #     # if this zpo has ztepor
    #     if zpo.ZTE_PO_Nr:
    #         # first check if this zponr is a refnr
    #         if zpo.ZTE_PO_Nr in sappo_with_ref:
    #             sappolist = list(sappo_with_ref[zpo.ZTE_PO_Nr])
    #             for sappo in sappolist:
    #                 # check math
    #                 if (sappo.Reference_PO_Number == zpo.ZTE_PO_Nr
    #                     and sappo.Material == zpo.ZTE_Material
    #                     # and sappo.PO_Quantity == zpo.ZTE_Qty
    #                 ):
    #                     newZPO = copy.deepcopy(zpo)
    #                     for k, v in sappo.__dict__.items():
    #                         newZPO.__dict__[k] = v
    #                     refMatch.append(newZPO)
    #                 else:
    #                     refDisMatch.append(zpo)
    #             continue
    #         # check if it is a normal sappo
    #         if zpo.ZTE_PO_Nr in sappo_without_ref:
    #             # do compare if this zpo record is right
    #             sappolist = list(sappo_without_ref[zpo.ZTE_PO_Nr])
    #             # compare item for item
    #             for sappo in sappolist:
    #                 # if every thing match
    #                 if (zpo.ZTE_PO_Nr == sappo.PurchNo
    #                     and zpo.ZTE_Material == sappo.Material
    #                     # and zpo.ZTE_Qty == sappo.PO_Quantity
    #                 ):
    #                     newZPO = copy.deepcopy(zpo)
    #                     # copy the information in sappo into zpo
    #                     for k, v in sappo.__dict__.items():
    #                         newZPO.__dict__[k] = v
    #                     normalMatch.append(newZPO)
    #                 else:
    #                     normalDisMatch.append(zpo)
    #             continue
    #         else:
    #             nosapMatch.append(zpo)
    #
    #
    # print("Step1: Match rate:",
    #       "Normalmatch", len(normalMatch), "Normaldismatch",len(normalDisMatch),
    #       "Refmatch", len(refMatch), "Refdismatch", len(refDisMatch),
    # )
    #
    # normalMatch.extend(refMatch)
    # normalDisMatch.extend(refDisMatch)
    # print("Step1: Total match rate", len(normalMatch), len(sappos),
    #       "Total dismatch rate", len(normalDisMatch), len(sappos)
    # )
    #
    # mixztpos = copy.deepcopy(normalMatch)
    # mixztpos.extend(normalDisMatch)
    #
    # fileWriter.outputObjectsToFile(normalMatch, 'Step1_ZPO_SAP_Match','output/dn_maker/')
    # fileWriter.outputObjectsToFile(normalDisMatch, 'Step1_ZPO_SAP_Dismatch','output/error/')
    # fileWriter.outputObjectsToFile(nosapMatch, 'Step1_ZPO_without_SAPPO','output/error/')
    # recordReader.storeRawData(normalMatch, 'Step1_ZPO_SAP_Match','output/raw/')
    # fileWriter.outputObjectsToFile(mixztpos, 'Step1_mixed_ZPO','output/dn_maker/')
    #
    # return normalMatch

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
                for k, v in orbmid.__dict__.items():
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



def step4_AddBmstatusToSappos(sappos, bmstatus):
    """

    :param sappos:
    :param bmstatus:
    :return:
    """
    # 1. make a bmstatus dict
    bm_dict = {}
    sitebm_dict = {}
    for bm in bmstatus:
        if bm.BAUMASSNAHME_ID not in bm_dict:
            bm_dict[bm.BAUMASSNAHME_ID] = set()
        bm_dict[bm.BAUMASSNAHME_ID].add(bm)
        if bm.BS_FE not in sitebm_dict:
            sitebm_dict[bm.BS_FE] = set()
        sitebm_dict[bm.BS_FE].add(bm)

    result = []
    nomatch = []
    bmdupCount = 0
    sitedupCount = 0
    for sappo in sappos:
        # check if this sppo has bsfe and bmid
        if sappo.NotesID and sappo.NotesID in bm_dict:
            bm_list = list(bm_dict[sappo.NotesID])
            if len(bm_list) == 1:
                bm = bm_list.pop()
                for k ,v in bm.__dict__.items():
                    sappo.__dict__[k] = v
                result.append(sappo)
            if len(bm_list) > 1:
                bmdupCount += 1
        # check if this sappo has bsfe but not bmid match
        if sappo.Equipment and sappo.Equipment in sitebm_dict:
            if re.match(".*(lte).*", sappo.ZTE_Project, re.IGNORECASE):
                bm_list = list(sitebm_dict[sappo.Equipment])
                if len(bm_list) == 1:
                    bm = bm_list.pop()
                    for k ,v in bm.__dict__.items():
                        sappo.__dict__[k] = v
                    result.append(sappo)
                if len(bm_list) > 1:
                    sitedupCount += 1
        else:
            nomatch.append(sappo)

    dns = [sappo for sappo in result if sappo.IST92
           and not sappo.ZTE_CM_No
           and int(sappo.Still_to_be_delivered_qty) != 0
           and not sappo.Deletion_Indicator
    ]

    fileWriter.outputObjectsToFile(result, 'Step4_SAPPO_with_BMSTATUS','output/dn_maker/')
    fileWriter.outputObjectsToFile(nomatch, 'Step3_SAPPO_without_BMSTATUS','output/error/')
    fileWriter.outputObjectsToFile(dns, 'Step4_DN','output/dn_maker/')

    print("Step4 Match rate", len(result), len(sappos),
          "Step4 No match", len(nomatch),
          "Step4 BM Duplicate", bmdupCount,
          "Step4 Site Dupicate", sitedupCount,
          "Step4 DN count", len(dns)
    )
    return result



























