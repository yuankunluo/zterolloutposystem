__author__ = 'yuluo'

import tools.fileReader as fileReader
import tools.fileWriter as fileWriter
import re


class CreaditMemoRecord(object):

    pass



# ----------------

def goThroughDictory(path, outputfilename = 'all_credit_memos', outputpath='output/creditmemo/', recursive = False):
    """

    :param path:
    :param recursive:
    :return:
    """
    rowObjs = fileReader.getAllRowObjectInPath(path)
    cmObjes = [readCreditMemoRecordFromRowobj(obj) for obj in rowObjs]
    fileWriter.writeObjects(cmObjes,outputfilename,outputpath)
    return cmObjes

def readCreditMemoRecordFromRowobj(rowObj):
    """

    :param rowObj: a Row Object present a record in excel
    :return: a CreditMemo Object Record
    """



    headers_regx = {
    'Belastungsanzeige':'Belastungsanzeige$|Belastungsanzeigen$',
    'CreditMemo':'CreditMemo$',
    'ConfirmationDate':'DateofConfirmation$|DateofPOConfirmation$|DateofPOConfirmationDDMMYY$',
    'ProductDescription':'Description$|Detail$|ProductDescription$|ProductDescription$',
    'PO':'PO$|POEquipment$|POService$',
    'PODate':'PODate$|PODateDDMMYY$',
    'Remark':'Remark$',
    'SiteID':'SiteID$',
    'Supplier':'Supplier$',
    'YEAR':'YEAR$',
    'Amount':'Amount|CMAmount',
    }
    cmRecord = CreaditMemoRecord()


    # initial object
    for k, v in headers_regx.items():
        cmRecord.__dict__[k] = None

    cmRecord.Project = rowObj.Sheetname
    cmRecord.Source = rowObj.Source

    for k, v in headers_regx.items():
        objkeys = rowObj.__dict__.keys()
        for objk in objkeys:
            if re.match(v, objk, re.IGNORECASE):
                #print("Match:", k, objk, rowObj.__dict__[objk])
                if re.search('date', objk, re.IGNORECASE):
                    cmRecord.__dict__[k] = unicode(rowObj.__dict__[objk])
                else:
                    cmRecord.__dict__[k] = fileReader.clearUnicode(rowObj.__dict__[objk])
    return cmRecord



