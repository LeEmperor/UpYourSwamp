// import fs from "fs";
// import path from "path";
// import { RealtimeVision } from "@overshoot/sdk";

// function requireEnv(name) {
//   const v = process.env[name];
//   if (!v) {
//     console.error(JSON.stringify({ error: `Missing env var ${name}` }));
//     process.exit(2);
//   }
//   return v;
// }

// const apiUrl = process.env.OVERSHOOT_API_URL || "https://cluster1.overshoot.ai/api/v0.2";
// const apiKey = requireEnv("OVERSHOOT_API_KEY");

// const videoPath = process.argv[2];
// if (!videoPath) {
//   console.error(JSON.stringify({ error: "Usage: node run_overshoot_video.mjs <video_path>" }));
//   process.exit(2);
// }
// if (!fs.existsSync(videoPath)) {
//   console.error(JSON.stringify({ error: `Video file not found: ${videoPath}` }));
//   process.exit(2);
// }

// // Browser “File” compatibility: Overshoot wants a File-like object in browser.
// // In Node, SDK may accept a Blob/File polyfill or a path depending on implementation.
// // If SDK requires true browser File, you must run this in an Electron/browser context.
// const bytes = fs.readFileSync(videoPath);
// const blob = new Blob([bytes], { type: "video/mp4" });

// // Some SDKs accept { file: blob, filename }.
// const videoFile = Object.assign(blob, { name: path.basename(videoPath) });

// const prompt = process.env.OVERSHOOT_PROMPT || "Describe what you see.";

// const outputSchema = {
//   type: "object",
//   properties: {
//     summary: { type: "string" },
//     objects: { type: "array", items: { type: "string" } },
//     count_people: { type: "number" }
//   },
//   required: ["summary"]
// };

// const processing = {
//   clip_length_seconds: Number(process.env.OVERSHOOT_CLIP_LEN || "1"),
//   delay_seconds: Number(process.env.OVERSHOOT_DELAY || "1"),
//   fps: Number(process.env.OVERSHOOT_FPS || "30"),
//   sampling_ratio: Number(process.env.OVERSHOOT_SAMPLING || "0.1")
// };

// let resultCount = 0;
// const maxResults = Number(process.env.OVERSHOOT_MAX_RESULTS || "10");

// const vision = new RealtimeVision({
//   apiUrl,
//   apiKey,
//   prompt,
//   source: { type: "video", file: videoFile },
//   outputSchema,
//   processing,
//   onResult: (result) => {
//     // result.result is a JSON string when outputSchema is provided (per your docs).
//     // We emit a normalized JSON object for Python.
//     let parsed = null;
//     try {
//       parsed = JSON.parse(result.result);
//     } catch {
//       parsed = { raw: result.result };
//     }

//     const out = {
//       ts: Date.now(),
//       data: parsed,
//       inference_latency_ms: result.inference_latency_ms,
//       total_latency_ms: result.total_latency_ms
//     };

//     process.stdout.write(JSON.stringify(out) + "\n");

//     resultCount += 1;
//     if (resultCount >= maxResults) {
//       vision.stop().then(() => process.exit(0)).catch(() => process.exit(0));
//     }
//   },
//   onError: (err) => {
//     process.stderr.write(JSON.stringify({ error: String(err) }) + "\n");
//   }
// });

// await vision.start();


// run_overshoot_video.mjs
import fs from "fs";
import path from "path";
import { RealtimeVision } from "@overshoot/sdk";

function requireEnv(name) {
  const v = process.env[name];
  if (!v) {
    process.stderr.write(JSON.stringify({ error: `Missing env var ${name}` }) + "\n");
    process.exit(2);
  }
  return v;
}

const apiUrl = process.env.OVERSHOOT_API_URL || "https://cluster1.overshoot.ai/api/v0.2";
const apiKey = requireEnv("OVERSHOOT_API_KEY");

const videoPath = process.argv[2];
if (!videoPath) {
  process.stderr.write(JSON.stringify({ error: "Usage: node run_overshoot_video.mjs <video_path>" }) + "\n");
  process.exit(2);
}
if (!fs.existsSync(videoPath)) {
  process.stderr.write(JSON.stringify({ error: `Video file not found: ${videoPath}` }) + "\n");
  process.exit(2);
}

// Try to adapt Node file bytes into a File-like object.
// If the Overshoot SDK requires a real browser environment, this may fail with "window is not defined".
const bytes = fs.readFileSync(videoPath);
const blob = new Blob([bytes], { type: "video/mp4" });
const videoFile = Object.assign(blob, { name: path.basename(videoPath) });

const prompt = process.env.OVERSHOOT_PROMPT || "describe what you see";

const processing = {
  clip_length_seconds: Number(process.env.OVERSHOOT_CLIP_LEN || "1"),
  delay_seconds: Number(process.env.OVERSHOOT_DELAY || "1"),
  fps: Number(process.env.OVERSHOOT_FPS || "30"),
  sampling_ratio: Number(process.env.OVERSHOOT_SAMPLING || "0.1")
};

let resultCount = 0;
const maxResults = Number(process.env.OVERSHOOT_MAX_RESULTS || "10");

const vision = new RealtimeVision({
  apiUrl,
  apiKey,
  prompt,
  source: { type: "video", file: videoFile },
  processing,
  onResult: (result) => {
    const out = {
      ts: Date.now(),
      text: result.result,
      inference_latency_ms: result.inference_latency_ms,
      total_latency_ms: result.total_latency_ms
    };

    process.stdout.write(JSON.stringify(out) + "\n");

    resultCount += 1;
    if (resultCount >= maxResults) {
      vision.stop().then(() => process.exit(0)).catch(() => process.exit(0));
    }
  },
  onError: (err) => {
    process.stderr.write(JSON.stringify({ error: String(err) }) + "\n");
  }
});

await vision.start();
