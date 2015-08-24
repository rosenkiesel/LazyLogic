# SINGLE(a)
# SEQ(a,b)
# OR(a,b)
# CHECK(a) (= AND)
# CHECK_NOT(a) (= AND_NOT)
# NON_EMPTY(a)
#
# SEQ(SEQ(a,b),c) -> SEQ(a,SEQ(b,c))
# OR(OR(a,b),c) -> OR(a,OR(b,c))
#
#
# Grammar:
#   - can_be_empty (Yes, No, undecided, locked_for_trying)
#   - can_be ( [..] ) { A in B.can_be && B in A.can_be -> A==B }
#   - can_start_with ( [...] )
#   - maybe_more_startsymbols (Yes, depends_on_children, No)
#   - parseable (Yes, No, undecided)
#   - parsing_equivalent (other Grammar)
#
# recur-symb <X>  -> inter_X,X = /*NOP*/
# Y in [X,X.can_start_with], a.can_be_emtpy is True:
#   Y |= a B/b        -> Y|= NON_EMPTY(a) B/b; Y |= B/b;
# Y in [X,X.can_start_with], a.can_be_emtpy is False:
#   Y |= a B/b        -> X |= a inter_a,X; inter_a,X |= B/b inter_Y,X
#   Y |= B/b          -> inter_B/b,X |= inter_Y,X
# Y,A in [X,X.can_start_with]:
#   Y |= A B          -> inter_A,X |= B inter_Y,X
# 
#
#
# a b -> there must be SEQ(a,x)
#
#
#

class Paddable_iter:
  def __init__(self, gen):
    self.prep = [iter(gen)]
    self.postp = []
  def __iter__(self):
    return self
  def next(self):
    while len(self.prep) > 0:
      try:
        return self.prep[-1].next()
      except StopIteration:
        del(self.prep[-1])
    while len(self.postp) > 0:
      try:
        return self.postp[0].next()
      except StopIteration:
        del(self.postp[0])
    raise StopIteration()
  def append(self,i):
    self.postp.append(iter(i))
  def prepend(self,i):
    self.prep.append(iter(i))

class Language:
  def __init__(self):
    self.grammar = []
  def __add__(self, other):
    ret = Language()
    ret.grammar = self.grammar + other.grammar
    return ret
    
@total_ordering
class Grammar:
  def check_empty(self):
    pass

  def __init__(self):
    self.can_be_emtpy = None
    self.terminal_level = None
    self.can_start_with = None
    self.parsing_eq = None

  def __le__(self,other):
    if not(self.parsing_eq is None):
      return self.parsing_eq < other
    while not(other.parsing_eq is None):
      other = other.parsing_eq
    return self.__class__.__name__ <= other.__class__.__name__
    

    
  # one solution                  (offset_next, matched_obj)
  # undecided/need more lookahead (None, None)
  # want preparsed                (True, Grammar)
  # error                         (False, .. )
  def parse(self, pre_parsed, instream, offset_start):
    if self.parse is Grammar.parse:
      yield (False, "this is undefined grammar. use subclass")
    potential_grammars = {self:{None}}
    parsed_grammars = {}
    results = []
    while len(potential_grammars)>0:
      gram = potential_grammars.keys()[0]
      if parsed_grammars.has_key(gram):
        parsed_grammars[gram].union( potential_grammars[gram] )
        del potential_grammars[gram]
        continue
      parsed_grammars[gram] = potential_grammars[gram]
      del potential_grammars[gram]
      matcher = gram.parse(pre_parsed, instream, offset_start)
      for matched in matcher:
        while matched[0] is None: # more input
          pre_parsed, instream = yield (None,None)
          matched = matcher.send(pre_parsed, instream)
        if matched[0] is False: # error
          yield matched
          return
        if matched[0] is True:
          new_gram = matched[1]
          if not potential_grammars.has_key(new_gram):
            potential_grammars[new_gram] = set([])
          potential_grammars[new_gram].union( {gram} )
        else:
          results.append( (gram,matched) )

    while len(results)>0:
      gram = results[-1][0]
      val = results[-1][1]
      del results[-1]

      pre2 = [ val[0] ]
      pre2.extend( pre_parsed[val[1]:] )
      if val[1] >= len(pre_parsed):
        instr2 = instream[ (val[1] - len(pre_parsed)): ]
      else
        instr2 = instream

      for listener in parsed_grammars[gram]:
        if listener is None: # our uplink
          yield val
          continue
        matcher = listener.parse(pre2, instr2, 0)
        for matched in matcher:
          while matched[0] is None: # more input
            pre_parsed, instream = yield (None,None)
            ############### TODO
            matched = matcher.send(pre_parsed, instream)
          if matched[0] is False: # error
            yield matched
            return
          if matched[0] is True:
            raise Exception("das kann nicht sein")
          else:
            results.append( (listener,matched) )



class SINGLE(Grammar):
  def __init__(self, obj):
    Grammar.__init__(self)
    self.char = obj
    self.can_be_empty = False
    self.terminal_level = (0,0)
    self.can_start_with = [self.char]
    self.matched_grammar = self # this class is its own MATCH
    
  def check_empty(self):
    pass  
    
  def __str__(self):
    return "<%s>"%self.char  
    
  def parse(self, pre_parsed, instream, offset_start):
    idx = offset_start - len(pre_parsed)

    if idx<0:
      if pre_parsed[offset_start] is self:
        yield (offset_start+1, self)
      return

    while (len(instream) <= idx):
      yield (None, None)
    if instream[idx] == self.char:
      yield (offset_start+1, self)
    return

