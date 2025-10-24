#!/usr/bin/env python3
import sys, json, math
from collections import defaultdict, OrderedDict
from lp_solver import simplex_minimize

TOL = 1e-9

def read_stdin():
    return json.loads(sys.stdin.read())

def compute_effective_rates(inp):
    machines = inp["machines"]
    modules = inp.get("modules", {})
    recipes = inp["recipes"]

    eff = {}
    prod_by_machine = {}
    speed_by_machine = {}
    for m, info in machines.items():
        spd = modules.get(m, {}).get("speed", 0.0)
        prod = modules.get(m, {}).get("prod", 0.0)
        prod_by_machine[m] = prod
        speed_by_machine[m] = spd

    for rname, r in recipes.items():
        m = r["machine"]
        base_cpm = machines[m]["crafts_per_min"]
        spd_mult = 1.0 + speed_by_machine.get(m, 0.0)
        time_s = float(r["time_s"])
        eff[rname] = base_cpm * spd_mult * 60.0 / time_s
    return eff, prod_by_machine

def classify_items(inp):
    recipes = inp["recipes"]
    items_in = defaultdict(float)
    items_out = defaultdict(float)
    for rname, r in recipes.items():
        for k,v in r.get("in", {}).items():
            items_in[k] += v
        for k,v in r.get("out", {}).items():
            items_out[k] += v
    all_items = set(items_in) | set(items_out)
    produced = set(items_out)
    consumed = set(items_in)
    raw_items = consumed - produced
    intermediates = (all_items - raw_items)
    return all_items, raw_items, intermediates

def build_balance_matrices(inp):
    recipes = inp["recipes"]
    (all_items, raw_items, intermediates) = classify_items(inp)
    target_item = inp["target"]["item"]
    target_rate = float(inp["target"]["rate_per_min"])
    eff, prod_by_machine = compute_effective_rates(inp)

    rnames = sorted(recipes.keys())
    r_index = {r:i for i,r in enumerate(rnames)}
    raw_list = sorted(raw_items)

    idx_x_end = len(rnames)
    idx_c_start = idx_x_end
    idx_c_end = idx_c_start + len(raw_list)
    y_idx = idx_c_end
    nvars = y_idx + 1

    A_eq = []
    b_eq = []

    # intermediates balance = 0 (exclude target)
    for item in sorted(intermediates):
        if item == target_item:
            continue
        row = [0.0]*nvars
        for rname, r in recipes.items():
            i = r_index[rname]
            m = r["machine"]
            prod = 1.0 + prod_by_machine.get(m, 0.0)
            for k,v in r.get("out", {}).items():
                if k == item:
                    row[i] += v * prod
            for k,v in r.get("in", {}).items():
                if k == item:
                    row[i] -= v
        A_eq.append(row)
        b_eq.append(0.0)

    # target balance = y * target_rate
    row = [0.0]*nvars
    for rname, r in recipes.items():
        i = r_index[rname]
        m = r["machine"]
        prod = 1.0 + prod_by_machine.get(m, 0.0)
        for k,v in r.get("out", {}).items():
            if k == target_item:
                row[i] += v * prod
        for k,v in r.get("in", {}).items():
            if k == target_item:
                row[i] -= v
    row[y_idx] = -target_rate
    A_eq.append(row)
    b_eq.append(0.0)

    # raw items: sum(out-in) + c_i = 0
    for j,item in enumerate(raw_list):
        row = [0.0]*nvars
        for rname, r in recipes.items():
            i = r_index[rname]
            m = r["machine"]
            prod = 1.0 + prod_by_machine.get(m, 0.0)
            for k,v in r.get("out", {}).items():
                if k == item:
                    row[i] += v * prod
            for k,v in r.get("in", {}).items():
                if k == item:
                    row[i] -= v
        row[idx_c_start + j] = 1.0
        A_eq.append(row)
        b_eq.append(0.0)

    A_ub = []
    b_ub = []

    # raw caps: c_i <= cap
    raw_caps = inp.get("limits", {}).get("raw_supply_per_min", {})
    for j,item in enumerate(raw_list):
        cap = float(raw_caps.get(item, float('inf')))
        if math.isfinite(cap):
            row = [0.0]*nvars
            row[idx_c_start + j] = 1.0
            A_ub.append(row)
            b_ub.append(cap)

    # machine caps: sum x_r / eff_r <= max_machines[m]
    max_m = inp.get("limits", {}).get("max_machines", {})
    by_machine = defaultdict(list)
    for rname, r in recipes.items():
        by_machine[r["machine"]].append(rname)
    for m, rlist in sorted(by_machine.items()):
        cap = float(max_m.get(m, float('inf')))
        if math.isfinite(cap):
            row = [0.0]*nvars
            for rname in rlist:
                i = r_index[rname]
                row[i] = 1.0 / (eff[rname] if eff[rname] > 0 else 1e30)
            A_ub.append(row)
            b_ub.append(cap)

    return (rnames, raw_list, A_eq, b_eq, A_ub, b_ub, y_idx, eff)

