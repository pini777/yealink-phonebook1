// node render.mjs beats OUT_DIR            -> one PNG per beat (+0.3s) contact frames
// node render.mjs video OUT.mp4 [workers]  -> 60fps, 4 subframes/frame blended (tmix)
import { chromium } from "/opt/node-tools/node_modules/playwright/index.mjs";
import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import path from "node:path";
const here = path.dirname(new URL(import.meta.url).pathname);
const url = "file://" + here + "/" + (process.env.PAGE || "index.html") + "?render";
const [mode, out, nw = "4"] = process.argv.slice(2);
const browser = await chromium.launch();
async function page() {
  const p = await browser.newPage({ viewport: { width: +(process.env.VW || 1440), height: +(process.env.VH || 1440) } });
  await p.goto(url); await p.evaluate(() => window.ready);
  return p;
}
const shot = (p, t) => p.evaluate(t => seek(t), t).then(() => p.locator("#stage").screenshot({ type: mode === "beats" ? "png" : "jpeg", quality: mode === "beats" ? undefined : 95 }));
if (mode === "beats") {
  mkdirSync(out, { recursive: true });
  const p = await page(); const P = await p.evaluate(() => BEAT);
  const NB = await p.evaluate(() => Math.round(LOOP / BEAT));
  for (let i = 0; i < NB; i++) {
    const buf = await shot(p, i * P + 0.3);
    (await import("node:fs")).writeFileSync(`${out}/b${String(i).padStart(2, "0")}.png`, buf);
  }
  for (const t of [0, (await p.evaluate(() => LOOP)) - 1 / 240]) (await import("node:fs")).writeFileSync(`${out}/edge_${t.toFixed(3)}.png`, await shot(p, t));
} else {
  const L = await (await page()).evaluate(() => LOOP);
  const frames = Math.round(L * 60), W = +nw, per = Math.ceil(frames / W);
  await Promise.all(Array.from({ length: W }, async (_, w) => {
    const p = await page(), f0 = w * per, f1 = Math.min(frames, f0 + per);
    const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", "240", "-i", "-",
      "-vf", "tmix=frames=4,select='eq(mod(n\\,4)\\,3)',setpts=N/60/TB", "-r", "60",
      "-c:v", "libx264", "-crf", "8", "-preset", "fast", "-pix_fmt", "yuv444p", `${out}.part${w}.mp4`], { stdio: ["pipe", "inherit", "inherit"] });
    for (let f = f0; f < f1; f++) for (let k = 0; k < 4; k++) {
      const buf = await shot(p, (f + (k - 1.5) / 4) / 60);
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
      if (w === 0 && k === 0 && f % 30 === 0) console.log(`frame ${f}/${f1}`);
    }
    ff.stdin.end(); await new Promise(r => ff.on("close", r));
  }));
  console.log(JSON.stringify({ frames, parts: W }));
}
await browser.close();
