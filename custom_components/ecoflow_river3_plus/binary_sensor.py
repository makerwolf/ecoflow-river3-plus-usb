"""Binary sensor platform for EcoFlow River 3."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .client import EcoflowRiver3Data
from .coordinator import EcoflowRiver3ConfigEntry
from .entity import EcoflowRiver3Entity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class EcoflowRiver3BinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describe an EcoFlow River 3 binary sensor."""

    is_on_fn: Callable[[EcoflowRiver3Data], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[EcoflowRiver3BinarySensorEntityDescription, ...] = (
    EcoflowRiver3BinarySensorEntityDescription(
        key="ac_input_active",
        translation_key="ac_input_active",
        device_class=BinarySensorDeviceClass.POWER,
        is_on_fn=lambda data: data.ac_input_active,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EcoflowRiver3ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up EcoFlow River 3 binary sensors."""
    async_add_entities(
        EcoflowRiver3BinarySensor(entry.runtime_data, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class EcoflowRiver3BinarySensor(EcoflowRiver3Entity, BinarySensorEntity):
    """Representation of an EcoFlow River 3 binary sensor."""

    entity_description: EcoflowRiver3BinarySensorEntityDescription

    @property
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        return self.entity_description.is_on_fn(self.coordinator.data)
