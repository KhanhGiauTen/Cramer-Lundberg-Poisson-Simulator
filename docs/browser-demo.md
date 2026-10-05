# Public Risk Simulator

Live demo: https://cramer-risk-lab.vercel.app

Vercel project `cramer-risk-lab`, owner `khanhgiauten`, root `web-demo`, Node 24.x. The React/Chart.js interface runs the original `cl_model.py` in a same-origin Pyodide worker. No server-side simulation, account, payment or private financial data is required.

## Model Contract

`browser_api.py` validates seven finite numeric parameters and integer seed/run counts. At most 1,000 runs, rate 100, horizon 100 and 500,000 expected claim events are allowed. It reuses `CramerLundbergModel.simulate()` and `_build_step_path()` unchanged. Random seeds increment per run. Up to 20 paths are plotted, the first 50 primary events are displayed, and the entire primary trace is downloadable.

The displayed path is the source model's **claim-epoch embedded jump chain**, not the continuously increasing premium path between claims. Paths stop at first ruin. Terminal values refer to the last embedded value, not a separately recomputed horizon surplus. Monte Carlo ruin frequency is a finite-sample observation, not an exact actuarial probability. Academic simulation only, no financial or insurance advice.

The UI preserves the last completed result when parameters change and marks it as stale. Reset does not silently replace the result. Stop terminates the worker and retry recreates it. Input, runtime and timeout errors are visible. JSON/CSV downloads use native local data-URL links.

## Build And Verification

```powershell
python -m unittest discover -s tests -v
cd web-demo
npm ci
npm run build
npm test
npm run dev -- --port 3003
```

Six Python tests cover source-model parity, reproducibility, invalid numbers, bounds/work budget, unknown fields, and first-ruin termination. `npm test` executes the same engine in Pyodide and compares it with native CPython: seed 42 has four primary events and 74 ruined runs out of 300. Floating event values match within 1e-8. This is a fixture, not a universal risk estimate.

`copy-runtime.mjs` copies pinned Pyodide assets and the current Python engine into public files. Checked-in engine copies support standalone `web-demo` CLI deployment; builds in the full repository synchronize them from the original sources. Keep source and generated copies together. The Python source is public, as in the original repository.
