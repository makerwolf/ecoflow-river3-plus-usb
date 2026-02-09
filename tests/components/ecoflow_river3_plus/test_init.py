"""Tests for EcoFlow River 3 integration setup."""

from __future__ import annotations

from unittest.mock import MagicMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


async def test_async_setup_and_unload_entry(
    hass: HomeAssistant,
    mock_ecoflow_client: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test successful setup and unload."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    mock_ecoflow_client.close.assert_called()
