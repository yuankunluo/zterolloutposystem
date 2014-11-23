__author__ = 'yuluo'

import recordReader as recordReader
import datetime
import pickle
from collections import Counter
import tools.fileWriter as fileWriter
import copy
import re



def getAllSAPData():
    sappos = recordReader.get_AllSappoInPath()
    sappns = recordReader.get_AllSapdnInPath()
    orbmids = recordReader.get_AllOrderBmidInPath()
    ztepos = recordReader.get_ALLZteposInPath()
    sapprs = recordReader.get_AllPurchesingRequestionsInPath()

    raw_dict = {}
    raw_dict['sappos'] = sappos
    raw_dict['sapdns'] = sappns
    raw_dict['orbmids'] = orbmids
    raw_dict['ztepos'] = ztepos
    raw_dict['sapprs'] = sapprs

    recordReader.storeRawData(raw_dict,"Raw_data_dict",'output/raw/')
    fileWriter.outputObjectDictToFile(raw_dict,"Raw_Data_ALL",'output/dn_maker/')

    return raw_dict



def startDoProject(raw_dict):

    projectDict = {
        'BBU': 'input/infra_bm_bbu/',
        'BPK': 'input/infra_bm_bpk/',
        # 'LTE': 'input/infra_bm_lte/',
        # 'RRUSWAP': 'input/infra_bm_rruswap/',
        # 'UMTSNEW': 'input/infra_bm_umtsnew/',
    }

    sappos =  raw_dict['sappos']
    sapdns = raw_dict['sapdns']
    orbmids = raw_dict['orbmids']
    ztepos = raw_dict['ztepos']
    sapprs = raw_dict['sapprs']


    result1 = step_1_AddOrbmidsToSapdns(orbmids,sapdns)
    result2 = step_2_AddSapPurchasingRequestToSapdns(sapprs, result1)
    result3 = step_3_AddSappToSapdns(sappos, result2)
    result4 = step_4_MixZtepoAndSapdn(ztepos, result3)

    dn_set = set()

    for project, bmpath in projectDict.items():
        try:
            bmstatus = recordReader.get_AllBMStatusRecordInPath(project, bmpath)
            step_5_addBmstatusToSapdns(project, bmstatus, result4)
        except Exception:
            continue

    # fileWriter.outputObjectsListToFile(dn_set,"Step_6_DN_ALL","output/dn_maker/")

    # return dn_set





def step_1_AddOrbmidsToSapdns(orbmids, sapdns, outputname=None, outputpath=None,):
    """

    :param orbmids:
    :param sapdns:
    :return:
    """
    sap_d = {u'Deletion_Indicator': None,
        u'Document_Date': u'41856',
        u'Goods_recipient': None,
        u'Item': u'10',
        u'Material': u'50017101',
        u'Order': u'50208413',
        u'Order_Quantity': u'1',
        u'Purchasing_Document': u'32013114',
        u'Short_Text': u'ZTE. UMTS ZN000168  3xR8882, no BBU , up',
        u'Still_to_be_delivered_qty': u'1'
    }


    print("step1_AddOrbmidsToSapdns" + "-"*20 + "\n")
    # build order dict
    order_dict = {}
    for orbmid in orbmids:
        if orbmid.Order:
            if orbmid.Order not in order_dict:
                order_dict[orbmid.Order] = set()
            order_dict[orbmid.Order].add(orbmid)


    # do match

    new_attrs = [u'Equipment', u'NotesID']


    order_to_order_match = set()
    noOrder_match = set()
    moreOrde_match = set()
    for sapdn in sapdns:

        # init the keys from orbmid
        for k in new_attrs:
            sapdn.__dict__[k] = None

        if sapdn.Order:
            if sapdn.Order in order_dict:
                orbm_set = order_dict[sapdn.Order]
                if len(orbm_set) == 1:
                    orbmid = list(orbm_set)[0]

                    for k, v in orbmid.__dict__.items():
                        if k in new_attrs:
                            sapdn.__dict__[k] = v

                    order_to_order_match.add(sapdn)
                else:
                    moreOrde_match.add(sapdn)
            else:
                noOrder_match.add(sapdn)
        else:
            noOrder_match.add(sapdn)

    print("Order-Order-Match rate", len(order_to_order_match), len(sapdns),
          "More Order match", len(moreOrde_match),
          "No Order match", len(noOrder_match)
    )

    if not outputname:
        outputname = "Step_1"
    if not outputpath:
        outputpath = 'output/dn_maker/'


    fileWriter.outputObjectsListToFile(sapdns,outputname+'_Sapdns_with_NotesID',outputpath)
    fileWriter.outputObjectsListToFile(moreOrde_match,outputname+"_Sapdns_with_NotesID", "output/error/")
    fileWriter.outputObjectsListToFile(noOrder_match,outputname+"_Sapdn_without_NotesID","output/error/")

    return sapdns



