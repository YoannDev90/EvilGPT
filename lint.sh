#!/usr/bin/env bash
set -euo pipefail

# Format code
ruff format
isort .

# Print project tree (filtered)
if command -v tree >/dev/null 2>&1; then
	echo "Project tree:"
	IGNORE_FILE=.gitignore
	EXCLUDES=".git"
	if [ -f "$IGNORE_FILE" ]; then
		# read non-empty, non-comment, non-negation lines
		GITIGNORE_EXCLUDES=$(grep -vE '^\s*(#|$|!)' "$IGNORE_FILE" | sed 's:^\./::; s:/*$::' | tr '\n' '|' | sed 's:|$::')
		if [ -n "$GITIGNORE_EXCLUDES" ]; then
			EXCLUDES="$EXCLUDES|$GITIGNORE_EXCLUDES"
		fi
	fi
	# fallback defaults if resulting pattern empty
	if [ -z "$EXCLUDES" ]; then
		EXCLUDES=".git|.venv|__pycache__"
	fi

	tree -a -I "$EXCLUDES" || true

	# Also update README.md section between <!-- TREE-START --> and <!-- TREE-END -->
	TMP_TREE=$(mktemp)
	tree -a -I "$EXCLUDES" > "$TMP_TREE" || true
	TMP_BLOCK=$(mktemp)
	{
		echo '```'
		cat "$TMP_TREE"
		echo '```'
		echo "<!-- TREE-END -->"
	} > "$TMP_BLOCK"
	README=README.md
	if grep -q "<!-- TREE-START -->" "$README"; then
		sed -n '1,/<!-- TREE-START -->/p' "$README" > "$README.tmp"
		cat "$TMP_BLOCK" >> "$README.tmp"
		sed -n '/<!-- TREE-END -->/,$p' "$README" | sed '1d' >> "$README.tmp"
		mv "$README.tmp" "$README"
	fi
	rm -f "$TMP_TREE" "$TMP_BLOCK"
else
	echo "'tree' not installed. Install with 'apt-get install tree' or 'brew install tree'."
fi
# Count lines of code and update README
if [ -f README.md ]; then
	echo "Code Statistics:"
	TMP_STATS=$(mktemp)
	
	# Check if cloc is available
	if command -v cloc >/dev/null 2>&1; then
		# Use cloc for code counting
		CLOC_OUTPUT=$(cloc . --exclude-dir=.venv,.git,__pycache__,.github --json 2>/dev/null || true)
		CLOC_JSON_FILE=$(mktemp)
		printf '%s' "$CLOC_OUTPUT" > "$CLOC_JSON_FILE"
		
		{
			echo "## Code Statistics"
			echo ""
			
			# Parse cloc JSON output
			if [ -s "$CLOC_JSON_FILE" ]; then
				python3 - "$CLOC_JSON_FILE" << 'PYSCRIPT'
import json
import sys

json_file = sys.argv[1]
try:
	with open(json_file, "r", encoding="utf-8") as fh:
		data = json.load(fh)
except Exception:
	print("*(cloc output unavailable)*")
	sys.exit(0)

total = data.get("SUM", {})
files_count = total.get("nFiles", 0)
code_lines = total.get("code", 0)
comment_lines = total.get("comment", 0)
blank_lines = total.get("blank", 0)

display_map = {
	"Bourne Shell": "Shell",
	"Python": "Python",
	"Markdown": "Markdown",
	"JSON": "JSON",
	"TOML": "TOML",
	"Text": "Text",
	"SVG": "SVG",
}

for lang in sorted(data.keys()):
	if lang in ["header", "SUM"]:
		continue
	lang_data = data.get(lang, {})
	label = display_map.get(lang, lang)
	print(f"**{label}:** {lang_data.get('nFiles', 0)} files, {lang_data.get('code', 0)} lines of code")
	print()

print(f"**Total:** {files_count} files, {code_lines} lines of code, {comment_lines} comments, {blank_lines} blank lines")
PYSCRIPT
			else
				echo "*(cloc output unavailable)*"
			fi
			
			echo ""
			echo "<!-- CODE-STATS-END -->"
		} > "$TMP_STATS"
		
		# Print to console
		if [ -s "$CLOC_JSON_FILE" ]; then
			echo "  $(python3 - "$CLOC_JSON_FILE" << 'PYSCRIPT'
import json
import sys

json_file = sys.argv[1]
try:
	with open(json_file, "r", encoding="utf-8") as fh:
		d = json.load(fh)
	print(f"Total: {d.get('SUM', {}).get('nFiles', 0)} files, {d.get('SUM', {}).get('code', 0)} lines of code")
