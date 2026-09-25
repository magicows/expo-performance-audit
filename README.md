# Expo Performance Audit

An installable agent skill for reviewing an Expo app before release. It inspects project code and configuration for performance risks, then guides an evidence-based report with actions the developer can review. The `SKILL.md` format can be used by compatible coding agents, including Codex, Claude Code, and Cursor.

## What it covers

- Lists: virtualization, row rendering, keys, and places where FlashList may be worth measuring.
- Images: caching, remote thumbnail sizing, and repeated large image use.
- Re-renders: context updates, unstable props, and work that needs profiler evidence.
- Animations: JS-driven paths and UI-thread alternatives.
- Startup: Hermes configuration, heavy imports, bundle analysis, and work before first paint.
- Device validation: a release-build checklist for a physical lower-end Android phone.

The audit labels static findings as candidates until the relevant code or runtime behavior confirms them. It cannot establish server image dimensions, frame drops, or real-device performance from source code alone.

## Install with `npx skills`

From this project directory, install the local [`expo-performance-audit`](expo-performance-audit/) skill using the [Skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add ./expo-performance-audit
```

The CLI lets you choose a supported agent. By default it installs for the current project; add `-g` to install for your user account across projects. If you publish this repository, the CLI can also install from its Git URL or a direct link to the skill directory.

Ask your agent, for example: `Use the expo-performance-audit skill to review /path/to/my-expo-app before release.` The skill performs a read-only review unless you also ask for fixes.

## Run the scanner directly

The bundled scanner uses Python 3 and the standard library. It produces a JSON inventory of review candidates:

```sh
python3 expo-performance-audit/scripts/scan.py /path/to/my-expo-app
```

Its output is an input to the audit, not a pass/fail score. See [`SKILL.md`](expo-performance-audit/SKILL.md) for the agent workflow and [`checks.md`](expo-performance-audit/references/checks.md) for the review criteria.

## Attribution

The idea and six-part checklist were inspired by Reddit user **u/Putrid-Ad6454** and their [“The performance checklist I run before shipping any React Native app” post on r/expo](https://www.reddit.com/r/expo/comments/1wowu10/the_performance_checklist_i_run_before_shipping/). This skill adapts that checklist into a code and configuration review, adds evidence limits, and includes steps that require profiling or a physical device.
