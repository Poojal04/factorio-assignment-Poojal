import json, subprocess, sys

def run(cmd, payload):
    p = subprocess.run(
        cmd.split(),
        input=json.dumps(payload).encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if p.returncode != 0:
        # print stderr to help you debug (still prints valid JSON from the tool to stdout only)
        print(p.stderr.decode(), file=sys.stderr)
    print(p.stdout.decode())

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_samples.py \"python factory/main.py\" \"python belts/main.py\"")
        sys.exit(1)

    factory_cmd = sys.argv[1]
    belts_cmd = sys.argv[2]

    # ----- sample for factory -----
    factory_sample_input = {
      "machines": {
        "assembler_1": {"crafts_per_min": 30},
        "chemical": {"crafts_per_min": 60}
      },
      "recipes": {
        "iron_plate": {
          "machine": "chemical",
          "time_s": 3.2,
          "in": {"iron_ore": 1},
          "out": {"iron_plate": 1}
        },
        "copper_plate": {
          "machine": "chemical",
          "time_s": 3.2,
          "in": {"copper_ore": 1},
          "out": {"copper_plate": 1}
        },
        "green_circuit": {
          "machine": "assembler_1",
          "time_s": 0.5,
          "in": {"iron_plate": 1, "copper_plate": 3},
          "out": {"green_circuit": 1}
        }
      },
      "modules": {
        "assembler_1": {"prod": 0.1, "speed": 0.15},
        "chemical": {"prod": 0.2, "speed": 0.1}
      },
      "limits": {
        "raw_supply_per_min": {"iron_ore": 5000, "copper_ore": 5000},
        "max_machines": {"assembler_1": 300, "chemical": 300}
      },
      "target": {"item": "green_circuit", "rate_per_min": 1800}
    }

    # ----- sample for belts -----
    belts_sample_input = {
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

    print("=== factory ===")
    run(factory_cmd, factory_sample_input)

    print("=== belts ===")
    run(belts_cmd, belts_sample_input)
