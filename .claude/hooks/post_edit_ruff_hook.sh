#!/bin/bash

# Post-edit Python linting hook for Claude Code
# This hook runs ruff to check Python files after editing
# Input: JSON via stdin from Claude Code
# Output: JSON response with decision control

# Read JSON input from stdin
INPUT=$(cat)

# Extract file path from the JSON input
# The input structure for PostToolUse contains: tool_use.result.filePath
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_use.result.filePath // empty')

# If no file path found, try alternate locations in the JSON
if [ -z "$FILE_PATH" ]; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_use.result.file_path // empty')
fi

if [ -z "$FILE_PATH" ]; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_use.input.file_path // empty')
fi

# If still no file path, exit gracefully
if [ -z "$FILE_PATH" ]; then
  echo '{"decision": "approve", "message": "No file path found in hook input"}'
  exit 0
fi

# Only check Python files
if [[ ! "$FILE_PATH" =~ \.py$ ]]; then
  echo '{"decision": "approve", "message": "Not a Python file, skipping linting"}'
  exit 0
fi

# Check if ruff is installed
if ! command -v ruff &> /dev/null; then
  echo '{"decision": "approve", "message": "⚠️ ruff not installed, skipping linting", "error": true}'
  exit 0
fi

# Run ruff linting
RUFF_OUTPUT=$(ruff check "$FILE_PATH" 2>&1)
RUFF_EXIT_CODE=$?

# Prepare the response message
if [ $RUFF_EXIT_CODE -eq 0 ]; then
  VALIDATION_MESSAGE="✅ Ruff linting passed for $(basename "$FILE_PATH")"
  ERROR_STATUS=false
else
  # Clean up the output for JSON encoding
  CLEANED_OUTPUT=$(echo "$RUFF_OUTPUT" | head -20 | jq -Rs .)
  VALIDATION_MESSAGE="❌ Ruff linting issues found in $(basename "$FILE_PATH"):\n$CLEANED_OUTPUT"
  ERROR_STATUS=true
fi

# Create JSON response
# Note: We always approve to not block the edit, but we show the validation results
cat <<EOF
{
  "decision": "approve",
  "message": $(echo -n "$VALIDATION_MESSAGE" | jq -Rs .),
  "metadata": {
    "file": "$FILE_PATH",
    "linting_issues": $ERROR_STATUS,
    "exit_code": $RUFF_EXIT_CODE
  }
}
EOF

exit 0