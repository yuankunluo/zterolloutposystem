__author__ = 'yuluo'

import recordReader as recordReader
import datetime
import pickle
from collections import Counter
import tools.fileWriter as fileWriter
import copy
import re




def gogogo():
    datadict = getAllSAPData()
    sapdns = doMatch(datadict)
    bmstaus = recordReader.get_AllBMStatusRecordInPath()
    result = step_6_AddBmstatusToSapdns(bmstaus, sapdns)
    return result

def getAllSAPData():
    sappos = recordReader.get_AllSappoInPath()
    sappns = recordReader.get_AllSapdnInPath()
    orbmids = recordReader.get_AllOrderBmidInPath()
    ztepos = recordReader.get_ALLZteposInPath()
    sapprs = recordReader.get_AllPurchesingRequestionsInPath()
    bookings = recordReader.get_ALLBookingStatus()

    raw_dict = {}
    raw_dict['sappos'] = sappos
    raw_dict['sapdns'] = sappns
    raw_dict['orbmids'] = orbmids
    raw_dict['ztepos'] = ztepos
    raw_dict['sapprs'] = sapprs
    raw_dict['bookings'] = bookings

    recordReader.storeRawData(raw_dict,"Raw_data_dict",'output/raw/')
    fileWriter.outputObjectDictToFile(raw_dict,"Raw_Data_ALL",'output/dn_maker/')

    return raw_dict


def doMatch(raw_dict):

    sappos = raw_dict['sappos']
    sapdns = raw_dict['sapdns']
    orbmids = raw_dict['orbmids']
    ztepos = raw_dict['ztepos']
    sapprs = raw_dict['sapprs']
    bookings = raw_dict['bookings']

    result1 = step_1_AddOrbmidsToSapdns(orbmids,sapdns)
    result2 = step_2_AddSapPurchasingRequestToSapdns(sapprs, result1)
    result3 = step_3_AddSappToSapdns(sappos, result2)
    result4 = step_4_MixZtepoAndSapdn(ztepos, result3)
    result5 = step_5_AddBookingstatusToSapdns(bookings, result4)
    recordReader.storeRawData(result5, "Step5_SAPDN_WITH_ZTEPO","output/raw/")

    return result5





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

    c_ztepos = copy.deepcopy(ztepos)
    c_sapdns = copy.deepcopy(sapdns)

    findDisMatchWithZteposAndSapdns(c_ztepos, c_sapdns)

    # dict with ztepo
    zpo_spmq_dict = {}
    for zpo in ztepos:
        if zpo.ZTE_Site_ID and zpo.ZTE_PO_Nr and zpo.ZTE_Material and zpo.ZTE_Qty:
            unique = (zpo.ZTE_Site_ID, zpo.ZTE_PO_Nr, zpo.ZTE_Material, zpo.ZTE_Qty)
            if unique not in zpo_spmq_dict:
                zpo_spmq_dict[unique] = set()
            zpo_spmq_dict[unique].add(zpo)

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


            if unique not in zpo_spmq_dict and unique_r not in zpo_spmq_dict:
                sapdn_notin_zpos.add(sapdn)
                continue
            elif unique in zpo_spmq_dict and unique_r not in zpo_spmq_dict:
                zpo_set = zpo_spmq_dict[unique]
            else:
                zpo_set = zpo_spmq_dict[unique_r]

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

    if not outputname:
        outputname = "Step_4"
    if not outputpath:
        outputpath = 'output/dn_maker/'


    fileWriter.outputObjectsListToFile(sapdn_notin_zpos,outputname+"_sapdn_notin_zpos","output/error/")
    fileWriter.outputObjectsListToFile(sapdn_zpo_morematch,outputname+"_sapdn_zpo_morematch","output/error/")
    fileWriter.outputObjectsListToFile(sapdns,outputname+"_SAPDN_ALL",outputpath)

    sapdn_with_zpo_set = set()
    for sapdn in sapdns:
        if "ZTE_PO_Nr" in sapdn.__dict__:
            sapdn_with_zpo_set.add(sapdn)


    fileWriter.outputObjectsListToFile(sapdn_with_zpo_set,outputname+"_SAPDN_With_ZPO",outputpath)

    return sapdn_with_zpo_set

def step_5_AddBookingstatusToSapdns(bookings, sapdns,outputname=None, outputpath = None,):
    """

    :param bookings:
    :param sapdns:
    :param outputname:
    :param outputpath:
    :return:
    """
    # build booking_dict : siteid-po : bookingobj


    print("step_5_MixZtepoAndSapdn" + "-"*20 + "\n")

    site_po_dict = {}
    for booking in bookings:
        if booking.Site_ID and booking.PO:
            unique = (booking.Site_ID, booking.PO)
            if unique not in site_po_dict:
                site_po_dict[unique] = set()
            site_po_dict[unique].add(booking)

    attrs = [u'Belegedatum', u'Buchungsdatum',u'Stautus']

    booking_match = set()
    booking_dismatch = set()
    for sapdn in sapdns:
        if 'ZTE_PO_Nr' in sapdn.__dict__ and u'Equipment' in sapdn.__dict__:
            unique = (sapdn.Equipment, sapdn.ZTE_PO_Nr)
            if unique in site_po_dict:
                booking_set = site_po_dict[unique]

                if len(booking_set) == 1:
                    booking = list(booking_set)[0]
                    for k, v in booking.__dict__.items():
                        if k in attrs:
                            sapdn.__dict__[k] = v
                    booking_match.add(sapdn)
            else:
                booking_dismatch.add(sapdn)

    print("Booking match", len(booking_match),"\nBooking dismatch", len(booking_dismatch))

    if not outputname:
        outputname = "Step_5"
    if not outputpath:
        outputpath = 'output/dn_maker/'



    fileWriter.outputObjectsListToFile(sapdns,outputname+"_SAPDN_With_Booking",outputpath)
    recordReader.storeRawData(sapdns, outputname+"_SAPDN_With_Booking",'output/error/')
    recordReader.storeRawData(booking_dismatch, outputname+"_SAPDN_Without_Booking",'output/error/')

    return sapdns



