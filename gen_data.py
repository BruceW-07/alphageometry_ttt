import graph as gh
import random as rd
import problem as pr
from absl import flags

ClauseNumMin = 2
ClauseNumMax = 7
ConstructNumMin = 1
ConstructNumMax = 3

_DEFS_FILE = flags.DEFINE_string(
    'defs_file',
    'defs.txt',
    'definitions of available constructions to state a problem.',
)
_RULES_FILE = flags.DEFINE_string(
    'rules_file', 'rules.txt', 'list of deduction rules used by DD.'
)

def main():
  global DEFINITIONS
  global RULES

  # definitions of terms used in our domain-specific language.
  DEFINITIONS = pr.Definition.from_txt_file(_DEFS_FILE.value, to_dict=True)
  # load inference rules used in DD.
  RULES = pr.Theorem.from_txt_file(_RULES_FILE.value, to_dict=True)

  g = gh.Graph()
  clause_num = rd.randint(ClauseNumMin, ClauseNumMax)
  for i in range(clause_num):
    # 找一个 clause
    flag = False
    while not flag:
      # 先找到第一个 construction (确认新点)
      cdef = rd.choice(list(DEFINITIONS.values()))
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
      # 如果 deps 不满足, 则继续随机
      if not flag:
        continue
      
      
      

      
