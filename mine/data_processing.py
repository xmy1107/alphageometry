import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../meliad_lib/meliad')))
import graph as gh
import problem as pr
import ddar
from absl import app, logging
import alphageometry

import random
import string

DEFS_FILE = '../defs.txt'
PROBLEMS_FILE = 'gen.txt'
PROBLEM_NAME =  'p2'
# PROBLEMS_FILE = '../examples.txt'
# PROBLEM_NAME =  'orthocenter_aux'
OUT_FILE = ''
RULES_FILE = '../rules.txt'

def main(_):
    global DEFINITIONS
    global RULES

    DEFINITIONS = pr.Definition.from_txt_file(DEFS_FILE, to_dict=True)
    RULES = pr.Theorem.from_txt_file(RULES_FILE, to_dict=True)

    problems = pr.Problem.from_txt_file(PROBLEMS_FILE, to_dict=True)

    p = problems[PROBLEM_NAME]

    # g, _ = gh.Graph.build_problem(this_problem, DEFINITIONS)

    # draw(g, this_problem, OUT_FILE)
    string = p.setup_str_from_problem(DEFINITIONS)
    string += ' {F1} x00'
    print("Problem string:", string)


if __name__ == '__main__':
    app.run(main)