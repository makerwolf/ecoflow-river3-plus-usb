"""Base entity for EcoFlow River 3 integration."""

from __future__ import annotations

from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import EcoflowRiver3Coordinator


class EcoflowRiver3Entity(CoordinatorEntity[EcoflowRiver3Coordinator]):
    """Base class for EcoFlow River 3 entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcoflowRiver3Coordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize an EcoFlow River 3 entity."""
        super().__init__(coordinator, context=description.key)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.unique_device_id}_{description.key}"
        self._attr_device_info = coordinator.device_info
