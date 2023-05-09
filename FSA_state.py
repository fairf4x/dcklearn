from ordered_set import OrderedSet

class FSAState(object):
    '''State of FSA has its typed arguments.'''

    def __init__(self,stateID,fsa):
        # stateID
        self._ID = stateID
        # FSA
        self._fsa = fsa
        # list of arguments
        self._args = []
        # dict of argument types {pos: type}
        self._argTypes = {}
        # dict of argument maps (pos: {'action1': argPos1,'action2': argPos2})
        self._argMaps = {}
    
    def updateArgData(self,typeMap=None,positionMap=None):
        # collect all relevant argument names from incoming and outgoing transitions
        if self._fsa.lastState(self._ID):
            args = self._fsa.getEdgeArguments(self._ID,True)
        else:
            inSet = self._fsa.getEdgeArguments(self._ID,True)
            outSet = self._fsa.getEdgeArguments(self._ID,False)
            args = OrderedSet.intersection(inSet,outSet)
        
        self._args = list(args)
        
        # collect argument types if data available
        if typeMap != None:
            for (pos,arg) in enumerate(self._args):
                # for each argument name its type should be defined in typeMap
                assert arg in typeMap
                self._argTypes[pos] = typeMap[arg]
        
        # record information about positions of arguments in actions if data available
        # This information is used to determine arguments for loop actions
                if positionMap != None:
                    if arg in positionMap:
                        self._argMaps[pos] = positionMap[arg]


    @property
    def args(self):
        return self._args

    @args.setter
    def args(self,value):
        self._args = value

    @property
    def typedArgs(self):
        '''Return list of pairs (argName,argType)'''
        res = []
        for (i,a) in enumerate(self._args):
            if i in self._argTypes:
                res.append((a,self._argTypes[i]))

        return res

    def positionMap(self,argPos):
        '''Return map of positions (e.g. {'act1':0,'act2':3}) for argument on argPos.'''
        if argPos in self._argMaps:
            return self._argMaps[argPos]
        else:
            return None

    def __repr__(self):
        return "args: {}\narg types: {}\naction mapping: {}\n".format(str(self._args),str(self._argTypes),str(self._argMaps))
