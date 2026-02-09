"""Tests for EcoFlow River 3 entities."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from homeassistant.components.ecoflow_river3_plus.client import (
    EcoflowRiver3ConnectionError,
)
from homeassistant.components.ecoflow_river3_plus.const import UPDATE_INTERVAL
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.util import utcnow

from .conftest import MOCK_DATA_RECOVERED

from tests.common import MockConfigEntry, async_fire_time_changed


async def test_sensor_states(
    hass: HomeAssistant,
    mock_ecoflow_client: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that entities are created with expected values."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED

    charge_state = hass.states.get("sensor.ecoflow_river_3_plus_charge_level")
    assert charge_state
    assert charge_state.state == "76"

    total_load_state = hass.states.get("sensor.ecoflow_river_3_plus_output_power")
    assert total_load_state
    assert pytest.approx(float(total_load_state.state)) == 258.8

    ac_input_state = hass.states.get(
        "binary_sensor.ecoflow_river_3_plus_ac_input_active"
    )
    assert ac_input_state
    assert ac_input_state.state == "on"


async def test_entity_availability_recovery(
    hass: HomeAssistant,
    mock_ecoflow_client: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test availability handling when communication fails and recovers."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.ecoflow_river_3_plus_charge_level")
    assert state
    assert state.state == "76"

    mock_ecoflow_client.update.side_effect = EcoflowRiver3ConnectionError("no data")
    future = utcnow() + UPDATE_INTERVAL
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("sensor.ecoflow_river_3_plus_charge_level")
    assert state
    assert state.state == STATE_UNAVAILABLE

    mock_ecoflow_client.update.side_effect = None
    mock_ecoflow_client.update.return_value = MOCK_DATA_RECOVERED
    async_fire_time_changed(hass, future + timedelta(seconds=UPDATE_INTERVAL.seconds))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("sensor.ecoflow_river_3_plus_charge_level")
    assert state
    assert state.state == "75"
