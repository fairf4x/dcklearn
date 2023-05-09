from itertools import zip_longest
from collections import defaultdict

def partition(elements, equiv):
    '''Find sets of elements that are equivalent according to equiv function.'''
    partitions = [] # Found partitions
    for e in elements: # Loop over each element
        found = False # Note it is not yet part of a know partition
        for p in partitions:
            if equiv(e, p[0]): # Found a partition for it!
                p.append(e)
                found = True
                break
        if not found: # Make a new partition for it.
            partitions.append([e])
    return partitions

def adjacencyList(setList):
    '''Make adjacency list from list of setList.
       This way we can describe graph using setList.
       setList = [S1,S2,S3,...]
       returns {x1:{set of x1's neighbours, x2: {set of x2's neighbours},...}

       x1,...,xN are elements found in some set S1,S2,..
       neighbours of x are all elements y such that (x in S and y in S) for some S?
    '''
    adjList = defaultdict(set)

    for S in setList:
        for x in S:
            for y in [e for e in S if e != x]:
                adjList[x].add(y)

    return adjList

def bfs(start,adjList):
    '''BFS graph represented by adjList from start and return set of reachable vertices.'''
    visited = []
    toVisit = [start]
    while len(toVisit) > 0:
        v = toVisit.pop()
        if not v in visited:
            visited.append(v)
        for n in adjList[v]:
            if not (n in visited):
                toVisit.insert(0,n)
    visited.sort()
    return visited

def getComponents(inList):
    '''inList = [Set1,Set2,...]
       Form components from elements found in union of all Sets.
       Two elements x,y are members of same component iff
       exists SetX such that x in SetX and y in SetX.
    '''
    # set of all elements
    elemSet = set([x for S in inList for x in S])

    # graph representation of inList
    adjList = adjacencyList(inList)

    componentSet = set()

    for e in elemSet:
        eClass = tuple(bfs(e,adjList))
        componentSet.add(eClass)

    return [set(c) for c in componentSet]

def getActionIndexList(action,plan):
    '''Get list of action occurence indices. Empty list means no such action is present in the plan.'''
    aoList = []
    for (i,(a,args)) in enumerate(plan):
        if a == action:
            aoList.append(i)

    return aoList

def compressPlan(plan,trace):
    '''Compress plan - first and last action will remain but all actions from actionSet
       will became one placeholder action
    '''
    # possibilities
    # 1) <leftEnd>,action *,<rightEnd>    (True,True)
    # 2) <leftEnd>,action *,splitAction   (True,False)
    # 3) splitAction,action *,<rightEnd>  (False,True)
    # 4) splitAction,action *,splitAction (False,False)

    (leftEdge,rightEdge,recursionType,splitAction) = trace

    # first and last action marking edges of the plan are already removed
    # in initializePattern

    # indices of split actions from previous level
    indices = getActionIndexList(splitAction,plan)
    splitAcnt = len(indices)
    planLen = len(plan)

    res = []

    if recursionType < 0:
        # head recursion
        assert splitAcnt == 1
        rightSplitIndex = indices[0]

        if (planLen >= 2) and (leftEdge == False):
            res.append(plan[0])   # pattern binding action
            res.append((None,[])) # placeholder action for action set
            res.append(plan[rightSplitIndex]) # split action
        elif leftEdge == True:
            # no pattern binding action on plan edge
            res.append((None,[])) # placeholder action for action set
            res.append(plan[rightSplitIndex]) # split action

    elif recursionType == 0:
        # middle recursion
        assert splitAcnt == 2
        assert planLen >= 2

        leftSplitIndex = indices[0]
        rightSplitIndex = indices[1]

        res = plan[:leftSplitIndex+1] + [(None,[])] + plan[rightSplitIndex:]

    elif recursionType > 0:
        # tail recursion
        assert splitAcnt == 1
        leftSplitIndex = indices[0]

        if (planLen >= 2) and (rightEdge == False):
            res.append(plan[leftSplitIndex]) # split action
            res.append((None,[])) # placeholder action for action set
            res.append(plan[-1])  # pattern binding action
        elif rightEdge == True:
            assert rightEdge == True
            res.append(plan[leftSplitIndex]) # split action
            res.append((None,[])) # placeholder action for action set
            # no pattern binding action on plan edge

    return res


