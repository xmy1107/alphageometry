---
title: alphageometry复现
date: 2025-07-03 18:48:15
tags:
---



# Code

[项目链接](https://github.com/google-deepmind/alphageometry)

fixed：numericals.py	check_cyclic	(a, b, c), *ps = points => a, b, c, *ps = points

graph.py	build_problem

# Method

[论文概要](https://zhuanlan.zhihu.com/p/679166024)



# AlphaGeometry Syntax

[解读1（from知乎）](https://www.zhihu.com/question/640049082)

[解读2（from谷歌共享文档）](https://docs.google.com/document/d/1K4QspqnGFCJ9hpFyPUvaJXE7SAWbt3XRBBtyXzGhsOo/edit?tab=t.0)

[解读3（from某github项目）](https://github.com/tpgh24/ag4masses?tab=readme-ov-file#the-problem-definition-language)



原语：

`coll a b c` : points `a b c` are collinear

`cong a b c e` : segments `ab` and `cd` are congruent (length equal)

`contri a b c p q r` : triangles `abc` and `pqr` are congruent

`cyclic a b c d` : 4 points `a b c d` are cocyclic

`eqangle a b c d p q r s` : the angles between lines `ab-cd` and `pq-rs` are equal. **Note that angles have directions (signs)** so the order between `a b` and `c d` matters. `eqangle a b c d c d a b` is false. The way to think about it is, angle `ab-cd` is the angle to turn line `ab` **clockwise** so it is parallel with the line `cd`. You can use counter-clockwise as the convention too, as long as for all angles the same convention is used

`eqratio a b c d p q r s` : segment length `ab/cd = pq/rs`

`midp m a b` : point `m` is the midpoint of `a` and `b`

`para a b c d` : segments `ab` and `cd` are parallel

`perp a b c d` : segments `ab` and `cd` are perpendicular to each other

`simtri a b c p q r` : triangles `abc` and `pqr` are similar



DD推导的公式基于`rules.txt`：

```
perp A B C D, perp C D E F, ncoll A B E => para A B E F		# AB ⊥ CD, CD ⊥ EF, ABE不共线 => AB // EF
cong O A O B, cong O B O C, cong O C O D => cyclic A B C D	# OA = OB, OB = OC, OC = OD => ABCD共圆
eqangle A B P Q C D P Q => para A B C D
cyclic A B P Q => eqangle P A P B Q A Q B
......
```

所有的操作都记录在`defs.txt`中：

六行为一组：`construction, rely, deps, basics, numerics, _ = data.split('\n')`

```
angle_mirror x a b c			# 对角abc以bc为对称轴作镜像反转
x : a b c x						# x由abcx决定
a b c = ncoll a b c				# abc需要满足的条件
x : eqangle b a b c b c b x		# ∠abc = ∠xbc
amirror a b c					# 另一种表示

circle x a b c					# 定义x为由abc确定的圆的圆心
x : a b c
a b c = ncoll a b c
x : cong x a x b, cong x b x c	# xa = xb = xc
bline a b, bline a c			# bline代表中垂线，这句是第一句的另一种表示
......
```

点+ '=' + 1-2个操作 => 点的构造，点的构造间用分号分隔。以一道证明垂心的题举例：

```
orthocenter
a b c = triangle; h = on_tline b a c, on_tline c a b ? perp a h b c
# abc为一三角形；hb ⊥ ac 并且 hc ⊥ ab。证明ha垂直bc
```

tips：

空格敏感，出现一个多余空格，哪怕不是在当前题目中，也会无法运行

# Config

[issue：GPU用不了](https://github.com/google-deepmind/alphageometry/issues/101)

`meliad`库需要`git checkout e8af054`



# Data Generation

