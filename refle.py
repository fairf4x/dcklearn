# refactored learning.py
import re
import operator
# own modules
from readplans import *
#from multichains import *
from pattern import *
from selector import selectAction
from retree import PlanRETree

def countAction(action,plan):
    cnt = 0
    for (aName,args) in plan:
        if action == aName:
            cnt += 1

    return cnt

def getActionIndexList(action,plan):
    '''Get list of action occurence indices. Empty list means no such action is present in the plan.'''
    aoList = []
    for (i,(a,args)) in enumerate(plan):
        if a == action:
            aoList.append(i)

    return aoList

def splitPlan(action,planIn):
    '''split plan to blocks between occurences of action with border actions included
       e.g. plan: [('lift', ('hhh2', 'ccc2', 'sss2', 'ppp2')),
             ('load', ('hhh1', 'ccc1', 'ttt1', 'p1')),
             ('drive', ('ttt1', 'ppp1', 'ppp2')),
             ('load', ('hhh1', 'ccc1', 'ttt1', 'p2')),
             ('load', ('hhh1', 'ccc1', 'ttt1', 'p3'))]
        splits to 4 blocks with "load" as action:
        [[('lift', ('hhh2', 'ccc2', 'sss2', 'ppp2')),
          ('load', ('hhh1', 'ccc1', 'ttt1', 'p1'))],

         [('load', ('hhh1', 'ccc1', 'ttt1', 'p1')),
          ('drive', ('ttt1', 'ppp1', 'ppp2')),
          ('load', ('hhh1', 'ccc1', 'ttt1', 'p2'))],

         [('load', ('hhh1', 'ccc1', 'ttt1', 'p2')),
          ('load', ('hhh1', 'ccc1', 'ttt1', 'p3'))],

         [('load', ('hhh1', 'ccc1', 'ttt1', 'p3'))]]
    '''

    plan = list(planIn)
    aoStack = getActionIndexList(action,plan)
    if len(aoStack) == 0:
        # the action was not found in the plan
        return None

    start = 0
    blockList = []
    while len(aoStack) > 0:
        end = aoStack.pop(0)
        # end index marks action occurence.
        # blocks are cut including start and excluding end index: <start,end>
        blockList.append(plan[start:end+1])
        start = end

    # we need to add last block
    blockList.append(plan[start:])

    return blockList

def trimPlan(plan,start=True,end=True):
    '''Cut first and last action from input plan.
       Return copy of the original plan.
    '''
    res = list(plan)

    if start and end:
        return res[1:-1]
    elif start and (not end):
        return res[1:]
    elif (not start) and end:
        return res[:-1]
    else:
        # this is equivalent to not calling trimPlan at all
        return plan

def processPlan(action,plan,headList,middleList,tailList):
    '''Update headList, middleList, tailList and patternList.
       Input: action used for split
              plan to split
    '''

    # split works like this:
    # B0 a0 B1 a1 B2 a2 B3
    # splitActions = [a0,a1,a2]
    # blocks = [[B0,a0],[a0,B1,a1],[a1,B2,a2],[a2,B3]]
    blocks = splitPlan(action,plan)

    # action is not present in the plan
    if blocks == None:
            # head block is whole plan
            headList.append(plan)
            return 0

    # count actions found in this particular plan (there is always one block more than actionCnt)
    actionCnt = len(blocks) - 1

    # manage blocks of actions - update global lists:
    # headList
    # middleList
    # tailList
    # patternList
    headBlock = []
    middleBlocks = []
    tailBlock = []
    # there should be always more than one action (if there is none splitRes == None earlier)
    assert actionCnt > 0
    if actionCnt == 1:
        # single action -> head.a.tail
        headBlock = blocks[0]
        tailBlock = blocks[1]
        headList.append(headBlock)
        tailList.append(tailBlock)
    elif actionCnt >= 2:
        # at least 2 actions -> head.a.(middle.a)*tail
        headBlock = blocks[0]
        middleBlocks = blocks[1:-1]
        tailBlock = blocks[-1]

        headList.append(headBlock)
        for b in middleBlocks:
            middleList.append(b)
        tailList.append(tailBlock)

    return actionCnt

def identicActionSeq(plans):
    '''Check if all action sequences are identical in given set of plans'''
    firstSeq = [a for (a,_) in plans[0]]

    for p in plans[1:]:
        seq = [a for (a,_) in p]
        if firstSeq != seq:
            return False

    return True

