#!/bin/bash

# Post-edit Python type checking hook for Claude Code
# This hook runs pyright to check Python files after editing
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
  echo '{"decision": "approve", "message": "Not a Python file, skipping type checking"}'
  exit 0
fi

# Check if pyright is installed
if ! command -v pyright &> /dev/null; then
  echo '{"decision": "approve", "message": "⚠️ pyright not installed, skipping type checking", "error": true}'
  exit 0
fi

# Run pyright type checking
PYRIGHT_OUTPUT=$(pyright "$FILE_PATH" 2>&1)
PYRIGHT_EXIT_CODE=$?

# Prepare the response message
if [ $PYRIGHT_EXIT_CODE -eq 0 ]; then
  VALIDATION_MESSAGE="✅ Pyright type checking passed for $(basename "$FILE_PATH")"
  ERROR_STATUS=false
else
  # Clean up the output for JSON encoding
  CLEANED_OUTPUT=$(echo "$PYRIGHT_OUTPUT" | head -20 | jq -Rs .)
  VALIDATION_MESSAGE="❌ Pyright type errors found in $(basename "$FILE_PATH"):\n$CLEANED_OUTPUT"
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
    "type_errors": $ERROR_STATUS,
    "exit_code": $PYRIGHT_EXIT_CODE
  }
}
EOF

exit 0