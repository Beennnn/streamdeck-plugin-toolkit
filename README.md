# Stream Deck plugin toolkit

The tools, commands and gotchas I use to **build, package and ship Elgato Stream
Deck plugins** — collected from real plugins (a Wi-Fi/Bluetooth picker, a MIDI note
display, …). It's a reference, not a framework: a checklist you can copy from.

> Focus: **macOS**, TypeScript plugins, distribution on the **Elgato Marketplace**
> (Maker Console) and via GitHub releases.

---

## The toolchain

| Tool | What it does | Install |
| --- | --- | --- |
| **[Node.js](https://nodejs.org)** 20+ | Runtime Stream Deck runs the plugin on | `brew install node` |
| **[@elgato/cli](https://www.npmjs.com/package/@elgato/cli)** (`streamdeck`) | Scaffold, **validate**, **pack**, **link**, **restart**, view logs | `npm i -g @elgato/cli` |
| **[@elgato/streamdeck](https://www.npmjs.com/package/@elgato/streamdeck)** | The plugin SDK (actions, settings, feedback, i18n) | `npm i @elgato/streamdeck` |
| **[Rollup](https://rollupjs.org)** + `@rollup/plugin-typescript`, `-commonjs`, `-node-resolve` | Bundle `src/*.ts` → one inlined `bin/plugin.js` (the SD runtime has no `node_modules`) | dev deps |
| **[TypeScript](https://www.typescriptlang.org)** | Typed plugin code | dev dep |
| **[librsvg](https://gitlab.gnome.org/GNOME/librsvg)** (`rsvg-convert`) | Rasterize SVG icons → the PNG sizes SD wants | `brew install librsvg` |
| **[blueutil](https://github.com/toy/blueutil)** *(optional)* | Example of a **bundled native helper** (Bluetooth connect) | `brew install blueutil` |
| **[Maker Console](https://maker.elgato.com)** | Submit & manage Marketplace products | web |

---

## Project skeleton

```
my-plugin/
├─ src/
│  ├─ plugin.ts              # entry: registers actions, calls streamDeck.connect()
│  └─ actions/*.ts           # one SingletonAction per action (@action({UUID}))
├─ com.author.myplugin.sdPlugin/
│  ├─ manifest.json          # the plugin definition (see below)
│  ├─ bin/plugin.js          # rollup output (gitignored)
│  ├─ imgs/…                 # icons (rasterized from SVG)
│  ├─ ui/*.html              # Property Inspector (settings panels)
│  ├─ layouts/*.json         # Stream Deck+ dial touch layouts
│  └─ <lang>.json            # locale files (en, fr, de, es, ja, ko, zh_CN)
├─ assets/*.svg + gen-icons.mjs
├─ rollup.config.mjs
├─ tsconfig.json
└─ package.json
```

Start one with `streamdeck create` (interactive scaffolder).

---

## The build / ship loop

```bash
npm run build                      # rollup -c → bin/plugin.js
streamdeck validate  my.sdPlugin   # schema + rules check
streamdeck link      my.sdPlugin   # symlink into Stream Deck (dev install)
streamdeck restart   com.author.myplugin   # reload the running plugin
npm run pack                       # → dist/*.streamDeckPlugin  (installer)
```

Handy `package.json` scripts:

```json
{
  "build": "rollup -c",
  "watch": "rollup -c -w --watch.onEnd=\"streamdeck restart com.author.myplugin\"",
  "icons": "node assets/gen-icons.mjs",
  "validate": "streamdeck validate com.author.myplugin.sdPlugin",
  "pack": "streamdeck pack com.author.myplugin.sdPlugin --output dist --force"
}
```

Two plugins from one repo? Make `rollup.config.mjs` export an **array** of bundles
(one input + output each) and chain `&&` in the validate/pack scripts. Pass a
per-bundle `outDir` to `@rollup/plugin-typescript` or it errors on the second one.

---

## Marketplace requirements (the ones that block submission)

Maker Console silently disables **Continue** if these aren't met — check them first:

- **`SDKVersion`: 3** (or later)
- **`Software.MinimumVersion`: "6.9"** (Stream Deck 6.9+)
- **DRM**: enable it via the **toggle in Maker Console** (not a manifest/CLI field).
- **Actions**: 2–30 per plugin. **Plugin name unique** on Marketplace.
- No **`Nodejs.Debug: "enabled"`** in a shipped manifest (dev-only debug port).

Publishing a JS plugin needs **no Apple signing / no Developer account** — it runs
inside the Stream Deck app. You do need a (free) **Maker Console** account.

### Icon sizes (per [Elgato guidelines](https://docs.elgato.com/guidelines/stream-deck/plugins/))

| Asset | Size |
| --- | --- |
| Plugin / marketplace icon | 256×256 **and** 512×512 PNG |
| Category / action-list icon | 20×20 + 40×40 (or 28×28 + 56×56), monochrome white on transparent |
| Key icon | 72×72 (144×144 @2x) |
| Dial touch layout | 200×100 |

---

## Icons pipeline

Keep **SVG sources** in `assets/`, rasterize to the exact PNGs with `rsvg-convert`
via a small `gen-icons.mjs` (`npm run icons`). Recolour a single-colour glyph per
state by string-replacing the fill and re-rasterizing — cheap way to get
amber/green/grey state variants without hand-editing files.

---

## Localization (i18n)

Ship one **`<lang>.json`** at the `.sdPlugin` root per language, each with a top-level
`"Localization"` object. Stream Deck picks the user's language automatically.

- Keys = the **English string** (manifest `Name`/`Tooltip`, or a dotted key like
  `dial.connecting`). Values = the translation. English is the fallback.
- In code: `streamDeck.i18n.t("dial.connecting")`.
- Standard set: `en, fr, de, es, ja, ko, zh_CN` (+ `zh_TW`).
- **sdpi-components does NOT translate plain PI labels** (only `__MSG_key__`, and it
  never loads your locales) — swap `label`/`placeholder`/button text yourself in a
  small script if you localize the settings panel.

---

## Stream Deck+ dial layouts

A custom touch layout is a `layouts/*.json` with an `id` and `items` (pixmap/text,
each with a `rect [x,y,w,h]` on a 200×100 canvas). Reference it from the action's
`Encoder.layout`. Update it live from code with
`action.setFeedback({ key: value })` — a text item accepts `{ value, color }` for
per-state colour. **Bump the layout `id`** when you change it, or Stream Deck serves
the cached one.

---

## Bundling a native helper (advanced)

If macOS has no API for what you need (e.g. connecting a Bluetooth device), bundle a
small binary in the plugin instead of asking users to `brew install`:

1. Put it in `helpers/`, ship a **universal** build (`clang -arch arm64 -arch
   x86_64 …` or `lipo`).
2. Resolve its path at runtime from `import.meta.url` (relative to `bin/plugin.js`).
3. On first use, **clear the Gatekeeper quarantine** on your own bundled binary:
   `xattr -dr com.apple.quarantine <path>` (no admin needed) + `chmod 0755`.
4. Respect the binary's licence (attribution for MIT, etc.).

---

## Distribution

- **Elgato Marketplace** — `npm run pack` → upload the `.streamDeckPlugin` in
  [Maker Console](https://maker.elgato.com), fill the listing, submit for review.
- **GitHub release** — attach the `.streamDeckPlugin`; users double-click to install.
  Great fallback while a Marketplace review is pending, or for beta builds.

---

## Gotchas I've actually hit

- **`@action({UUID})` must sit directly above the class.** Slipping a `const`/comment
  between the decorator and `export class …` detaches it → *"The action's manifestId
  cannot be undefined"* and the plugin crash-loops. (The `tsc` "Decorators are not
  valid here" warning is the real tell.)
- **Periodic `setInterval` re-renders must read `await action.getSettings()` fresh** —
  not the settings captured at `onWillAppear`. Otherwise a key added empty keeps
  re-rendering its placeholder and overwrites a later selection.
- **Rollup + two bundles:** give each a `outDir` under its own plugin dir, or the TS
  plugin errors (`outDir must be inside the same directory as the 'file' option`).
- **Maker Console upload flow is finicky:** after a refresh the file can show but
  *Continue* stays greyed — re-select the file to re-trigger validation.
- **macOS Wi-Fi is Location-gated:** apps can't read SSID names without Location, and
  a plugin can't get Location — so no in-range scan and no instant precise join. Plan
  around it. (Long write-up in the wifi-picker repo.)

---

## Links

- [Stream Deck SDK docs](https://docs.elgato.com/streamdeck/sdk/introduction/getting-started/)
- [Plugin guidelines](https://docs.elgato.com/guidelines/stream-deck/plugins/)
- [Distribution](https://docs.elgato.com/streamdeck/sdk/introduction/distribution/)
- [Maker Console](https://maker.elgato.com) · [Become a Maker](https://docs.elgato.com/makers/general/become-a-maker/)
- My plugins: [BenLab on Marketplace](https://marketplace.elgato.com/@benlab)

---

*Maintained by BenLab. MIT licensed — copy freely.*
