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