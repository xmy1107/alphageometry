import random
import string

TURNS = 7

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

    # 三类调用
    calls1 = ["circle"]               # 3 点 → 点
    calls2 = ["midpoint", "mirror"]   # 2 点 → 点
    calls3 = ["on_line","on_tline","on_bline","on_circle","on_pline"]  # 2 点 → 线

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
            x = next_var()
            for _ in range(n):
                call = random.choice(calls3)
                pts = random.sample([p for p in used if p!=x], 2)
                segs.append(f"{call} {x} {' '.join(pts)}")
            lines.append(f"{x} = " + ", ".join(segs))

    return lines

if __name__ == "__main__":
    script = random_geometry()
    file_path = './gen.txt'
    with open(file_path, 'w') as f:
        for i in range(1, len(script)):
            if i!=1: f.write('\n')
            problemstr = f"p{i}\n" + '; '.join(script[:i])
            f.write(problemstr)