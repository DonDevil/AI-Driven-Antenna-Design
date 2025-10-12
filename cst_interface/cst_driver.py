import json
import os
from cst.interface import DesignEnvironment

class CSTDriver:
    def __init__(self, cst_project=None):
        self.de = DesignEnvironment()
        self.mws = self.de.new_mws() if cst_project is None else self.de.open_mws(cst_project)

        # Load macro commands
        json_path = os.path.join(os.path.dirname(__file__), "commands.json")
        with open(json_path, "r") as f:
            self.commands = json.load(f)

    def run_command(self, name: str, **kwargs):
        """
        Run a predefined CST VBA macro by name with optional parameters.
        Example:
            driver.run_command("export_s11", filename="C:\\temp\\s11.txt")
        """
        if name not in self.commands:
            raise ValueError(f"Unknown command: {name}")

        macro = self.commands[name]
        if kwargs:
            macro = macro.format(**kwargs)

        self.mws.model3d.add_to_history(name, macro)

    def run_solver(self):
        """Shortcut for running solver directly"""
        self.run_command("run_solver")
