__author__ = 'yuankunluo'


from app_dnmaker.recordReader import Record

from tools import fileReader
from tools import fileWriter
from app_dnmaker import recordReader
import copy
import re


class GermanReportRecord(Record):
    pass

class GermanUpdateRecord(Record):




    def __init__(self, bm, german):
        update_attr = [u'BAUMASSNAHME_ID',u'BS_FE',u'Sheetname',u'NBNEU',u'PRICING']

        for gk, gv in german.__dict__.items():
            if gk in bm.__dict__:
                if gv != bm.__dict__[gk]:
                    self.__dict__[gk+"_NEW"] = bm.__dict__[gk]
                    self.__dict__[gk+"_OLD"] = gv
                    self.__dict__.pop(gk, gv)
            if gk in update_attr:
                self.__dict__[gk] = gv




def step1_getAllGermanProjectRecordsInPath(inputPath="input/germany_summary/", outputFilename=None, outputPath = None):
    """

    :param inputPath:
    :param outputFilename:
    :return:
    """
    HEADER_REGX ={
    u'BAUMASSNAHME_ID':u'BAUMASSNAHME_ID$',
    u'BS_FE': u'BSFE$|BS_FE$',
    u'Booking': u'Booking$',
    u'Booking_Date': u'Booking_Date$',
    u'CM': u'CM$',
    u'DO_TYP_NAME': u'DO_TYP_NAME$',
    u'HW_BANF':u'HW_BANF$',
    u'HW_PO': u'HW_PO$',
    u'IST100': u'IST100$',
    u'IST21': u'IST21$',
    u'IST26': u'IST26$',
    u'IST82': u'IST82$',
    u'IST92': u'IST92$',
    u'NBNEU': u'NBNEU$',
    u'PRICING':u'PRICING$',
    u'Rowindex':u'Rowindex$',
    u'Sheetname':u'Sheetname$',
    }


    SHEET_NAME = [u'BBU Extension',u'New UMTS',u'RRU Swap',
                  u'3rd and 4th Carrier Expansion',
                  u'New LTE'
    ]

    rowObjecs = fileReader.getAllRowObjectInBook(fileReader.getTheNewestFileLocationInPath(inputPath))


    result = {}

    for k in SHEET_NAME:
        if k not in result:
            result[k] = set()

    for row in rowObjecs:
        # read right sheet name only
        if row.Sheetname in SHEET_NAME:
            gmsObj = GermanReportRecord()
            # init attributs
            for k in HEADER_REGX.keys():
                gmsObj.__dict__[k] = None

            for k, v in row.__dict__.items():
                for ak, areg in HEADER_REGX.items():
                    if re.match(areg, k):
                        gmsObj.__dict__[ak] = fileReader.clearUnicode(v)

            result[row.Sheetname].add(gmsObj)

    if not outputFilename:
        outputFilename = "RAW_German_summary"
    if not outputPath:
        outputPath = "output/bm_updater/"

    fileWriter.outputObjectDictToFile(result,
                                      outputFilename,
                                      outputPath)
    recordReader.storeRawData(result,outputFilename,"output/raw/")

    return result


def step2_getBMstatusInPath(bmpath='input/infra_bmstatus/'):
    """

    :param bmstatus:
    :param germanDict:
    :return:
    """


    bmstatus = recordReader.get_AllBMStatusRecordInPath(inputpath=bmpath,
            outputfilename="Infra_BM_All",outputpath="output/bm_updater/")

    return bmstatus



def step3_updateBmStatusToGermanReportRecord(bmstatus, germanDict):

    germanDict = copy.deepcopy(germanDict)

    attris = [u'IST92',u'IST21',
              u'IST26',u'IST82',u'IST100',]


    # build bmstatus dict
    bmbsnb_dict = {}
    bmbs_dict = {}

    for bm in bmstatus:
        if bm.BAUMASSNAHME_ID and bm.BS_FE and bm.NBNEU:
            unique = (bm.BAUMASSNAHME_ID, bm.BS_FE, bm.NBNEU)
            if unique not in bmbsnb_dict:
                bmbsnb_dict[unique] = set()
            bmbsnb_dict[unique].add(bm)

        if bm.BAUMASSNAHME_ID and bm.BS_FE:
            unique = (bm.BAUMASSNAHME_ID, bm.BS_FE)
            if unique not in bmbs_dict:
                bmbs_dict[unique] = set()
            bmbs_dict[unique].add(bm)


    update_set = set()
    for sheet, germans in germanDict.items():
        for german in germans:
            if german.BAUMASSNAHME_ID and german.BS_FE and german.NBNEU:
                unique = (german.BAUMASSNAHME_ID, german.BS_FE, german.NBNEU)
                # if this unique is ok
                if unique in bmbsnb_dict:
                    bm_set = bmbsnb_dict[unique]
                    if len(bm_set) == 1:
                        bm = list(bm_set)[0]
                        updated = False
                        for bk, bv in bm.__dict__.items():
                            if bk in attris:
                                if (german.__dict__[bk] != bm.__dict__[bk]):
                                    updated = True
                        if updated:
                            update = GermanUpdateRecord(bm, german)
                            update_set.add(update)

                        for bk, bv in bm.__dict__.items():
                            if bk in german.__dict__:
                                german.__dict__[bk] = bv


            if german.BAUMASSNAHME_ID and german.BS_FE and not german.NBNEU:
                    unique = (german.BAUMASSNAHME_ID, german.BS_FE)
                    if unique in bmbs_dict:
                        bm_set = bmbsnb_dict[unique]
                        if len(bm_set) == 1:
                            bm = list(bm_set)[0]
                        updated = False
                        for bk, bv in bm.__dict__.items():
                            if bk in attris:
                                if (german.__dict__[bk] != bm.__dict__[bk]):
                                    updated = True
                        if updated:
                            update = GermanUpdateRecord(bm, german)
                            update_set.add(update)

                        for bk, bv in bm.__dict__.items():
                            if bk in german.__dict__:
                                german.__dict__[bk] = bv

    print("Updatecount", len(update_set))

    fileWriter.outputObjectDictToFile(germanDict,'German_Project_Summary',
                                      'output/bm_updater/','%Y%m%d')

    fileWriter.outputObjectsListToFile(update_set,'German_Project_Summary_updatelist',
                                   'output/bm_updater/')



    return germanDict









