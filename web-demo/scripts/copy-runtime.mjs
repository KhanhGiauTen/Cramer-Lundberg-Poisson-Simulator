import { access, copyFile, mkdir, readdir } from "node:fs/promises";
const runtime = new URL("../public/runtime/", import.meta.url);
await mkdir(runtime, { recursive: true });
const source = new URL("../node_modules/pyodide/", import.meta.url);
for (const file of await readdir(source)) {
  if (/\.(mjs|js|wasm|zip|json)$/.test(file))
    await copyFile(new URL(file, source), new URL(file, runtime));
}
const engine = new URL("../public/engine/", import.meta.url);
await mkdir(engine, { recursive: true });
for (const file of ["cl_model.py", "browser_api.py"]) {
  const original = new URL(`../../${file}`, import.meta.url),
    destination = new URL(file, engine);
  try {
    await access(original);
    await copyFile(original, destination);
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
    await access(destination);
  }
}
