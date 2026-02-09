"""Sensor platform for EcoFlow River 3."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .client import EcoflowRiver3Data
from .coordinator import EcoflowRiver3ConfigEntry
from .entity import EcoflowRiver3Entity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class EcoflowRiver3SensorEntityDescription(SensorEntityDescription):
    """Describe an EcoFlow River 3 sensor."""

    value_fn: Callable[[EcoflowRiver3Data], StateType]


def _minutes_or_none(value: int | None) -> int | None:
    """Normalize invalid minute values."""
    if value is None or value < 0:
        return None
    return value


SENSOR_DESCRIPTIONS: tuple[EcoflowRiver3SensorEntityDescription, ...] = (
    EcoflowRiver3SensorEntityDescription(
        key="charge_level",
        translation_key="charge_level",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.charge_level,
    ),
    EcoflowRiver3SensorEntityDescription(
        key="battery_time_remaining",
        translation_key="battery_time_remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _minutes_or_none(data.battery_time_remaining),
    ),
    EcoflowRiver3SensorEntityDescription(
        key="remaining_charge_time",
        translation_key="remaining_charge_time",
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _minutes_or_none(data.remaining_charge_time),
    ),
    EcoflowRiver3SensorEntityDescription(
        key="total_load",
        translation_key="total_load",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.total_load,
    ),
    EcoflowRiver3SensorEntityDescription(
        key="total_draw",
        translation_key="total_draw",
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.total_draw,
    ),
    EcoflowRiver3SensorEntityDescription(
        key="ac_draw",
        translation_key="ac_draw",
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.ac_draw,
    ),
    EcoflowRiver3SensorEntityDescription(
        key="solar_dc_draw",
        translation_key="solar_dc_draw",
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.solar_dc_draw,
    ),
    EcoflowRiver3SensorEntityDescription(
        key="ac_load",
        translation_key="ac_load",
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.ac_load,
    ),
    EcoflowRiver3SensorEntityDescription(
        key="dc_load",
        translation_key="dc_load",
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.dc_load,
    ),
    EcoflowRiver3SensorEntityDescription(
        key="usb_a_load",
        translation_key="usb_a_load",
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.usb_a_load,
    ),
    EcoflowRiver3SensorEntityDescription(
        key="usb_c_load",
        translation_key="usb_c_load",
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.usb_c_load,
    ),
    EcoflowRiver3SensorEntityDescription(
        key="system_temperature",
        translation_key="system_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.system_temperature,
    ),
    EcoflowRiver3SensorEntityDescription(
        key="battery_temperature",
        translation_key="battery_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.battery_temperature,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EcoflowRiver3ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up EcoFlow River 3 sensors."""
    async_add_entities(
        EcoflowRiver3Sensor(entry.runtime_data, description)
        for description in SENSOR_DESCRIPTIONS
    )


class EcoflowRiver3Sensor(EcoflowRiver3Entity, SensorEntity):
    """Representation of an EcoFlow River 3 sensor."""

    entity_description: EcoflowRiver3SensorEntityDescription

    @property
    def native_value(self) -> StateType:
        """Return the current sensor state."""
        return self.entity_description.value_fn(self.coordinator.data)
