---
id: MISSION-003
summary: Implement Windows Registry Hooks for Context Menu Integration
type: OS Integration/Windows Specific
status: Backlog
created_at: '2025-12-27T12:28:34.103395'
user_story: As a Windows user, I want to right-click a folder in Explorer, select
  'Copy with FolderCopier', and have the application launch immediately with the selected
  folder path passed as an argument.
description: Develop a utility function (likely in `utils.py` or a new module, e.g.,
  `win_integration.py`) to interact with the Windows Registry. This function must
  create the necessary keys under `HKEY_CLASSES_ROOT\Directory\shell` to register
  the context menu item. The command executed must correctly pass the selected folder
  path (`%V` or similar Windows placeholder) as a command-line argument to `main.py`
  (or a wrapper script if necessary).
acceptance_criteria:
- A new Python function exists to safely write the required context menu keys to the
  Windows Registry.
- The registered context menu item appears when right-clicking any folder in Windows
  Explorer.
- Executing the context menu item launches the application.
- The path of the right-clicked folder is successfully parsed as a command-line argument
  within `main.py`.
design_approved: false
final_approved: false
comments: []
approval_history: []
---

# Implement Windows Registry Hooks for Context Menu Integration

## User Story
As a Windows user, I want to right-click a folder in Explorer, select 'Copy with FolderCopier', and have the application launch immediately with the selected folder path passed as an argument.

## Description
Develop a utility function (likely in `utils.py` or a new module, e.g., `win_integration.py`) to interact with the Windows Registry. This function must create the necessary keys under `HKEY_CLASSES_ROOT\Directory\shell` to register the context menu item. The command executed must correctly pass the selected folder path (`%V` or similar Windows placeholder) as a command-line argument to `main.py` (or a wrapper script if necessary).

## Acceptance Criteria
- [ ] A new Python function exists to safely write the required context menu keys to the Windows Registry.
- [ ] The registered context menu item appears when right-clicking any folder in Windows Explorer.
- [ ] Executing the context menu item launches the application.
- [ ] The path of the right-clicked folder is successfully parsed as a command-line argument within `main.py`.
