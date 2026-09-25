---
name: expo-performance-audit
description: Audit an Expo or React Native project for release performance risks in lists, images, rendering, animation, and startup, then produce an evidence-based report with device checks. Use for performance reviews and pre-release audits, not ordinary feature implementation.
---

# Expo Performance Audit

Audit the project the user identifies. Default to a read-only review and a report; change application code only if the user also asks for fixes. Treat the checklist as hypotheses to verify, not lint rules. A static scan finds candidates, while profiling and device tests establish performance impact.

## Workflow

1. Locate the Expo app root (`package.json` with `expo` in dependencies), its SDK version, routing setup, app config, platform targets, and any existing performance measurements. In a monorepo, identify each relevant app. If the named path is not an Expo project, explain that and stop the audit rather than guessing.
2. Run `python3 <skill-dir>/scripts/scan.py <app-root>` to collect read-only candidates. Inspect the cited files and nearby code before making a finding. The scanner is deliberately heuristic and its output is not the report.
3. Review [references/checks.md](references/checks.md) for the checklist, severity guidance, version caveats, and what source code can establish. Resolve dynamic configuration or wrapper components by inspection when possible. Do not claim a server image is oversized, a context causes widespread renders, or a callback causes dropped frames without evidence.
4. If a usable release build, device, profiler, or existing trace is available, measure the relevant path. Record build mode, device, screen, data size, and before/after metrics. Do not launch builds, download dependencies, or run long exports merely to fill a report unless the user requested those operations or they are clearly warranted in the working environment.
5. Report verified findings with path and line, why each matters, and a concrete next action. Distinguish **confirmed source/configuration issue**, **candidate to measure**, **needs runtime/device verification**, and **checked with no issue found**. State which checks could not be completed. Include a short prioritized plan, with physical budget Android testing as an explicit handoff item when no such device was used.

## Reporting rules

- Cover the user's six areas: lists, images, re-renders, animation, startup, and lower-end Android validation. Add only relevant adjacent checks from the reference, such as JS-thread work, memory/scroll stability, and bundle analysis.
- For each finding, give evidence and confidence. An import, dependency, or JSX shape alone is usually a review candidate; inspect call sites and data flow. Do not manufacture a pass when evidence is missing.
- Avoid blanket rewrites. Small or static `FlatList` usage can be appropriate; `renderItem` identity and `React.memo` help only under particular update patterns. Compare FlashList on a release build before recommending migration, and account for its recycling behavior and installed major version.
- Expo normally uses Hermes by default. Flag an explicit JSC override or unresolved native configuration; absence of `jsEngine` is not a failure.
- A cached image component does not prove that the server supplies appropriately sized images. `contentFit` changes display geometry, not downloaded pixel dimensions. For remote thumbnails, ask for actual response dimensions, bytes, cache headers, and device measurements if these cannot be inspected.
- On native Expo Router, do not present async routes as production bundle splitting. Consider deferred component evaluation or navigation options only after checking the project's Expo SDK and current platform support.
- Profile in release mode for conclusions; development and simulator results can guide investigation but cannot substitute for a lower-end physical Android run.
