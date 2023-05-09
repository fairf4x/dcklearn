from functools import reduce
from graphviz import Digraph
from ordered_set import OrderedSet
import pyddl
import re
from FSA_state import FSAState

def getAlphabet(stack):
    '''Filter only operator names from given list.
       Ignore parenthesis and look into sets.'''
    for item in stack:
        if isinstance(item,tuple):
            if len(item) == 2:
                (name,args) = item
                yield name
        elif isinstance(item,set):
            for elem in item:
                yield elem

def getArgPositions(argName,actInstanceList):
    """Returns list of positions taken by given argument in action instances in the list."""
    res = {}
    for (a,argList) in actInstanceList:
            posList = []
            for (i,arg) in enumerate(argList):
                if arg == argName:
                        posList.append(i)
            if len(posList) > 0:
                res[a] = posList

    return res

class FSA(object):
    ''' Finite State Automaton: A = (States, Alphabet, Init, Goals, Transitions)'''
    LAMBDA_PREF='_'

    def __init__(self):
        '''initialize empty automaton with initial state, given alphabet and no goal or transitions'''
        # list of integers
        self._states = []
        # dict of state data {stateID:FSAState}
        self._state_data = {}
        # set of strings
        self._alphabet = set()
        self._init = None
        self._goals = []
        self._transitions = [] # list of tuples (origState,action,destState)
                               # orig/destState .. int, action .. (aName,argList)

    @staticmethod
    def initFromStack(stack):
        '''Initialize FSA from stack of symbols:
           1) action with arguments - tuple ('actionName',['arg1','arg2',...,'argN'])
              lambda action names should begin with prefix '_'
           2) action set - set of strings
           3) parenthesis - either '(' or ')'
           4) repetition symbol - '*','+' or '[:number:]' '''

        # set of all actions mentioned in the stack (sets expanded)
        alphabet = set(getAlphabet(stack))

        A = FSA()

        status = {}
        status['FSA'] = A            # constructed FSA
        status['lastState'] = None      # last added state
        status['stateStack'] = []    # stack of states at the beginning of parenthesis group
        status['prevSymbol'] = None  # previous symbol from the stack
        status['foundingActionMap'] = {} # for each state remember

        # main loop through the stack
        for sym in stack:
            if isinstance(sym,str):
                # handle parenthesis and repetition symbols
                FSA.handleString(sym,stack,status)
                continue
            elif isinstance(sym,tuple):
                # handle action with arguments
                FSA.handleAction(sym,stack,status)
                continue
            elif isinstance(sym,set):
                # handle action set
                FSA.handleSet(sym,stack,status)

        # State arguments can be initialized before merging into the domain
        # as well as lambda transition arguments

        # state arguments are computed from resulting FSA structure
        # they are not needed when building the structure
        # status['FSA'].updateStateArgs()

        # status['FSA'].initializeLambdaTransArgs()

        return status['FSA']

    @staticmethod
    def handleString(sym,stack,status):
        if sym == '(':
            # handle opening bracket
            status['stateStack'].append(status['lastState'])
            status['prevSymbol'] = sym
        elif sym == ')':
            # handle closing bracket
            status['prevSymbol'] = sym
        elif sym == '*':
            FSA.repeatGroup(status,True)
            status['prevSymbol'] = sym
        elif sym == '+':
            FSA.repeatGroup(status,False)
            status['prevSymbol'] = sym
        elif sym.isdigit():
            if sym == '0':
                # no middle section - nothing to repeat
                status['prevSymbol'] = sym
            elif sym == '1':
                # middle section is present once in all plans
                FSA.copyGroup(status)
                status['prevSymbol'] = sym
        else:
            # symbol not recognized - ERROR
            assert(True)
    @staticmethod
    def copyGroup(status):
        '''
            Copy group of tokens between parenthesis or one token before repetition symbol 1.
        '''
        # repeat group of tokens
        maxState = -1 # initialize maxState variable with harmless value
        if status['prevSymbol'] != ')':
            # there was no parenthesis group (e.g.: "action 1") - copy one last action and state
            # collect all transitions that enter to or leave from last state and copy them
            copyTransList = []
            for (orig,act,dest) in status['FSA'].filterTransitions(status['lastState'],True):
                trans = (dest,act,dest+1)
                copyTransList.append(trans)
            # collect all transitions that leave last state and copy them as well
            for (orig,act,dest) in status['FSA'].filterTransitions(status['lastState'],False):
                (aname,argList) = act
                if aname.startswith(FSA.LAMBDA_PREF):
                    actRenamed = ("{}-{}-{}".format(FSA.LAMBDA_PREF,orig+1,orig))
                    newLambdaAct = (actRenamed,argList)
                    trans = (orig+1,newLambdaAct,orig)
                else:
                    trans = (orig+1,act,orig)
                copyTransList.append(trans)

            # add all collected transitions

            # collect state IDs
            stateSet = set()
            for trans in copyTransList:
                status['FSA'].addTransition(trans)
                (orig,act,dest) = trans
                stateSet.add(orig)
                stateSet.add(dest)

            # determine highest stateID
            maxState = max(stateSet)
        else:
            # this is the end of parenthesis group (e.g. "({load,unload}.drive) 1") - copy part of automaton
            highState = status['lastState']
            lowState = status['stateStack'].pop()
            copyTransList = status['FSA'].getTransitionSet(status,lowState,highState)
            # move all transitions in such a manner that the group starts in highState
            diff = highState - lowState
            assert diff > 0
            stateSet = set()
            for trans in copyTransList:
                (orig,act,dest) = trans
                stateSet.add(orig)
                stateSet.add(dest)
                # move start/end point of the transition by diff
                trans[0] = trans[0]+diff
                trans[2] = trans[2]+diff

            maxState = max(stateSet)

        # update lastState to keep track of used state IDs
        if maxState > status['lastState']:
            status['lastState'] = maxState

    @staticmethod
    def getTransitionSet(status,lowState,highState):
        # TODO: test
        '''Return list of all transitions in an automaton fragment between lowState and highState'''
        def processNode(state,whiteSet,fsaHandle):
            res = []
            whiteSet.remove(state)
            for (orig,act,dest) in fsaHandle.filterTransitions(state,False):
                if dest in whiteSet:
                    res.append([orig,act,dest])
                    neighList = processNode(dest,whiteSet,fsaHandle)
                    if neighList != None:
                        res = res + neighList
            return res

        whiteSet = set(range(lowState,highState+1))
        transList = []
        for s in range(lowState,highState+1):
            if s in whiteSet:
                actList = processNode(s,whiteSet,status['FSA'])
                if actList != None:
                    transList = transList + actList

        return transList

    @staticmethod
    def repeatGroup(status,skip = True):
        '''Repeat group of tokens between parenthesis or one token before repetition symbol + or *
           skip ... True/False is flag whether the group can be omited completely or has to be present at least once
        '''
        # repeat group of tokens
        if status['prevSymbol'] != ')':
            # there was no parenthesis group (e.g.: "action+") - return to the state before the lastState
            returnState = status['lastState'] - 1
        else:
            # this is the end of parenthesis group (e.g. "({load,unload}.drive)+")- return to the state before the start of the group
            returnState = status['stateStack'].pop()

        lastState = status['lastState']
        lambdaName = "{}l-{}-{}".format(FSA.LAMBDA_PREF,lastState,returnState)
        # arguments of lambda function has to be filled in after the FSA is complete
        trans = (lastState,(lambdaName,[]),returnState)
        status['FSA'].addTransition(trans)

        # skip the group of tokens if the group is not the first expression in the stack
        if skip and (returnState > 0):
            (orig,skipAction) = status['FSA'].getEnteringAction(returnState)
            trans = (orig,skipAction,lastState)
            status['FSA'].addTransition(trans)

    @staticmethod
    def handleAction(sym,stack,status):
        # add new transition
        if status['lastState'] == None:
            originState = 0 # initialize state counter
        else:
            originState = status['lastState']
        destState = originState + 1
        trans = (originState,sym,destState)
        status['lastState'] = destState
        status['FSA'].addTransition(trans)

    @staticmethod
    def handleSet(sym,stack,status):
        for elem in sym:
            if status['lastState'] == None:
                originState = 0 # initialize state counter
            else:
                originState = status['lastState']
            destState = originState
            trans = (originState,(elem,None),destState)
            status['lastState'] = destState
            status['FSA'].addTransition(trans)

    @property
    def alphabet(self):
        return self._alphabet

    @property
    def states(self):
        return self._states

    @property
    def init(self):
        return self._init

    @property
    def goals(self):
        return self._goals

    @property
    def transitions(self):
        return self._transitions

    def filterTransitions(self,baseState,incoming):
        for (orig,act,dest) in self._transitions:
            if incoming:
                # only transitions with actions represented as ('actionName',[arg1,..,argN])
                if dest == baseState and isinstance(act,tuple):
                    yield (orig,act,dest)
            else:
                if orig == baseState and isinstance(act,tuple):
                    yield (orig,act,dest)

    def selectTransitions(self,patt):
        '''Generate transitions such that the action name matches regexp compiled from patt'''
        regExp = re.compile(patt)
        for T in self._transitions:
            (orig,act,dest) = T
            if isinstance(act,tuple) and (len(act) == 2):
                (aName,args) = act
                if regExp.match(aName):
                    yield T

    def lastState(self,stateID):
        '''Decide if stateID is the last state of the FSA'''
        return (self._states[-1] == stateID)

    def collectStateData(self,domain):
        # walk through all FSA edges and record types for all arguments
        # (argName,typeSet)
        argTypeMap = {}
        argPosMap = {}
        for (orig,trans,dest) in self._transitions:
          
            # collect all argument types, filter the most general ones for later use
            (aName,argList) = trans
            # skip lambda actions - they are not in the original domain
            if aName.startswith(FSA.LAMBDA_PREF):
                continue

            # skip loops (TODO: maybe we want to initialize their arguments instead?)
            if orig == dest:
                continue

            domainAct = domain.getAction(aName)
            domainArgList = domainAct.parameters
            assert len(argList) == len(domainArgList)
            for (i,arg) in enumerate(argList):
                # skip unnamed arguments (TODO: maybe we want to process them instead?)
                if arg == '?':
                    continue
                # extend type list if the arg is already there
                if arg in argTypeMap:
                    foundTypeSet = set(argTypeMap[arg])
                    domainTypeSet = set(domainArgList[i][1])
                    foundTypeSet.update(domainTypeSet)
                    argTypeMap[arg] = list(foundTypeSet)
                else:
                    argTypeMap[arg] = domainArgList[i][1]
                
                # update position map
                if arg in argPosMap:
                    if aName in argPosMap[arg]:
                        # if this fails there is one argument used twice among aName parameters
                        assert i == argPosMap[arg][aName]
                    else:
                        argPosMap[arg][aName] = i
                else:
                    argPosMap[arg] = dict([(aName,i)])

        # select most general type of all collected types for each argument
        for arg in argTypeMap:
            origList = argTypeMap[arg]
            general = reduce(domain.moreGeneral,origList)
            assert general != None # this happens when there are two uncomparable types in origList (i.e. moreGeneral returns None)
            argTypeMap[arg] = general
        
        # DEBUG:
        # print(argTypeMap) # initialized
        # print(argPosMap) # initialized

        # fill in state details for each state
        for sID in self._states:
            assert sID in self._state_data
            state = self._state_data[sID]
            state.updateArgData(argTypeMap,argPosMap)
        # now each state should have complete information about itself:
        # ID,argumentList,argumentTypeList
        # e.g.: 3,['?x1','?x4','?x6'],['hand','container','level']

    def updateStateArgs(self,domain=None):
        '''Reinitialize arguments for each FSA state.'''
        self._states.sort()

        for s in self._states[:-1]:
            inSet = self.getEdgeArguments(s,True)
            outSet = self.getEdgeArguments(s,False)
            args = OrderedSet.intersection(inSet,outSet)
            self.setStateArgs(s,args)

        # last state does not have outgoing edges (except for possible lambdas)
        # its arguments are set using incoming arguments only
        lastState = self._states[-1]
        inSet = self.getEdgeArguments(lastState,True)
        self.setStateArgs(lastState,inSet)

        # if the domain is given we can read argument types
        if domain != None:
            # get most general type for each named argument (FSA state arguments) used in transitions of FSA
            # and map of positions of state arguments in actions
            self.collectStateData(domain)

    def initializeLambdaTransArgs(self):
        # iterate over all lambda transitions
        for LT in self.selectTransitions('^{}.*'.format(self.LAMBDA_PREF)):
            (orig,act,dest) = LT
            (aName,args) = act
            origArgs = self.getStateArgs(orig)
            args.extend(origArgs)

    def getEnteringAction(self,state):
        '''Return pair (origin,action) where:
           action .. action entering given state from the lowest predecessing state
           origin .. origin of the transition from the lowest predecessor
           We suppose that the initial FSA state is always 0 and the states are
           labeled with increasing numbers.'''
        # first state does not have any entering action
        assert state != 0
        enteringAction = None
        actMin = None
        for (orig,act,dest) in self.filterTransitions(state,True):
            if orig == dest:
                # skip loops
                continue
            if enteringAction == None:
                # first run - initialize
                actMin = orig
                enteringAction = act
            else:
                if orig < actMin:
                    # update result
                    actMin = orig
                    enteringAction = act

        # some action should be selected
        assert enteringAction != None
        return (actMin,enteringAction)

    def getEdgeArguments(self,baseState,incoming):
        '''Return union of all arguments from all actions incoming/leaving to/from baseState.
           incoming=True -> incoming only, incoming=False -> leaving only'''
        setList = []
        for (orig,action,dest) in self.filterTransitions(baseState,incoming):
            (aName,argList) = action
            # lambda actions should begin with prefix '_' - we do not consider them here
            # loop actions does not have argList
            if (aName[0] != FSA.LAMBDA_PREF) and (argList != None):
                # we need to preserve argument order
                setList.append(OrderedSet(argList))

        if len(setList) == 0:
            return set()
        else:
            res = reduce(OrderedSet.union,setList)
            res.discard('?')
            return res

    def getEdgeActions(self,baseState,incoming,includeLoops=False):
        '''Return list of actions from all transitions incoming/leaving to/from baseStateself.
           incoming=True -> incoming only, incoming=False -> leaving only'''
        actionList = []
        for (orig,action,dest) in self.filterTransitions(baseState,incoming):
            (aName,argList) = action
            if (aName[0] != FSA.LAMBDA_PREF):
                if includeLoops:
                    actionList.append(action)
                else:
                    if argList != None:
                        actionList.append(action)

        return actionList

    def getStateArgs(self,state):
        '''Return argument variable names for given state number.
           state is integer refering to one of FSA states
           Returns: list of strings'''
        if state in self._state_data:
            return self._state_data[state].args
        else:
            return None

    def setStateArgs(self,state,argList):
        '''args should be represented as a list of strings
           state should be integer refering to one of FSA states
           This method will overwrite existing arguments'''
        assert state in self._state_data
        self._state_data[state].args = argList

    def addTransition(self,T):
        '''T = (orig,symbol,dest) where orig should be existing state,
        symbol should be present in alphabet and dest is the transition target state
        which may or may not be present'''

        (orig,sym,dest) = T
        assert (orig != None) and (dest != None)
        (action,args) = sym

        # extend alphabet if needed (lambda actions)
        if action not in set(self._alphabet):
            self._alphabet.add(action)

        if not (dest in self._states):
            self._states.append(dest)
            self._state_data[dest] = FSAState(dest,self)

        if not (orig in self._states):
            self._states.append(orig)
            self._state_data[orig] = FSAState(orig,self)

        if not (T in self._transitions):
            self._transitions.append(T)

    def markGoal(self,goalStateID):
        '''Mark goalStateID as goal state in the automaton.'''
        assert goalStateID in self._states

        self._goals.append(goalStateID)

    def buildGraph(self):
        sPref = 's'

        f = Digraph('FSA')

        # nodes
        f.attr('node', shape='circle')
        labelMap = {}
        for s in self._states:
            args = self._state_data[s].args
            if len(args) == 0:
                nodeLabel = '({}{})'.format(sPref,s)
            else:
                argStr =  ' '.join(str(a) for a in args)
                nodeLabel = '({}{} {})'.format(sPref,s,argStr)

            labelMap[s] = nodeLabel
            f.node(nodeLabel)

        # edges
        for (orig,act,dest) in self._transitions:
            origLabel = labelMap[orig]
            destLabel = labelMap[dest]
            (aName,args) = act
            if (args == None) or (len(args) == 0):
                edgeLabel = '({} -)'.format(aName)
            else:
                argStr = ' '.join(str(a) for a in args)
                edgeLabel = '({} {})'.format(aName,argStr)

            f.edge(origLabel,destLabel,edgeLabel)

        return f

    def render(self,diagramFile,diagramFormat):
        g = self.buildGraph()

        g.render(filename=diagramFile,format=diagramFormat,formatter='cairo',renderer='cairo',cleanup=True)

    def saveDiagram(self,filename):
        '''Save diagram source'''
        g = self.buildGraph()

        g.save(filename)

    @staticmethod
    def renameArguments(pddlAction,fsaAction):
        '''Change variable names in pddl action to match fsa action arguments.'''

        # vytvorit mapovani parametru akci z domeny na promenne
        mapping = {}
        (aName,argList) = fsaAction
        if argList == None:
            # no arguments in this FSA action
            return

        paramList = pddlAction.parameters
        assert len(paramList) == len(argList)
        pairs = [(param,arg) for ((param,types),arg) in zip(paramList,argList)]

        # debugging
        #print('Rename args in {}'.format(aName))
        #print(pairs)

        # rename domain action variables
        for (param,arg) in pairs:
            if arg != '?':
                pddlAction.renameArg(param,arg)
   
    def copyRequirements(self,domain,newDomain):
        newDomain.requirements = domain.requirements

    def copyTypeDefinitions(self,domain,newDomain):
        newDomain.addTypeList(domain.getTypeList())
   
    def addPredicates(self,domain,newDomain):
        '''Extend domain with added predicates (representing FSA states) in order to create newDomain.'''
        # state predicates
        for s in self._states:
            pName = "s{}".format(s)
            # DEBUG
            print(pName)
            print(self._state_data[s].typedArgs)
            print("ENTER")
            enterAct = self.filterTransitions(s,True)
            for (orig,act,dest) in enterAct:
                actionName = act[0]
                if orig != dest and actionName[0] != FSA.LAMBDA_PREF:
                    print(actionName)
                    pddlAct = domain.getAction(act[0])
                    print(pddlAct.precond)
                    print(pddlAct.effects)
            print("LEAVE")
            leaveAct = self.filterTransitions(s,False)
            for (orig,act,dest) in leaveAct:
                actionName = act[0]
                if orig != dest and actionName[0] != FSA.LAMBDA_PREF:
                    print(actionName)
                    pddlAct = domain.getAction(act[0])
                    print(pddlAct.precond)
                    print(pddlAct.effects)
            # GUDEB
            newPredicate = pyddl.pddlPredicateDef(pName)

            argsTyped = self._state_data[s].typedArgs

            for (arg,argT) in argsTyped:
                newPredicate.addParam(tuple([arg,[argT]]))

            newDomain.addPredicate(newPredicate)
        # copy original predicates
        # these are not real copies - assuming we do not need to use new objects here
        for p in domain.getPredicateList():
            newDomain.addPredicate(p)
    
    def initLoopArguments(self,actName,actArity,stateID):
        '''Initialize arguments for loop action pddlAction with origin in stateID.'''
        newArgList = ['?']*actArity
        for (pos,argName) in enumerate(self._state_data[stateID].args):
            # find position pos of argName
            argMap = self._state_data[stateID].positionMap(pos)
            if argMap != None:
                if actName in argMap:
                    newArgList[argMap[actName]] = argName
                else:
                    # TODO: determine argument name from context (i.e. previous state and next state) 
                    pass
            else:
                pass

        return newArgList

    def addActions(self,domain,newDomain):
        # process each FSA edge into new action
        for T in self._transitions:
            (orig,act,dest) = T
            (aName,argList) = act

            if aName[0] == FSA.LAMBDA_PREF:
                # lambda actions are already named with orig-dest suffix
                tActionName = "{}".format(aName)
            else:
                tActionName = "{}-{}-{}".format(aName,orig,dest)

            # find matching action in the original domain
            pddlA = domain.getAction(aName)
            if pddlA != None:
                cloneA = pyddl.pddlAction(tActionName,pddlA)
                # rename arguments in pddl action clone to match FSA action arguments
                # and state arguments

                # modify argList to include state predicate parameters
                # in case of loop actions
                if orig == dest:
                    # initialize newArgList
                    arity = len(pddlA.parameters)
                    newArgList = self.initLoopArguments(aName,arity,orig)

                    FSA.renameArguments(cloneA,(aName,newArgList))
                else:
                    FSA.renameArguments(cloneA,act)
            else:
                # in case of lambda action we just need empty action
                cloneA = pyddl.pddlAction(tActionName)

            origState = 's{}'.format(orig)
            origStateArgs = self._state_data[orig].args
            destState = 's{}'.format(dest)
            destStateArgs = self._state_data[dest].args

            precondTerm = pyddl.pddlAtomicTerm(origState,origStateArgs)

            if orig != dest:
                effectTerm = pyddl.pddlAtomicTerm(destState,destStateArgs)
                cancelTerm = pyddl.pddlNegativeTerm(origState,origStateArgs)
                # originState holding
                cloneA.extendPrecond(precondTerm)
                # originState canceled and destState holding
                cloneA.extendEffect(effectTerm)
                cloneA.extendEffect(cancelTerm)
            else:
                # originState holding
                cloneA.extendPrecond(precondTerm)

            if aName[0] == FSA.LAMBDA_PREF:
                # lambda action typed parameter list collection
                allTermList = [precondTerm,effectTerm,cancelTerm]
                allTermSet = set(allTermList)
                argNameSet = set()
                for t in allTermSet:
                    stateID = int((t.predicateName)[1:])
                    argsTyped = self._state_data[stateID].typedArgs
                    for (argName,argType) in argsTyped:
                        if not(argName in argNameSet):
                            argNameSet.add(argName)
                            cloneA.addParam((argName,[argType]))

            newDomain.addAction(cloneA)

    def merge2PDDLdomain(self,pddlDomain,domainName):
        domain = pyddl.readDomain(pddlDomain)

        # update FSA state argument information (based on resulting FSA structure)
        # self.updateStateArgs(domain)

        # create new domain to integrate changes
        newDomain = pyddl.pddlDomain()

        newDomain.docName = domainName

        # copy unchanged stuff
        self.copyRequirements(domain,newDomain)

        self.copyTypeDefinitions(domain,newDomain)

        # add state predicates and modified actions from FSA
        self.addPredicates(domain,newDomain)

        self.addActions(domain,newDomain)

        return str(newDomain)

    def __repr__(self):
        '''Print textual representation of given FSA in dot format.
        '''
        g = self.buildGraph()

        return g.source
