#!/usr/bin/python3

import re
# option parsing
from optparse import OptionParser
from pathlib import Path

import refle
from FSA import *

def main():
    usage = "usage: %prog -p PLANDIR [-r RE] [-o OUT -f FORMAT] [-m DOMAIN]"
    parser = OptionParser(usage=usage)

    parser.add_option("-p", "--path", dest="planDir", metavar="PLANDIR", default=None,
                      help="Path to directory with plans.")
    parser.add_option("-r", "--regexp", dest="filterStr", metavar="RE", default="..*",
                      help="Only plans matching given RE will be used for learning.")
    parser.add_option("-o", "--output", dest="outFileName", metavar="OUT", default=None,
                          help="Output filename base string.")
    parser.add_option("-f", "--format", dest="outFormat", metavar="FORMAT", default=None,
                          help="Output file format (gv,png,svg,pdf)")
    parser.add_option("-m", "--mergePDDL", dest="pddlDomain", metavar="DOMAIN", default=None,
                      help="Path to PDDL domain file.")

    (options, args) = parser.parse_args()

    planDir = options.planDir
    filterStr = options.filterStr
    outFileName = options.outFileName
    outFormat = options.outFormat
    pddlDomain = options.pddlDomain

    if planDir == None:
        print('Missing path to plans (option -p)')
        return

    expr=re.compile(filterStr)

    stack = refle.processDomain(planDir,expr)

    A = FSA.initFromStack(stack)

    # do we render diagram?
    diagram = True

    # do we render PDDL file?
    pddlOut = True

    if outFileName == None:
        print('Output file not specified. Use -o "NAME"')
        diagram = False
        pddlOut = False

    if outFormat == None:
        diagram = False

    imageFormats = set(['png','svg','pdf'])

    if (not (outFormat in imageFormats)) and (outFormat != 'gv'):
        print('File format not specified or unknown.')
        diagram = False

    if diagram:
        # render image
        if outFormat in imageFormats:
             A.render(outFileName,outFormat)
        else:
            # save graphviz textual representation
            if outFormat == 'gv':
                A.saveDiagram("{}.{}".format(outFileName,outFormat))
    else:
        print("Option -f missing - FSA diagram not rendered.")

    if pddlDomain == None:
        print('No domain specified. Use -m "PATH_TO_DOMAIN_FILE"')
        pddlOut = False

    if pddlOut:
        # output PDDL file - merging FSA to specified domain
        pddlText = A.merge2PDDLdomain(pddlDomain,outFileName)
        with open("{}.pddl".format(outFileName),"w",encoding="utf-8") as pddlOutFile:
            print(pddlText,file=pddlOutFile)


if __name__ == "__main__":
    main()
