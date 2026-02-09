"""The EcoFlow River 3 integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import EcoflowRiver3ConfigEntry, EcoflowRiver3Coordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant, config_entry: EcoflowRiver3ConfigEntry
) -> bool:
    """Set up EcoFlow River 3 from a config entry."""
    coordinator = EcoflowRiver3Coordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()

    config_entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: EcoflowRiver3ConfigEntry
) -> bool:
    """Unload an EcoFlow River 3 config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        await config_entry.runtime_data.async_shutdown()
    return unload_ok
