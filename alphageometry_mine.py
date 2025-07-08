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

"""Run DD+AR or AlphaGeometry solver.

Please refer to README.md for detailed instructions.
"""

import traceback

from absl import app
from absl import flags
from absl import logging
import ddar
import graph as gh
import lm_inference as lm
import pretty as pt
import problem as pr
import subprocess
import os

_GIN_SEARCH_PATHS = flags.DEFINE_list(
    'gin_search_paths',
    ['third_party/py/meliad/transformer/configs'],
    'List of paths where the Gin config files are located.',
)
_GIN_FILE = flags.DEFINE_multi_string(
    'gin_file', ['base_htrans.gin'], 'List of Gin config files.'
)
_GIN_PARAM = flags.DEFINE_multi_string(
    'gin_param', None, 'Newline separated list of Gin parameter bindings.'
)

_PROBLEMS_FILE = flags.DEFINE_string(
    'problems_file',
    'imo_ag_30.txt',
    'text file contains the problem strings. See imo_ag_30.txt for example.',
)
_PROBLEM_NAME = flags.DEFINE_string(
    'problem_name',
    'imo_2000_p1',
    'name of the problem to solve, must be in the problem_file.',
)
_MODE = flags.DEFINE_string(
    'mode', 'ddar', 'either `ddar` (DD+AR) or `alphageometry`')
_DEFS_FILE = flags.DEFINE_string(
    'defs_file',
    'defs.txt',
    'definitions of available constructions to state a problem.',
)
_RULES_FILE = flags.DEFINE_string(
    'rules_file', 'rules.txt', 'list of deduction rules used by DD.'
)
_CKPT_PATH = flags.DEFINE_string('ckpt_path', '', 'checkpoint of the LM model.')
_VOCAB_PATH = flags.DEFINE_string(
    'vocab_path', '', 'path to the LM vocab file.'
)
_OUT_FILE = flags.DEFINE_string(
    'out_file', '', 'path to the solution output file.'
)  # pylint: disable=line-too-long
_BEAM_SIZE = flags.DEFINE_integer(
    'beam_size', 1, 'beam size of the proof search.'
)  # pylint: disable=line-too-long
_SEARCH_DEPTH = flags.DEFINE_integer(
    'search_depth', 1, 'search depth of the proof search.'
)  # pylint: disable=line-too-long

DEFINITIONS = None  # contains definitions of construction actions
RULES = None  # contains rules of deductions


def natural_language_statement(logical_statement: pr.Dependency) -> str:
  """Convert logical_statement to natural language.

  Args:
    logical_statement: pr.Dependency with .name and .args

  Returns:
    a string of (pseudo) natural language of the predicate for human reader.
  """
  names = [a.name.upper() for a in logical_statement.args]
  names = [(n[0] + '_' + n[1:]) if len(n) > 1 else n for n in names]
  return pt.pretty_nl(logical_statement.name, names)


def proof_step_string(
    proof_step: pr.Dependency, refs: dict[tuple[str, ...], int], last_step: bool
) -> str:
  """Translate proof to natural language.

  Args:
    proof_step: pr.Dependency with .name and .args
    refs: dict(hash: int) to keep track of derived predicates
    last_step: boolean to keep track whether this is the last step.

  Returns:
    a string of (pseudo) natural language of the proof step for human reader.
  """
  premises, [conclusion] = proof_step

  premises_nl = ' & '.join(
      [
          natural_language_statement(p) + ' [{:02}]'.format(refs[p.hashed()])
          for p in premises
      ]
  )

  if not premises:
    premises_nl = 'similarly'

  refs[conclusion.hashed()] = len(refs)

  conclusion_nl = natural_language_statement(conclusion)
  if not last_step:
    conclusion_nl += ' [{:02}]'.format(refs[conclusion.hashed()])

  return f'{premises_nl} \u21d2 {conclusion_nl}'


