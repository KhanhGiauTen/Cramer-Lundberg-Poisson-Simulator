let python;
self.onmessage = async ({ data }) => {
  try {
    if (!python) {
      self.postMessage({ type: "status", text: "Loading Python runtime..." });
      const indexURL = new URL("/runtime/", self.location.origin).href;
      const { loadPyodide } = await import(
        /* @vite-ignore */ `${indexURL}pyodide.mjs`
      );
      python = await loadPyodide({ indexURL });
      for (const file of ["cl_model.py", "browser_api.py"]) {
        const response = await fetch(`/engine/${file}`);
        if (!response.ok) throw new Error("Simulation source unavailable");
        python.FS.writeFile(file, await response.text());
      }
      await python.runPythonAsync("from browser_api import simulate_public");
    }
    self.postMessage({ type: "status", text: "Running seeded simulations..." });
    python.globals.set("simulation_params", JSON.stringify(data));
    const start = performance.now();
    const result = JSON.parse(
      await python.runPythonAsync("simulate_public(simulation_params)"),
    );
    self.postMessage({
      type: "result",
      result,
      seconds: (performance.now() - start) / 1000,
    });
  } catch (error) {
    python = undefined;
    self.postMessage({ type: "error", text: error.message });
  }
};