class SEQ_Match:
  def __init__(self,grammar, a, b):
    self.matched_grammar = grammar
    self.a=a
    self.b=b
    pass
  def __str__(self):  
    return "SEQ[%s,%s]"%(self.a,self.b)
    
class SEQ(Grammar):
  def check_empty(self):
    if self.can_be_emtpy is None:
      self.can_be_empty = -1
      self.a.check_empty()
      self.b.check_empty()
      self.can_be_empty = None
      if (self.a.can_be_empty is True) & (self.b.can_be_empty is True):
        self.can_be_empty = True
      if (self.a.can_be_empty is False) | (self.b.can_be_empty is False):
        self.can_be_empty = False  

  def __init__(self,a,b):
    Grammar.__init__(self)
    self.a = a
    self.b = b
    self.check_empty()

  def parse(self, pre_parsed, instream, offset_start):
    idx = offset_start - len(pre_parsed)

    if idx<0:
      if pre_parsed[offset_start].matched_grammar is self:
        yield (offset_start+1, self)
      return


    a_matcher = self.a.parse(pre_parsed, instream, offset_start)
    for a_matched in a_matcher:
      while a_matched[0] is None: # more input
        pre_parsed, instream = yield (None,None)
        a_matched = a_matcher.send(pre_parsed, instream)
      if a_matched[0] is True: # want pre_parsed subgrammar
        yield a_matched
        continue
      if a_matched[0] is False: # error
        yield a_matched
        return
      more_parse_grams_b = {self.b : ([],{None})}
      parse_grams_b = {}
      for b_gram in more_parse_grams_b:
        if parse_grams_b.has_key(b_gram):
          parse_grams_b[b_gram][1].union(more_parse_grams[b_gram][1])
          #DO NOT DELETE, for will skip next grammar otherwise
          #del more_parse_grams_b[b_gram]
          continue
        b_matcher = b_gram.parse(pre_parsed, instream, a_matched[0])
        for b_matched in b_matcher:
          while b_matched[0] is None: # more input
            pre_parsed, instream = yield (None,None)
            b_matched = b_matcher.send(pre_parsed, instream)
          if b_matched[0] is False:
            yield b_matched
            return
          if b_matched[0] is True:
            if a_matched[0] == offset_start:
              yield b_matched
              continue
            else:
              pass
              ################## <- TODO
          yield ( b_matched[0], SEQ_Match(self, a_matched[1], b_matched[1] ) )
        
        
class OR_Match:
  def __init__(self,gram, idx, sub):
    self.sub=sub
    self.idx=idx
    pass
  def __str__(self):  
    return "OR[%d,%s]"%(self.idx,self.sub)

class OR(Grammar):
  def check_empty(self):
    if self.can_be_emtpy is None:
      self.can_be_empty = -1
      self.a.check_empty()
      self.b.check_empty()
      self.can_be_empty = None
      if (self.a.can_be_empty is True) | (self.b.can_be_empty is True):
        self.can_be_empty = True
      if (self.a.can_be_empty is False) & (self.b.can_be_empty is False):
        self.can_be_empty = False  

  def __init__(self,a,b):
    Grammar.__init__(self)
    self.a = a
    self.b = b
    self.check_empty()

  def parse(self, instream, offset_start):
    a_matcher = self.a.parse(instream, offset_start)
    for a_matched in a_matcher:
      if a_matched[0] is None:
        yield (None,None)
        continue
      if a_matched[0] is False:
        yield a_matched
        return
      yield ( a_matched[0], OR_Match(self, 0, a_matched[1] ) )

    b_matcher = self.b.parse(instream, offset_start)
    for b_matched in b_matcher:
      if b_matched[0] is None:
        yield (None,None)
        continue
      if b_matched[0] is False:
        yield b_matched
        return
      yield ( b_matched[0], OR_Match(self, 1, b_matched[1] ) )
      

class CHECK_Match:
  def __init__(self, gram, res):
    self.res = res
    
  def __str__(self):
    return "CHECKED[%s]"%self.res
      
class CHECK(Grammar):
  def __init__(self,gram):
    Grammar.__init__(self)
    self.gram=gram
    self.can_be_empty = True
  def parse(self,instream,offset_start):
    matcher = self.gram.parse(instream,offset_start)
    for matched in matcher:
      if matched[0] is None:
        yield (None,None)
        continue
      if matched[0] is False:
        yield matched
        return
      yield ( offset_start, CHECK_Match(self, matched[1] ) )

class CHECK_NOT_Match:
  def __init__(self, gram):
    self.gram = gram
    
  def __str__(self):
    return "CHECKED_NOT[..]"
    
class CHECK_NOT(Grammar):
  def __init__(self,gram):
    Grammar.__init__(self)
    self.gram=gram
    self.can_be_empty = True

  def parse(self,instream,offset_start):
    matcher = self.gram.parse(instream,offset_start)
    for matched in matcher:
      if matched[0] is None:
        yield (None,None)
        continue
      if matched[0] is False:
        yield matched
        return
      return # if we have a match, we yield nothing  
    yield ( offset_start, CHECK_NOT_Match(self) )

pp = OR( SINGLE('a'), SEQ( SINGLE('x'), SINGLE('y')) );
pp = SEQ( CHECK_NOT(SINGLE('x')) , pp );

def list_matches( gram, str ):
  mm = gram.parse(str,0)
  for res in mm:
    print "--<%s>--[%d]"%(res[1],res[0])


list_matches(pp,['b','a'])
list_matches(pp,['b','x'])
list_matches(pp,['x','a'])
list_matches(pp,['x','b'])
list_matches(pp,['x','a','y'])
list_matches(pp,['x','y','b'])
list_matches(pp,['a','a'])