def write_solution(g: gh.Graph, p: pr.Problem, out_file: str, printlog : bool = False) -> list[str]:
  """Output the solution to out_file.

  Args:
    g: gh.Graph object, containing the proof state.
    p: pr.Problem object, containing the theorem.
    out_file: file to write to, empty string to skip writing to file.
  """

  setup, aux, proof_steps, refs = ddar.get_proof_steps(
      g, p.goal, merge_trivials=False
  )
  
  count_points = []

  solution = '\n=========================='
  solution += '\n * From theorem premises:\n'
  premises_nl = []
  for premises, [points] in setup:
    solution += ' '.join([p.name.upper() for p in points]) + ' '
    if not premises:
      continue
    premises_nl += [
        natural_language_statement(p) + ' [{:02}]'.format(refs[p.hashed()])
        for p in premises
    ]
  solution += ': Points\n' + '\n'.join(premises_nl)

  solution += '\n\n * Auxiliary Constructions:\n'
  aux_premises_nl = []
  for premises, [points] in aux:
    solution += ' '.join([p.name.upper() for p in points]) + ' '
    count_points.extend([p.name for p in points])
    aux_premises_nl += [
        natural_language_statement(p) + ' [{:02}]'.format(refs[p.hashed()])
        for p in premises
    ]
  solution += ': Points\n' + '\n'.join(aux_premises_nl)

  if not printlog: return count_points


  # some special case where the deduction rule has a well known name.
  r2name = {
      'r32': '(SSS)',
      'r33': '(SAS)',
      'r34': '(Similar Triangles)',
      'r35': '(Similar Triangles)',
      'r36': '(ASA)',
      'r37': '(ASA)',
      'r38': '(Similar Triangles)',
      'r39': '(Similar Triangles)',
      'r40': '(Congruent Triangles)',
      'a00': '(Distance chase)',
      'a01': '(Ratio chase)',
      'a02': '(Angle chase)',
  }

  solution += '\n\n * Proof steps:\n'

  my_solution = "各结论需要的条件："
  for i, step in enumerate(proof_steps):
    _, [con] = step
    nl = proof_step_string(step, refs, last_step=i == len(proof_steps) - 1)

    premises, [conclusion] = step
    prems_idx = [refs[p.hashed()] for p in premises]
    my_solution += f"结论[{refs[conclusion.hashed()]}] 由条件 {prems_idx}推出"

    rule_name = r2name.get(con.rule_name, '')
    nl = nl.replace('\u21d2', f'{rule_name}\u21d2 ')
    solution += '{:03}. '.format(i + 1) + nl + '\n'

  solution += '==========================\n'

  my_solution += "\n每个结论涉及的点名："
  for i, step in enumerate(proof_steps):
      _, [conclusion] = step
      point_names = sorted({pt.name.upper() for pt in conclusion.args})
      desc = natural_language_statement(conclusion)
      my_solution += f"结论[{refs[conclusion.hashed()]}]: {desc} 涉及点: {''.join(point_names)}"

  if printlog:
    logging.info(solution)
    # logging.info(my_solution)
  if out_file:
    with open(out_file, 'w') as f:
      f.write(solution)
    logging.info('Solution written to %s.', out_file)


def get_lm(ckpt_init: str, vocab_path: str) -> "lm.LanguageModelInference": # 前向引用
  lm.parse_gin_configuration(
      _GIN_FILE.value, _GIN_PARAM.value, gin_paths=_GIN_SEARCH_PATHS.value
  )

  return lm.LanguageModelInference(vocab_path, ckpt_init, mode='beam_search')


def run_ddar(g: gh.Graph, p: pr.Problem, out_file: str, printlog: bool = False) -> bool:
  """Run DD+AR.

  Args:
    g: gh.Graph object, containing the proof state.
    p: pr.Problem object, containing the problem statement.
    out_file: path to output file if solution is found.

  Returns:
    Boolean, whether DD+AR finishes successfully.
  """
  ddar.solve(g, RULES, p, max_level=1000)

  goal_args = g.names2nodes(p.goal.args)
  if not g.check(p.goal.name, goal_args):
    logging.info('DD+AR failed to solve the problem.')
    return False

  write_solution(g, p, out_file, printlog)

  gh.nm.draw(
      g.type2nodes[gh.Point],
      g.type2nodes[gh.Line],
      g.type2nodes[gh.Circle],
      g.type2nodes[gh.Segment])
  return True


def translate_constrained_to_constructive(
    point: str, name: str, args: list[str]
) -> tuple[str, list[str]]:
  """Translate a predicate from constraint-based to construction-based.

  Args:
    point: str: name of the new point
    name: str: name of the predicate, e.g., perp, para, etc.
    args: list[str]: list of predicate args.

  Returns:
    (name, args): translated to constructive predicate.
  """
  if name in ['T', 'perp']:
    a, b, c, d = args
    if point in [c, d]:
      a, b, c, d = c, d, a, b
    if point == b:
      a, b = b, a
    if point == d:
      c, d = d, c
    if a == c and a == point:
      return 'on_dia', [a, b, d]
    return 'on_tline', [a, b, c, d]

  elif name in ['P', 'para']:
    a, b, c, d = args
    if point in [c, d]:
      a, b, c, d = c, d, a, b
    if point == b:
      a, b = b, a
    return 'on_pline', [a, b, c, d]

  elif name in ['D', 'cong']:
    a, b, c, d = args
    if point in [c, d]:
      a, b, c, d = c, d, a, b
    if point == b:
      a, b = b, a
    if point == d:
      c, d = d, c
    if a == c and a == point:
      return 'on_bline', [a, b, d]
    if b in [c, d]:
      if b == d:
        c, d = d, c  # pylint: disable=unused-variable
      return 'on_circle', [a, b, d]
    return 'eqdistance', [a, b, c, d]

  elif name in ['C', 'coll']:
    a, b, c = args
    if point == b:
      a, b = b, a
    if point == c:
      a, b, c = c, a, b
    return 'on_line', [a, b, c]

  elif name in ['^', 'eqangle']:
    a, b, c, d, e, f = args

    if point in [d, e, f]:
      a, b, c, d, e, f = d, e, f, a, b, c

    x, b, y, c, d = b, c, e, d, f
    if point == b:
      a, b, c, d = b, a, d, c

    if point == d and x == y:  # x p x b = x c x p
      return 'angle_bisector', [point, b, x, c]

    if point == x:
      return 'eqangle3', [x, a, b, y, c, d]

    return 'on_aline', [a, x, b, c, y, d]

  elif name in ['cyclic', 'O']:
    a, b, c = [x for x in args if x != point]
    return 'on_circum', [point, a, b, c]

  return name, args


