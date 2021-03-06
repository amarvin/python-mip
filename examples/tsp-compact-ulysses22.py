"""Example that solves the Traveling Salesman Problem using the simple compact
formulation presented in Miller, C.E., Tucker, A.W and Zemlin, R.A. "Integer
Programming Formulation of Traveling Salesman Problems". Journal of the ACM
7(4). 1960."""

from typing import Tuple
from math import floor, cos, acos
from itertools import product
from sys import stdout as out
from mip import Model, xsum, minimize, BINARY

# constants as stated in TSPlib doc
# https://www.iwr.uni-heidelberg.de/groups/comopt/software/TSPLIB95/tsp95.pdf
PI = 3.141592
RRR = 6378.388

def rad(val: float) -> float:
    """conver to radians"""
    mult = 1.0
    if val < 0.0:
        mult = -1.0
        val = abs(val)

    deg = float(floor(val))
    minute = val - deg
    return (PI * (deg + 5*minute/3)/180)*mult

def dist(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """computes geographical distance"""
    q1 = cos(p1[1] - p2[1])
    q2 = cos(p1[0] - p2[0])
    q3 = cos(p1[0] + p2[0])
    return int(floor(RRR*acos(0.5*((1.0+q1)*q2-(1.0-q1)*q3))+1.0))


# coordinates of ulysses22 tsplib instance
coord = [(38.24, 20.42), (39.57, 26.15), (40.56, 25.32), (36.26, 23.12),
         (33.48, 10.54), (37.56, 12.19), (38.42, 13.11), (37.52, 20.44),
         (41.23, 09.10), (41.17, 13.05), (36.08, -5.21), (38.47, 15.13),
         (38.15, 15.35), (37.51, 15.17), (35.49, 14.32), (39.36, 19.56),
         (38.09, 24.36), (36.09, 23.00), (40.44, 13.57), (40.33, 14.15),
         (40.37, 14.23), (37.57, 22.56)]

# latitude and longitude
coord = [(rad(x), rad(y)) for (x, y) in coord]

# distances in an upper triangular matrix

# number of nodes and list of vertices
n, V = len(coord), set(range(len(coord)))

# distances matrix
c = [[0 if i == j
      else dist(coord[i], coord[j]) for j in V] for i in V]

model = Model()

# binary variables indicating if arc (i,j) is used on the route or not
x = [[model.add_var(var_type=BINARY) for j in V] for i in V]

# continuous variable to prevent subtours: each city will have a
# different sequential id in the planned route except the first one
y = [model.add_var() for i in V]

# objective function: minimize the distance
model.objective = minimize(xsum(c[i][j]*x[i][j] for i in V for j in V))

# constraint : leave each city only once
for i in V:
    model += xsum(x[i][j] for j in V - {i}) == 1

# constraint : enter each city only once
for i in V:
    model += xsum(x[j][i] for j in V - {i}) == 1

# subtour elimination
for (i, j) in product(V - {0}, V - {0}):
    if i != j:
        model += y[i] - (n+1)*x[i][j] >= y[j]-n

# optimizing
model.threads = 4
model.optimize(max_seconds=100)

# checking if a solution was found
if model.num_solutions:
    out.write('route with total distance %g found: %s'
              % (model.objective_value, 0))
    nc = 0
    while True:
        nc = [i for i in V if x[nc][i].x >= 0.99][0]
        out.write(' -> %s' % nc)
        if nc == 0:
            break
    out.write('\n')

# sanity tests
from mip import OptimizationStatus
if model.status == OptimizationStatus.OPTIMAL:
    assert round(model.objective_value) == 7013
elif model.status == OptimizationStatus.FEASIBLE:
    assert round(model.objective_value) >= 7013
else:
    assert model.objective_bound <= 7013 + 1e-7
