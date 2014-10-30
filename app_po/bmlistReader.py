__author__ = 'luoyuankun'


from models import Baumathname, Site
from tools import fileReader
from tools import fileWriter
from polistReader import clearUnicode
import re


# -----------------
class AnyRowObject():
    """
    Read excel , and using the header as class properties
    """

    def __str__(self):
        return "AnyRowObject"

def readAnyRowObjectFromSheet(sheet):
    """
    Read any content from sheet, and make AnyRowObject for this sheet
    :param sheet: Worksheet
    :return: a list of AnyRowObject
    """
    result = []
    header = [unicode(h.value) for h in sheet.row(0)]
    if len(''.join(header)) == 0:
        return []
    else:
        for rx in range(1, sheet.nrows):
            rowObj = AnyRowObject()
            rowObj.Source = clearUnicode(sheet.source)
            for hx in range(len(header)):
                if (sheet.row(rx)[hx]).value:
                    reg = r'^IST|DATUM|PLAN'
                    if re.match(reg, header[hx]):
                        rowObj.__dict__[header[hx]] = (sheet.row(rx)[hx]).value
                    else:
                        rowObj.__dict__[header[hx]] = clearUnicode((sheet.row(rx)[hx]).value)
                else:
                    rowObj.__dict__[header[hx]] = None
            result.append(rowObj)
    return result


def goThrouthBMDirectory(path='input/bmstatus/test/'):

    sheets = fileReader.getAllSheetsInPath(path)
    # read bm
    rowObjs = []
    for sheet in sheets:
        rowObj = readAnyRowObjectFromSheet(sheet)
        rowObjs.extend(rowObj)
    readBMStatusFromAnyRowObject(rowObjs)


def readBMStatusFromAnyRowObject(anyRowObjects):
    """
    Read Site and BM information from anyRowObjects

    :param anyRowObjects: A list of anyRowObjects
    :return: None
    """
    count = 0
    for rowObj in anyRowObjects:
        bsfe = rowObj.BS_FE
        old_Sites = Site.objects.filter(BS_FE = bsfe)
        # test if there are no Site in db
        if len(old_Sites) == 0:
            # make new Site
            createNewSiteFromAnyRowObj(rowObj)
        count += 1
        #print("Adding %d / %d"%(count, len(anyRowObjects)))

def createNewSiteFromAnyRowObj(anyRowObj):
    """
    Create a Site Instance from the given rowObj
    :param anyRowObj: AnyRowObject
    :return: a Site Object
    """
    # build new Site Instance
    newSite = Site()
    if anyRowObj.BS_FE:
        createNewObjFromOldObj(newSite, anyRowObj)
        newSite.save()
        # build new BM
        if anyRowObj.BAUMASSNAHME_ID:
            newBM = Baumathname()
            createNewObjFromOldObj(newBM, anyRowObj)
            newBM.BS_FE = newSite
            newBM.save()
            # make link
            newSite.Baumathnames.add(newBM)
        newSite.save()
        #print('Create new Site %s'%(newSite.BS_FE))


def createNewObjFromOldObj(newObj, oldObj):
    """

    :param newObj:
    :param oldObj:
    :return: None
    """
    site_keys = newObj.__dict__.keys()
    # delete keys that not in anyRowObj
    for sk in site_keys:
        if not sk in oldObj.__dict__.keys():
            site_keys.remove(sk)
    for sk in site_keys:
        newObj.__dict__[sk] = oldObj.__dict__[sk]


def storeBM(bms):
    pass