def initializePattern(actionSet,plans,domainSignature,trace,level):
    '''Initialize pattern when there is no available action that could be used to split plans further'''
    print('No action selected at level {}'.format(level))
    print('returning: {}'.format(actionSet))
    # end of recursion
    # init pattern
    # possibilities:
    # 1) empty blocks - border actions only
    # 2) nonempty blocks - border actions + set of actions

    # Cut off edge actions if they are just
    # dummy None actions marking beginning and end of the plan
    (leftEnd,rightEnd,recursionType,prevSplit) = trace
    plansTrimmed = list(map(lambda p:trimPlan(p,leftEnd,rightEnd),plans))

    if len(actionSet) != 0:
        # nonempty blocks
        if identicActionSeq(plans):
            # all plans has identic action sequence
            return Pattern.fromplans(plansTrimmed,domainSignature)
        else:
            # at least one plan has different action sequence
            # first and last action should be same for all plans
            # there are some actions from actionSet in between them
            return Pattern.fromborders(plansTrimmed,domainSignature,trace)
    else:
        # empty blocks - action sequence is always the same
        # there are only border actions from previous split
        return Pattern.fromplans(plansTrimmed,domainSignature)

def makeRE(plans,domainSignature,trace,level):
    # plans - list of input plans with border actions included
    # level - recursion level

    # information about head or tail recursive call
    # leftEnd - left edge of plan
    # rightEnd - right edge of plan
    # recursionType - head/middle/tail marked with -1/0/1
    # name of previous split action
    (leftEnd,rightEnd,recursionType,prevSplit) = trace
    if level == 0:
        assert leftEnd and rightEnd

    # get set of all actions in all plans except for the first and last action
    # border actions are used to connect patterns
    # there are virtual actions on plan edges we want to leave out

    if leftEnd and rightEnd:
        actionSet = set([a for p in plans for (a,args) in p if a != None])
    elif leftEnd and (not rightEnd):
        actionSet = set([a for p in plans for (a,args) in p[:-1] if a != None])
    elif (not leftEnd) and rightEnd:
        actionSet = set([a for p in plans for (a,args) in p[1:] if a != None])
    elif (not leftEnd) and (not rightEnd):
        actionSet = set([a for p in plans for (a,args) in p[1:-1] if a != None])

    # returning leaf node
    if len(actionSet) == 0:
        pattern = initializePattern(actionSet,plans,domainSignature,trace,level)
        return (actionSet,pattern)
    else:
        # at least one action - we need to select one

        # cut off first and last action from all plans
        # those should be only split actions or dummy actions (first and last from plan)
        trimmedPlans = list(map(lambda p:trimPlan(p),plans))

        actionSplitData = dict()
        # we need to select the best action to split over all plans
        # we make a split and record all the data - this will be scored later to select the best action
        # only the data produced by best split action will be processed further
        for action in actionSet:
            # initialization of internal loop variables
            # P.a.(R.a)*.Q
            headList = []
            middleList = []
            tailList = []

            # count max and min number of occurences across all plans
            # initialize counters
            maxAcnt = 0
            minAcnt = max([len(p) for p in plans])

            # we need total action count to disambiguate scoring
            totalCnt = 0
            impossibleSplit = False
            # splitting each plan into three parts and cummulating head, middle and tail block lists
            for plan in trimmedPlans:

                actionCnt = processPlan(action,plan,headList,middleList,tailList)

                totalCnt = totalCnt + actionCnt

                if actionCnt > maxAcnt:
                    maxAcnt = actionCnt

                if actionCnt < minAcnt:
                    minAcnt = actionCnt

            # (minAcnt,maxAcnt,totalCnt,head,middle,tail)
            dataPack = (minAcnt,maxAcnt,totalCnt,headList,middleList,tailList)

            actionSplitData[action] = dataPack

        # we use recorded data to determine which should be used for split at this level
        action = selectAction(actionSplitData)

    print('lvl {}: {}'.format(level,action))

    # no action was chosen (e.g. no common action in all plans - see selectAction)
    # returning trivial node
    if action == None:
        pattern = initializePattern(actionSet,plans,domainSignature,trace,level)
        return (actionSet,pattern)

    # if changing code below check dataPack for indices
    topMinAcnt = actionSplitData[action][0]
    topMaxAcnt = actionSplitData[action][1]


    topHeadList = []
    topMiddleList = []
    topTailList = []

    # splitting each plan into three parts and cummulating head, middle and tail block lists
    for plan in plans:
        processPlan(action,plan,topHeadList,topMiddleList,topTailList)

    assert (topMinAcnt > 0) and (topMaxAcnt > 0)

    middleRepetition = ''
    if topMinAcnt == topMaxAcnt:
        if (topMinAcnt < 2):
            # head.a.tail - no middle section at all
            middleRepetition = "0"
        elif (topMinAcnt == 2):
            # head.a.(middle.a).tail - middle section is present exactly once in all plans
            middleRepetition = "1"
        elif (topMinAcnt > 2):
            # head.a.(middle.a).(middle.a).tail - middle section is present at least once
            middleRepetition = "+"
    else: # topMinAcnt < topMaxAcnt
        if (topMinAcnt < 2):
            # head.a.tail - middle section can be completely ommited
            middleRepetition = "*"
        elif (topMinAcnt >= 2):
            # head.a.(middle.a).(middle.a).tail - middle section can be present once or more
            middleRepetition = "+"

    assert(middleRepetition != '')

    res = PlanRETree(action,level,middleRepetition)

    patterns = []

    # recursive call for nonempty action sets
    # trace information is passed down:
    # (bool,bool,int,string) - (leftPlanEdge,rightPlanEdge,recursionType,prevSplit)
    # recursion type can be:
    # -1 - head recursion
    # 0 - middle recursion
    # 1 - tail recursion
    print('--- HEAD {} ----'.format(level))
    (res.head,headPattern) = makeRE(topHeadList,domainSignature,(leftEnd,False,-1,action),level+1)

    if len(topMiddleList) > 0:
        print('--- MIDDLE {} ----'.format(level))
        (res.middle,middlePattern) = makeRE(topMiddleList,domainSignature,(False,False,0,action),level+1)
    else:
        print('--- EMPTY MIDDLE {} ----'.format(level))
        res.middle = set()
        middlePattern = None

    print('--- TAIL {} ----'.format(level))
    (res.tail,tailPattern) = makeRE(topTailList,domainSignature,(False,rightEnd,1,action),level+1)

    # pattern construction
    if headPattern != None:
        patterns.append(headPattern)

    if middlePattern != None:
        patterns.append(middlePattern)

    if tailPattern != None:
        patterns.append(tailPattern)

    combinedPattern = Pattern.connectPatterns(patterns,domainSignature)

    # returning non-trivial node
    return (res,combinedPattern)

