"""Runnable demos for fast-a11y-py.

Usage:
    python examples/basic.py              # Run all examples
    python examples/basic.py check        # Check a page with violations
    python examples/basic.py clean        # Check a clean page
    python examples/basic.py filter       # Filter by impact level
"""

from __future__ import annotations

import sys

from fast_a11y import fast_a11y


def demo_check():
    """Check a page with accessibility violations."""
    print("\n=== Check Page for Violations ===\n")

    html = """<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
  <img src="hero.jpg">
  <a href="/about"></a>
  <input type="text">
  <button></button>
</body>
</html>"""

    results = fast_a11y(html)

    print(f"Violations: {len(results['violations'])}")
    print(f"Passes: {len(results['passes'])}")
    print(f"Incomplete: {len(results['incomplete'])}\n")

    for v in results["violations"]:
        print(f"  [{v['impact']}] {v['id']}: {v['description']}")
        print(f"  Nodes: {len(v['nodes'])}\n")


def demo_clean():
    """Check a clean, accessible page."""
    print("\n=== Clean Page ===\n")

    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Accessible Page</title>
</head>
<body>
  <main>
    <h1>Welcome</h1>
    <img src="photo.jpg" alt="A sunset over the ocean">
    <a href="/about">About us</a>
    <button>Submit</button>
    <label for="name">Name</label>
    <input id="name" type="text">
  </main>
</body>
</html>"""

    results = fast_a11y(html)

    print(f"Violations: {len(results['violations'])}")
    print(f"Passes: {len(results['passes'])}")
    if not results["violations"]:
        print("No accessibility violations found.")
    print()


def demo_filter():
    """Filter violations by impact level."""
    print("\n=== Filter Critical Only ===\n")

    html = """<!DOCTYPE html>
<html>
<body>
  <img src="a.jpg">
  <img src="b.jpg" alt="">
  <a href="/x"></a>
</body>
</html>"""

    results = fast_a11y(html)

    critical = [v for v in results["violations"] if v["impact"] == "critical"]
    serious = [v for v in results["violations"] if v["impact"] == "serious"]

    print(f"Critical: {len(critical)}")
    for v in critical:
        print(f"  {v['id']}: {len(v['nodes'])} instances")
    print(f"Serious: {len(serious)}")
    for v in serious:
        print(f"  {v['id']}: {len(v['nodes'])} instances")
    print()


DEMOS = {
    "check": demo_check,
    "clean": demo_clean,
    "filter": demo_filter,
}


def main():
    args = sys.argv[1:]

    if args:
        for name in args:
            if name in DEMOS:
                DEMOS[name]()
            else:
                print(f"Unknown demo: {name}")
                print(f"Available: {', '.join(DEMOS.keys())}")
                sys.exit(1)
    else:
        for demo_fn in DEMOS.values():
            demo_fn()


if __name__ == "__main__":
    main()
