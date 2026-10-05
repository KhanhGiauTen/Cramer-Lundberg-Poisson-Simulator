import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { loadPyodide } from "pyodide";

const root = fileURLToPath(new URL("../../", import.meta.url));
const params = {
  u: 20,
  c: 15,
  lambda_rate: 3,
  mu_claim: 4,
  T: 10,
  runs: 300,
  seed: 42,
};
const expected = JSON.parse(
  execFileSync(
    "python",
    [
      "-c",
      `from browser_api import simulate_public; print(simulate_public('${JSON.stringify(params)}'))`,
    ],
    { cwd: root, encoding: "utf8" },
  ),
);
const python = await loadPyodide({
  indexURL: fileURLToPath(new URL("../node_modules/pyodide/", import.meta.url)),
});
for (const file of ["cl_model.py", "browser_api.py"])
  python.FS.writeFile(
    file,
    await readFile(new URL(`../../${file}`, import.meta.url), "utf8"),
  );
python.runPython("from browser_api import simulate_public");
python.globals.set("params_json", JSON.stringify(params));
const raw = python.runPython("simulate_public(params_json)"),
  actual = JSON.parse(raw);
assert.equal(python.runPython("simulate_public(params_json)"), raw);
assert.equal(actual.ruinedRuns, expected.ruinedRuns);
assert.equal(actual.primary.events.length, expected.primary.events.length);
for (let i = 0; i < actual.primary.events.length; i++) {
  for (const key of ["surplus", "event_time", "claim_size"])
    assert.ok(
      Math.abs(
        actual.primary.events[i][key] - expected.primary.events[i][key],
      ) < 1e-8,
      `Mismatch at event ${i}: ${key}`,
    );
}
console.log(
  `PASS native Python / Pyodide parity: ${actual.primary.events.length} primary events, ${actual.ruinedRuns}/300 ruined runs; deterministic seed`,
);