def wrapPlans(plans,action):
    for p in plans:
        p.insert(0,action)
        p.append(action)

def getDomainSignature(plans):
    signature = {}
    for p in plans:
        for (a,args) in p:
            if not (a in signature):
                signature[a] = len(args)
    return signature

def  integratePattern2Stack(stack,patternCl):
    '''Rewrite simple strings in RETree stack to pairs (actionName,argTuple) from Pattern.'''
    newStack = []
    # reverse pattern in order to use it as stack of actions to process
    patt = patternCl.__repr__()
    patt.reverse()

    for elem in stack:
        if (elem == '(') or (elem == ')') or (elem == '*') or (elem == '+'):
            newStack.append(elem)
        elif (isinstance(elem,str) and elem.isdigit()):
            # either '0' or '1' marking middle group repetition
            newStack.append(elem)
        elif isinstance(elem,set):
            # process action set
            newStack.append(elem)
            pattEl = patt.pop()
            # check pattern
            assert pattEl == None
        elif isinstance(elem,str):
            # process action
            pattEl = patt.pop()
            (act,args) = pattEl
            assert isinstance(act,str) and isinstance(args,list)
            pattElTup = (act,tuple(args))
            # pattern action and element action must match
            assert act == elem
            newStack.append(pattElTup)

    return newStack

def processDomain(dataRoot,exprList):
    plans = getPlansWithArgs(dataRoot,exprList)
    domainSignature = getDomainSignature(plans)
    # wrapPlans - add void action to the beggining and to the end of each plan
    wrapPlans(plans,(None,None))
    # plans .. list of plans
    # domainSignature .. map of possible actions with their argument count
    # (leftEnd, rightEnd, recursionType, prevSplit) .. information about previous recursive call
    # level = 0 .. recursion level
    (reTree,pattern) = makeRE(plans,domainSignature,(True,True,0,None),0)

    # DEBUG printout
    print('=== Tree walk ===')
    reTree.walkTree(0)
    print('=== Pattern ( length = {}, noneCnt = {}) ==='.format(len(pattern.__repr__()),pattern.__repr__().count(None)))
    print(pattern)
    print('=== labelActions ===')
    reTree.labelActions()
    print('=== tree stack ===')
    reStack = reTree.__repr__()
    print(reStack)
    print('=== stack with arguments ===')
    combinedStack = integratePattern2Stack(reStack,pattern)
    print(combinedStack)
    return combinedStack
