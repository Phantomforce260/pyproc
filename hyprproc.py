import subprocess
import re

from dataclasses import dataclass

@dataclass
class HyprClient:
    address: str
    title: str
    workspace: str
    class_name: str
    pid: int

    def __str__(self):
        return f"""{self.title.strip()} (PID {self.pid})
    Class: {self.class_name} | Workspace: {self.workspace}"""

class Hypr:
    def clients_raw(self):
        return subprocess.run(
            ["hyprctl", "clients"],
            capture_output=True,
            text=True
        ).stdout

    def clients(self):
        raw = self.clients_raw()

        blocks = raw.strip().split("\n\n")
        clients = []

        for block in blocks:
            lines = block.splitlines()

            header = lines[0]
            match = re.match(r"Window (\S+) -> (.*):", header)

            if not match:
                continue

            address, title = match.groups()

            data = {}
            for line in lines[1:]:
                if ":" not in line:
                    continue
                key, value = line.strip().split(":", 1)
                data[key.strip()] = value.strip()

            workspace = int(data.get("workspace", "0").split()[0])
            class_name = data.get("class", str())
            pid = int(data.get("pid", 0))

            clients.append(HyprClient(
                address = address,
                title = title,
                workspace = workspace,
                class_name = class_name,
                pid = pid
            ))

        return clients


if __name__ == "__main__":
    hypr = Hypr()
    apps = hypr.clients()

    print(f"\n{'-' * 50}")
    print(f"   Running Applications ({len(apps)} found)")
    print(f"{'-' * 50}\n")
    for app in apps:
        print(app)
    print(f"\n{'-' * 50}\n")
