"""Bounded JSON adapter; the browser runs the original Python model unchanged."""

import json
import math
from dataclasses import asdict
from cl_model import CramerLundbergModel

LIMITS = {"u": (0,100000), "c": (.01,10000), "lambda_rate": (.01,100),
          "mu_claim": (.01,10000), "T": (.1,100), "runs": (1,1000), "seed": (0,2147483647)}


def simulate_public(raw):
    params = json.loads(raw)
    if not isinstance(params, dict) or set(params) != set(LIMITS):
        raise ValueError("Expected the seven simulation parameters")
    for key, (low, high) in LIMITS.items():
        value = params[key]
        if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"Invalid {key}: expected {low} to {high}")
    if any(int(params[key]) != params[key] for key in ("runs", "seed")):
        raise ValueError("Runs and seed must be integers")
    if params["lambda_rate"] * params["T"] * params["runs"] > 500000:
        raise ValueError("Reduce rate, horizon or runs: the expected-event budget is 500,000")
    paths, terminal, ruined = [], [], 0
    primary = None
    for index in range(int(params["runs"])):
        model = CramerLundbergModel(params["u"],params["c"],params["lambda_rate"],params["mu_claim"],params["T"],int(params["seed"])+index)
        result = model.simulate()
        ruined += int(result.ruined)
        final = result.events[-1].surplus if result.events else params["u"]
        terminal.append(final)
        if index < 20:
            times, values = model._build_step_path(result)
            paths.append({"times":times,"values":values,"ruined":result.ruined})
        if index == 0:
            primary = {"events":[asdict(event) for event in result.events],"ruinTime":result.ruin_time}
    return json.dumps({"parameters":params,"paths":paths,"terminal":terminal,"ruinedRuns":ruined,
                       "ruinFraction":ruined/params["runs"],"primary":primary,
                       "scope":"Claim-epoch embedded jump chain; paths stop at first ruin. Academic simulation, not financial advice."},allow_nan=False)