def check_valid_args(name: str, args: list[str]) -> bool:
  """Check whether a predicate is grammarically correct.

  Args:
    name: str: name of the predicate
    args: list[str]: args of the predicate

  Returns:
    bool: whether the predicate arg count is valid.
  """
  if name == 'perp':
    if len(args) != 4:
      return False
    a, b, c, d = args
    if len({a, b}) < 2:
      return False
    if len({c, d}) < 2:
      return False
  elif name == 'para':
    if len(args) != 4:
      return False
    a, b, c, d = args
    if len({a, b, c, d}) < 4:
      return False
  elif name == 'cong':
    if len(args) != 4:
      return False
    a, b, c, d = args
    if len({a, b}) < 2:
      return False
    if len({c, d}) < 2:
      return False
  elif name == 'coll':
    if len(args) != 3:
      return False
    a, b, c = args
    if len({a, b, c}) < 3:
      return False
  elif name == 'cyclic':
    if len(args) != 4:
      return False
    a, b, c, d = args
    if len({a, b, c, d}) < 4:
      return False
  elif name == 'eqangle':
    if len(args) != 8:
      return False
    a, b, c, d, e, f, g, h = args
    if len({a, b, c, d}) < 3:
      return False
    if len({e, f, g, h}) < 3:
      return False
  return True


def try_translate_constrained_to_construct(string: str, g: gh.Graph) -> str:
  """Whether a string of aux construction can be constructed.

  Args:
    string: str: the string describing aux construction.
    g: gh.Graph: the current proof state.

  Returns:
    str: whether this construction is valid. If not, starts with "ERROR:".
  """
  if string[-1] != ';':
    return 'ERROR: must end with ;'

  head, prem_str = string.split(' : ')
  point = head.strip()

  if len(point) != 1 or point == ' ':
    return f'ERROR: invalid point name {point}'

  existing_points = [p.name for p in g.all_points()]
  if point in existing_points:
    return f'ERROR: point {point} already exists.'

  prem_toks = prem_str.split()[:-1]  # remove the EOS ' ;'
  prems = [[]]

  for i, tok in enumerate(prem_toks):
    if tok.isdigit():
      if i < len(prem_toks) - 1:
        prems.append([])
    else:
      prems[-1].append(tok)

  if len(prems) > 2:
    return 'ERROR: there cannot be more than two predicates.'

  clause_txt = point + ' = '
  constructions = []

  for prem in prems:
    name, *args = prem

    if point not in args:
      return f'ERROR: {point} not found in predicate args.'

    if not check_valid_args(pt.map_symbol(name), args):
      return 'ERROR: Invalid predicate ' + name + ' ' + ' '.join(args)

    for a in args:
      if a != point and a not in existing_points:
        return f'ERROR: point {a} does not exist.'

    try:
      name, args = translate_constrained_to_constructive(point, name, args)
    except:  # pylint: disable=bare-except
      return 'ERROR: Invalid predicate ' + name + ' ' + ' '.join(args)

    if name == 'on_aline':
      if args.count(point) > 1:
        return f'ERROR: on_aline involves twice {point}'

    constructions += [name + ' ' + ' '.join(args)]

  clause_txt += ', '.join(constructions)
  clause = pr.Clause.from_txt(clause_txt)

  try:
    g.copy().add_clause(clause, 0, DEFINITIONS)
  except:  # pylint: disable=bare-except
    return 'ERROR: ' + traceback.format_exc()

  return clause_txt


def insert_aux_to_premise(pstring: str, auxstring: str) -> str:
  """Insert auxiliary constructs from proof to premise.

  Args:
    pstring: str: describing the problem to solve.
    auxstring: str: describing the auxiliar construction.

  Returns:
    str: new pstring with auxstring inserted before the conclusion.
  """
  setup, goal = pstring.split(' ? ')
  return setup + '; ' + auxstring + ' ? ' + goal