class Pattern(object):
    '''
    The pattern is defined by action sequence and list of argument positions with unique object.
    List of positions is never shorter then 2 (we are looking for bindings between actions)
    Eg. sample plan:

    ('lift', ('h1', 'c1', 's1', 'p1'))
    ('load', ('h1', 'c1', 't1', 'p1'))

    yields pattern:

    ['lift','load']
    [{(1, 0), (0, 0)}, {(0, 1), (1, 1)}, {(0, 3), (1, 3)}]
    '''
    pSequence = []
    pEqSetList = []
    dSignature = None

    def __init__(self,seq,patt,domainSignature):
        '''Initialize new pattern with given action sequence and list of equivalence sets.'''

        self.pSequence = seq
        self.pEqSetList = patt
        self.dSignature = domainSignature

    @classmethod
    def fromplans(cls,plans,domainSignature):
        '''Initialize new pattern on list of plans with identic action sequences.'''

        (pSequence,pEqSetList) = Pattern.plans2patt(plans)

        return cls(pSequence,pEqSetList,domainSignature)

    @classmethod
    def fromborders(cls,plans,domainSignature,trace):
        '''Initialize empty pattern connecting only attributes of border actions'''

        # compress plans
        # - all actions between first and last action became one empty action
        # - if there is no action between first and last it will become one empty action

        compressedPlans = list(map(lambda p:compressPlan(p,trace),plans))

        #firstLen = len(compressedPlans[0])
        #if firstLen <= 3:
        #    print('Debug here!')

        # invariants ensured here:
        # 1) all plans has equal length 1 or 2
        # 2) first and last actions are same for all plans
        # 3) middle action is always empty action - as a position holder for zero or more actions from actionSet

        (pSequence,pEqSetList) = Pattern.plans2patt(compressedPlans)

        return cls(pSequence,pEqSetList,domainSignature)

    def __repr__(self):
        argMap = self.getVariableMap('?x')

        res = []
        for (i,e) in enumerate(self.pSequence):
            if e in self.dSignature:
                # action name
                args = []
                a = (e,args)
                # action arguments
                for j in range(0,self.dSignature[e]):
                    if (i,j) in argMap:
                        args.append(argMap[(i,j)])
                    else:
                        args.append('?')
                res.append(a)
            else:
                # None
                res.append(None)
        return res

    def __str__(self):
        return str(self.__repr__())

    def __len__(self):
        return len(self.__repr__())

    def getVariableMap(self,varPrefix):
        # make map resolving given position e.g. (0,3) to unique variable name
        argMap = {}
        varNum = 0
        for s in self.pEqSetList:
            for pos in s:
                argMap[pos] = "{}{}".format(varPrefix,varNum)
            varNum = varNum + 1

        return argMap

    @property
    def equivalenceSets(self):
        return self.pEqSetList

    @equivalenceSets.setter
    def equivalenceSets(self,value):
        self.pEqSetList = value

    @property
    def sequence(self):
        return self.pSequence

    @sequence.setter
    def sequence(self,value):
        self.pSequence = value

    # helper functions independent of Pattern object
    @staticmethod
    def plans2patt(plans):
        ''' Process plans into sequence and list of equivalence sets.
            plans .. list of input plans
        '''

        # initialize action sequence and object positions with the first plan
        (actSeq,maskList) = Pattern.getEqClasses(plans[0])

        # sequence of action names
        # initialize action sequence from the first plan
        # - all plans should have identic sequence
        pSequence = actSeq

        # set of masks - one mask is set of positions (actionIndex,argIndex)
        pEqSetList = maskList

        # update object positions with all available plans - if action sequence matches
        for plan in plans[1:]:
            (planSeq,maskList) = Pattern.getEqClasses(plan)

            ## check plan sequence
            # all plans should have identic action sequence
            assert pSequence == planSeq

            ## update pEqSetList - list of equivalence sets  defining the pattern
            # we need to iterate on copy - self.pattern may be changed during iteration (and this leads to item skipping)
            patternCopy = list(pEqSetList)
            for mask in patternCopy:
                # get submasks - equivalence set is mask of positions
                subMaskList = Pattern.getSubsequences(plan,mask)
                subMaskCnt = len(subMaskList)

                if subMaskCnt == 0:
                    # delete sequence of positions (equivalence class) - no matching subsequence longer than 1 found
                    pEqSetList.remove(mask)
                elif subMaskCnt == 1:
                    # only one mask longer than 1 found
                    subMaskLen = len(subMaskList[0])
                    origLen = len(mask)
                    if subMaskLen < origLen:
                        # submask is shorter than original mask - replace original
                        pEqSetList.remove(mask)
                        pEqSetList.append(subMaskList[0])
                    # at this point we know that the mask is exact match - no need for change
                elif subMaskCnt > 1:
                    # more than one submask longer than 1 found
                    # delete original mask
                    pEqSetList.remove(mask)
                    # add all masks longer than 1
                    for m in subMaskList:
                        pEqSetList.append(m)

        # check for patterns over empty middle block - two identic actions
        if (len(pSequence) == 2) and (pSequence[0] == pSequence[1]):
            # get argument position sets
            args0 = {pos for setList in pEqSetList for (i,pos) in setList if i == 0}
            args1 = {pos for setList in pEqSetList for (i,pos) in setList if i == 1}

            commonArgs = args0 & args1

            # delete duplicit action from the sequence
            pSequence.pop(1)
            # replace list of equivalence sets
            pEqSetList = [{(0,pos)} for pos in commonArgs]


        return (pSequence,pEqSetList)

    @staticmethod
    def getObjectPositions(obj,plan):
            '''Get list of positions for given object in given plan.
               eg. obj='p1'
                   plan = [
                ('drive', ('t1', 'p0', 'p1')),
                ('lift', ('h1', 'c1', 's1', 'p1')),
                ('load', ('h1', 'c1', 't1', 'p1')),
                ('drive', ('t1', 'p1', 'p2')),
                ('lift', ('h2', 'c2', 's2', 'p2'))]
                return set of pairs (action index, argument index):

                set((0,2),(1,3),(2,3),(3,1))
            '''
            res = []
            for (i,(a,args)) in enumerate(plan):
                if (a,args) == (None,None):
                    continue
                for (j,arg) in enumerate(args):
                    if arg == obj:
                        res.append((i,j))
            return set(res)

    @staticmethod
    def nonEmpty(plan):
        '''Generate only nonempty actions from given plan.'''
        for (aName,args) in plan:
            if aName != None:
                yield (aName,args)

    @staticmethod
    def getEqClasses(plan):
        # sequence of action names
        actionSequence = [a for (a,_) in plan]
        # get all objects from the plan
        objList = set([o for (x,ol) in Pattern.nonEmpty(plan) for o in ol])

        maskList = []
        for o in objList:
            mask = Pattern.getObjectPositions(o,plan)
            if len(mask) > 1:
                maskList.append(mask)

        return (actionSequence,maskList)

    @staticmethod
    def posEquality(posA,posB,plan):
        '''Compare objects on given positions with respect to given plan.'''
        (actIndexA,argIndexA) = posA
        (actIndexB,argIndexB) = posB
        try:
            return plan[actIndexA][1][argIndexA] == plan[actIndexB][1][argIndexB]
        except IndexError:
            return False


    @staticmethod
    def getSubsequences(plan,posSeq):
        '''plan - define argument matrix
           posSeq - positions in argument matrix to check for subsequences

           return lists of positions with identical objects
        '''
        parts = partition(posSeq,lambda x,y:Pattern.posEquality(x,y,plan))
        return [set(p) for p in parts if len(p) > 1]

    @staticmethod
    def sequenceMatch(patternSeq,planSeq):
        '''Check if plan action sequence matches pattern action sequence.
           Sets are allowed in pattern action sequence.
        '''
        for (pattSeqI,planSeqI) in zip(patternSeq,planSeq):
            assert (isinstance(pattSeqI,set) or isinstance(pattSeqI,str))
            assert isinstance(planSeqI,str)

            # if there is a set of actions in pattern sequence we check membership in this set
            if isinstance(pattSeqI,set):
                if not (planSeqI in pattSeqI):
                    return False
            # else we check equality of action names
            else:
                if planSeqI != pattSeqI:
                    return False

        # nothing went wrong => there is a match
        return True

    @staticmethod
    def reduceMask(maskList,excludeSet):
        '''Remove all positions refering to action on index position from excludeSet.
        This will remove all references to positions of
        all actions with respective indices.
        '''
        res = []
        # inspect all masks
        for origMask in maskList:
            reducedMask = []
            # exclude positions according to excludeSet
            for (actIndex,argIndex) in origMask:
                if not (actIndex in excludeSet):
                    reducedMask.append((actIndex,argIndex))

            if len(reducedMask) > 0:
                res.append(set(reducedMask))

        return res

    @staticmethod
    def shiftMask(posSetList,delta,start=0):
        '''Shift all positions in all sets for delta.
           posSetList = [{(0,1),(1,3),(2,0)},{(0,2),(1,2)}]
           delta = 3
           =>
           [{(3,1),(4,3),(5,0)},{(3,2),(4,2)}]
        '''
        res = []
        for S in posSetList:
            newS = set()
            for (act,arg) in S:
                if act >= start:
                    # shift positions with high index
                    newS.add((act+delta,arg))
                else:
                    # preserve positions with lower indices
                    newS.add((act,arg))
            res.append(newS)

        return res

    @staticmethod
    def connect2(a,b,domainSignature):
        '''Connect 2 patterns.
           a = [A,B,C],[set1,set2,set3,...]
           b = [C,D,E],[set4,set5,set6,...]

           0 1 2 3 4
           A,B,C
               C,D,E

           A,B,C,D,E

           - sets not referencing any argument of C are copied
           - sets referencing common argument of C are merged together
        '''
        if len(a.sequence) == 0:
            return b

        if len(b.sequence) == 0:
            return a

        assert len(a.sequence) > 0
        assert len(b.sequence) > 0

        seqA = a.sequence
        seqB = b.sequence

        delta = len(seqA) - 1

        assert seqA[-1] == seqB[0]

        newSequence = seqA + seqB[1:]

        maskA = a.equivalenceSets
        maskB = b.equivalenceSets

        shiftedMaskB = Pattern.shiftMask(maskB,delta)

        connectedMasks = maskA + shiftedMaskB

        splitActionIndex = delta

        # list of position sets to copy (no attribute from split action referenced)
        copyList = []
        # list of position sets to merge (using attributes from split action)
        mergeList = []
        for S in connectedMasks:
            splitArgFound = False
            for (a,i) in S:
                if a == splitActionIndex:
                    splitArgFound = True
                    mergeList.append(S)
                    break
            if not splitArgFound:
                copyList.append(S)

        mergedList = getComponents(connectedMasks)

        # extend copyList with new elements from mergedList
        for m in mergedList:
            if not m in copyList:
                copyList.append(m)

        return Pattern(newSequence,copyList,domainSignature)

    @staticmethod
    def connectPatterns(pattList,domainSignature):
        '''Connect all patterns in the list into one long pattern.'''
        # Pattern 1
        # orig list: [('lift', ('h1', 'c1', 's1', 'p1')), ('load', ('h1', 'c1', 't1', 'p1'))]
        #
        # ['lift','load']
        # [{(1, 0), (0, 0)}, {(0, 1), (1, 1)}, {(0, 3), (1, 3)}]
        #
        # Pattern 2
        # orig list: [('drive', ('t1', 'p1', 'p2')), ('unload', ('h2', 'c1', 't1', 'p2')), ('drop', ('h2', 'c1', 's2', 'p2'))]
        #
        # ['drive','unload','drop']
        # [{(1, 2), (0, 0)}, {(1, 3), (2, 3), (0, 2)}, {(2, 0), (1, 0)}, {(1, 1), (2, 1)}]
        # TODO: ensure that the pattern contains only the action sequence without arguments
        assert len(pattList) > 0

        # only one pattern - nothing to do
        if len(pattList) == 1:
            return pattList[0]

        # there are at least 2 patterns - recursion
        firstPatt = pattList[0]
        restCombined = Pattern.connectPatterns(pattList[1:],domainSignature)

        return Pattern.connect2(firstPatt,restCombined,domainSignature)
