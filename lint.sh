#!/usr/bin/env bash
set -euo pipefail

# Format code
ruff format
isort .

# Print project tree (filtered)
if command -v tree >/dev/null 2>&1; then
	echo "\nProject tree:"
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
	echo "\n'tree' not installed. Install with 'apt-get install tree' or 'brew install tree'."
fi

# Update README.md dependencies section from requirements.txt
if [ -f README.md ] && [ -f requirements.txt ]; then
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
	rm -f "$TMP_DEPS"
fi