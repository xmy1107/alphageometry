import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../meliad_lib/meliad')))

import graph as gh
import problem as pr
import ddar
from absl import app, logging, flags
import alphageometry
import geometry as geom

FLAGS = flags.FLAGS
flags.DEFINE_string('name', '', 'Problem name to solve')

DEFS_FILE = '../defs.txt'
PROBLEMS_FILE = 'examples.txt'
OUT_FILE = ''
RULES_FILE = '../rules.txt'

def draw(g: gh.Graph, p: pr.Problem, out_file: str) -> bool:
  """Run DD+AR.

  Args:
    g: gh.Graph object, containing the proof state.
    p: pr.Problem object, containing the problem statement.
    out_file: path to output file if solution is found.

  Returns:
    Boolean, whether DD+AR finishes successfully.
  """
  ddar.solve(g, RULES, p, max_level=10)

  goal_args = g.names2nodes(p.goal.args)
  if not g.check(p.goal.name, goal_args):
    logging.info('DD+AR failed to solve the problem.')
    return False
  

  # logging.info('DD+AR successed to solve the problem.')
  # print("Yes")

  # for condition in ['perp', 'cong', 'coll']:
  #    for a in 
  # p.goal = pr.Construction.from_txt("cong a d b e")
  alphageometry.write_solution(g, p, out_file, True)
  # count_points = alphageometry.write_solution(g, p, out_file, False)
  # print("Count points: ", count_points)
  g.sort_conclusions()
  print('\n'.join([' '.join(con) for con in g.all_conclusions]))
  print("Size of all_conclutions: ", len(g.all_conclusions))

  gh.nm.draw(
      g.type2nodes[gh.Point],
      g.type2nodes[gh.Line],
      g.type2nodes[gh.Circle],
      g.type2nodes[gh.Segment])
  return True

def get_node_type(node: geom.Node) -> str:
    if isinstance(node, geom.Point):
        return "Point"
    elif isinstance(node, geom.Line):
        return "Line"
    elif isinstance(node, geom.Segment):
        return "Segment"
    elif isinstance(node, geom.Circle):
        return "Circle"
    elif isinstance(node, geom.Angle):
        return "Angle"
    elif isinstance(node, geom.Ratio):
        return "Ratio"
    elif isinstance(node, geom.Measure):
        return "Measure"
    elif isinstance(node, geom.Value):
        return "Value"
    elif isinstance(node, geom.Direction):
        return "Direction"
    else:
        return "Unknown"
def main(_):
  global DEFINITIONS
  global RULES

  DEFINITIONS = pr.Definition.from_txt_file(DEFS_FILE, to_dict=True)
  RULES = pr.Theorem.from_txt_file(RULES_FILE, to_dict=True)

  problems = pr.Problem.from_txt_file(PROBLEMS_FILE, to_dict=True)
  problem_name = FLAGS.name

  if problem_name not in problems:
      raise ValueError(f'Problem name `{problem_name}` not found in `{PROBLEMS_FILE}`')

  this_problem = problems[problem_name]

  g, _ = gh.Graph.build_problem(this_problem, DEFINITIONS)

  draw(g, this_problem, OUT_FILE)

  # all = g.all_nodes()
  # for item in all:
  #   print(item.name, get_node_type(item))
    

  # Set = set(getattr(g, 'all_conclusions', []))
  # print(Set)

if __name__ == '__main__':
  app.run(main)