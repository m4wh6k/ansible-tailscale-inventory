#!/usr/bin/env python3

import json
import platform
import subprocess

if platform.system() == "Linux":
    tailscale_cmd = "tailscale"
elif platform.system() == "Darwin":
    tailscale_cmd = "/Applications/Tailscale.app/Contents/MacOS/Tailscale"

tailscale_proc = subprocess.run(
    [tailscale_cmd, "status", "--self", "--json"],
    capture_output=True,
)
tailscale_output_json = json.loads(tailscale_proc.stdout)

inventory = {
    "_meta": {"hostvars": {}},
    "all": {"hosts": []},
    "online": {"hosts": []},
    "offline": {"hosts": []},
    "self": {"hosts": [tailscale_output_json["Self"]["HostName"]]},
}

all_hosts = list(
    tailscale_output_json["Peer"].values(),
)
all_hosts.append(
    tailscale_output_json["Self"],
)

for v in all_hosts:
    inventory["all"]["hosts"].append(v["HostName"])

    inventory["_meta"]["hostvars"][v["HostName"]] = {
        "ansible_host": v["DNSName"],
        "tailscale_ips": v["TailscaleIPs"],
    }

    if v["Online"]:
        inventory["online"]["hosts"].append(v["HostName"])
    else:
        inventory["offline"]["hosts"].append(v["HostName"])

    if v["OS"] not in inventory:
        inventory[v["OS"]] = {"hosts": []}
    inventory[v["OS"]]["hosts"].append(v["HostName"])

    if "Tags" in v:
        for tag in v["Tags"]:
            safe_tag = tag.replace(":", "_")
            if safe_tag in inventory:
                inventory[safe_tag]["hosts"].append(v["HostName"])
            else:
                inventory[safe_tag] = {"hosts": [v["HostName"]]}

print(json.dumps(inventory))
