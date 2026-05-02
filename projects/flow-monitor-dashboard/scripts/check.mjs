import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectDir = path.resolve(scriptDir, "..");

const files = [
  "server.js",
  "flow-log-presets.json",
  "flow-skill-map.json",
  "flow-step-skill-map.json",
];

for (const relativePath of files) {
  const fullPath = path.join(projectDir, relativePath);
  const content = fs.readFileSync(fullPath, "utf8");
  if (relativePath.endsWith(".json")) {
    JSON.parse(content);
  }
}