def step_2_AddSapPurchasingRequestToSapdns(sapprs, sapdns,outputname=None, outputpath = None):


    pr_d = {
            u'Delivery_Date': u'20111010',
            u'Name_of_Vendor': u'ZTE CORPORATION',
            u'Purchase_Requisition': u'10245793'
    }

    print("step_2_AddSapPurchasingRequestToSapdns" + "-"*20 + "\n")

    # build a Order_PO_ITEM_Mat dict
    opim_dict = {}
    for pr in sapprs:
        if (pr.Order and pr.Purchase_Order
            and pr.Purchase_Order_Item and pr.Material):
            unique = (pr.Order, pr.Purchase_Order, pr.Purchase_Order_Item, pr.Material)
            if unique not in opim_dict:
                opim_dict[unique] = set()
            opim_dict[unique].add(pr)

    # do match with sapdns
    unique_match = set()
    unique_dismatch = set()
    pr_more_match = set()
    for sapdn in sapdns:
        if (sapdn.Order and sapdn.Purchasing_Document
            and sapdn.Item and sapdn.Material):
            unique = (sapdn.Order, sapdn.Purchasing_Document, sapdn.Item, sapdn.Material)

            if unique in opim_dict:
                pr_set = opim_dict[unique]
                if len(pr_set) == 1:
                    pr = list(pr_set)[0]
                    for k, v in pr.__dict__.items():
                        if k in pr_d:
                            sapdn.__dict__[k] = v
                    unique_match.add(sapdn)
                else:
                    pr_more_match = pr_more_match.union(pr_set)
            else:
                unique_dismatch.add(sapdn)


    if not outputname:
        outputname = "Step_2"
    if not outputpath:
        outputpath = 'output/dn_maker/'

    print("Unique Math", len(unique_match), len(sapdns),
          "Unique Dismath", len(unique_dismatch), len(sapdns),
          "PurchsingRequest more match", len(pr_more_match)
    )

    fileWriter.outputObjectsListToFile(sapdns, outputname+"_Sapdns_with_PR",outputpath)
    fileWriter.outputObjectsListToFile(unique_dismatch, outputname+"_Sapdn_unique_dismatch","output/error/")
    fileWriter.outputObjectsListToFile(pr_more_match, outputname+ "_PR_more_match", "output/error/")

    return sapdns



def step_3_AddSappToSapdns(sappos, sapdns,outputname=None, outputpath = None,):
    """

    :param sappos:
    :param sapdns:
    :return:
    """

    spo_d = {
            u'Material_Description': u'ZTE 3G R8840(DC) +OLP(DC)+ cable set',
            u'Reference_PO_Number': None
    }

    print("step_3_AddSappToSapdns" + "-"*20 + "\n")

    # build P_I_M_Q key
    pimq_dict = {}
    for spo in sappos:
        if (spo.PurchNo and spo.Item_of_PO and spo.Material and spo.PO_Quantity):
            unique = (spo.PurchNo, spo.Item_of_PO, spo.Material, spo.PO_Quantity)
            if unique not in pimq_dict:
                pimq_dict[unique] = set()
            pimq_dict[unique].add(spo)

    print("PIMQ dict rate", len(pimq_dict), len(sappos))


    #
    unique_match = set()
    unique_more = set()
    unique_dismatch = set()
    for sapdn in sapdns:
        if (sapdn.Purchasing_Document and sapdn.Item
            and sapdn.Material and sapdn.Order_Quantity):
            unique = (sapdn.Purchasing_Document , sapdn.Item, sapdn.Material , sapdn.Order_Quantity)

            if unique in pimq_dict:
                spo_set = pimq_dict[unique]
                if len(spo_set) == 1:
                    sappo = list(spo_set)[0]
                    for k, v in sappo.__dict__.items():
                        if k in spo_d:
                            sapdn.__dict__[k] = v
                    unique_match.add(sapdn)
                if len(spo_set)>1:
                    unique_more = unique_more.union(spo_set)
            else:
                unique_dismatch.add(sapdn)


    print("Unique_match rate", len(unique_match), len(sapdns),
          "Dismath rate", len(unique_dismatch), len(sapdns),
          "Unique more match", len(unique_more)
    )


    if not outputname:
        outputname = "Step_3"
    if not outputpath:
        outputpath = 'output/dn_maker/'


    fileWriter.outputObjectsListToFile(sapdns,outputname +'_SAPDN_With_SAPPO_ALL',outputpath)
    fileWriter.outputObjectsListToFile(unique_dismatch,outputname + '_SAPDN_SAPPO_uniquedismatch','output/error/')
    fileWriter.outputObjectsListToFile(unique_more, outputname + "_SAPPO_mormath","output/error/")

    sapdns_still = set()
    for sapdn in sapdns:
        if sapdn.Still_to_be_delivered_qty:
            if int(sapdn.Still_to_be_delivered_qty) != 0:
                sapdns_still.add(sapdn)

    fileWriter.outputObjectsListToFile(sapdns_still, outputname+"_SAPD_With_SAPPO_StillToBeDelivery", outputpath)

    return sapdns






