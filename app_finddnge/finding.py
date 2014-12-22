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
    not_find = []
    # print(dnge_list)

    walk_tree = {}

    print("*"*30)
    for (dirpath, dirnames, filenames) in os.walk(dngesinput):
        for fname in filenames:
            reg = '.*(DNGE\d+).*'
            match = re.match(reg, fname)
            if match:
                fname_clean = match.groups()[0]
                fname_clean = unicode(fname_clean)
                walk_tree[fname_clean] = (dirpath, fname)
            else:
                print("%s does not match" %(fname))

    print("*"*30)
    find_count = 0
    for dnge in dnge_list:
        if dnge in walk_tree:
            dirpath = walk_tree[dnge][0]
            fname = walk_tree[dnge][1]
            content = ""
            with open(dirpath + "/" + fname , 'rb') as f1:
                content = f1.read()
            with open(outputpath + fname ,"wb") as f2:
                f2.write(content)
            find_count += 1
        else:
            print(dnge + " can not be found")


    print("*"*30)
    print("Find %d in %d" % (find_count, len(dnge_list)))
    print("Done")

    return dnge_list, file_list

