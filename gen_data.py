import graph as gh
import random as rd
import problem as pr
import time
from absl import flags
from absl import app

ClauseNumMin = 2
ClauseNumMax = 7
ConstructNumMin = 1
ConstructNumMax = 2

_DEFS_FILE = flags.DEFINE_string(
    'defs_file',
    'defs.txt',
    'definitions of available constructions to state a problem.',
)
_RULES_FILE = flags.DEFINE_string(
    'rules_file', 'rules.txt', 'list of deduction rules used by DD.'
)

def main(_):
  global DEFINITIONS
  global RULES

  # definitions of terms used in our domain-specific language.
  DEFINITIONS = pr.Definition.from_txt_file(_DEFS_FILE.value, to_dict=True)
  # load inference rules used in DD.
  RULES = pr.Theorem.from_txt_file(_RULES_FILE.value, to_dict=True)

  g = gh.Graph()
  added = []
  plevel = 0
  clauses = []
  clause_num = rd.randint(ClauseNumMin, ClauseNumMax)
  for i in range(clause_num):
    # 找一个 clause
    flag = False
    new_points = []
    constructions = []
    while not flag:
      # 先找到第一个 construction (确认新点)
      cdef = rd.choice(list(DEFINITIONS.values()))
      print(cdef.construction.name)
      if len(cdef.args) > len(g.type2nodes['Point']):
        continue
      # 从已有点中随机选一些点作为新 construction 的参数
      points = rd.sample(g.type2nodes['Point'], len(cdef.args))
      # 建立从 args 到 points 的映射
      mapping = dict(zip(cdef.construction.args, points))
      flag = True
      for d in cdef.deps.constructions:
        args = [mapping[arg] for arg in d.args]
        if not g.check(d.name, args):
          flag = False
          break
      
      if flag:
        new_points = cdef.points
        constructions.append(cdef.construction)
    else:
      cons_num = rd.randint(1, ClauseNumMax)

      # 如果 cdef 中没有 args (即纯构造类的 construction), 则只选择一个 construction
      if len(cdef.args) == 0:
        cons_num = 1

      # 对当前 clause 找每一个 construction
      for i in range(cons_num - 1):
        flag = 0
        start_time = time.time()
        while not flag: 
          if time.time() - start_time > 1:  # 1 second timeout
            break
          cdef = rd.choice(list(DEFINITIONS.values()))
          if len(cdef.points) != len(new_points):
            continue
          points = rd.sample(g.type2nodes['Point'], len(cdef.args))
          mapping = dict(zip(cdef.construction.args, points))
          flag = True
          for d in cdef.deps.constructions:
            args = [mapping[arg] for arg in d.args]
            if not g.check(d.name, args):
              flag = False
              break
          
          if flag:
            constructions.append(cdef.construction)

      new_clause = pr.Clause(new_points, constructions)
      adds, plevel = g.add_clause(
        new_clause, plevel, DEFINITIONS,
      )
      added += adds
      clauses.append(new_clause)
    
  g.plevel = plevel

  for clause in clauses:
    print(clause, end='; ')
  
if __name__ == '__main__':
  app.run(main)
      