def run_max_rate(inp):
    rnames, raw_list, A_eq, b_eq, A_ub, b_ub, y_idx, eff = build_balance_matrices(inp)
    nvars = len(A_eq[0])
    c = [0.0]*nvars
    c[y_idx] = -1.0  # maximize y
    status, x, obj = simplex_minimize(c, A_eq, b_eq, A_ub, b_ub)
    if status != "optimal":
        return status, None, None, None, None, None
    return "optimal", x, -obj, rnames, raw_list, eff

def run_min_machines(inp):
    rnames, raw_list, A_eq, b_eq, A_ub, b_ub, y_idx, eff = build_balance_matrices(inp)
    nvars = len(A_eq[0])
    # add y <= 1 and -y <= -1
    row1 = [0.0]*nvars; row1[y_idx] = 1.0
    row2 = [0.0]*nvars; row2[y_idx] = -1.0
    A_ub2 = A_ub + [row1, row2]
    b_ub2 = b_ub + [1.0, -1.0]
    c = [0.0]*nvars
    for idx, rname in enumerate(rnames):
        c[idx] = 1.0 / (eff[rname] if eff[rname] > 0 else 1e30) + 1e-12*(idx+1)
    status, x, obj = simplex_minimize(c, A_eq, b_eq, A_ub2, b_ub2)
    return status, x, obj, rnames, raw_list, eff

def main():
    inp = read_stdin()
    status, x, maxy, rnames, raw_list, eff = run_max_rate(inp)
    target_rate = float(inp["target"]["rate_per_min"])

    if status != "optimal":
        out = {"status":"infeasible","max_feasible_target_per_min":0.0,"bottleneck_hint":["LP failed"]}
        sys.stdout.write(json.dumps(out, separators=(",",":"))); return

    if maxy < 1.0 - 1e-9:
        hints = []
        limits = inp.get("limits", {})
        max_m = limits.get("max_machines", {})
        recipes = inp["recipes"]
        from collections import defaultdict
        used = defaultdict(float)
        for i, rname in enumerate(rnames):
            m = recipes[rname]["machine"]
            used[m] += x[i] / (eff[rname] if eff[rname] > 0 else 1e30)
        for m, cap in max_m.items():
            if used[m] >= cap - 1e-7:
                hints.append(f"{m} cap")
        raw_caps = limits.get("raw_supply_per_min", {})
        for j,item in enumerate(raw_list):
            c_i = x[len(rnames)+j]
            cap = float(raw_caps.get(item, float('inf')))
            if math.isfinite(cap) and c_i >= cap - 1e-7:
                hints.append(f"{item} supply")
        out = {"status":"infeasible",
               "max_feasible_target_per_min": maxy*target_rate,
               "bottleneck_hint": sorted(list(dict.fromkeys(hints)))}
        sys.stdout.write(json.dumps(out, separators=(",",":"))); return

    status2, x2, obj2, rnames, raw_list, eff = run_min_machines(inp)
    if status2 != "optimal":
        x2 = x  # fallback feasible

    recipes = inp["recipes"]
    per_recipe = OrderedDict()
    per_machine = defaultdict(float)
    raw_use = OrderedDict()

    for i, rname in enumerate(rnames):
        per_recipe[rname] = float(x2[i])
        m = recipes[rname]["machine"]
        per_machine[m] += x2[i] / (eff[rname] if eff[rname] > 0 else 1e30)

    for j,item in enumerate(raw_list):
        raw_use[item] = float(x2[len(rnames)+j])

    out = {
        "status":"ok",
        "per_recipe_crafts_per_min": per_recipe,
        "per_machine_counts": {k: float(per_machine[k]) for k in sorted(per_machine.keys())},
        "raw_consumption_per_min": raw_use
    }
    sys.stdout.write(json.dumps(out, separators=(",",":")))

if __name__ == "__main__":
    main()
