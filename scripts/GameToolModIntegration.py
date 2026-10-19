"""Additive mounting of Mods and shared AI controls in the verified existing Hub."""
from __future__ import annotations
from tkinter import ttk, TclError
from types import SimpleNamespace
from GameToolAutomation import AutomationService
from GameToolAutomationPanel import AutomationPanel
from game_mod_ops.panel import ModWorkflowPanel

VERSION = "0.1.1"


def navigation_registry(workspace_api):
    # Existing stable identifiers/default tests remain unchanged. This host opts
    # into additive routes; view switching never constructs another pane.
    def record(ident,title,route,summary,keywords):
        return dict(id=ident,title=title,route=route,domain=workspace_api.DOMAINS[3],
                    summary=summary,scope='Explicit actions only; no games, capture or driver changes',keywords=keywords)
    additions=[record('page.mods','Mods & downloads','mods','Plan, download and stage original mod files with preserved receipts.','nexus kingmaker umm mods'),
               record('page.automation','AI & automation','automation','Review typed AI requests, share sanitized summaries and approve exact actions.','ai mcp agent automation context'),
               record('page.system-control','System control center','system-control','Explore selected instructions and capabilities, inspect activity and check a draft request.','architecture instructions triggers sync chats preflight')]
    goals=[record('goal.mods','Prepare my game mods','mods','Choose one game recipe and review downloads before installation.','mods download manager'),
           record('goal.ai','Work with AI safely','automation','Preview requests and share only selected information.','ai automation approval reports'),
           record('goal.understand-system','Understand my system and request','system-control','Read source evidence and compare request wording before submission.','architecture rules request preflight')]
    return workspace_api.FeatureRegistry(features=workspace_api.DEFAULT_FEATURES+tuple(additions),
                                        goals=workspace_api.DEFAULT_GOALS+tuple(goals))


class Integration:
    def __init__(self,notebook,data_dir,status,focus=False):
        self.service=AutomationService(data_dir)
        ModView, AIView = ModWorkflowPanel, AutomationPanel
        if focus:
            from GameToolFocusPanels import FocusModPanel, FocusAutomationPanel
            ModView, AIView = FocusModPanel, FocusAutomationPanel
        self.mods=ModView(notebook,data_root=self.service.mods_root)
        self.automation=AIView(notebook,self.service,status,
                                       peer_busy=lambda:bool(self.mods.worker and self.mods.worker.is_alive()))
        self.mods.peer_busy=lambda:self.automation.busy
        self.mods.pack_propagate(True)
        notebook.add(self.mods,text='Mods')
        notebook.add(self.automation,text='AI & automation')
        self.routes={'mods':self.mods,'automation':self.automation}
        self.system_control = None
        try:
            from GameToolSystemControlPanel import SystemControlPanel
            self.system_control = SystemControlPanel(notebook)
            notebook.add(self.system_control, text='System control')
            self.routes['system-control'] = self.system_control
        except (ImportError, OSError, ValueError, TclError):
            # A missing optional view must not disable existing Mods/AI owners.
            pass
        # Do not hand tkinter's mutable children dictionary to generic role discovery.
        self.mods_roles=SimpleNamespace(mode=self.mods.mode,status=self.mods.status,
            tree=self.mods.tree,details=self.mods.details,checks=self.mods.checks)
        self.automation_roles=SimpleNamespace(tree=self.automation.tree,output=self.automation.output,
            state=self.automation.state,watch=self.automation.watch,buttons=self.automation.buttons)
    def can_close(self):
        a=self.mods.can_close(); b=self.automation.can_close()
        return a and b
    def close(self):
        if self.system_control is not None:
            self.system_control.close()
        self.automation.close()
        # The Mods pane cancels its own callbacks on Destroy.
