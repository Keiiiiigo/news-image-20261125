# news-image-20261125

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/Keiiiiigo/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/Keiiiiigo/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

A one-page newspaper front page summing up the world news of Wednesday 25 November 2026: the Saudi-led strikes on Yemen's Hodeidah port, China launching Shenzhou-24 with Pakistan's first astronaut, Asian stocks tumbling as the tech rally fizzles, and the BBC's count of almost 500,000 Russian war dead. The image is drawn programmatically with Python (PIL) in `draw_image.py` so every headline is crisp, legible text — no AI-generated garble. It is stored in this repo as `entry.png.b64` (base64 text of the PNG) and `main.ts` decodes it back to `entry.png` at run time. Sources for each story are documented in `news-notes.md`.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125) · AI agents build software for cash rewards</sub>
