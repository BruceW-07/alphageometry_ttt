# Copyright 2023 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Implements DAG-level traceback."""

from typing import Any

import geometry as gm
import pretty as pt
import problem


pretty = pt.pretty


def point_levels(
    setup: list[problem.Dependency], existing_points: list[gm.Point]
) -> list[tuple[set[gm.Point], list[problem.Dependency]]]:
  """Reformat setup into levels of point constructions."""
  levels = []
  for con in setup:
    plevel = max([p.plevel for p in con.args if isinstance(p, gm.Point)])

    while len(levels) - 1 < plevel:
      levels.append((set(), []))

    for p in con.args:
      if not isinstance(p, gm.Point):
        continue
      if existing_points and p in existing_points:
        continue

      levels[p.plevel][0].add(p)

    cons = levels[plevel][1]
    cons.append(con)

  return [(p, c) for p, c in levels if p or c]


def point_log(
    setup: list[problem.Dependency],
    ref_id: dict[tuple[str, ...], int],
    existing_points=list[gm.Point],
) -> list[tuple[list[gm.Point], list[problem.Dependency]]]:
  """Reformat setup into groups of point constructions."""
  log = []

  levels = point_levels(setup, existing_points)

  for points, cons in levels:
    for con in cons:
      if con.hashed() not in ref_id:
        ref_id[con.hashed()] = len(ref_id)

    log.append((points, cons))

  return log


def setup_to_levels(
    setup: list[problem.Dependency],
) -> list[list[problem.Dependency]]:
  """Reformat setup into levels of point constructions."""
  levels = []
  for d in setup:
    plevel = max([p.plevel for p in d.args if isinstance(p, gm.Point)])
    while len(levels) - 1 < plevel:
      levels.append([])

    levels[plevel].append(d)

  levels = [lvl for lvl in levels if lvl]
  return levels


def separate_dependency_difference(
    query: problem.Dependency,
    log: list[tuple[list[problem.Dependency], list[problem.Dependency]]],
) -> tuple[
    list[tuple[list[problem.Dependency], list[problem.Dependency]]],
    list[problem.Dependency],
    list[problem.Dependency],
    set[gm.Point],
    set[gm.Point],
]:
  """Identify and separate the dependency difference."""
  setup = []
  log_, log = log, []
  for prems, cons in log_:
    # 若没有 prems, 则把 cons 加入 setup
    if not prems:
      setup.extend(cons)
      continue
    cons_ = []
    for con in cons:
      # 如果 rule_name 是 'c0', 则表示它是题目中的条件, 加入 setup
      if con.rule_name == 'c0':
        setup.append(con)
      # 否则加入 cons_
      else:
        cons_.append(con)
    if not cons_:
      continue

    # 如果 cons_ 里有 'ind', 则把 'ind' 从 prems 中去掉
    prems = [p for p in prems if p.name != 'ind']
    # 把去掉了 'ind' 的 prems 和去掉了 setup 的 cons_ 加入 log
    log.append((prems, cons_))

  points = set(query.args)
  queue = list(query.args)
  i = 0
  while i < len(queue):
    q = queue[i]
    i += 1
    if not isinstance(q, gm.Point):
      continue
    # 把 query.args 中 Point 类型的 args 的 rely_on 加入 points 和 queue
    for p in q.rely_on:
      if p not in points:
        points.add(p)
        queue.append(p)

  setup_, setup, aux_setup, aux_points = setup, [], [], set()
  for con in setup_:
    # 不处理 name == 'ind' 的命题
    if con.name == 'ind':
      continue
    # 如果 con 的 args 里有不在 points 里的点, 则把 cons 加入 aux_setup,
    # 把不在 points 里的点加入 aux_points
    elif any([p not in points for p in con.args if isinstance(p, gm.Point)]):
      aux_setup.append(con)
      aux_points.update(
          [p for p in con.args if isinstance(p, gm.Point) and p not in points]
      )
    # 否则加入 setup
    else:
      setup.append(con)

  return log, setup, aux_setup, points, aux_points


def recursive_traceback(
    query: problem.Dependency,
) -> list[tuple[list[problem.Dependency], list[problem.Dependency]]]:
  """Recursively traceback from the query, i.e. the conclusion."""
  visited = set()
  log = []
  stack = []

  def read(q: problem.Dependency) -> None:
    # 在回溯过程中, 可能会多次遇到自己 (导致多余的推导), 因此需要把这些多余的部分去掉.
    q = q.remove_loop()
    hashed = q.hashed()
    if hashed in visited:
      return

    if hashed[0] in ['ncoll', 'npara', 'nperp', 'diff', 'sameside']:
      return

    # nonlocal 表示这里的 stack 是在外部定义的 stack
    nonlocal stack

    stack.append(hashed)
    prems = []

    # 如果 q 的 rule_name 不是 CONSTRUCTION_RULE, 则说明 q 是一个推导, 需要递归处理 q 的 why
    if q.rule_name != problem.CONSTRUCTION_RULE:
      all_deps = [] # 去重后的 q.why
      dep_names = set() # 用于去重
      for d in q.why:
        if d.hashed() in dep_names:
          continue
        dep_names.add(d.hashed())
        all_deps.append(d)

      for d in all_deps:
        h = d.hashed()
        # 如果 d 没有被访问过, 则递归处理 d
        if h not in visited:
          read(d)
        # 如果 d 被访问过, 则加入 prems (premises) 中
        if h in visited:
          prems.append(d)

    # 把 q 的哈希值加入 visited
    visited.add(hashed)
    hashs = sorted([d.hashed() for d in prems])
    found = False
    for ps, qs in log:
      # 如果在 log 里已经出现过这组 prems, 则把 q 加入 qs (conclusion) 中
      if sorted([d.hashed() for d in ps]) == hashs:
        qs += [q]
        found = True
        break
    if not found:
      log.append((prems, [q]))

    stack.pop(-1)

  read(query)

  # post process log: separate multi-conclusion lines
  log_, log = log, []
  for ps, qs in log_:
    for q in qs:
      log.append((ps, [q]))

  return log


