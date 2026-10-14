"""Compatibility names for the merged 0.25 workspace owner.

The canonical implementation lives in GameToolGameWorkspaces; this module does
not subclass an older host or create a second registry/queue.
"""
from GameToolGameWorkspaces import (GameWorkspaces, KeybindScopedAutomation,
    KeybindOnlyAutomation)

class KeybindGameWorkspaces(GameWorkspaces):
    pass

__all__=["KeybindGameWorkspaces","KeybindScopedAutomation","KeybindOnlyAutomation"]
