// News-image entry for make.fun competition news-image-20261125 (Node 22,
// standard library only). The front page is drawn offline by draw_image.py
// (PIL, no network) and stored in this repo as text (entry.png.b64, the
// base64 of entry.png) so the entry stays text-only; this program decodes it
// and writes entry.png to the grader's output directory.
//
// Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const b64 = readFileSync(join(here, 'entry.png.b64'), 'utf8').trim();
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, 'entry.png'), Buffer.from(b64, 'base64'));
