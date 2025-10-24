#!/usr/bin/env python3
import sys, json, math
from collections import deque, defaultdict

TOL = 1e-9

class Dinic:
    def __init__(self, n):
        self.n = n
        self.head = [-1]*n
        self.to, self.cap, self.nxt = [], [], []
        self.level = [0]*n
        self.it = [0]*n

    def add_edge(self, u, v, c):
        self.to.append(v); self.cap.append(float(c)); self.nxt.append(self.head[u]); self.head[u] = len(self.to)-1
        self.to.append(u); self.cap.append(0.0);        self.nxt.append(self.head[v]); self.head[v] = len(self.to)-1

    def bfs(self, s, t):
        self.level = [-1]*self.n
        q = deque([s]); self.level[s] = 0
        while q:
            u = q.popleft()
            e = self.head[u]
            while e != -1:
                if self.cap[e] > TOL and self.level[self.to[e]] < 0:
                    self.level[self.to[e]] = self.level[u] + 1
                    q.append(self.to[e])
                e = self.nxt[e]
        return self.level[t] >= 0

    def dfs(self, u, t, f):
        if u == t: return f
        e = self.it[u]
        while e != -1:
            if self.cap[e] > TOL and self.level[self.to[e]] == self.level[u] + 1:
                ret = self.dfs(self.to[e], t, min(f, self.cap[e]))
                if ret > 0:
                    self.cap[e] -= ret
                    self.cap[e^1] += ret
                    return ret
            self.it[u] = self.nxt[e]
            e = self.it[u]
        return 0.0

    def maxflow(self, s, t):
        flow = 0.0
        INF = 1e30
        while self.bfs(s, t):
            self.it = self.head[:]
            while True:
                pushed = self.dfs(s, t, INF)
                if pushed <= TOL: break
                flow += pushed
        return flow

    def reachable_from(self, s):
        seen = [False]*self.n
        q = deque([s]); seen[s] = True
        while q:
            u = q.popleft()
            e = self.head[u]
            while e != -1:
                if self.cap[e] > TOL and not seen[self.to[e]]:
                    seen[self.to[e]] = True
                    q.append(self.to[e])
                e = self.nxt[e]
        return seen

def read_stdin():
    return json.loads(sys.stdin.read())

def belts_solve(inp):
    nodes = list(inp["nodes"])
    idx = {name:i for i,name in enumerate(nodes)}
    sink = inp["sink"]
    sources = {k: float(v) for k,v in inp["sources"].items()}
    node_caps = inp.get("node_caps", {})
    edges = list(inp["edges"])

    # node splitting (except sources/sink)
    split_in, split_out = {}, {}
    cur_nodes = nodes[:]

    def add_node(name):
        if name in idx: return idx[name]
        idx[name] = len(cur_nodes); cur_nodes.append(name); return idx[name]

    for v, cap in node_caps.items():
        if v == sink or v in sources: continue
        vin, vout = f"{v}#in", f"{v}#out"
        add_node(vin); add_node(vout)
        split_in[v] = idx[vin]; split_out[v] = idx[vout]

    transformed = []
    for v, cap in node_caps.items():
        if v == sink or v in sources: continue
        transformed.append((f"{v}#in", f"{v}#out", 0.0, float(cap)))

    for e in edges:
        u, v = e["from"], e["to"]
        lo = float(e.get("lo", 0.0)); hi = float(e.get("hi", 0.0))
        u2 = f"{u}#out" if u in split_out else u
        v2 = f"{v}#in"  if v in split_in  else v
        add_node(u2); add_node(v2)
        transformed.append((u2, v2, lo, hi))

    N = len(idx)
    Sstar, Tstar = N, N+1
    g = Dinic(N+2)

    # lower-bound transform
    demand = [0.0]*N
    edgelist = []
    for (u,v,lo,hi) in transformed:
        ui, vi = idx[u], idx[v]
        cap = hi - lo
        if cap < -1e-9:
            return {"status":"infeasible","cut_reachable":[], "deficit":{"demand_balance":0,"tight_nodes":[],"tight_edges":[]}}
        g.add_edge(ui, vi, max(0.0, cap))
        edgelist.append((ui, vi, lo, hi, len(g.to)-2))
        demand[ui] -= lo
        demand[vi] += lo

    # circulation trick: add infinite sink->source edges
    sink_node = sink if sink not in split_in else f"{sink}#in"
    sink_idx = idx[sink_node]
    for sname, sup in sources.items():
        s_node = sname if sname not in split_out else f"{sname}#out"
        s_idx = idx[s_node]
        g.add_edge(sink_idx, s_idx, 1e30)

    # encode supplies into demand vector
    total_supply = 0.0
    for sname, sup in sources.items():
        s_node = sname if sname not in split_out else f"{sname}#out"
        s_idx = idx[s_node]
        demand[s_idx] -= sup
        total_supply += sup
    demand[sink_idx] += total_supply

    total_pos = 0.0
    for i,val in enumerate(demand):
        if val > 1e-9:
            g.add_edge(Sstar, i, val)
            total_pos += val
        elif val < -1e-9:
            g.add_edge(i, Tstar, -val)

    flow = g.maxflow(Sstar, Tstar)
    if flow + 1e-6 < total_pos:
        reach = g.reachable_from(Sstar)
        cut_reach = [name for name, i_ in idx.items() if i_ < N and reach[i_]]
        tight_edges = []
        for (ui, vi, lo, hi, eidx) in edgelist:
            if ui < N and vi < N and reach[ui] and not reach[vi]:
                if g.cap[eidx] <= 1e-9:
                    # map back names
                    # (no heavy logic; just raw ids)
                    tight_edges.append({"from": [k for k,v in idx.items() if v==ui][0],
                                        "to":   [k for k,v in idx.items() if v==vi][0],
                                        "flow_needed": 0})
        deficit = total_pos - flow
        return {"status":"infeasible",
                "cut_reachable": sorted(cut_reach),
                "deficit":{"demand_balance": deficit, "tight_nodes": [], "tight_edges": tight_edges}}

    # feasible: reconstruct flows = lo + (hi-lo - residual)
    inv = {i:name for name,i in idx.items()}
    flows = []
    for (ui, vi, lo, hi, eidx) in edgelist:
        sent = (hi - lo) - g.cap[eidx]
        f = lo + sent
        u = inv[ui]; v = inv[vi]
        if u.endswith("#out"): u = u[:-4]
        if v.endswith("#in"):  v = v[:-3]
        flows.append({"from": u, "to": v, "flow": float(max(0.0,f))})

    return {"status":"ok", "max_flow_per_min": sum(sources.values()), "flows": flows}

def main():
    inp = read_stdin()
    out = belts_solve(inp)
    sys.stdout.write(json.dumps(out, separators=(",",":")))

if __name__ == "__main__":
    main()
