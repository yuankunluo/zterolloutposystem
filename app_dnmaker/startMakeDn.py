__author__ = 'yuluo'

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
    projectDict = {'BBU': 'input/infra_bmstatus_bbu/',
                    'BPK': 'input/infra_bmstatus_bpk/',
                    'LTE': 'input/infra_bmstatus_lte/',
                    'RRUSWAP': 'input/infra_bmstatus_rruswap/',
                    'UMTSNEW': 'input/infra_bmstatus_umtsnew/'
    }


    sappos =  raw_dict['sappos']
    sapdns = raw_dict['sapdns']
    orbmids = raw_dict['orbmids']
    ztepos = raw_dict['ztepos']








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


    fileWriter.outputObjectsListToFile(sapdns,outputname +'_SAPDN_With_SAPPO',outputpath)
    fileWriter.outputObjectsListToFile(unique_dismatch,outputname + '_SAPDN_SAPPO_uniquedismatch','output/error/')
    fileWriter.outputObjectsListToFile(unique_more, outputname + "_SAPPO_mormath","output/error/")

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

    # build siteid-po-mat-qty dict









def new_step2_addBmstatusToSapdns(projectname, bmstatus, sapdns, outputname=None, outputpath = None,):
    """

    :param bmstatus: all bm92
    :param sapdns:
    :return:
    """
    bmstatus = copy.deepcopy(bmstatus)
    sapdns = copy.deepcopy(sapdns)


    #build bm_dict
    bmbs_dict = {}
    bsonly_dict = {}
    bmonly_dict = {}

    bmstatus = list(bmstatus)

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
        # add bmonly:
            if bm.BAUMASSNAHME_ID not in bmonly_dict:
                bmonly_dict[bm.BAUMASSNAHME_ID] = set()
                bmonly_dict[bm.BAUMASSNAHME_ID].add(bm)
            else:
                bmonly_dict.pop(bm.BAUMASSNAHME_ID)


    print("BMBS dict", len(bmbs_dict),
          "BSONLY dict", len(bsonly_dict),
          "BMONLY dict", len(bmonly_dict)
    )


    bmbs_match = set()
    bsonly_match = set()
    match = set()
    nomatch = set()

    # do match
    for sapdn in sapdns:
        bm0 = bmstatus[0]
        for k, v in bm0.__dict__.items():
            if k not in sapdn.__dict__:
                sapdn.__dict__[k] = None

        # check if this sapdn has information
        if sapdn.Equipment and sapdn.NotesID:
            unique_bmbs = (sapdn.NotesID, sapdn.Equipment)
            # 1 check bmbs match
            if unique_bmbs in bmbs_dict:
                bm_set = bmbs_dict[unique_bmbs]
                if len(bm_set) == 1:
                    bm = list(bm_set)[0]
                    for k, v in bm.__dict__.items():
                        sapdn.__dict__[k] = v
                    sapdn.MATCH_TYPE = "BM_BS"
                    bmbs_match.add(sapdn)
                    match.add(sapdn)
                    continue

            # 2 check bsonly match

            elif unique_bmbs not in bmbs_dict and sapdn.Equipment in bsonly_dict:
                bm_set = bsonly_dict[sapdn.Equipment]
                if len(bm_set) == 1:
                    bm = list(bm_set)[0]
                    for k, v in bm.__dict__.items():
                        sapdn.__dict__[k] = v
                    bsonly_match.add(sapdn)
                    sapdn.MATCH_TYPE = "BS_ONLY"
                    match.add(sapdn)
                    continue
            else:
                nomatch.add(sapdn)

    print("BMBS match", len(bmbs_match),
          "BSONLY match", len(bsonly_match),
          "Total match", len(match),
          "No match", len(nomatch)
    )


    if not outputname:
        outputname = "Step_2"
    if not outputpath:
        outputpath = 'output/dn_maker/'

    if projectname:
        outputname = projectname + "_" + outputname


    sapdns_with_bmid = [sapdn for sapdn in sapdns if sapdn.BAUMASSNAHME_ID]

    fileWriter.outputObjectsListToFile(bmbs_match,outputname + "_bmbs_match",'output/error/')
    fileWriter.outputObjectsListToFile(bsonly_match,outputname + '_bsonly_match','output/error/')
    fileWriter.outputObjectsListToFile(nomatch,outputname + "_nomatch",'output/error/')
    fileWriter.outputObjectsListToFile(sapdns_with_bmid,outputname + "_sapdns_with_bmid",'output/error/')

    fileWriter.outputObjectsListToFile(sapdns,outputname+'_SAPDN_WITHBMID', 'output/dn_maker/')

    print("ADD bmid to sapdn rate", len(sapdns_with_bmid), len(sapdns))

    return sapdns_with_bmid






