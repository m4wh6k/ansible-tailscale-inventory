from ansible_tailscale_inventory import (
    tailscale_status_to_ansible_inventory,
)
from tests.mock_data import (
    expected_ansible_inventory_output,
    mock_tailscale_status_output,
)


def test_tailscale_status_to_ansible_inventory() -> None:
    """
    Using mock data we test given mock tailscale output the ansible inventory matches
    the expected output structure
    """

    assert (
        tailscale_status_to_ansible_inventory(mock_tailscale_status_output)
        == expected_ansible_inventory_output
    )
