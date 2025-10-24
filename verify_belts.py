#!/usr/bin/env python3
import sys, json

TOL = 1e-9

def main():
    out = json.loads(sys.stdin.read())
    if out.get("status") == "ok":
        assert "flows" in out
        assert isinstance(out["flows"], list)
        # Each flow entry must have from,to,flow
        for e in out["flows"]:
            assert "from" in e and "to" in e and "flow" in e
            assert e["flow"] >= -TOL
    else:
        assert "cut_reachable" in out
        assert "deficit" in out
    sys.stdout.write(json.dumps({"status":"ok"}, separators=(",",":")))

if __name__ == "__main__":
    main()