except Exception:
	print("Total: unavailable")
PYSCRIPT
)"
		fi
		rm -f "$CLOC_JSON_FILE"
	else
		echo "  cloc not installed. Install with: brew install cloc (macOS) or apt-get install cloc (Linux)"
		
		{
			echo "## Code Statistics"
			echo ""
			echo "*(cloc not available)*"
			echo ""
			echo "<!-- CODE-STATS-END -->"
		} > "$TMP_STATS"
	fi
	
	if grep -q "<!-- CODE-STATS-START -->" "$README"; then
		sed -n '1,/<!-- CODE-STATS-START -->/p' "$README" > "$README.tmp"
		cat "$TMP_STATS" >> "$README.tmp"
		sed -n '/<!-- CODE-STATS-END -->/,$p' "$README" | sed '1d' >> "$README.tmp"
		mv "$README.tmp" "$README"
	fi
	rm -f "$TMP_STATS"
fi
if [ -f README.md ] && [ -f requirements.txt ]; then
	echo "Updating dependencies list (fetching from PyPI)..."
	TMP_DEPS=$(mktemp)
	{
		echo '```markdown'
		while IFS= read -r requirement; do
			case "$requirement" in
				''|\#*)
					continue
					;;
			esac
			# derive package name (strip extras and version specifiers)
			pkg=$(printf '%s' "$requirement" | sed -E 's/\[.*\]//; s/[<>=!~].*$//; s/\s.*$//')
			pkg_lc=$(printf '%s' "$pkg" | tr '[:upper:]' '[:lower:]')

			# try fetch metadata from PyPI
			info=$(curl -s --fail "https://pypi.org/pypi/$pkg_lc/json" || true)
			if [ -n "$info" ]; then
				summary_version=$(printf '%s' "$info" | python3 -c 'import sys,json
d=json.load(sys.stdin)
info=d.get("info",{})
s=info.get("summary") or ""
v=info.get("version") or ""
s=s.replace("\\n"," ").strip()
print(s+"||"+v)') || true
				summary=${summary_version%%||*}
				version=${summary_version#*||}
				if [ -n "$summary" ]; then
					echo "- \`$requirement\` - $summary (latest: $version)"
				else
					echo "- \`$requirement\` - latest: $version"
				fi
			else
				echo "- \`$requirement\`"
			fi
		done < requirements.txt
		echo '```'
		echo "<!--DEPS-END-->"
	} > "$TMP_DEPS"
	if grep -q "<!--DEPS-START-->" README.md; then
		sed -n '1,/<!--DEPS-START-->/p' README.md > README.md.tmp
		cat "$TMP_DEPS" >> README.md.tmp
		sed -n '/<!--DEPS-END-->/,$p' README.md | sed '1d' >> README.md.tmp
		mv README.md.tmp README.md
	fi
	echo "  Dependencies updated ✓"
	rm -f "$TMP_DEPS"
fi

if [ -f README.md ] && [ -f .env ]; then
	echo "Copying environment variable names to README..."
	python3 - << 'PYSCRIPT'
import os

env_file = '.env'
if not os.path.isfile(env_file):
	print(f"{env_file} not found. Skipping environment variable update.")
else:
	with open(env_file, 'r', encoding='utf-8') as f:
		lines = f.readlines()
	var_names = []
	for line in lines:
		line = line.strip()
		if line and not line.startswith('#') and '=' in line:
			var_name = line.split('=', 1)[0].strip()
			var_names.append(var_name)
	if var_names:
		readme_file = 'README.md'
		if os.path.isfile(readme_file):
			with open(readme_file, 'r', encoding='utf-8') as f:
				readme_content = f.read()
			start_marker = '<!--ENV-START-->'
			end_marker = '<!--ENV-END-->'
			if start_marker in readme_content and end_marker in readme_content:
				# preserve markers and replace the inner block with a code fence listing env keys
				s_idx = readme_content.find(start_marker) + len(start_marker)
				e_idx = readme_content.find(end_marker)
				prefix = readme_content[:s_idx]
				suffix = readme_content[e_idx:]
				env_block = '\n```env\n'
				for var in var_names:
					env_block += f"{var}=\n"
				env_block += '```\n'
				new_content = prefix + env_block + suffix
				with open(readme_file, 'w', encoding='utf-8') as f:
					f.write(new_content)
				print("  Environment variables updated ✓")
			else:
				print(f"Markers {start_marker} and {end_marker} not found in {readme_file}. Skipping update.")
		else:
			print(f"{readme_file} not found. Skipping environment variable update.")
PYSCRIPT
fi

echo "✅ All updates completed!"