#!/usr/bin/env python3
"""Read-only Expo performance inventory. Every finding requires human review."""

import argparse
import json
import re
import sys
from pathlib import Path


SKIP_DIRS = {
    ".git", ".expo", ".next", ".turbo", "android", "ios", "build", "coverage",
    "dist", "node_modules", "vendor", "web-build",
}
SOURCE_EXTS = {".js", ".jsx", ".ts", ".tsx"}
IMPORT_RE = re.compile(
    r"\bimport\s+(?:(?P<clause>[^;]*?)\s+from\s+)?['\"](?P<module>[^'\"]+)['\"]",
    re.S,
)
REQUIRE_RE = re.compile(r"\brequire\s*\(\s*['\"]([^'\"]+)['\"]\s*\)")
LIST_TAG_RE = re.compile(r"<(?P<name>FlatList|SectionList|VirtualizedList|FlashList)\b")
RENDER_ITEM_RE = re.compile(
    r"\brenderItem\s*=\s*\{\s*(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>",
    re.S,
)
CONTEXT_RE = re.compile(r"\bcreateContext\s*(?:<[^;]+?>)?\s*\(")
PROVIDER_VALUE_RE = re.compile(r"<\w+(?:\.\w+)?Provider\b[^>]*\bvalue\s*=\s*\{\s*\{", re.S)
ANIMATION_RE = re.compile(r"\bAnimated\.(?:timing|spring|decay)\s*\(")
JS_DRIVER_RE = re.compile(r"\buseNativeDriver\s*:\s*false\b")
HEAVY_MODULE_RE = re.compile(r"^(?:moment|lodash|lodash-es)$")


def names_from_import(clause):
    names = set()
    if not clause:
        return names
    braces = re.search(r"\{([^}]*)\}", clause, re.S)
    if braces:
        for part in braces.group(1).split(","):
            token = part.strip().split()
            if token:
                names.add(token[-1])
    return names


def location(source, offset):
    line = source.count("\n", 0, offset) + 1
    excerpt = source.splitlines()[line - 1].strip()
    return line, excerpt[:180]


def candidate(out, kind, path, source, match, detail):
    line, excerpt = location(source, match.start())
    out.append({"kind": kind, "path": str(path), "line": line,
                "excerpt": excerpt, "review": detail})


def scan_file(path, relative, out):
    if path.stat().st_size > 1_000_000:
        return "large source file skipped: " + str(relative)
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeError, OSError):
        return "unreadable source file skipped: " + str(relative)

    imports = list(IMPORT_RE.finditer(source))
    rn_images = set()
    expo_images = set()
    for match in imports:
        module = match.group("module")
        names = names_from_import(match.group("clause"))
        if module == "react-native" and "Image" in names:
            rn_images.add("Image")
        if module == "expo-image" and "Image" in names:
            expo_images.add("Image")
        if module == "react-native":
            for alias in re.findall(r"\bImage\s+as\s+(\w+)", match.group("clause") or ""):
                rn_images.add(alias)
        if module == "expo-image":
            for alias in re.findall(r"\bImage\s+as\s+(\w+)", match.group("clause") or ""):
                expo_images.add(alias)
        if HEAVY_MODULE_RE.fullmatch(module):
            candidate(out, "heavy_import", relative, source, match,
                      "Inspect production bundle cost and usage before replacing this import.")
    for match in REQUIRE_RE.finditer(source):
        if HEAVY_MODULE_RE.fullmatch(match.group(1)):
            candidate(out, "heavy_import", relative, source, match,
                      "Inspect production bundle cost and usage before replacing this require.")

    for match in LIST_TAG_RE.finditer(source):
        candidate(out, "list", relative, source, match,
                  "Inspect data size, row cost, keys, updates, and release-device behavior.")
    for match in RENDER_ITEM_RE.finditer(source):
        candidate(out, "inline_render_item", relative, source, match,
                  "Check whether parent updates recreate the callback and whether that affects measured list performance.")
    for name in rn_images - expo_images:
        for match in re.finditer(r"<" + re.escape(name) + r"\b", source):
            candidate(out, "react_native_image", relative, source, match,
                      "Check source type, cache behavior, delivered dimensions, and repeated rendering.")
    for match in CONTEXT_RE.finditer(source):
        candidate(out, "context", relative, source, match,
                  "Inspect provider value updates and consumers; profile commits before splitting context.")
    for match in PROVIDER_VALUE_RE.finditer(source):
        candidate(out, "inline_provider_value", relative, source, match,
                  "Inspect whether provider value identity changes unnecessarily and affects consumers.")
    for match in ANIMATION_RE.finditer(source):
        candidate(out, "animated_api", relative, source, match,
                  "Inspect driver, animated properties, and release-mode frame behavior.")
    for match in JS_DRIVER_RE.finditer(source):
        candidate(out, "js_animation_driver", relative, source, match,
                  "Check whether the animated property requires JS driver and whether this path drops frames.")
    return None


def sources(root):
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = sorted(directory.iterdir())
        except OSError:
            continue
        for path in entries:
            if path.is_symlink():
                continue
            if path.is_dir() and path.name not in SKIP_DIRS:
                stack.append(path)
            elif path.is_file() and path.suffix in SOURCE_EXTS and not path.name.endswith(".d.ts"):
                yield path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app_root", type=Path)
    args = parser.parse_args()
    root = args.app_root.expanduser().resolve()
    package_path = root / "package.json"
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        parser.error(f"cannot read package.json at {root}: {error}")
    dependencies = {**package.get("devDependencies", {}), **package.get("dependencies", {})}
    if "expo" not in dependencies:
        parser.error(f"{root} does not declare an Expo dependency")

    config = None
    config_path = root / "app.json"
    config_note = "No static app.json; inspect app.config.* or native configuration."
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config_note = "Static app.json read; dynamic/native overrides may still apply."
        except (OSError, UnicodeError, json.JSONDecodeError):
            config_note = "app.json could not be parsed; inspect configuration manually."
    expo_config = config.get("expo", config) if isinstance(config, dict) else {}
    if not isinstance(expo_config, dict):
        expo_config = {}
    engine = {key: value for key, value in (
        ("default", expo_config.get("jsEngine")),
        ("ios", expo_config.get("ios", {}).get("jsEngine") if isinstance(expo_config.get("ios"), dict) else None),
        ("android", expo_config.get("android", {}).get("jsEngine") if isinstance(expo_config.get("android"), dict) else None),
    ) if value is not None}
    findings = []
    skipped = []
    count = 0
    for path in sources(root):
        count += 1
        note = scan_file(path, path.relative_to(root), findings)
        if note:
            skipped.append(note)
    print(json.dumps({
        "app_root": str(root), "expo_version": dependencies["expo"],
        "relevant_dependencies": {name: dependencies[name] for name in sorted(dependencies)
                                  if name in {"expo-image", "expo-router", "@shopify/flash-list",
                                              "react-native-reanimated", "react-native-worklets", "moment", "lodash"}},
        "config_note": config_note, "explicit_js_engine": engine,
        "source_files_seen": count, "skipped": skipped,
        "candidates": sorted(findings, key=lambda item: (item["path"], item["line"], item["kind"])),
        "warning": "Candidate inventory only; inspect source and measure runtime behavior before reporting issues.",
    }, indent=2))


if __name__ == "__main__":
    main()
