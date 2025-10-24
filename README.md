# ERP.AI – Part 2 (Factory Steady State & Bounded Belts)

Two deterministic CLI tools that **read JSON from stdin** and **write JSON to stdout** (no extra prints/logs):

- `factory/main.py` — steady-state production with modules, raw caps, machine caps, and cycles. Finds a feasible plan for the target rate, then minimizes total machines.
- `belts/main.py` — bounded max-flow with **lower bounds** and **node throughput caps**; returns a valid flow or an infeasibility certificate.

Both complete in ≤2s on typical laptop inputs provided for assessment.

---

## 1) Factory — Modeling & Numerics

### Variables
- `x_r ≥ 0` — crafts/min for each recipe `r`.
- `c_i ≥ 0` — net consumption/min for each **raw** item `i`.
- `y ≥ 0` — scalar that scales the requested target rate (Phase A only).

### Effective craft rates (modules per machine type)
For recipe `r` on machine type `m`:

- `base_cpm = machines[m].crafts_per_min`
- `speed_mult = 1 + modules[m].speed   (default 0)`
- `eff_crafts_per_min(r) = base_cpm * speed_mult * 60 / time_s(r)`

**Productivity** multiplies outputs only: every `out_r[i]` is scaled by `(1 + modules[m].prod)`. Inputs are not scaled.

### Steady-state balances
For each item `i`:

- **Intermediates (including cyclic/byproduct chains)**  
  `Σ_r out_r[i]*(1+prod_m)*x_r − Σ_r in_r[i]*x_r = 0`

- **Target item `t`**  
  `Σ_r out_r[t]*(1+prod_m)*x_r − Σ_r in_r[t]*x_r = y * target_rate`

- **Raw items `i`**  
  `Σ_r out_r[i]*(1+prod_m)*x_r − Σ_r in_r[i]*x_r + c_i = 0` with `0 ≤ c_i ≤ cap_i`.  
  (Net consumption only; bounded by raw supply.)