def step_6_AddBmstatusToSapdns(bmstatus, sapdns, outputname=None, outputpath = None,):
    """

    :param projectname:
    :param bmstatus:
    :param sapdns:
    :param outputname:
    :param outputpath:
    :return:
    """

    print("\nstep_6_addBmstatusToSapdns" + '-'*20)

    d = {u'2Mbit-CE-Erweiterung',
        u'Erweiterung 2nd Carrier UMTS',
        u'Neues NE',
        u'Neues NE LTE',
        u'Systemtechnikwechsel',
        u'TRX/CE-Abr\xfcstung',
        u'Upgrade Systemtechnik'
    }


    bm_vorlages_dict = {
        'BPK':[u'2Mbit-CE-Erweiterung',u'Erweiterung 2nd Carrier UMTS',
               u'TRX/CE-Abr\xfcstung',u'Upgrade Systemtechnik'],
        'SWAP':[u'Systemtechnikwechsel'],
        'LTE_NEW':[u'Neues NE LTE',],
        'UNMT_NEW':[u'Neues NE',]
    }

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

    attris = [u'BAUMASSNAHME_ID', u'BS_FE',u'IST92',
              u'STRASSE', u'PLZ',u'GEMEINDE_NAME',u'NBNEU',
              u'BAUMASSNAHMEVORLAGE',u'BESCHREIBUNG',u'PRICING',
    ]

    nomatch_set = set()
    bmbsmatch_set = set()
    bsonlymatch_set = set()
    allmatch_set = set()
    more_bmidmatch_set = set()
    # do match
    for sapdn in sapdns:
        # set it't matched to false
        sapdn.__dict__['Matched'] = False

        # check if this sapdn has information
        if sapdn.Equipment and sapdn.NotesID:
            unique_bmbs = (sapdn.NotesID, sapdn.Equipment)
            # 1 check bmbs match
            if unique_bmbs in bmbs_dict:
                bm_set = bmbs_dict[unique_bmbs]
                bsonly = False
            # 2 check bsonly match
            elif sapdn.Equipment in bsonly_dict:
                bm_set = bsonly_dict[sapdn.Equipment]
                bsonly = True
            else:
                continue

            if len(bm_set) == 1:
                bm = list(bm_set)[0]

                # set this sapdn to matched
                sapdn.Matched = True
                for k, v  in bm.__dict__.items():
                    if k in attris:
                        sapdn.__dict__[k] = v
                if bsonly:
                    sapdn.__dict__['MatchType'] = 'BSONLY'
                    bsonlymatch_set.add(sapdn)
                else:
                    sapdn.__dict__['MatchType'] = 'BMBSBOTH'
                    bmbsmatch_set.add(sapdn)
                allmatch_set.add(sapdn)
            else:
                more_bmidmatch_set = more_bmidmatch_set.union(bm_set)
                more_bmidmatch_set.add(sapdn)

    # remove all matched sapdns

    new_sapdns = set()
    for sapdn in sapdns:
        if not sapdn.Matched:
            new_sapdns.add(sapdn)

    print("BMBS match", len(bmbsmatch_set),
          "BSONLY match", len(bsonlymatch_set),
          "Total match", len(allmatch_set),
          "No match", len(nomatch_set),
          "Rest SAPDNS", len(new_sapdns),
          "More BMID match", len(more_bmidmatch_set)
    )


    if not outputname:
        outputname = "Step_6"
    if not outputpath:
        outputpath = 'output/dn_maker/'


    # make a output dict with projectname-matchedsapdn
    output_dict = {}

    # make a new dict to output
    for sapdn in allmatch_set:
        if sapdn.BAUMASSNAHMEVORLAGE:
            for proname, vorlages in bm_vorlages_dict.items():
                if sapdn.BAUMASSNAHMEVORLAGE in vorlages:
                    if proname not in output_dict:
                        output_dict[proname] = set()
                    output_dict[proname].add(sapdn)

    # output dict
    for proname, matchsapdns in output_dict.items():
        fileWriter.outputObjectsListToFile(matchsapdns,outputname +"_SAPDN_BM_Matched" + "_" + proname,outputpath)


    # output error
    fileWriter.outputObjectsListToFile(bmbsmatch_set,outputname + "_bmbs_match",'output/error/')
    fileWriter.outputObjectsListToFile(bsonlymatch_set,outputname + '_bsonly_match','output/error/')
    fileWriter.outputObjectsListToFile(more_bmidmatch_set,outputname + "_more_bmidmatch",'output/error/')
    # output no matched sapdn
    fileWriter.outputObjectsListToFile(new_sapdns,outputname+"_SAPDN_DISMATCH",outputpath)
    print("ADD bmid to sapdn rate", len(allmatch_set), len(sapdns))

    return new_sapdns





def findDisMatchWithZteposAndSapdns(ztepos, sapdns):
    """

    :param ztepos:
    :param sapdns:
    :return:
    """
    # do po dict po: (m, qty)
    pass




































































