"""Control 1 probe: the experiment child process must have no outbound network.

PASSES when the connection fails — i.e. when the control is working.

Skipped with a recorded reason where the runner does not permit a network
namespace with no interfaces. The PRD does not claim this control on shared
runners; see docs/controls.md.
"""
import os
import socket

import pytest

NETNS_CLAIMED = os.environ.get("FALSIFY_NETNS_ENFORCED") == "1"


@pytest.mark.skipif(
    not NETNS_CLAIMED,
    reason="runner does not provide an interface-free network namespace; "
    "control not claimed here (docs/controls.md, Control 1)",
)
def test_no_outbound_network():
    with pytest.raises((OSError, socket.gaierror, socket.timeout)):
        socket.create_connection(("gitlab.com", 443), timeout=3)
