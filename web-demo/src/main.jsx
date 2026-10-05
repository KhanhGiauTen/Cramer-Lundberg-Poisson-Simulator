import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Chart, registerables } from "chart.js";
import {
  ArrowLeft,
  ArrowUpRight,
  Download,
  LoaderCircle,
  Play,
  RotateCcw,
  Square,
  TrendingUp,
} from "lucide-react";
import "./styles.css";
Chart.register(...registerables);

const DEFAULT = {
  u: 20,
  c: 15,
  lambda_rate: 3,
  mu_claim: 4,
  T: 10,
  runs: 300,
  seed: 42,
};
const FIELDS = [
  ["u", "Initial capital", 0, 100000, 0.5],
  ["c", "Premium rate", 0.01, 10000, 0.01],
  ["lambda_rate", "Claim arrival rate", 0.01, 100, 0.01],
  ["mu_claim", "Mean claim size", 0.01, 10000, 0.01],
  ["T", "Time horizon", 0.1, 100, 0.1],
  ["runs", "Simulation runs", 1, 1000, 1],
  ["seed", "Random seed", 0, 2147483647, 1],
];
const dataUrl = (value) =>
  `data:application/json;charset=utf-8,${encodeURIComponent(JSON.stringify(value, null, 2))}`;

function PathChart({ result, mode }) {
  const canvas = useRef(null);
  useEffect(() => {
    if (!result) return;
    const paths = mode === "single" ? result.paths.slice(0, 1) : result.paths;
    const datasets = paths.map((path, index) => ({
      label: `Path ${index + 1}${path.ruined ? " / ruin" : ""}`,
      data: path.times.map((x, i) => ({ x, y: path.values[i] })),
      stepped: "after",
      borderColor:
        index === 0 ? "#087f66" : path.ruined ? "#c46b7b" : "#76a3ce",
      borderWidth: index === 0 ? 2.5 : 1,
      pointRadius: 0,
    }));
    datasets.push({
      label: "Ruin boundary",
      data: [
        { x: 0, y: 0 },
        { x: result.parameters.T, y: 0 },
      ],
      borderColor: "#b8364f",
      borderDash: [5, 5],
      borderWidth: 1,
      pointRadius: 0,
    });
    const chart = new Chart(canvas.current, {
      type: "line",
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: matchMedia("(prefers-reduced-motion: reduce)").matches
            ? 0
            : 250,
        },
        parsing: false,
        scales: {
          x: {
            type: "linear",
            min: 0,
            max: result.parameters.T,
            title: { display: true, text: "Time" },
            grid: { color: "#eef0f2" },
          },
          y: {
            title: { display: true, text: "Claim-epoch surplus" },
            grid: { color: "#eef0f2" },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: { mode: "nearest", intersect: false },
        },
      },
    });
    return () => chart.destroy();
  }, [result, mode]);
  return (
    <div className="plot">
      <canvas
        ref={canvas}
        role="img"
        aria-label={
          mode === "single"
            ? "Seeded claim-epoch surplus path"
            : "Twenty seeded surplus paths"
        }
      />
    </div>
  );
}

