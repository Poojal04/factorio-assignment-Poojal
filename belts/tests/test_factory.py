import json, subprocess, os, pathlib

FACT_CMD = os.environ.get("FACTORY_CMD", "python factory/main.py")
ROOT = pathlib.Path(__file__).resolve().parents[1]

def run_case(payload):
    p = subprocess.run(FACT_CMD.split(), input=json.dumps(payload).encode(),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(ROOT))
    assert p.returncode == 0, p.stderr.decode()
    return json.loads(p.stdout.decode())

def test_sample():
    payload = {
      "machines": {"assembler_1":{"crafts_per_min":30},"chemical":{"crafts_per_min":60}},
      "recipes": {
        "iron_plate":{"machine":"chemical","time_s":3.2,"in":{"iron_ore":1},"out":{"iron_plate":1}},
        "copper_plate":{"machine":"chemical","time_s":3.2,"in":{"copper_ore":1},"out":{"copper_plate":1}},
        "green_circuit":{"machine":"assembler_1","time_s":0.5,"in":{"iron_plate":1,"copper_plate":3},"out":{"green_circuit":1}}
      },
      "modules": {"assembler_1":{"prod":0.1,"speed":0.15},"chemical":{"prod":0.2,"speed":0.1}},
      "limits": {"raw_supply_per_min":{"iron_ore":5000,"copper_ore":5000},"max_machines":{"assembler_1":300,"chemical":300}},
      "target": {"item":"green_circuit","rate_per_min":1800}
    }
    out = run_case(payload)
    assert out["status"] in ("ok","infeasible")
    if out["status"] == "ok":
        assert abs(out["per_recipe_crafts_per_min"]["green_circuit"] - 1800) < 1e-6
        for v in out["raw_consumption_per_min"].values():
            assert v >= -1e-6
