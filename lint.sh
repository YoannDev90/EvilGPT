#!/usr/bin/env bash
set -euo pipefail

# Format code
ruff format
isort .

# Print project tree (filtered)
if command -v tree >/dev/null 2>&1; then
	echo "\nProject tree:" 
	tree -a -I ".venv|.git|__pycache__" || true
	# Also update README.md section between <!-- TREE-START --> and <!-- TREE-END -->
	TMP_TREE=$(mktemp)
	tree -a -I ".venv|.git|__pycache__" > "$TMP_TREE" || true

	# Build new block file
	TMP_BLOCK=$(mktemp)
	{
		echo "<!-- TREE-START -->"
		echo '```'
		cat "$TMP_TREE"
		echo '```'
		echo "<!-- TREE-END -->"
	} > "$TMP_BLOCK"

	# Replace section in README.md
	README=README.md
	if grep -q "<!-- TREE-START -->" "$README"; then
		# head to start marker
		sed -n '1,/<!-- TREE-START -->/p' "$README" > "$README.tmp"
		# append new block
		cat "$TMP_BLOCK" >> "$README.tmp"
		# append rest after end marker
		sed -n '/<!-- TREE-END -->/,$p' "$README" | sed '1d' >> "$README.tmp"
		mv "$README.tmp" "$README"
	fi
	rm -f "$TMP_TREE" "$TMP_BLOCK"
else
	echo "\n'tree' not installed. Install with 'apt-get install tree' or 'brew install tree'."
fi