def collx_to_coll_setup(
    setup: list[problem.Dependency],
) -> list[problem.Dependency]:
  """Convert collx to coll in setups."""
  result = []
  for level in setup_to_levels(setup):
    hashs = set()
    for dep in level:
      if dep.name == 'collx':
        dep.name = 'coll'
        dep.args = list(set(dep.args))

      if dep.hashed() in hashs:
        continue
      hashs.add(dep.hashed())
      result.append(dep)

  return result


def collx_to_coll(
    setup: list[problem.Dependency],
    aux_setup: list[problem.Dependency],
    log: list[tuple[list[problem.Dependency], list[problem.Dependency]]],
) -> tuple[
    list[problem.Dependency],
    list[problem.Dependency],
    list[tuple[list[problem.Dependency], list[problem.Dependency]]],
]:
  """Convert collx to coll and dedup."""
  setup = collx_to_coll_setup(setup)
  aux_setup = collx_to_coll_setup(aux_setup)

  con_set = set([p.hashed() for p in setup + aux_setup])
  log_, log = log, []
  for prems, cons in log_:
    prem_set = set()
    prems_, prems = prems, []
    for p in prems_:
      if p.name == 'collx':
        p.name = 'coll'
        p.args = list(set(p.args))
      if p.hashed() in prem_set:
        continue
      prem_set.add(p.hashed())
      prems.append(p)

    cons_, cons = cons, []
    for c in cons_:
      if c.name == 'collx':
        c.name = 'coll'
        c.args = list(set(c.args))
      if c.hashed() in con_set:
        continue
      con_set.add(c.hashed())
      cons.append(c)

    if not cons or not prems:
      continue

    log.append((prems, cons))

  return setup, aux_setup, log


def get_logs(
    query: problem.Dependency, g: Any, merge_trivials: bool = False
) -> tuple[
    list[problem.Dependency],
    list[problem.Dependency],
    list[tuple[list[problem.Dependency], list[problem.Dependency]]],
    set[gm.Point],
]:
  """Given a DAG and conclusion N, return the premise, aux, proof."""
  # 返回一列 deps
  query = query.why_me_or_cache(g, query.level)
  # 返回一列 (ps, [q]), ps 为 premises, q 为 conclusion
  log = recursive_traceback(query)
  log, setup, aux_setup, setup_points, _ = separate_dependency_difference(
      query, log
  )

  setup, aux_setup, log = collx_to_coll(setup, aux_setup, log)

  setup, aux_setup, log = shorten_and_shave(
      setup, aux_setup, log, merge_trivials
  )

  return setup, aux_setup, log, setup_points


def shorten_and_shave(
    setup: list[problem.Dependency],
    aux_setup: list[problem.Dependency],
    log: list[tuple[list[problem.Dependency], list[problem.Dependency]]],
    merge_trivials: bool = False,
) -> tuple[
    list[problem.Dependency],
    list[problem.Dependency],
    list[tuple[list[problem.Dependency], list[problem.Dependency]]],
]:
  """Shorten the proof by removing unused predicates."""
  log, _ = shorten_proof(log, merge_trivials=merge_trivials)

  all_prems = sum([list(prems) for prems, _ in log], [])
  all_prems = set([p.hashed() for p in all_prems])
  setup = [d for d in setup if d.hashed() in all_prems]
  aux_setup = [d for d in aux_setup if d.hashed() in all_prems]
  return setup, aux_setup, log


def join_prems(
    con: problem.Dependency,
    con2prems: dict[tuple[str, ...], list[problem.Dependency]],
    expanded: set[tuple[str, ...]],
) -> list[problem.Dependency]:
  """Join proof steps with the same premises."""
  h = con.hashed()
  if h in expanded or h not in con2prems:
    return [con]

  result = []
  for p in con2prems[h]:
    result += join_prems(p, con2prems, expanded)
  return result


def shorten_proof(
    log: list[tuple[list[problem.Dependency], list[problem.Dependency]]],
    merge_trivials: bool = False,
) -> tuple[
    list[tuple[list[problem.Dependency], list[problem.Dependency]]],
    dict[tuple[str, ...], list[problem.Dependency]],
]:
  """Join multiple trivials proof steps into one."""
  pops = set()
  con2prem = {}
  for prems, cons in log:
    assert len(cons) == 1
    con = cons[0]
    if con.rule_name == '':  # pylint: disable=g-explicit-bool-comparison
      con2prem[con.hashed()] = prems
    elif not merge_trivials:
      # except for the ones that are premises to non-trivial steps.
      pops.update({p.hashed() for p in prems})

  for p in pops:
    if p in con2prem:
      con2prem.pop(p)

  expanded = set()
  log2 = []
  for i, (prems, cons) in enumerate(log):
    con = cons[0]
    if i < len(log) - 1 and con.hashed() in con2prem:
      continue

    hashs = set()
    new_prems = []

    for p in sum([join_prems(p, con2prem, expanded) for p in prems], []):
      if p.hashed() not in hashs:
        new_prems.append(p)
        hashs.add(p.hashed())

    log2 += [(new_prems, [con])]
    expanded.add(con.hashed())

  return log2, con2prem
