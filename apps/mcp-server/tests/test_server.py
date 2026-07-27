"""MCP scaffold tests."""

from gradpath_mcp import create_server


def test_server_has_expected_name() -> None:
    server = create_server()

    assert server.name == "GradPath AI"
