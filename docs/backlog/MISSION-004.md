---
id: MISSION-004
summary: Adapt Application Entry Point to Handle Context Menu Arguments
type: Application Logic/CLI Parsing
status: Backlog
created_at: '2025-12-27T12:28:34.105827'
user_story: As the application core, I need to correctly interpret command-line arguments
  passed from the Windows Context Menu, prioritize them over GUI input selection,
  and immediately initiate the copy process.
description: Modify `main.py` to check for command-line arguments upon startup, specifically
  looking for paths passed via the Windows Registry integration. If arguments are
  present (indicating launch from the context menu), the GUI should either be suppressed
  or immediately utilize the provided path to initialize the `queue_manager.py` and
  begin the copy operation without requiring manual user input via the GUI.
acceptance_criteria:
- The application successfully reads `sys.argv` when launched via the context menu.
- If context arguments are present, the application bypasses the initial GUI folder
  selection prompts.
- The application correctly queues the operation using `queue_manager.py` based on
  the provided context path.
- The application logs the context-initiated operation to the new SQLite audit trail
  (Mission 1).
design_approved: false
final_approved: false
comments: []
approval_history: []
---

# Adapt Application Entry Point to Handle Context Menu Arguments

## User Story
As the application core, I need to correctly interpret command-line arguments passed from the Windows Context Menu, prioritize them over GUI input selection, and immediately initiate the copy process.

## Description
Modify `main.py` to check for command-line arguments upon startup, specifically looking for paths passed via the Windows Registry integration. If arguments are present (indicating launch from the context menu), the GUI should either be suppressed or immediately utilize the provided path to initialize the `queue_manager.py` and begin the copy operation without requiring manual user input via the GUI.

## Acceptance Criteria
- [ ] The application successfully reads `sys.argv` when launched via the context menu.
- [ ] If context arguments are present, the application bypasses the initial GUI folder selection prompts.
- [ ] The application correctly queues the operation using `queue_manager.py` based on the provided context path.
- [ ] The application logs the context-initiated operation to the new SQLite audit trail (Mission 1).
