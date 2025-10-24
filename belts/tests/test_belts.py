import json, subprocess, os, pathlib

BELT_CMD = os.environ.get("BELTS_CMD", "python belts/main.py")
ROOT = pathlib.Path(__file__).resolve().parents[1]

def run_case(payload):
    p = subprocess.run(BELT_CMD.split(), input=json.dumps(payload).encode(),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(ROOT))
    assert p.returncode == 0, p.stderr.decode()
    return json.loads(p.stdout.decode())

def test_basic_feasible():
    payload = {
        "nodes": ["s1","s2","a","b","c","sink"],
        "edges": [
            {"from":"s1","to":"a","lo":0,"hi":900},
            {"from":"a","to":"b","lo":0,"hi":900},
            {"from":"b","to":"sink","lo":0,"hi":900},
            {"from":"s2","to":"a","lo":0,"hi":600},
            {"from":"a","to":"c","lo":0,"hi":600},
            {"from":"c","to":"sink","lo":0,"hi":600}
        ],
        "sources": {"s1":900, "s2":600},
        "sink": "sink",
        "node_caps": {"a": 2000}
    }
    out = run_case(payload)
    assert out["status"] == "ok"
    assert out["max_flow_per_min"] == 1500

def test_infeasible():
    payload = {
        "nodes": ["s1","a","sink"],
        "edges": [
            {"from":"s1","to":"a","lo":0,"hi":100},
            {"from":"a","to":"sink","lo":0,"hi":50}
        ],
        "sources": {"s1":80},
        "sink": "sink",
        "node_caps": {}
    }
    out = run_case(payload)
    assert out["status"] == "infeasible"
    assert "cut_reachable" in out
