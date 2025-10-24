#!/usr/bin/env python3
import json, random, sys
random.seed(0)

def gen():
    nodes = ["s1","s2","a","b","c","sink"]
    edges = [
        {"from":"s1","to":"a","lo":0,"hi":random.randint(500,1000)},
        {"from":"a","to":"b","lo":0,"hi":random.randint(500,1000)},
        {"from":"b","to":"sink","lo":0,"hi":random.randint(500,1000)},
        {"from":"s2","to":"a","lo":0,"hi":random.randint(300,800)},
        {"from":"a","to":"c","lo":0,"hi":random.randint(300,800)},
        {"from":"c","to":"sink","lo":0,"hi":random.randint(300,800)},
    ]
    sources = {"s1": random.randint(400,900), "s2": random.randint(300,700)}
    node_caps = {"a": random.randint(1000,2200)}
    sink = "sink"
    return {"nodes":nodes,"edges":edges,"sources":sources,"sink":sink,"node_caps":node_caps}

if __name__ == "__main__":
    sys.stdout.write(json.dumps(gen(), separators=(",",":")))
