__author__ = 'yuankunluo'


import tools.fileReader as fileReader
import tools.fileWriter as fileWriter
import os
import re



def goToFindDNGEFromListInDirectory(findlist='input/finddnge_list/', dngesinput='input/dnge/',
                                outputpath='output/finddnge/'):
    """

    :param findlist:
    :param dngesinput:
    :param output:
    :return:
    """

    row_list = fileReader.getAllRowObjectInPath(findlist,True)
    dnge_list = [r.DNGE for r in row_list]
    file_list = []
    # print(dnge_list)


    find_count = 0
    for (dirpath, dirnames, filenames) in os.walk(dngesinput):
        for fname in filenames:

            #fname_clean = re.sub('(\.xls?x)|(\.pdf)', '', fname, re.IGNORECASE)
            reg = '.*(DNGE\d+).*'
            match = re.match(reg, fname)
            if match:
                fname_clean = match.groups()[0]
                fname_clean = unicode(fname_clean)
                file_list.append(fname_clean)
                if fname_clean in dnge_list:
                    content = None
                    with open(dirpath + "/" + fname, "rb") as f:
                        content = f.read()
                    with open(outputpath + fname, "wb") as f2:
                        f2.write(content)
                    find_count += 1

    print("Find %d in %d" % (find_count, len(dnge_list)))
    print("Done")

    return dnge_list, file_list

