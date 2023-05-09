from itertools import chain

class PlanRETree(object):

    index = 0

    def __init__(self,splitAction,level,middleRep):
        self._action = splitAction
        self._level = level
        self._middleRep = middleRep
        self._head = None
        self._middle = None
        self._tail = None
        # array for indices of split action in resulting regexp
        self._indices = []

    def head():
        doc = "The head of plan before spliting action."
        def fget(self):
            return self._head
        def fset(self, value):
            self._head = value
        def fdel(self):
            del self._head
        return locals()
    head = property(**head())

    def middle():
        doc = "The middle part of plan between two spliting actions."
        def fget(self):
            return self._middle
        def fset(self, value):
            self._middle = value
        def fdel(self):
            del self._middle
        return locals()
    middle = property(**middle())

    def tail():
        doc = "The tail part of the plan after last spliting action."
        def fget(self):
            return self._tail
        def fset(self, value):
            self._tail = value
        def fdel(self):
            del self._tail
        return locals()
    tail = property(**tail())

    def allSuccSet(self):
        if isinstance(self._head,set) and isinstance(self._middle,set) and isinstance(self._tail,set):
           return True
        else:
           return False

    def allSuccEmptySet(self):
        if self.allSuccSet():
            if len(self._head) == 0 and len(self._middle) == 0 and len(self._head) == 0:
                return True
            else:
                return False
        else:
            return False

    def walkTree(self,indent):
        prefix = " "*indent
        # terminate recursion
        if self.allSuccEmptySet():
            print("{}{}.".format(prefix,self._action))
            return

        # ---- HEAD ----
        if isinstance(self._head,set):
            if len(self._head) > 0:
                print("{}{}".format(prefix,self._head))
            #else:
            #    print("{}<empty HEAD set>".format(prefix))
        elif isinstance(self._head,PlanRETree):
            self._head.walkTree(indent+1)

        # ---- MIDDLE ----
        if isinstance(self._middle,set):
            if len(self._middle) > 0:
                # print split action twice

                print("{}{}".format(prefix,self._action))
                print("{}({}".format(prefix,self._middle))
                print("{}{}){}".format(prefix,self._action,self._middleRep))
            else:
                # print split action only once
                print("{}{}".format(prefix,self._action))
        elif isinstance(self._middle,PlanRETree):
            # print split action twice
            print("{}{}".format(prefix,self._action))
            self._middle.walkTree(indent+1)
            print("{}{}".format(prefix,self._action))

        # ---- TAIL ----
        if isinstance(self._tail,set):
            if len(self._tail) > 0:
                print("{}{}".format(prefix,self._tail))
            #else:
            #    print("{}<empty TAIL set>".format(prefix))
        elif isinstance(self._tail,PlanRETree):
            self._tail.walkTree(indent+1)

    def labelActions(self):
        # terminate recursion
        if self.allSuccSet():
            print("{} : {}".format(self._action,PlanRETree.index))
            PlanRETree.index = PlanRETree.index + 1
            return

        # ---- HEAD ----
        if isinstance(self._head,PlanRETree):
            self._head.labelActions()

        print("{} : {}".format(self._action,PlanRETree.index))
        PlanRETree.index = PlanRETree.index + 1

        # ---- MIDDLE ----
        if isinstance(self._middle,PlanRETree):
            self._middle.labelActions()
            print("{} : {}".format(self._action,PlanRETree.index))
            PlanRETree.index = PlanRETree.index + 1
        elif isinstance(self._middle,set):
            if len(self._middle) > 0:
                print("{} : {}".format(self._action,PlanRETree.index))
                PlanRETree.index = PlanRETree.index + 1

        # ---- TAIL ----
        if isinstance(self._tail,PlanRETree):
            self._tail.labelActions()

    def __str__(self):
        return str(self.__repr__())

    def __repr__(self):
        res = []
        # all blocks are trivial
        if self.allSuccSet():
            if self.allSuccEmptySet():
                res = chain([self._action], [self._middleRep])
            if len(self._head) > 0 and len(self._middle) == 0 and len(self._tail) == 0:
                res = chain([self._head],
                      [self._action], [self._middleRep])
            if len(self._head) == 0 and len(self._middle) > 0 and len(self._tail) == 0:
                res = chain([self._action],
                      ['('], [self._middle],
                      [self._action], [')'], [self._middleRep])
            if len(self._head) == 0 and len(self._middle) == 0 and len(self._tail) > 0:
                res = chain([self._action], [self._middleRep],
                      [self._tail])
            if len(self._head) == 0 and len(self._middle) > 0 and len(self._tail) > 0:
                res = chain([self._action],
                      ['('], [self._middle],
                      [self._action], [')'], [self._middleRep],
                      [self._tail])
            if len(self._head) > 0 and len(self._middle) == 0 and len(self._tail) > 0:
                res = chain([self._head],
                      [self._action], [self._middleRep],
                      [self._tail])
            if len(self._head) > 0 and len(self._middle) > 0 and len(self._tail) == 0:
                res = chain([self._head],
                      [self._action],
                      ['('], [self._middle],
                      [self._action], [')'], [self._middleRep])
            if len(self._head) > 0 and len(self._middle) > 0 and len(self._tail) > 0:
                res = chain([self._head],
                      [self._action],
                      ['('], [self._middle],
                      [self._action], [')'], [self._middleRep],
                      [self._tail])
            return list(res)

        # all blocks are nontrivial
        if isinstance(self._head,PlanRETree) and isinstance(self._middle,PlanRETree) and isinstance(self._tail,PlanRETree):
            headStack = self._head.__repr__()
            middleStack = self._middle.__repr__()
            tailStack = self._tail.__repr__()
            res = chain(headStack,
                                  [self._action],
                                  ['('],middleStack,
                                  [self._action],[')'],[self._middleRep],
                                  tailStack)
            return list(res)

        # head block is trivial
        elif isinstance(self._head,set) and isinstance(self._middle,PlanRETree) and isinstance(self._tail,PlanRETree):
            middleStack = self._middle.__repr__()
            tailStack = self._tail.__repr__()

            if len(self._head) == 0:
                res = chain([self._action],
                                      ['('],middleStack,
                                      [self._action],[')'],[self._middleRep],
                                      tailStack)
            else:
                res = chain([self._head],
                      [self._action],
                      ['('], middleStack,
                      [self._action], [')'], [self._middleRep],
                      tailStack)
            return list(res)

        # tail block is trivial
        elif isinstance(self._head,PlanRETree) and isinstance(self._middle,PlanRETree) and isinstance(self._tail,set):
            headStack = self._head.__repr__()
            middleStack = self._middle.__repr__()
            if len(self._tail) == 0:
                res = chain(headStack,
                      [self._action],
                      ['('], middleStack,
                      [self._action], [')'], [self._middleRep])
            else:
                res = chain(headStack,
                      [self._action],
                      ['('], middleStack,
                      [self._action], [')'], [self._middleRep],
                      [self._tail])
            return list(res)

        # middle block is trivial
        elif isinstance(self._head,PlanRETree) and isinstance(self._middle,set) and isinstance(self._tail,PlanRETree):
            headStack = self._head.__repr__()
            tailStack = self._tail.__repr__()
            if len(self._middle) == 0:
                    res = chain(headStack,
                          [self._action], [self._middleRep],
                          tailStack)
            else:
                res = chain(headStack,
                      [self._action],
                      ['('], [self._middle],
                      [self._action], [')'], [self._middleRep],
                      tailStack)
            return list(res)

        # head is nontrivial
        elif isinstance(self._head,PlanRETree) and isinstance(self._middle,set) and isinstance(self._tail,set):
            headStack = self._head.__repr__()
            # both middle and tail are empty sets
            if len(self._middle) == 0 and len(self._tail) == 0:
                res = chain(headStack,
                      [self._action], [self._middleRep])
            elif len(self._middle) == 0 and len(self._tail) > 0:
                res = chain(headStack,
                      [self._action], [self._middleRep],
                      [self._tail])
            elif len(self._middle) > 0 and len(self._tail) == 0:
                res = chain(headStack,
                      [self._action],
                      ['('], [self._middle],
                      [self._action], [')'], [self._middleRep])
            elif len(self._middle) > 0 and len(self._tail) > 0:
                res = chain(headStack,
                      [self._action],
                      ['('], [self._middle],
                      [self._action], [')'], [self._middleRep],
                      [self._tail])
            return list(res)

        # tail is nontrivial
        elif isinstance(self._head,set) and isinstance(self._middle,set) and isinstance(self._tail,PlanRETree):
            tailStack = self._tail.__repr__()
            # both head and middle are empty sets
            if len(self._head) == 0 and len(self._middle) == 0:
                res = chain([self._action], [self._middleRep],
                      tailStack)
            elif len(self._head) == 0 and len(self._middle) > 0:
                res = chain([self._action],
                      ['('], [self._middle],
                      [self._action], [')'], [self._middleRep],
                      tailStack)
            elif len(self._head) > 0 and len(self._middle) == 0:
                res = chain([self._head],
                      [self._action], [self._middleRep],
                      tailStack)
            elif len(self._head) > 0 and len(self._middle) > 0:
                res = chain([self._head],
                      [self._action],
                      ['('], [self._middle],
                      [self._action], [')'], [self._middleRep],
                      tailStack)
            return list(res)

        # middle is nontrivial
        elif isinstance(self._head,set) and isinstance(self._middle,PlanRETree) and isinstance(self._tail,set):
            middleStack = self._middle.__repr__()
            # both head and tail are empty sets
            if len(self._head) == 0 and len(self._tail) == 0:
                res = chain([self._action],
                      ['('], middleStack,
                      [self._action], [')'], [self._middleRep])
            elif len(self._head) == 0 and len(self._tail) > 0:
                res = chain([self._action],
                      ['('], middleStack,
                      [self._action], [')'], [self._middleRep],
                      [self._tail])
            elif len(self._head) > 0 and len(self._tail) == 0:
                res = chain([self._head],
                      [self._action],
                      ['('], middleStack,
                      [self._action], [')'], [self._middleRep])
            elif len(self._head) > 0 and len(self._tail) > 0:
                res = chain([self._head],
                      [self._action],
                      ['('], middleStack,
                      [self._action], [')'], [self._middleRep],
                      [self._tail])
            return list(res)
