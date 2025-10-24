"""
A tiny deterministic two-phase simplex LP solver.
min c^T x  s.t.  A_eq x = b_eq,  A_ub x <= b_ub,  x >= 0
Uses Bland's rule for anti-cycling. Small/medium LPs only.

Returns: (status, x, obj) with status in {"optimal","infeasible","unbounded"}
"""
from typing import List, Tuple
import math

EPS = 1e-10

def simplex_minimize(c, A_eq, b_eq, A_ub, b_ub):
    import copy
    m_eq = len(A_eq)
    n = len(c)
    m_ub = len(A_ub)

    # Build Phase I tableau with artificial vars for equalities and slacks for <=
    T_rows = []
    rhs = []

    # equalities + artificials
    for i in range(m_eq):
        row = A_eq[i][:] + [0.0]*m_ub + [0.0]*m_eq
        row[n + m_ub + i] = 1.0
        T_rows.append(row)
        rhs.append(b_eq[i])

    # inequalities + slacks
    for i in range(m_ub):
        row = A_ub[i][:] + [0.0]*m_ub + [0.0]*m_eq
        row[n + i] = 1.0
        T_rows.append(row)
        rhs.append(b_ub[i])

    var_total = n + m_ub + m_eq
    m_total = len(T_rows)

    # Phase I objective: minimize sum(artificials)
    c1 = [0.0]*(n + m_ub) + [1.0]*m_eq

    # Initial basis: artificials for eq rows; slacks for ub rows
    basis = []
    for i in range(m_eq):
        basis.append(n + m_ub + i)
    for i in range(m_ub):
        basis.append(n + i)

    # Build tableau with objective row reduced by current basis
    def build_tableau(rows, rhs, obj):
        A = [r[:] + [rhs_i] for r, rhs_i in zip(rows, rhs)]
        obj_row = obj[:] + [0.0]
        for r, bvar in enumerate(basis):
            coef = obj_row[bvar]
            if abs(coef) > EPS:
                rr = A[r]
                for k in range(len(obj_row)):
                    obj_row[k] -= coef * rr[k]
        A.append(obj_row)
        return A

    tableau = build_tableau(T_rows, rhs, c1)

    def pivot(col, row):
        piv = tableau[row][col]
        if abs(piv) < EPS: return False
        inv = 1.0/piv
        # normalize pivot row
        for j in range(len(tableau[row])):
            tableau[row][j] *= inv
        # eliminate
        for i in range(len(tableau)):
            if i == row: continue
            factor = tableau[i][col]
            if abs(factor) > EPS:
                for j in range(len(tableau[i])):
                    tableau[i][j] -= factor * tableau[row][j]
        basis[row] = col
        return True

    def choose_entering():
        last = tableau[-1]
        for j in range(len(last)-1):
            if last[j] < -1e-12:  # negative reduced cost -> enter (min)
                return j
        return None

    def choose_leaving(col):
        best = None
        best_row = None
        for i in range(len(tableau)-1):
            a = tableau[i][col]
            if a > 1e-12:
                ratio = tableau[i][-1] / a
                if ratio < -1e-12:  # skip negative rhs
                    continue
                if (best is None) or (ratio < best - 1e-12) or (abs(ratio - best) <= 1e-12 and basis[i] > basis[best_row]):
                    best = ratio
                    best_row = i
        return best_row

    # Phase I
    while True:
        col = choose_entering()
        if col is None:
            break
        row = choose_leaving(col)
        if row is None:
            return ("unbounded", None, None)
        pivot(col, row)

    if tableau[-1][-1] > 1e-8:
        return ("infeasible", None, None)

    # Phase II: rebuild constraints without artificials
    # Reconstruct original constraints (same order)
    T_rows2 = []
    rhs2 = []
    for i in range(m_eq):
        T_rows2.append(A_eq[i][:] + [0.0]*m_ub)
        rhs2.append(b_eq[i])
    for i in range(m_ub):
        row = A_ub[i][:] + [0.0]*m_ub
        row[n + i] = 1.0
        T_rows2.append(row)
        rhs2.append(b_ub[i])

    # New basis: slacks for ub rows; unknown for eq rows
    basis = [None]*m_eq + [n+i for i in range(m_ub)]

    tableau = [r[:] + [rhs2[i]] for i, r in enumerate(T_rows2)]
    c2 = c[:] + [0.0]*m_ub
    obj_row = c2[:] + [0.0]
    for r, bvar in enumerate(basis):
        if bvar is not None:
            coef = obj_row[bvar]
            if abs(coef) > EPS:
                rr = tableau[r]
                for k in range(len(obj_row)):
                    obj_row[k] -= coef * rr[k]
    tableau.append(obj_row)

    # drive unknown eq rows to a basis
    for i in range(len(basis)):
        if basis[i] is None:
            for j in range(n+m_ub):
                if (j not in basis) and abs(tableau[i][j]) > 1e-9:
                    pivot(j, i)
                    break

    # Phase II simplex
    while True:
        col = choose_entering()
        if col is None:
            break
        row = choose_leaving(col)
        if row is None:
            return ("unbounded", None, None)
        pivot(col, row)

    # extract solution
    var_total = n + m_ub
    x = [0.0]*var_total
    for i in range(len(basis)):
        b = basis[i]
        if b is not None and b < var_total:
            x[b] = tableau[i][-1]
    obj = tableau[-1][-1]
    for i in range(len(x)):
        if -1e-9 < x[i] < 0:
            x[i] = 0.0
    return ("optimal", x[:n], obj)
