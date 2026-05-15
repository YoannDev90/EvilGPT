#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# 1. Format code (run only if available)
# ---------------------------------------------------------------------------
echo "Running formatters if available..."
if command -v ruff >/dev/null 2>&1; then
    echo "  Running ruff format..."
    ruff format . || true
else
    echo "  Skipping ruff (not installed)"
fi
if command -v isort >/dev/null 2>&1; then
    echo "  Running isort..."
    isort . || true
else
    echo "  Skipping isort (not installed)"
fi
if command -v removestar >/dev/null 2>&1; then
    echo "  Running removestar..."
    removestar . || true
else
    echo "  Skipping removestar (not installed)"
fi

# ---------------------------------------------------------------------------
# 2. Project tree → stdout + README (between <!-- TREE-START --> / <!-- TREE-END -->)
# ---------------------------------------------------------------------------
python3 << 'EOF'
import subprocess, sys, re
from pathlib import Path

GITIGNORE = Path(".gitignore")
README    = Path("README.md")

# Build exclusion pattern for `tree -I`
excludes = [".git"]
if GITIGNORE.exists():
    for line in GITIGNORE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("!"):
            excludes.append(line.removeprefix("./").rstrip("/"))
pattern = "|".join(excludes) or ".git"

if subprocess.run(["which", "tree"], capture_output=True).returncode != 0:
    print("'tree' not installed. Install with: apt-get install tree / brew install tree")
    sys.exit(0)

tree_output = subprocess.run(
    ["tree", "-a", "-I", pattern],
    capture_output=True, text=True
).stdout

print("Project tree:")
print(tree_output)

if not README.exists():
    sys.exit(0)

content = README.read_text()
block = f"\n```\n{tree_output}```\n"
new_content = re.sub(
    r"(<!-- TREE-START -->).*?(<!-- TREE-END -->)",
    lambda m: m.group(1) + block + m.group(2),
    content, flags=re.DOTALL
)
if new_content != content:
    README.write_text(new_content)
EOF

# ---------------------------------------------------------------------------
# 3. Code stats (cloc) → stdout + README (between <!-- CODE-STATS-START --> / <!-- CODE-STATS-END -->)
# ---------------------------------------------------------------------------
python3 << 'EOF'
import subprocess, json, re, sys
from pathlib import Path

README = Path("README.md")

if subprocess.run(["which", "cloc"], capture_output=True).returncode != 0:
    print("cloc not installed. Install with: brew install cloc / apt-get install cloc")
    sys.exit(0)

result = subprocess.run(
    ["cloc", ".", "--exclude-dir=.venv,.git,__pycache__,.github", "--json"],
    capture_output=True, text=True
)
try:
    data = json.loads(result.stdout)
except json.JSONDecodeError:
    print("Could not parse cloc output.")
    sys.exit(0)

DISPLAY = {"Bourne Shell": "Shell", "Python": "Python", "Markdown": "Markdown",
           "JSON": "JSON", "TOML": "TOML", "Text": "Text", "SVG": "SVG"}

lines = ["## Code Statistics", ""]
for lang in sorted(data):
    if lang in ("header", "SUM"):
        continue
    label = DISPLAY.get(lang, lang)
    d = data[lang]
    lines.append(f"**{label}:** {d['nFiles']} files, {d['code']} lines of code")
    lines.append("")

total = data.get("SUM", {})
summary = (f"**Total:** {total.get('nFiles',0)} files, {total.get('code',0)} lines of code, "
           f"{total.get('comment',0)} comments, {total.get('blank',0)} blank lines")
lines.append(summary)
print("Code Statistics:")
print(summary)

if not README.exists():
    sys.exit(0)

block = "\n" + "\n".join(lines) + "\n"
content = README.read_text()
new_content = re.sub(
    r"(<!-- CODE-STATS-START -->).*?(<!-- CODE-STATS-END -->)",
    lambda m: m.group(1) + block + m.group(2),
    content, flags=re.DOTALL
)
if new_content != content:
    README.write_text(new_content)
EOF

# ---------------------------------------------------------------------------
# 4. PyPI dependencies → README (between <!--DEPS-START--> / <!--DEPS-END-->)
# ---------------------------------------------------------------------------
python3 << 'EOF'
import re, json, sys
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

README       = Path("README.md")
REQUIREMENTS = Path("requirements.txt")

if not README.exists() or not REQUIREMENTS.exists():
    sys.exit(0)

def fetch_pypi(pkg):
    try:
        with urlopen(f"https://pypi.org/pypi/{pkg.lower()}/json", timeout=5) as r:
            info = json.loads(r.read())["info"]
            return info.get("summary", "").replace("\n", " ").strip(), info.get("version", "")
    except (URLError, KeyError):
        return "", ""

print("Updating dependencies list (fetching from PyPI)...")
lines = ["```markdown"]
for raw in REQUIREMENTS.read_text().splitlines():
    raw = raw.strip()
    if not raw or raw.startswith("#"):
        continue
    pkg = re.split(r"[\[<>=!~\s]", raw)[0]
    summary, version = fetch_pypi(pkg)
    if summary:
        lines.append(f"- `{raw}` - {summary} (latest: {version})")
    elif version:
        lines.append(f"- `{raw}` - latest: {version}")
    else:
        lines.append(f"- `{raw}`")
lines.append("```")

block = "\n" + "\n".join(lines) + "\n"
content = README.read_text()
new_content = re.sub(
    r"(<!--DEPS-START-->).*?(<!--DEPS-END-->)",
    lambda m: m.group(1) + block + m.group(2),
    content, flags=re.DOTALL
)
if new_content != content:
    README.write_text(new_content)
    print("  Dependencies updated ✓")
EOF

# ---------------------------------------------------------------------------
# 5. Env var names → README (between <!--ENV-START--> / <!--ENV-END-->)
# ---------------------------------------------------------------------------
python3 << 'EOF'
import re, sys
from pathlib import Path

README   = Path("README.md")
ENV_FILE = Path(".env")

if not README.exists() or not ENV_FILE.exists():
    sys.exit(0)

print("Copying environment variable names to README...")
var_names = []
for line in ENV_FILE.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        var_names.append(line.split("=", 1)[0].strip())

if not var_names:
    sys.exit(0)

block = "\n```env\n" + "".join(f"{v}=\n" for v in var_names) + "```\n"
content = README.read_text()
new_content = re.sub(
    r"(<!--ENV-START-->).*?(<!--ENV-END-->)",
    lambda m: m.group(1) + block + m.group(2),
    content, flags=re.DOTALL
)
if new_content != content:
    README.write_text(new_content)
    print("  Environment variables updated ✓")
EOF

echo "✅ All updates completed!"