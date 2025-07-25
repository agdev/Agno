I need to create or update a session summary file with the following parameters:
- First argument: Session name (e.g., "faq_fix")
- Second argument: Target directory path (e.g., "/home/yoda/Library/Projects/Portfolio/Agno/docs/changes/sessions")

Usage: /create_update_session_summary session_name target_directory

Steps:
1. Parse arguments to extract session name and target directory
2. Create the filename format: {session_name}_session_summary_{current_date}.md where current_date is in YYYYMMDD format
3. Ensure the target directory exists
4. Check if the file already exists in the specified directory
5. If the file exists, read its current content and update it with new session information
6. If the file doesn't exist, create a new one with a detailed session summary template
7. Generate a comprehensive summary of the current session including:
   - Session overview and objectives
   - Key tasks completed
   - Code changes made
   - Issues encountered and resolved
   - Next steps and follow-up items
   - Technical decisions and rationale

Let me parse the arguments and create the session summary:

```bash
# Parse arguments - expecting "session_name target_directory"
IFS=' ' read -r session_name target_directory <<< "$ARGUMENTS"

# Validate arguments
if [ -z "$session_name" ] || [ -z "$target_directory" ]; then
    echo "Error: Both session_name and target_directory are required"
    echo "Usage: /create_update_session_summary session_name target_directory"
    echo "Example: /create_update_session_summary faq_fix /home/yoda/Library/Projects/Portfolio/Agno/docs/changes/sessions"
    exit 1
fi

# Normalize the target directory path
target_directory=$(realpath "$target_directory" 2>/dev/null || echo "$target_directory")

# Create the target directory if it doesn't exist
mkdir -p "$target_directory"
if [ $? -ne 0 ]; then
    echo "Error: Failed to create directory $target_directory"
    exit 1
fi

# Verify the directory was created and is accessible
if [ ! -d "$target_directory" ]; then
    echo "Error: Directory $target_directory does not exist after creation"
    exit 1
fi

if [ ! -w "$target_directory" ]; then
    echo "Error: Directory $target_directory is not writable"
    exit 1
fi

# Get current date in YYYYMMDD format
current_date=$(date +%Y%m%d)

# Create the filename
filename="${session_name}_session_summary_${current_date}.md"
filepath="${target_directory}/${filename}"

# Ensure filepath uses absolute path and normalize it
filepath=$(realpath "$filepath" 2>/dev/null || echo "$filepath")

echo "=== SESSION SUMMARY CREATION ==="
echo "Target file: $filepath"
echo "Directory: $target_directory"
echo "Session name: $session_name"
echo "Date: $current_date"
echo "Directory exists: $([ -d "$target_directory" ] && echo "YES" || echo "NO")"
echo "Directory writable: $([ -w "$target_directory" ] && echo "YES" || echo "NO")"
echo "=================================="

# Check if file exists and handle accordingly
if [ -f "$filepath" ]; then
    echo "✓ Updating existing session summary: $filename"
    echo "Current content of $filename:"
    cat "$filepath"
    echo "---"
    echo "Please provide additional information to update this session summary."
else
    echo "✓ Creating new session summary file: $filename"
    echo "Directory contents before creation:"
    ls -la "$target_directory"
    
    # Create the file with proper permissions
    touch "$filepath"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create file $filepath"
        exit 1
    fi
    
    echo "✓ File created successfully at: $filepath"
    echo "File exists: $([ -f "$filepath" ] && echo "YES" || echo "NO")"
fi
```

Now I'll create or update the session summary with detailed information about the current session, including all the key activities, code changes, decisions made, and next steps. The file will be placed in the exact directory specified as the second argument.