def new_step4_MixZteposIntoSapdns(projectname,ztepos, sapdns,outputname=None, outputpath = None,):
    """

    :param ztepos:
    :param sapdns:
    :return:
    """

    ztepos = copy.deepcopy(ztepos)
    sapdns = copy.deepcopy(sapdns)

    d_sappo = {u'SAP_Doc_Date': u'41800',
     u'SAP_Item_of_PO': u'10',
     u'SAP_Material': u'50016774',
     u'SAP_Material_Description': u'ZTE. UMTS ZN000078  MCO BS8900B 3 RSU82,',
     u'SAP_PO_Quantity': u'1',
     u'SAP_PurchNo': u'32010557',
     u'SAP_Reference_PO_Number': u'43098103'}

    d_sapdn = {u'Deletion_Indicator': u'L',
     u'Document_Date': u'40638',
     u'Document_item': u'0',
     u'Goods_recipient': None,
     u'Item': u'10',
     u'Material': u'50014172',
     u'Order': u'50083852',
     u'Order_Quantity': u'1',
     u'Order_Unit': u'ST',
     u'Purchasing_Document': u'32003539',
     u'Purchasing_Info_Rec': u'5300116271',
     u'SAP_Doc_Date': u'40638',
     u'SAP_Item_of_PO': u'10',
     u'SAP_Material': u'50014172',
     u'SAP_Material_Description': u'ZTE DBS NodeB BS8700 DC, ZN000001',
     u'SAP_PO_Quantity': u'1',
     u'SAP_PurchNo': u'32003539',
     u'SAP_Reference_PO_Number': None,
     u'Short_Text': u'ZTE DBS NodeB BS8700 DC, ZN000001',
     u'Still_to_be_delivered_qty': u'0'}



    sap_refmq_dict = {}
    sap_pmq_dict = {}
    sap_bs_m_dict = {}
    count = 0
    for sapdn in sapdns:
        if (sapdn.SAP_Reference_PO_Number and sapdn.Material and sapdn.Order_Quantity):
            unique = (sapdn.SAP_Reference_PO_Number,sapdn.Material,sapdn.Order_Quantity)
            if unique not in sap_refmq_dict:
                sap_refmq_dict[unique] = set()
            sap_refmq_dict[unique].add(sapdn)
            count += 1

        if (not sapdn.SAP_Reference_PO_Number
            and sapdn.Purchasing_Document
            and sapdn.Material
            and sapdn.Order_Quantity
        ):
            unique = (sapdn.Purchasing_Document, sapdn.Material,sapdn.Order_Quantity)
            if unique not in sap_pmq_dict:
                sap_pmq_dict[unique] = set()
            sap_pmq_dict[unique].add(sapdn)
            count += 1
        if sapdn.Equipment and sapdn.Material:
            unique = (sapdn.Equipment, sapdn.Material)
            if unique not in sap_bs_m_dict:
                sap_bs_m_dict[unique] = set()
            sap_bs_m_dict[unique].add(sapdn)

    print("Refm_dict", len(sap_refmq_dict), "pm_dict", len(sap_pmq_dict), len(sapdns),
          "Diff", len(sapdns)-count, len(sapdns)-len(sap_refmq_dict)-len(sap_pmq_dict)
    )




    zpo_d = {'Hidden': False,
     'ZTE_CM_Date': u'40638',
     'ZTE_CM_No': u'5101009596',
     'ZTE_Contract_No': u'S4DE2009121802UMTP1',
     'ZTE_Delivery_Date': u'40410',
     'ZTE_Item_Code': None,
     'ZTE_Material': u'50014172',
     'ZTE_Origin_Mcode': u'50014172',
     'ZTE_Origin_Qty': u'1',
     'ZTE_PO_Amount': u'2000',
     'ZTE_PO_Date': u'40371',
     'ZTE_PO_Nr': u'32001158',
     'ZTE_Product_Description': u'B8200 (2 Bpc) + 3XR8840 + 3XOLP(DC) + cable set for B8200/RRU/OLP',
     'ZTE_Project': u'UMTS New',
     'ZTE_Qty': u'1',
     'ZTE_Remark': None,
     'ZTE_Site_ID': u'18534033'}

    # build ztepo dict
    zpo_pmr_dict = {}

    for zpo in ztepos:
        if zpo.ZTE_PO_Nr and zpo.ZTE_Material and zpo.ZTE_Qty:
            unique = (zpo.ZTE_PO_Nr, zpo.ZTE_Material, zpo.ZTE_Qty)
            if unique not in zpo_pmr_dict:
                zpo_pmr_dict[unique] = set()
            zpo_pmr_dict[unique].add(zpo)

    # do match


    match = set()
    zpo_nomatch = set()
    morematch = set()
    oneuniquematch  = set()
    more_zpo = set()
    more_sapdn = set()
    onlyBsfeMatch = set()
    for unique, zposet in zpo_pmr_dict.items():
        # it's a normal po
        if unique in sap_pmq_dict:
            spo_set = sap_pmq_dict[unique]
        elif unique in sap_refmq_dict and unique not in sap_pmq_dict :
            spo_set = sap_refmq_dict[unique]
        else:
            spo_set = None

        # if this unique has sappo
        if spo_set and zposet:
            # unique onlye
            if len(spo_set) == len(zposet) == 1:
                # one to one match
                sapdn = list(spo_set)[0]
                zpo = list(zposet)[0]
                for k, v in zpo.__dict__.items():
                    sapdn.__dict__[k] = v
                oneuniquematch.add(sapdn)
                match.add(sapdn)
            else:
                if len(spo_set) < len(zposet):
                    #
                    #  sap has less po, that means wrong zpo record
                    more_zpo = more_zpo.union(zposet)
                if len(spo_set) > len(zposet) and len(spo_set)>1 and len(zposet)>0:
                    # sap has more po than zpolist
                    # it means has more position
                    spo_l = list(spo_set)
                    zpo_l = list(zposet)
                    zpo = zpo_l[0]
                    for i in range(len(spo_l)):
                        sapdn = spo_l[i]
                        try:
                            new_zpo = zpo_l[i]
                        except Exception:
                            new_zpo = zpo
                        for k, v in new_zpo.__dict__.items():
                            sapdn.__dict__[k] = v
                        morematch.add(sapdn)
                        match.add(sapdn)

        else:
            # if this ztepo set has not match with sapdn set
            # we check it with the sapdn_bsfe-dict to match every ztp's site id
            # using the Only one bsfe to match
            for zpo in list(zposet):
                if zpo.ZTE_Site_ID and zpo.ZTE_Material:
                    unique = (zpo.ZTE_Site_ID, zpo.ZTE_Material)
                    if unique in sap_bs_m_dict:
                        sap_set = sap_bs_m_dict[unique]
                        for sapdn in list(sap_set):
                            for k,v in zpo.__dict__.items():
                                sapdn.__dict__[k] = v
                            match.add(sapdn)
                            onlyBsfeMatch.add(sapdn)
                else:
                    zpo_nomatch.add(zpo)

    print("One-unique match", len(oneuniquematch), len(sapdns), len(ztepos),
          "MoreSAPPO-match", len(morematch),
          "Total Match", len(match), len(sapdns),
          "Only BSFE match", len(onlyBsfeMatch), len(sapdns)
    )


    if not outputname:
        outputname = "Step_4"
    if not outputpath:
        outputpath = 'output/dn_maker/'

    if projectname:
        outputname = projectname + "_" + outputname

    fileWriter.outputObjectsListToFile(zpo_nomatch,outputname +"_ZPO_nomatch","output/error/")
    fileWriter.outputObjectsListToFile(list(more_sapdn),outputname+"_More_SAPDN","output/error/")
    fileWriter.outputObjectsListToFile(list(more_zpo),outputname+"_More_ZTEPO","output/error/")
    fileWriter.outputObjectsListToFile(list(match),outputname+"_Matach_taotal",outputpath)

    return match









