function App() {
  const [params, setParams] = useState({ ...DEFAULT }),
    [result, setResult] = useState(null),
    [busy, setBusy] = useState(false),
    [status, setStatus] = useState("Ready to run the Python model."),
    [error, setError] = useState(""),
    [mode, setMode] = useState("single"),
    [seconds, setSeconds] = useState(null);
  const worker = useRef(null),
    timeout = useRef(null);
  useEffect(
    () => () => {
      worker.current?.terminate();
      clearTimeout(timeout.current);
    },
    [],
  );
  function stop() {
    worker.current?.terminate();
    worker.current = null;
    clearTimeout(timeout.current);
    setBusy(false);
    setStatus("Simulation stopped.");
  }
  function run(event) {
    event?.preventDefault();
    setError("");
    setBusy(true);
    setStatus("Starting Python worker...");
    if (!worker.current) {
      worker.current = new Worker(
        new URL("./simulation.worker.js", import.meta.url),
        { type: "module" },
      );
      worker.current.onmessage = ({ data }) => {
        if (data.type === "status") setStatus(data.text);
        else {
          clearTimeout(timeout.current);
          setBusy(false);
          if (data.type === "result") {
            setResult(data.result);
            setSeconds(data.seconds);
            setStatus("Simulation complete.");
          } else {
            setError(data.text);
            setStatus("Parameters or runtime need attention.");
          }
        }
      };
      worker.current.onerror = () => {
        stop();
        setError("Python worker failed to start. Reload and retry.");
      };
    }
    worker.current.postMessage(params);
    timeout.current = setTimeout(() => {
      stop();
      setError("Simulation timed out. Reduce the run count and retry.");
    }, 120000);
  }
  const changed =
    result &&
    Object.keys(DEFAULT).some((key) => params[key] !== result.parameters[key]);
  const csv = result
    ? "data:text/csv;charset=utf-8," +
      encodeURIComponent(
        [
          "index,event_time,waiting_time,claim_size,premium_income,surplus",
          ...result.primary.events.map((e) =>
            [
              e.index,
              e.event_time,
              e.waiting_time,
              e.claim_size,
              e.premium_income,
              e.surplus,
            ].join(","),
          ),
        ].join("\n"),
      )
    : undefined;
  return (
    <>
      <header>
        <a
          className="brand"
          href="https://khanh-portfolio-ochre.vercel.app/projects/cramer-lundberg"
        >
          <TrendingUp size={21} />
          Risk Lab
        </a>
        <nav>
          <a href="https://khanh-portfolio-ochre.vercel.app/projects/cramer-lundberg">
            <ArrowLeft size={15} />
            Portfolio
          </a>
          <a
            href="https://github.com/KhanhGiauTen/Cramer-Lundberg-Poisson-Simulator"
            target="_blank"
            rel="noreferrer"
          >
            Source
            <ArrowUpRight size={15} />
          </a>
        </nav>
      </header>
      <main>
        <div className="heading">
          <div>
            <p className="eyebrow">COMPOUND POISSON / SEEDED PYTHON MODEL</p>
            <h1>Cramer-Lundberg Risk Simulator</h1>
          </div>
          <span className="engine">Original Python / Pyodide</span>
        </div>
        <p className="notice">
          <strong>Academic simulation only.</strong> Simplified exponential
          waiting times and claims; not financial or insurance advice. Paths
          stop at first ruin.
        </p>
        <div className="workspace">
          <form className="controls" onSubmit={run}>
            <div className="section-heading">
              <h2>Parameters</h2>
              <button
                className="icon"
                type="button"
                aria-label="Reset parameters"
                title="Reset parameters"
                disabled={busy}
                onClick={() => setParams({ ...DEFAULT })}
              >
                <RotateCcw size={16} />
              </button>
            </div>
            {FIELDS.map(([key, label, min, max, step]) => (
              <label key={key}>
                {label}
                <input
                  type="number"
                  required
                  min={min}
                  max={max}
                  step={step}
                  value={params[key]}
                  disabled={busy}
                  onChange={(event) =>
                    setParams({
                      ...params,
                      [key]:
                        event.target.value === ""
                          ? ""
                          : Number(event.target.value),
                    })
                  }
                />
              </label>
            ))}
            {busy ? (
              <button className="primary" type="button" onClick={stop}>
                <Square size={15} />
                Stop simulation
              </button>
            ) : (
              <button className="primary" type="submit">
                <Play size={16} />
                Run simulation
              </button>
            )}
            <div className="status" role="status">
              {busy && <LoaderCircle size={15} className="spinner" />}
              {status}
            </div>
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
          </form>
          <section className="results" aria-label="Simulation results">
            <div className="result-heading">
              <h2>Claim-epoch surplus</h2>
              <div className="segmented" role="tablist" aria-label="Path view">
                {[
                  ["single", "Single path"],
                  ["ensemble", "Ensemble"],
                ].map(([key, label]) => (
                  <button
                    type="button"
                    role="tab"
                    key={key}
                    aria-selected={mode === key}
                    onClick={() => setMode(key)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
            {result ? (
              <PathChart result={result} mode={mode} />
            ) : (
              <div className="empty plot">
                <TrendingUp size={42} />
                <span>No simulation result yet</span>
              </div>
            )}
            <div className="legend">
              <span>
                <i className="green" />
                Seeded primary path
              </span>
              <span>
                <i className="red" />
                Ruin boundary / ruined paths
              </span>
              <span>Embedded jump chain, not continuous premium flow</span>
            </div>
            <div className="metrics">
              <div>
                <span>Observed ruin frequency</span>
                <strong>
                  {result ? `${(result.ruinFraction * 100).toFixed(1)}%` : "--"}
                </strong>
              </div>
              <div>
                <span>Ruined runs</span>
                <strong>
                  {result
                    ? `${result.ruinedRuns} / ${result.parameters.runs}`
                    : "--"}
                </strong>
              </div>
              <div>
                <span>Primary claim events</span>
                <strong>{result ? result.primary.events.length : "--"}</strong>
              </div>
              <div>
                <span>Python execution</span>
                <strong>
                  {seconds === null ? "--" : `${seconds.toFixed(3)}s`}
                </strong>
              </div>
            </div>
            <div className="exports">
              <span>
                {changed
                  ? "Parameters changed. Results still belong to the previous run."
                  : result
                    ? `Seed ${result.parameters.seed} / horizon ${result.parameters.T}`
                    : "U(t) = u + c t - cumulative claims"}
              </span>
              <div>
                <a
                  className="secondary"
                  aria-disabled={!result}
                  href={result ? dataUrl(result) : undefined}
                  download="risk-simulation.json"
                >
                  <Download size={15} />
                  Results JSON
                </a>
                <a
                  className="secondary"
                  aria-disabled={!result}
                  href={csv}
                  download="claim-events.csv"
                >
                  <Download size={15} />
                  Trace CSV
                </a>
              </div>
            </div>
            <div className="trace-heading">
              <h2>Primary event trace</h2>
              <span>
                {result?.primary.ruinTime != null
                  ? `Ruin at t = ${result.primary.ruinTime.toFixed(4)}`
                  : result
                    ? "No ruin within the simulated horizon"
                    : ""}
              </span>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Event</th>
                    <th>Arrival time</th>
                    <th>Wait</th>
                    <th>Claim</th>
                    <th>Premium</th>
                    <th>Surplus</th>
                  </tr>
                </thead>
                <tbody>
                  {result?.primary.events.slice(0, 50).map((e) => (
                    <tr key={e.index}>
                      <td>{e.index}</td>
                      <td>{e.event_time.toFixed(4)}</td>
                      <td>{e.waiting_time.toFixed(4)}</td>
                      <td>{e.claim_size.toFixed(4)}</td>
                      <td>{e.premium_income.toFixed(4)}</td>
                      <td className={e.surplus < 0 ? "negative" : ""}>
                        {e.surplus.toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {result && result.primary.events.length === 0 && (
                <p className="table-empty">
                  No claims arrived before the horizon.
                </p>
              )}
            </div>
          </section>
        </div>
        <footer>
          <span>
            Monte Carlo frequency is sample-dependent, not an exact ruin
            probability.
          </span>
          <span>
            Up to 20 plotted paths / first 50 trace rows / full trace in
            downloads
          </span>
        </footer>
      </main>
    </>
  );
}
createRoot(document.getElementById("root")).render(<App />);
