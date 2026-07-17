# Proposal to Elgato — an official local pre-publication checker

**Status:** idea to pitch to Elgato (Maker team). Not yet sent.
**Owner:** BenLab (Beennnn).
**Date noted:** 2026-07-17.

## The pitch

Give creators a small tool they run **locally, before submitting**, that checks a
Stream Deck icon pack or plugin against the same things Maker Console review
rejects for — reports every problem in plain language, and **auto-fixes the ones
that can be fixed safely**. Fewer round-trips of "submit → wait days → rejected
for a one-line issue → fix → resubmit", less reviewer load, higher first-pass
approval rate.

We built two working tools doing exactly this from our own rejections; we'd like
to offer them (or the approach) to Elgato as an official, distributable checker.

## Why it matters (evidence from our own submissions)

Every one of these was a machine-detectable defect that cost a full review cycle:

- **Icon pack** — *"the preview images of the GIFs aren't loading, please ensure
  this icon pack is packaged correctly via iconpackman."* Root cause: animated
  icons shipped without the companion first-frame poster PNG the Icon Library
  renders in the grid. 100% detectable and auto-fixable locally.
- **Plugins (Wi-Fi + Bluetooth)** — *"icons used inside the Stream Deck app for
  category and actions will need to be white"* and *"mention of a bluetooth action
  we don't see included."* Both are a script check away.

A creator waiting days to be told "your in-app icon isn't white" is a bad
experience for them and wasted triage for the reviewer.

## What the tools already do

Two open-source checkers (MIT, Python 3 + Pillow), each with a `verify` gate and a
`--fix` auto-repair mode, ~96–98% test coverage:

### Icon packs — [`sdicons verify`](https://github.com/Beennnn/stream-deck-icons)
- **Checks:** companion poster present + 144×144 PNG for every animated icon;
  144×144 sizes; ≤80-char names; tags without `", "` (which iconpackman rejects);
  duplicate paths/names; manifest store-quality; previews ≤3; can also verify a
  built `.streamDeckIconPack` container.
- **`--fix`:** generates every missing/wrong companion poster from the animation's
  first frame; splits `", "` tags. Idempotent.

### Plugins — [`sdplugin-verify`](https://github.com/Beennnn/streamdeck-plugin-toolkit)
- **Checks:** in-app icons (plugin `Icon`, `CategoryIcon`, each action `Icon`,
  @1x+@2x) are white `#FFFFFF` monochrome on transparent — with key `States[].Image`
  and the store icon correctly exempt; no user-visible cross-plugin/foreign feature
  reference; manifest gate (`SDKVersion`≥3, `Software.MinimumVersion`≥6.9, 2–30
  actions, no `Nodejs.Debug`, valid UUID matching the folder, referenced images +
  Property Inspector files present); can verify a built `.streamDeckPlugin`.
- **`--fix`:** whitens coloured in-app icons (RGB→#FFFFFF, alpha kept) without
  touching key art; generates missing @2x variants. Idempotent. Foreign references
  are reported, never auto-edited (they need human intent).

Both cleanly separate **machine-checkable** items from **human-only** ones (demo
video, gallery re-shoot, the final Submit) and never claim the human steps are done.

## Suggested shape for an official version

1. **A single `streamdeck check <path>`** subcommand in Elgato's own CLI /
   `@elgato/cli`, covering packs and plugins, exit-non-zero on any blocker.
2. **`--fix`** for the safe, unambiguous repairs (posters, white icons, @2x).
3. **Wire it into Maker Console upload** — run the same checks server-side and show
   the creator the exact failing item *at upload time*, not days later in an email.
4. **Publish the rules** (a JSON schema + a prose spec) so third-party tooling
   stays in lockstep — the internal `iconpackman` behaviour (companion posters) is
   the kind of rule that's currently only discoverable by reverse-engineering.

## Next step (human)

Reach out to the Maker team (reply on a review thread, or `maker@elgato.com`) with
this doc + links to the two repos, and offer to contribute the checks upstream.
