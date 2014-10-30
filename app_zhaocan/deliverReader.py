__author__ = 'yuluo'
import tools.fileReader as fileReader
from tools.fileReader import clearUnicode
import tools.fileWriter as fileWriter
import re
from collections import OrderedDict

class BSSTO(object):

    def __init__(self):
        self.BS_STO = None
        self.BS_FES = {}

class BSFE(object):

    def __init__(self):
        self.BS_STO = None
        self.BS_FE = None
        self.Type = None

class ESWAP(object):
    pass

def goThroughDirectory(sitePath = 'input/zhaocan/site', eswapPath = 'input/zhaocan/eswap'):
    """

    :param sitePath:
    :param eswapPath:
    :return:
    """
    siteRecords = fileReader.getAllRowObjectInPath(sitePath)
    eswapRecords = fileReader.getAllRowObjectInPath(eswapPath)
    # select only in total

    result = doMixThing(siteRecords, eswapRecords)
    fileWriter.outputDeliverRecord(result)
    return result


def doMixThing(siteRecors, eswapRecors):
    """

    :param siteRecors:
    :param eswapRecors:
    :return:
    """
    # delete duplicated bsstos
    # bsstos_nr = [fileReader.clearUnicode(sR.BS_STO) for sR in siteRecors]
    # bsstos_nr = set(bsstos_nr)
    # bsstos_nr = list(bsstos_nr)
    #
    # BSSTO_DICT = {}
    #
    # BSFE_TO_BST_DICT = {}

    # for sR in siteRecors:
    #     sr_BS_STO = fileReader.clearUnicode(sR.BS_STO)
    #     sr_LTE_BS_FE = fileReader.clearUnicode(sR.LTE_BS_FE)
    #     sr_UMTS_BS_FE = fileReader.clearUnicode(sR.UMTS_BS_FE)
    #     if sr_BS_STO not in BSSTO_DICT.keys():
    #         bstObj = BSSTO()
    #         bstObj.BS_STO = sr_BS_STO
    #         bstObj.BS_FES[sr_LTE_BS_FE] = []
    #         bstObj.BS_FES[sr_UMTS_BS_FE] = []
    #         BSSTO_DICT[sr_BS_STO] = bstObj
    #     else:
    #         bstObj = BSSTO_DICT[sr_BS_STO]
    #         for bsfe in [sr_LTE_BS_FE, sr_UMTS_BS_FE]:
    #             if bsfe not in bstObj.BS_FES.keys():
    #                 bstObj.BS_FES[bsfe] = []
    #
    #     BSFE_TO_BST_DICT[sr_UMTS_BS_FE] = BSSTO_DICT[sr_BS_STO]
    #     BSFE_TO_BST_DICT[sr_LTE_BS_FE] = BSSTO_DICT[sr_BS_STO]
    #
    # error_count = 0
    #
    # for esR in eswapRecors:
    #     try:
    #         esR_Reference = fileReader.clearUnicode(esR.Reference)
    #         esR_Qty = fileReader.clearUnicode(esR.Qty)
    #         esR_Site_Equipment = fileReader.cleanString(esR.Site_Equipment)
    #         # get the bst key
    #
    #         bstNr = BSFE_TO_BST_DICT[esR_Reference]
    #         bstObj = BSSTO_DICT[bstNr]
    #         bstObj.BS_FES[esR_Reference].append((esR_Site_Equipment, esR_Qty))
    #     except Exception:
    #         print(esR.__dict__.keys(), esR.Package_SN)
    #         error_count += 1
    #
    # print("Errorcount",error_count)

    BSFE_TO_STO = {}
    for sR in siteRecors:
        for k in [u'LTE_BS_FE', u'UMTS_BS_FE']:
            BSFE_TO_STO[clearUnicode(sR.__dict__[k])] = [clearUnicode(sR.BS_STO), k]

    temp = []

    for sR in eswapRecors:
        try:
            bsto_type = BSFE_TO_STO[clearUnicode(sR.Reference)]
            bsto = bsto_type[0]
            type = bsto_type[1]
            if re.search('lte', type, re.IGNORECASE):
                sR.Type = 'LTE'
            if re.search('umts', type, re.IGNORECASE):
                sR.Type = 'UMTS'
            else:
                continue
            sR.BS_STO = bsto
            temp.append(sR)
        except Exception:
            pass
            # print(sR.__dict__)


    result = OrderedDict()
    # for es in temp:
    #     bs_sto = es.BS_STO
    #     bs_fe = clearUnicode(es.Reference)
    #     if bs_sto not in result.keys():
    #         result[bs_sto] = OrderedDict()
    #         bstObj = result[bs_sto]
    #         bstObj[bs_fe] = []
    #     BSTO = result[bs_sto]
    #     if bs_fe not in BSTO.keys():
    #         BSTO[bs_fe] = []
    #     BSTO[bs_fe].append((unicode(es.Site_Equipment), unicode(es.Qty)))

    for es in temp:
        bs_sto = clearUnicode(es.BS_STO)
        bs_fe = clearUnicode(es.Reference)
        equipment = es.Site_Equipment
        qty = es.Qty
        type = es.Type
        if bs_fe not in result.keys(): # this bsfe not in reslt
            bsfeObj = BSFE()
            bsfeObj.BS_FE = bs_fe
            bsfeObj.BS_STO = bs_sto
            bsfeObj.Type = type
            bsfeObj.Products = [(equipment, qty)]
            bsfeObj.Count = 1
            try:
                bsfeObj.Summer = int(qty)
            except Exception:
                pass
            result[bs_fe] = bsfeObj
        else:
            bsfeObj = result[bs_fe]
            bsfeObj.Products.append((equipment, qty))
            bsfeObj.Count += 1
            try:
                bsfeObj.Summer += int(qty)
            except Exception:
                pass
    return result




def prePareToWrite(result):

    Objects = []


    for sto_nr, valueDict in result.items():
        for bs_fe, content in valueDict.items():
            pass


















