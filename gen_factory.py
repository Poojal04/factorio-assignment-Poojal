#!/usr/bin/env python3
import json, random, sys

random.seed(0)

def gen():
    machines = {
        "assembler_1": {"crafts_per_min": 30},
        "chemical": {"crafts_per_min": 60}
    }
    recipes = {
        "iron_plate": {"machine":"chemical","time_s":3.2,"in":{"iron_ore":1},"out":{"iron_plate":1}},
        "copper_plate":{"machine":"chemical","time_s":3.2,"in":{"copper_ore":1},"out":{"copper_plate":1}},
        "green_circuit":{"machine":"assembler_1","time_s":0.5,"in":{"iron_plate":1,"copper_plate":3},"out":{"green_circuit":1}}
    }
    modules = {"assembler_1":{"prod":0.1,"speed":0.15},"chemical":{"prod":0.2,"speed":0.1}}
    limits = {
        "raw_supply_per_min":{"iron_ore": random.randint(2000,6000), "copper_ore": random.randint(2000,6000)},
        "max_machines":{"assembler_1": random.randint(100,400), "chemical": random.randint(100,400)}
    }
    target = {"item":"green_circuit","rate_per_min": random.choice([900,1200,1800,2400])}
    return {"machines":machines,"recipes":recipes,"modules":modules,"limits":limits,"target":target}

if __name__ == "__main__":
    sys.stdout.write(json.dumps(gen(), separators=(",",":")))