def translate_sentence(model_path, sentence, gpu=0, beam_size=30, n_best=30):
    """
    用法：
    sentence = "a b c = triangle ; h = on_tline b a c , on_tline c a b ? perp a h b c"
    translated = translate_sentence("mine/run/model_step_1000.pt", sentence, gpu=0)
    print(f"Translated sentences: {translated}")
    print(f"Best translation: {translated[0]}")
    """
    with open("temp_input.txt", "w") as f:
        f.write(sentence)
    
    output_file = "temp_output.txt"
    
    cmd = [
        "onmt_translate", 
        "-model", model_path, 
        "-src", "temp_input.txt", 
        "-output", output_file, 
        "-gpu", str(gpu), 
        "-beam_size", str(beam_size),
        "-n_best", str(n_best),
        "-verbose"
    ]
    
    subprocess.run(cmd, check=True)
    
    with open(output_file, "r") as f:
        translated_sentences = [line.strip() for line in f.readlines()]
    
    subprocess.run("rm temp_input.txt temp_output.txt", shell=True)
    
    return translated_sentences

def run_alphageometry(
    model: "lm.LanguageModelInference", # 前向引用
    p: pr.Problem,
    search_depth: int,
    beam_size: int,
    out_file: str,
    pstring: str
) -> bool:
  g, _ = gh.Graph.build_problem(p, DEFINITIONS)

  # if run_ddar(g, p, out_file):
  #   return True

  pstring_to_string = lambda pstring: pstring.replace(',', ' ,').replace(';', ' ;')
  string_to_pstring = lambda string: string.replace(' ,', ',').replace(' ;', ';')

  beam_queue = []
  beam_queue.append((g, pstring))

  for i, (g, pstring) in enumerate(beam_queue):
    logging.info('Processing beam %d', i)
    string = pstring_to_string(pstring)
    logging.info('Solving: "%s"', pstring)

    candidates = translate_sentence(_CKPT_PATH.value, string, gpu=0)

    print(f"Candidates: {candidates}")

    for aux in candidates:
      # logging.info('Add auxiliary point: "%s"\n', aux)
      paux = string_to_pstring(aux)

      candidate_pstring = insert_aux_to_premise(pstring, paux)

      logging.info('Solving: "%s"', candidate_pstring)
      try:
        p_new = pr.Problem.from_txt(candidate_pstring)
      except Exception as e:
        logging.info('Failed to parse problem: "%s", error: %s', candidate_pstring, str(e))
        continue

      try:
        g_new, _ = gh.Graph.build_problem(p_new, DEFINITIONS)
      except Exception as e:
        logging.info('Failed to build graph from problem: "%s", error: %s', candidate_pstring, str(e))
        continue

      if run_ddar(g_new, p_new, out_file, True):
        logging.info('Solved.')
        return True

  return False


def main(_):
  global DEFINITIONS
  global RULES

  # definitions of terms used in our domain-specific language.
  DEFINITIONS = pr.Definition.from_txt_file(_DEFS_FILE.value, to_dict=True)
  # load inference rules used in DD.
  RULES = pr.Theorem.from_txt_file(_RULES_FILE.value, to_dict=True)

  # when using the language model,
  # point names will be renamed to alphabetical a, b, c, d, e, ...
  # instead of staying with their original names,
  # in order to match the synthetic training data generation.
  need_rename = _MODE.value != 'ddar'

  # load problems from the problems_file,
  problems = pr.Problem.from_txt_file(
      _PROBLEMS_FILE.value, to_dict=True, translate=need_rename
  )

  if _PROBLEM_NAME.value not in problems:
    raise ValueError(
        f'Problem name `{_PROBLEM_NAME.value}` '
        + f'not found in `{_PROBLEMS_FILE.value}`'
    )

  this_problem = problems[_PROBLEM_NAME.value]
  print("Problem content: ", this_problem.txt())

  if _MODE.value == 'ddar':
    g, _ = gh.Graph.build_problem(this_problem, DEFINITIONS)
    run_ddar(g, this_problem, _OUT_FILE.value)

  elif _MODE.value == 'alphageometry':
    # model = get_lm(_CKPT_PATH.value, _VOCAB_PATH.value)
    model = None
    run_alphageometry(
        model,
        this_problem,
        _SEARCH_DEPTH.value,
        _BEAM_SIZE.value,
        _OUT_FILE.value,
        this_problem.txt()
    )

  else:
    raise ValueError(f'Unknown FLAGS.mode: {_MODE.value}')


if __name__ == '__main__':
  app.run(main)
