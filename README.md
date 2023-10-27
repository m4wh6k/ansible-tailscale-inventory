# ansible-tailscale-inventory
Dynamic Ansible inventory for your Tailscale hosts. Allows you to reach your
Tailscale hosts easily with Ansible.

## Usage
From one of your Tailscale nodes on your network, make
`ansible-tailscale-inventory.py` available as an inventory to Ansible. This can
be done as an argument to the `-i` option on Ansible commands, or by setting
the `ANSIBLE_INVENTORY` environment variable's value as the path to the script.

Note: At the time of writing, the inventory script has been tested with macOS
and Linux, but not Windows.

## Ansible Groups
`ansible-tailscale-inventory.py` automatically provides a few groups.
- There are groups of hosts for each operating system (`macOS`, `linux`, etc)
- Online hosts are found in the `online` group, offline hosts in the `offline`
group
- The `self` group includes the local host
- Each Tailscale tag that has at least one host will be a group as well. The
  name will be formatted as `tag_TagName` (dashes will be replace with underscores)

## Inventory Metadata
The inventory automatically adds all available Tailscale IPs as a list in the
fact `tailscale_ips`.

## Contributing
Contributions are welcomed. Please feel free to submit or fix issues.
Please format python with `black`.
