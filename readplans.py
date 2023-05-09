import sys
import os
import re

def filterFiles(fileList,expr):
    '''Filter only files matching given expression.'''
    for f in fileList:
        if expr.match(f):
            yield f

def getPlansWithArgs(dataRoot,exprList):
    '''Return list of all plans found in the dataRoot filtered by expr'''

    files = [f for f in os.listdir(dataRoot) if (os.path.isfile(os.path.join(dataRoot, f)))]
    plans = []
    for f in filterFiles(files,exprList):
        print('reading: {}'.format(f))
        with open(os.path.join(dataRoot,f),'r') as pfile:
            plan = []
            for line in pfile:
                strLine = line.strip('()\n')
                # TODO: use regexp to filter out empty or commented lines
                if len(strLine) == 0:
                    continue
                tokens = strLine.split(' ')
                if len(tokens) > 1:
                    action = tuple([tokens[0],tuple(tokens[1:])])
                else:
                    action = tuple([tokens[0],tuple()])
                plan.append(action)

            plans.append(plan)

    return plans
