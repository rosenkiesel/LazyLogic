# A Bool-Signal that can change over time.
# The circuits are SSA (single static assignment)
# values are:
#    True
#    False
#    None (Transient)
#
#
#
# Source does NOT notify if:
#   [X, Y]        -> [X, Y]     (nothing changed) 
#   [X, !push]    -> [X, push]  (pushing gets enabled)
#   [None, !push] -> [X, !push] (value gets known but not pushed)
# Source does notify if:
#   [X, push]     -> [Y, Z]     (pushing gets disabled or value changes)
#   [True/False,Y]-> [X, Y]     (oldvalue invalidated)
#
#
#
# Source --> A --> [B] -- C -- D -- Dest
# "pull":
# Source --> A --> B --> [C] -- D -- Dest
# "push":
# Source --> A --> [B] -- C -- D -- Dest
#
#
#
#
# silence = (oldvalue==None) AND NOT(willPush)
#
#
def lazyBoolToInt(lb):
	if lb is None:
		return 0
	if lb is True:
		return 1
	if lb is False:	
		return -1
	raise("the acceptable values are [True, False, None]")

def intToLazyBool(ii):
	if ii is 0:
		return None
	if ii is 1:
		return True
	if ii is -1:	
		return False
	raise("the acceptable values are [-1,0,+1]")

# Proxy for not-yet defined Signal
class lazyLogicSignal(object):
	def __init__(self):
		self.__dict__["source"] = None
		self.listeners = []
	def __setattr__(self, name, val):
		if name != "source":
			#raise("the only settable attribute is source")
			self.__dict__[name] = val
		else:
			if not(self.source is None):
				raise("source has already been set")			
			self.__dict__[name] = val
			val.addListeners(self.listeners)
			self.listeners = []		
	def __getattr__(self, name):	
		if name != "value":
			#raise("the only settable attribute is source")
			return self.__dict__[name]
		else:
			if self.source is None:
				raise("source has NOT been set")			
			return self.source.value

	def addListener(self, listener):
		self.addListeners([listener])
	def addListeners(self, listeners):
		if self.source is None:
			self.listeners+=listeners
		else:
			self.source.addListeners(listeners)
	def pullValue(self):
		self.source.pullValue()

# Signal from the Outside (a Sensor)
# someone has to set the value
class lazyLogic(object):
	idx=0
	def __init__(self):
		self.listeners = []
		self.__dict__["value"]=None
		self.willPush = False
		self.pulling = False
		self.idx = lazyLogic.idx
		lazyLogic.idx = lazyLogic.idx+1
		print("created Node %d"%self.idx)
	def addListener(self, listener):
		self.listeners.append(listener)
	def addListeners(self, listeners):
		self.listeners += listeners
	def notifyListeners(self):
		print("Node %d notifying Listeners.."%self.idx)
		if self.value is None: # ask if they need an update next time
			needsPush = False
			for ll in self.listeners:
				needsPush = needsPush or ll.notify(self)
			self.willPush = needsPush
		else:
			for ll in self.listeners:
				ll.notify(None)
			self.willPush = True
	def pushIfNeeded(self):
		if self.willPush:
			self.notifyListeners()
	def newValueIs(self,val):
		if not val in [True, False, None]:
			raise("the only settable values are [True, False, None]")
		if not self.value is val:
			oldval = self.__dict__["value"]
			self.__dict__["value"]=val
			self.pushIfNeeded()
	def pullValue(self):
		self.willPush=True
		self.notifyListeners()
		self.willPush=True
	def __setattr__(self, name, val):
		if name != "value":
			#raise("the only settable attribute is value")
			self.__dict__[name] = val
		else:
			self.newValueIs(val)
	def __and__(self,other):
		return lazyLogic_And(self,other)
	def __or__(self,other):
		return lazyLogic_Or(self,other)
	def __invert__(self):
		return lazyLogic_Not(self)

class lazyLogic_And(lazyLogic):
	def __init__(self,a,b):
		print "create AND["
		super(self.__class__,self).__init__()
		self.a = a
		self.b = b
		self.a.addListener(self)
		self.b.addListener(self)
	def pullValue(self):
		if self.value is None and not self.willPush:
			print("pulling for Node %d"%self.idx)
			self.willPush=True
			self.a.pullValue()
			self.b.pullValue()
			self.willPush=True
	def notify(self,source):
		iA = lazyBoolToInt(self.a.value)
		iB = lazyBoolToInt(self.b.value)
		iX = min(iA,iB)
		val = intToLazyBool( iX )
		self.newValueIs(val)
		needsPush = (val is None) and self.willPush
		return needsPush

class lazyLogic_Or(lazyLogic):
	def __init__(self,a,b):
		super(self.__class__,self).__init__()
		self.a = a
		self.b = b
		self.a.addListener(self)
		self.b.addListener(self)
	def pullValue(self):
		if self.value is None and not self.willPush:
			print("pulling for Node %d"%self.idx)
			self.willPush=True
			self.a.pullValue()
			self.b.pullValue()
			self.willPush=True
	def notify(self,source):
		iA = lazyBoolToInt(self.a.value)
		iB = lazyBoolToInt(self.b.value)
		iX = max(iA,iB)
		val = intToLazyBool( iX )
		self.newValueIs(val)
		needsPush = (val is None) and self.willPush
		return needsPush

class lazyLogic_Not(lazyLogic):
	def __init__(self,a):
		print "create NOT["
		super(self.__class__,self).__init__()
		self.a = a
		self.a.addListener(self)
	def pullValue(self):
		if self.value is None and not self.willPush:
			print("pulling for Node %d"%self.idx)
			self.willPush=True
			self.a.pullValue()
			self.willPush=True
	def notify(self,source):
		iA = lazyBoolToInt(self.a.value)
		iX = -iA
		val = intToLazyBool( iX )
		self.newValueIs(val)
		needsPush = (val is None) and self.willPush
		return needsPush


def nand(a,b):
	aa = a&b
	print aa
	naa = ~aa
	print naa
	return naa

def showthem():
  Q.pullValue()
  Qi.pullValue()
  print "-------------"
  print R.value,S.value,Q.value,Qi.value

S=lazyLogic()
R=lazyLogic()
Q=lazyLogicSignal()
Qi=lazyLogicSignal()
Q.source = nand(S,Qi)
Qi.source = nand(R,Q)

S.value = True
showthem()
S.value = False
showthem()
R.value = False
