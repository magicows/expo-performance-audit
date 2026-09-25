# Review checks and evidence limits

Use this as a decision guide, not a list of automatic violations. SDK and library behavior changes: check the installed versions and current official docs before prescribing an API or migration.

## Lists

- Inventory `FlatList`, `SectionList`, `VirtualizedList`, `FlashList`, hand-built `.map()` scroll regions, and their actual data sizes and row complexity. A short settings menu need not move to FlashList. For long or costly lists, inspect row cost, stable keys, pagination, virtualization settings, and update frequency; compare candidates in a release build on the target device.
- Inspect `renderItem`, `keyExtractor`, `extraData`, row props, and any object/function props created during parent renders. Inline `renderItem` is a clue, not proof of slow frames. Memoizing a row only helps when its props remain stable and rendering is expensive enough. Check callback dependencies for correctness; never copy an empty dependency array over changing state.
- For FlashList, inspect installed major version. Its cells recycle: row local state tied to an item may leak across recycled items. Check explicit nested `key` props and mixed item types. Current v2 guidance favors stable props and `getItemType` for heterogeneous rows; older size-estimate advice may not apply.

## Images

- Identify React Native `Image`, `expo-image`, custom wrappers, remote and local sources, and whether repeated list images use an appropriate cache. React Native `Image` use alone does not prove refetching; cache behavior varies by platform, URL, and headers. `expo-image` offers disk/memory caching, but `cachePolicy="none"` opts out.
- For remote thumbnails, inspect URL parameters, image service transformations, API fields, or actual responses to compare delivered dimensions and byte size with displayed size and density. If only client code is available, mark server resizing as unverified. `contentFit` does not reduce transfer size.
- Check large local image assets and repeated full-resolution decodes when relevant. A giant asset used once may still cost startup or memory.

## Re-renders and JS work

- Inspect broad context providers, changing `value` objects, high-frequency state, expensive selectors, and rows subscribed to global state. A large context is a candidate; prove unnecessary commits with React Native DevTools Profiler before recommending a split. Also inspect whether provider values are memoized and whether consumers need all fields.
- Check synchronous storage, JSON parsing, large data transforms, or expensive work in entry modules, root layouts, render paths, and interactions. This can delay first render or block the JS thread. Prefer measured hot paths to speculative memoization.

## Animation

- Identify gesture-linked and per-frame animations driven by React state, `Animated` with `useNativeDriver: false`, and Reanimated worklets. `useNativeDriver: false` can be required for unsupported properties; evaluate the specific animation and dropped frames. Reanimated moves suitable work to the UI runtime, but it is not automatically faster for every animation. Prefer transform/opacity over layout-changing properties for hot animations where visually equivalent.

## Startup and bundle

- Check explicit engine overrides per platform and native projects if present. Hermes is Expo's default; missing `jsEngine` is normal. Treat dynamic `app.config.*` as unresolved until evaluated or inspected.
- Find root imports of heavy packages, such as full `lodash` or `moment`, and inspect actual bundled cost before replacing them. Installed dependencies alone are insufficient evidence. Expo Atlas can attribute production bundle modules. Its exported `atlas.jsonl` can contain transformed source and inlined public environment values, so keep it local unless sharing is authorized.
- Inspect root/layout imports and synchronous initialization for work before first paint. Screen deferral can help but must match navigator, SDK, and platform. Native Expo Router async routes currently do not provide production bundle splitting; avoid claiming they do.

## Device verification and report

- On a physical lower-end Android phone, with a release build and representative data, check cold/warm launch, long-list scroll and fling, image-heavy navigation, key animations during JS work, memory growth after repeated navigation, and network-limited image loading. Record device model, Android version, build type, data size, and any metrics or observations. Simulator/emulator checks can be supplementary.
- Report each issue as `severity | status | file:line | evidence | impact | action`. Use high severity for a demonstrated release-path regression or obvious heavy blocking work, medium for a supported risk with meaningful exposure, and low for a review candidate. Keep unmeasured items explicitly labeled.
- End with: checks completed, checks unavailable, prioritized next actions, and the physical Android test handoff. If nothing actionable is found, say so without implying the app is performance-certified.

## Primary documentation

- [Expo Hermes](https://docs.expo.dev/guides/using-hermes/)
- [Expo Image](https://docs.expo.dev/versions/latest/sdk/image/)
- [Expo bundle analysis](https://docs.expo.dev/guides/analyzing-bundles/)
- [Expo Router async routes](https://docs.expo.dev/router/web/async-routes/)
- [Expo debugging and profiling](https://docs.expo.dev/debugging/tools/)
- [FlashList performance](https://shopify.github.io/flash-list/docs/fundamentals/performance/)
- [FlashList v2 usage](https://shopify.github.io/flash-list/docs/usage/)
- [Reanimated performance](https://docs.swmansion.com/react-native-reanimated/docs/guides/performance/)
