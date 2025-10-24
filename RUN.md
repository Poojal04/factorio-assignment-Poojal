# RUN.md — Quick Guide

## Run Samples
```bash
cd part2_assignment
python run_samples.py "python factory/main.py" "python belts/main.py"

Run Individual Tools

Factory

python factory/main.py < input.json > output.json


Belts

python belts/main.py < graph.json > flow.json

Run Tests
FACTORY_CMD="python factory/main.py" BELTS_CMD="python belts/main.py" pytest -q

Notes

Input via stdin, output as single JSON on stdout.

No extra prints or logs.

Execution ≤ 2 seconds per case.