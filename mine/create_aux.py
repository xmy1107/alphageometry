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
import multiprocessing

DEFS_FILE = '../defs.txt'
# PROBLEMS_FILE = 'gen.txt'
# PROBLEM_NAME =  'p2'
OUT_FILE = './gen.txt'
RULES_FILE = '../rules.txt'

TURNS = 6

def random_geometry():
    """
    随机生成一段几何构造脚本：
    - 首句：triangle a b c; 或 segment a b;
    - 接着 5 轮系统调用，每轮随机第一/二/三类之一。
    返回一个字符串列表，每项是一行（或逗号分隔的两行）脚本。
    """
    lines = []
    used = set()

    # 1) 初始构造
    if random.choice(["triangle", "segment"]) == "triangle":
        lines.append("a b c = triangle a b c")
        used |= {"a", "b", "c"}
    else:
        lines.append("a b = segment a b")
        used |= {"a", "b"}

    # 变量名生成器：从未用过的小写字母里依次拿
    avail = (ch for ch in string.ascii_lowercase if ch not in used)
    def next_var():
        v = next(avail)
        used.add(v)
        return v

    # 四类调用
    calls1 = ["circle"]               # 3 点 → 点
    calls2 = ["midpoint", "mirror"]   # 2 点 → 点
    calls3 = ["on_line","on_bline","on_circle"]  # 2 点 → 线
    calls4 = ["on_tline","on_pline"]    # 3 点 → 线

    # 2) 五轮调用
    for _ in range(TURNS):
        kind = random.choice([1,2,3])
        if kind in (1,2):
            # 生成一个新点
            if kind == 1 and len(used) >= 3:
                call = random.choice(calls1)
                pts = random.sample([p for p in used], 3)
            else:
                call = random.choice(calls2)
                pts = random.sample([p for p in used], 2)
            x = next_var()
            lines.append(f"{x} = {call} {x} {' '.join(pts)}")

        else:
            # 生成 1 条或 2 条新线
            n = 2 if random.choice([True, False]) else 1
            segs = []
            x = next_var() # 这里len(used)加一了
            for _ in range(n):
                if len(used) >= 4: call = random.choice(calls3 + calls4)  # 3 点 → 线
                else: call = random.choice(calls3) # 2 点 → 线
                pts = random.sample([p for p in used if p!=x], 3 if call in calls4 else 2)
                segs.append(f"{call} {x} {' '.join(pts)}")
            lines.append(f"{x} = " + ", ".join(segs))

    return lines

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

  # goal_args = g.names2nodes(p.goal.args)
#   if not g.check(p.goal.name, goal_args):
    # logging.info('DD+AR failed to solve the problem.')
    # return False
  

  # logging.info('DD+AR successed to solve the problem.')
  # print("Yes")

  # for condition in ['perp', 'cong', 'coll']:
  #    for a in 
  # p.goal = pr.Construction.from_txt("cong a d b e")
#   count_points = alphageometry.write_solution(g, p, out_file, False)
  g.sort_conclusions()
#   print('\n'.join([' '.join(con) for con in g.all_conclusions]))
#   print("Size of all_conclutions: ", len(g.all_conclusions))

#   gh.nm.draw(
#       g.type2nodes[gh.Point],
#       g.type2nodes[gh.Line],
#       g.type2nodes[gh.Circle],
#       g.type2nodes[gh.Segment])
  return True

def main(_):
    global DEFINITIONS
    global RULES

    DEFINITIONS = pr.Definition.from_txt_file(DEFS_FILE, to_dict=True)
    RULES = pr.Theorem.from_txt_file(RULES_FILE, to_dict=True)

    for _ in range(1):
        print(f"\nTrying to generate a new geometry script in {_}th iteration.")
        # script = random_geometry()
        # script = [      # 假的
        #     'a b = segment a b',
        #     'c = mirror c a b',
        #     'd = mirror d b a',
        #     'e = on_bline e d c'
        # ]

        script = [      # 真的
            "a b c = triangle",
            "d = on_tline d b a c, on_tline d c a b",
            "e = on_line e a c, on_line e b d"
        ]

        prev_conclusions = set()
        
        print("Generated script: ",'\n'.join(script))
        # if not nm.check('para', [e, f, p, q]):
        out = False
        for i in range(2, len(script) + 1):
            try:
                problem_str = '; '.join(script[:i])
                last_line = script[i-1]
                t = last_line.split('=')[0].strip().split()[0]

                # 构造 pr.Problem 对象
                this_problem = pr.Problem.from_txt(problem_str, translate=True)
                g, _ = gh.Graph.build_problem(this_problem, DEFINITIONS)
                draw(g, this_problem, OUT_FILE)

                curr_conclusions = set(tuple(con) for con in getattr(g, 'all_conclusions', []))
                new_conclusions = curr_conclusions - prev_conclusions

                print(f'\n{i}th step\'s new conclusions:')
                print('\n'.join([' '.join(con) for con in new_conclusions]))

                for concl in new_conclusions:
                    if t not in concl:          # 找到一组同构判定下以为有辅助点的问题
                        # print("prev: ",prev_conclusions)
                        # print("new: ",new_conclusions)
                        # print("curr: ",curr_conclusions)
                        
                        this_problem = pr.Problem.from_txt(f"{problem_str} ? {' '.join(concl)}", translate=True)
                        # this_problem.goal = pr.Construction.from_txt(f"{' '.join(concl)}")
                        ddar.solve(g, RULES, this_problem, max_level=10)
                        count_points = alphageometry.write_solution(g, this_problem, '', False)
                        if len(count_points) > 0:       # 找到真的有辅助点的问题
                            problem_str = '; '.join(script[:i-1])
                            this_problem = pr.Problem.from_txt(f"{problem_str} ? {' '.join(concl)}", translate=True)
                            g, _ = gh.Graph.build_problem(this_problem, DEFINITIONS)
                            ddar.solve(g, RULES, this_problem, max_level=10)
                            goal_args = g.names2nodes(this_problem.goal.args)
                            if g.check(this_problem.goal.name, goal_args):  # 必须是原本解不出来的问题
                               out = True
                               print('假的辅助点问题')
                               break

                            with open(OUT_FILE, 'a') as f:
                                f.write(f"{problem_str} ? {' '.join(concl)}\n")
                            # alphageometry.write_solution(g, this_problem, '', True)
                            out = True
                            break
                prev_conclusions = curr_conclusions

            except Exception as e:
                print(f"Error at problem {i}: {e}")
                break
            if out:
                break

if __name__ == '__main__':
    # app.run(main)  # 输出log用这个
    main(None)

# 多线程改下面
# def run_thread(thread_id):
#     """
#     每个线程运行的主函数，动态修改 OUT_FILE 为 gen{thread_id}.txt
#     """
#     global OUT_FILE
#     OUT_FILE = f'gen{thread_id}.txt'  # 根据线程 ID 修改输出文件

#     print(f"线程 {thread_id} 开始运行，输出文件为 {OUT_FILE}")
#     main(None)  # 调用主函数

# if __name__ == '__main__':
#     num_threads = 16
#     processes = []

#     for i in range(num_threads):
#         p = multiprocessing.Process(target=run_thread, args=(i + 1,))
#         processes.append(p)
#         p.start()

#     for p in processes:
#         p.join()