def step_4_MixZtepoAndSapdn(ztepos, sapdns, outputname=None, outputpath = None,):
    """

    :param ztepos:
    :param sapdns:
    :param outputname:
    :param outputpath:
    :return:
    """

    print("step_4_MixZtepoAndSapdn" + "-"*20 + "\n")

    # dict with ztepo
    zpo_spmq_dict = {}
    zpo_nocm = set()
    for zpo in ztepos:
        if not zpo.ZTE_CM_No:
            zpo_nocm.add(zpo)
            if zpo.ZTE_Site_ID and zpo.ZTE_PO_Nr and zpo.ZTE_Material and zpo.ZTE_Qty:
                unique = (zpo.ZTE_Site_ID, zpo.ZTE_PO_Nr, zpo.ZTE_Material, zpo.ZTE_Qty)
                if unique not in zpo_spmq_dict:
                    zpo_spmq_dict[unique] = set()
                zpo_spmq_dict[unique].add(zpo)

    print("zpo spmq dict", len(zpo_spmq_dict),"ZPO no-cm set", len(zpo_nocm))



    if not outputname:
        outputname = "Step_4"
    if not outputpath:
        outputpath = 'output/dn_maker/'


    zpo_attrs = {
        'ZTE_CM_No': u'5101531993',
        'ZTE_Contract_No': None,
        'ZTE_Origin_Mcode': u'50017038',
        'ZTE_PO_Amount': u'1848',
        'ZTE_PO_Nr': u'32012562',
        'ZTE_Project': u'UMTS Swap',
        'rowindex': u'1002'
    }

    sapdn_notin_zpos = set()
    sapdn_zpo_onematch = set()
    sapdn_zpo_morematch = set()
    for sapdn in sapdns:
        if sapdn.Equipment and sapdn.Purchasing_Document and sapdn.Material and sapdn.Order_Quantity:
            unique = (sapdn.Equipment, sapdn.Purchasing_Document, sapdn.Material, sapdn.Order_Quantity)

            if u"Reference_PO_Number" in sapdn.__dict__: # has ref po
                unique_r = (sapdn.Equipment, sapdn.Reference_PO_Number, sapdn.Material, sapdn.Order_Quantity)
            else:
                unique_r = None

            if unique in zpo_spmq_dict:
                zpo_set = zpo_spmq_dict[unique]
            elif unique not in zpo_spmq_dict and unique_r and unique_r in zpo_spmq_dict:
                zpo_set = zpo_spmq_dict[unique_r]
            else:
                sapdn_notin_zpos.add(sapdn)
                continue

            if len(zpo_set) == 1:
                sapdn_zpo_onematch.add(sapdn)
                zpo = list(zpo_set)[0]
                for k, v in zpo.__dict__.items():
                    if k in zpo_attrs:
                        sapdn.__dict__[k] = v

            else:
                sapdn_zpo_morematch.add(sapdn)
                sapdn_zpo_morematch = sapdn_zpo_morematch.union(zpo_set)


    print("ZPO AND SAPDN SPMQ ONE-ONE MATCH", len(sapdn_zpo_onematch))
    print("SAPPO not in ZPO", len(sapdn_notin_zpos))
    print("ZPO AND SAPDN SPMQ ONE-More MATCH", len(sapdn_zpo_morematch))

    fileWriter.outputObjectsListToFile(sapdn_notin_zpos,outputname+"_sapdn_notin_zpos","output/error/")
    fileWriter.outputObjectsListToFile(sapdn_zpo_morematch,outputname+"_sapdn_zpo_morematch","output/error/")
    fileWriter.outputObjectsListToFile(sapdns,outputname+"_SAPDN_ALL",outputpath)

    sapdn_with_zpo_set = set()
    for sapdn in sapdns:
        if "ZTE_PO_Nr" in sapdn.__dict__:
            sapdn_with_zpo_set.add(sapdn)

    fileWriter.outputObjectsListToFile(sapdn_with_zpo_set,outputname+"_SAPDN_With_ZPO",outputpath)

    return sapdn_with_zpo_set




