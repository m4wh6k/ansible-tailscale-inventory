#!/usr/bin/env python3
# MIT License

# Copyright (c) 2022 Mat Hornbeek

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import json
import platform
import subprocess
import sys
from typing import Any, TypedDict

ansible_inventory_type = dict[str, dict[str, list[str] | dict[str, Any]]]


class InventoryType(TypedDict):
    """
    Type annotation for internal representation of the inventory
    """

    metadata: dict[str, dict[str, Any]]  # Maps hostnames to mappings of their hostvars
    groups: dict[str, list[str]]  # Maps group names to their list of group members


class TailscaleHostType(TypedDict, total=False):
    """
    Type annotation for Tailscale hosts within status JSON
    """

    Active: bool
    Addrs: list[str] | None
    Capabilities: list[str]
    CapMap: dict[str, Any]
    Created: str
    CurAddr: str | None
    DNSName: str
    ExitNode: bool
    ExitNodeOption: bool
    HostName: str
    ID: str
    InEngine: bool
    InMagicSock: bool
    InNetworkMap: bool
    KeyExpiry: str
    LastHandshake: str
    LastSeen: str
    LastWrite: str
    Online: bool
    OS: str
    PeerAPIURL: list[str]
    PublicKey: str
    Relay: str
    RxBytes: int
    Tags: list[str]
    TailscaleIPs: list[str]
    TxBytes: int
    UserID: int


class TailscaleStatusType(TypedDict):
    """
    Type annotation for the Tailscale status JSON
    """

    AuthURL: str
    BackendState: str
    CertDomains: list[str]
    ClientVersion: dict[str, Any]
    CurrentTailnet: dict[str, Any]
    Health: Any
    MagicDNSSuffix: str
    Peer: dict[str, TailscaleHostType]
    Self: TailscaleHostType
    TailscaleIPs: list[str]
    TUN: bool
    User: dict[str, Any]
    Version: str


def get_tailscale_status() -> TailscaleStatusType:
    """
    Returns raw status information from the local tailscale install
    """

    # Select tailscale binary to run based upon OS name
    system_os_name = platform.system()
    if system_os_name == "Linux":
        tailscale_cmd = "tailscale"
    elif system_os_name == "Darwin":
        tailscale_cmd = "/Applications/Tailscale.app/Contents/MacOS/Tailscale"
    else:
        print(f"{system_os_name} not currently supported. Contributions welcome!")
        sys.exit(1)

    try:
        tailscale_proc = subprocess.run(  # noqa: S603
            [tailscale_cmd, "status", "--self", "--json"],
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as e:
        print(f"tailscale command not found: {e}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"tailscale command failed. Is tailscale running?: {e}")
        sys.exit(1)

    tailscale_output_json: TailscaleStatusType = json.loads(tailscale_proc.stdout)
    return tailscale_output_json


def assemble_all_tailscale_hosts(
    ts_status: TailscaleStatusType,
) -> list[TailscaleHostType]:
    """
    Processes tailscale status into a list of all hosts with their metadata, including
    the "self" host
    """

    all_hosts: list[TailscaleHostType] = list(ts_status["Peer"].values())
    all_hosts.append(ts_status["Self"])
    return all_hosts


def assemble_inventory(
    tailscale_hosts: list[TailscaleHostType],
    tailscale_self_hostname: str,
) -> InventoryType:
    """
    Given a list of tailscale hosts with their metadata return an inventory object. This
    is where we select set the metadata ansible will be aware of for each host as
    hostvars, and defines group memberships. The "self" hostname needs to be identified
    explicitly so it can be put into its own group
    """

    # Create the base inventory data structure
    inventory: InventoryType = {
        "metadata": {},
        "groups": {
            "all": [],
            "online": [],
            "offline": [],
            "self": [tailscale_self_hostname],
        },
    }

    for host_data in tailscale_hosts:
        # We intentionally avoid adding any the funnel-ingress-node to the inventory
        # because we can't manage it
        if host_data["HostName"] == "funnel-ingress-node":
            continue

        # We ignore endpoints that have no OS, like Mullvad exit nodes
        if not host_data["OS"]:
            continue

        # We add each host to the list of all hosts
        inventory["groups"]["all"].append(host_data["HostName"])

        # Set host's inventory metadata
        inventory["metadata"][host_data["HostName"]] = {
            "ansible_host": host_data["DNSName"],
            "tailscale_ips": host_data["TailscaleIPs"],
        }

        # Hosts that are offline will still be present in the inventory. We set-up these
        # groups so host patterns can be used to skip offline hosts. We could omit the
        # offline hosts entirely but there may be use cases where one does want to see
        # an error if they attempt to connect to an offline host
        if host_data["Online"]:
            inventory["groups"]["online"].append(host_data["HostName"])
        else:
            inventory["groups"]["offline"].append(host_data["HostName"])

        # If we encounter an OS type we don't have in the inventory yet, we create a
        # group for it, then we always add each host to the group for that OS
        if host_data["OS"] not in inventory["groups"]:
            inventory["groups"][host_data["OS"]] = []
        inventory["groups"][host_data["OS"]].append(host_data["HostName"])

        # We create groups for host tags. Tag names have to be modified to be compatible
        # with ansible
        if "Tags" in host_data:
            for tag in host_data["Tags"]:
                safe_tag = tag.replace(":", "_").replace("-", "_")
                if safe_tag in inventory["groups"]:
                    inventory["groups"][safe_tag].append(host_data["HostName"])
                else:
                    inventory["groups"][safe_tag] = [host_data["HostName"]]

    return inventory


def format_ansible_inventory(inventory: InventoryType) -> ansible_inventory_type:
    """
    Given an inventory object, returns the inventory formatted to be read by ansible
    """

    # Create the base ansible inventory object
    ansible_inventory: ansible_inventory_type = {
        "_meta": {"hostvars": inventory["metadata"]},
    }

    # Create groups
    for key, value in inventory["groups"].items():
        ansible_inventory[key] = {"hosts": value}

    return ansible_inventory


def tailscale_status_to_ansible_inventory(
    ts_status: TailscaleStatusType,
) -> ansible_inventory_type:
    """
    Given a tailscale status object this returns an ansible inventory object
    """

    ts_all_hosts = assemble_all_tailscale_hosts(ts_status)
    inventory = assemble_inventory(ts_all_hosts, ts_status["Self"]["HostName"])
    return format_ansible_inventory(inventory)


def main() -> None:
    """
    This is the main function run when the script is executed
    """

    ts_status = get_tailscale_status()
    ansible_inventory = tailscale_status_to_ansible_inventory(ts_status)
    print(json.dumps(ansible_inventory, indent=2, sort_keys=True))


if __name__ == "__main__":
    # This makes it so the main() function will only run when the script is executed
    # directly vs being imported for tests
    main()
