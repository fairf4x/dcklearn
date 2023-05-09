import statistics

def selectTopSubset(data,scoreFunction,inputSet,maximize=True,treshold=None):
    ''' Select subset from inputSet that has top score computed by scoreFunction on data
        scoreFunction should take two arguments - key to the data dictionary and the data dictionary itself
        inputSet .. base set we want to select from
        maximize .. True if we want to maximize score (False otherwise)
        treshold .. if maximal score is under treshold (or minimalscore over it) return empty set
    '''

    # list of pairs: (action,score)
    scoreTable = [(a,scoreFunction(a,data)) for a in inputSet]

    if len(scoreTable) == 0:
        return []

    if maximize:
        topScore = max([s for (a,s) in scoreTable])
        if not (treshold == None) and (topScore < treshold):
            return []
    else:
        topScore = min([s for (a,s) in scoreTable])
        if not (treshold == None) and (topScore > treshold):
            return []

    # replace all actions with other than topScore with None
    onlyTop = [a if s == topScore else None for (a,s) in scoreTable]
    # filter out None values to get list of top scoring actions
    return list(filter((None).__ne__,onlyTop))

def lengthVariance(planList):
    '''Count how many different lengths do plans in planList have.'''
    # - get list of lenghts for each plan
    # - make set from the list - only unique numbers remains
    # - count unique lengths
    return len(set([len(p) for p in planList]))

def differentObjectCount(planList):
    '''Return median of different object counts.'''
    objectCount = []
    for p in planList:
        objectSet = set()
        for (actName,argTup) in p:
            objectSet.update(argTup)
    
        objectCount.append(len(objectSet))

    if len(objectCount) == 0:
        return 1000000
    else:
        return statistics.median(objectCount)

def minLength(planList):
    '''Determine minimal plan length among all plans in the list'''
    if len(planList) > 0:
        return min([len(p) for p in planList])
    else:
        return 0

########## scoring functions ########
# data dictionary: {action: (minAcnt,maxAcnt,totalCnt,patterns,head,middle,tail)}

def atLeastOnceEverywhere(action,data):
    if data[action][0] > 0:
        return 1
    else:
        return 0

def middleListVariance(action,data):
    # data_actionX = (minAcnt,maxAcnt,totalAcnt,headList,middleList,tailList)
    return lengthVariance(data[action][4])

def objectFocus(action,data):
    '''Count number of different objects referenced in the plan.
    Low count should indicate that plan is focused on small set of objects.'''
    middleList = data[action][4]
    return differentObjectCount(middleList) 

def minLengthSum(action,data):
    minLenHead = minLength(data[action][3])
    minLenMiddle = minLength(data[action][4])
    minLenTail = minLength(data[action][5])
    return (minLenHead + minLenMiddle + minLenTail)

def minOccurence(action,data):
    return data[action][0]

def maxOccurence(action,data):
    return data[action][1]

def totalOccurence(action,data):
    return data[action][2]

def selectAction(actionSplitData):
    '''Select one action based on actionSplitData
    actionSplitData = {'action1':data_action1,action2:data_action2,...}
    data_actionX = (minAcnt,maxAcnt,totalAcnt,headList,middleList,tailList)
    minAcnt ... minimal count of actionX among all plans
    maxAcnt ... maximal count of actionX among all plans
    totalAcnt ... total count of actionX in all plans
    headList ... list of subplans from beginning of plans (see refle.py processPlan and splitPlan)
    middleList ... list of subplans from middle of plans
    tailList ... list of subplans from tails of plans
    '''
    # TODO: maybe we should use stack of scoring functions for disambiguation

    actionSet = actionSplitData.keys()

    ## filters ##

    # select actions occuring at least once in every plan
    topActions = selectTopSubset(actionSplitData,atLeastOnceEverywhere,actionSet,maximize=True,treshold=1)
    if len(topActions) == 0:
        # if there are no such actions selection failed
        return None
    else:
        # disambiguation1
        topActionsD1 = selectTopSubset(actionSplitData,middleListVariance,topActions,maximize=False)
        #topActionsD1 = selectTopSubset(actionSplitData,objectFocus,topActions,maximize=False)
        if len(topActionsD1) == 1:
            # there is only one action in the set
            return topActionsD1[0]
        else:
            topActionsD2 = selectTopSubset(actionSplitData,minLengthSum,topActionsD1,maximize=False)
            if len(topActionsD2) == 1:
                return topActionsD2[0]
            else:
                # we can possibly disambiguate further - for now we let lexicographic order decide
                topASorted = sorted(topActionsD2)
                return topASorted[0]