def step_5_addBmstatusToSapdns(projectname, bmstatus, sapdns, outputname=None, outputpath = None,):
    """

    :param projectname:
    :param bmstatus:
    :param sapdns:
    :param outputname:
    :param outputpath:
    :return:
    """

    print("\nstep_5_addBmstatusToSapdns" + '-'*20)

    #build bm_dict
    bmbs_dict = {}
    bsonly_dict = {}

    for bm in bmstatus:
        # add bmbs_dict
        if bm.BAUMASSNAHME_ID and bm.BS_FE:
            unique = (bm.BAUMASSNAHME_ID, bm.BS_FE)
            if unique not in bmbs_dict:
                bmbs_dict[unique] = set()
            bmbs_dict[unique].add(bm)
        # add bsonly
        if bm.BS_FE:
            if bm.BS_FE not in bsonly_dict:
                bsonly_dict[bm.BS_FE] = set()
            bsonly_dict[bm.BS_FE].add(bm)


    print(
        "BMBS dict", len(bmbs_dict),
        "BSONLY dict", len(bsonly_dict),
    )


    bmbs_match = set()
    bsonly_match = set()
    match_set = set()
    nomatch = set()

    bm_attris = [u'BAUMASSNAHME_ID', u'BS_FE',u'IST92',
              u'STRASSE', u'PLZ',u'GEMEINDE_NAME', u'PRICING',u'NBNEU',
              u'BAUMASSNAHMEVORLAGE',u'BAUMASSNAHMETYP',u'BESCHREIBUNG',
    ]

    # do match
    for sapdn in sapdns:
        # check if this sapdn has information
        if sapdn.Equipment and sapdn.NotesID:
            unique_bmbs = (sapdn.NotesID, sapdn.Equipment)

            # 1 check bmbs match
            if unique_bmbs in bmbs_dict:
                bm_set = bmbs_dict[unique_bmbs]
                # match only one
                if len(bm_set) == 1:
                    bm = list(bm_set)[0]
                    for k, v in bm.__dict__.items():
                        if k == 'IST92':
                            sapdn.__dict__[k] = v
                    sapdn.MATCH_TYPE = "BM_BS"
                    bmbs_match.add(sapdn)
                    match_set.add(sapdn)
                    sapdns.pop(sapdn)
                    continue

            # 2 check bsonly match

            elif unique_bmbs not in bmbs_dict and sapdn.Equipment in bsonly_dict:
                bm_set = bsonly_dict[sapdn.Equipment]
                # match only one site id
                if len(bm_set) == 1:
                    bm = list(bm_set)[0]
                    for k, v in bm.__dict__.items():
                        if k in bm_attris:
                            sapdn.__dict__[k] = v
                    bsonly_match.add(sapdn)
                    sapdn.MATCH_TYPE = "BS_ONLY"
                    match_set.add(sapdn)
                    sapdns.pop(sapdn)
                    continue
            else:
                nomatch.add(sapdn)

    print("BMBS match", len(bmbs_match),
          "BSONLY match", len(bsonly_match),
          "Total match", len(match_set),
          "No match", len(nomatch),
          "Rest SAPDNS", len(sapdns)
    )


    if not outputname:
        outputname = "Step_5"
    if not outputpath:
        outputpath = 'output/dn_maker/'

    if projectname:
        outputname = projectname + "_" + outputname


    sapdns_with_bmid = [sapdn for sapdn in sapdns if sapdn.BAUMASSNAHME_ID]

    fileWriter.outputObjectsListToFile(bmbs_match,outputname + "_bmbs_match",'output/error/')
    fileWriter.outputObjectsListToFile(bsonly_match,outputname + '_bsonly_match','output/error/')
    fileWriter.outputObjectsListToFile(nomatch,outputname + "_nomatch",'output/error/')
    fileWriter.outputObjectsListToFile(sapdns_with_bmid,outputname + "_sapdns_with_bmid",'output/error/')

    fileWriter.outputObjectsListToFile(sapdns,outputname+'_SAPDN_With_BMSTATUS', outputpath)

    print("ADD bmid to sapdn rate", len(sapdns_with_bmid), len(sapdns))

    return sapdns_with_bmid









































































