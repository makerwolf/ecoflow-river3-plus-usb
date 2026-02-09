"""DataUpdateCoordinator for EcoFlow River 3."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import EcoflowRiver3Client, EcoflowRiver3Data, EcoflowRiver3Error
from .const import (
    CONF_DEVICE_SERIAL_NUMBER,
    CONF_PRODUCT_ID,
    CONF_USB_SERIAL_NUMBER,
    CONF_VENDOR_ID,
    DEFAULT_NAME,
    DEFAULT_PRODUCT_ID,
    DEFAULT_VENDOR_ID,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

type EcoflowRiver3ConfigEntry = ConfigEntry[EcoflowRiver3Coordinator]


class EcoflowRiver3Coordinator(DataUpdateCoordinator[EcoflowRiver3Data]):
    """Coordinate EcoFlow River 3 telemetry polling."""

    config_entry: EcoflowRiver3ConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: EcoflowRiver3ConfigEntry) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

        vendor_id = int(config_entry.data.get(CONF_VENDOR_ID, DEFAULT_VENDOR_ID))
        product_id = int(config_entry.data.get(CONF_PRODUCT_ID, DEFAULT_PRODUCT_ID))
        usb_serial_number = config_entry.data.get(CONF_USB_SERIAL_NUMBER)

        self.api = EcoflowRiver3Client(
            serial_device=config_entry.data[CONF_DEVICE],
            vendor_id=vendor_id,
            product_id=product_id,
            usb_serial_number=usb_serial_number,
        )
        self._unavailable_logged = False
        _LOGGER.debug(
            "Configured device=%s vid=%04x pid=%04x usb_serial=%s",
            config_entry.data[CONF_DEVICE],
            vendor_id,
            product_id,
            usb_serial_number,
        )

    @property
    def unique_device_id(self) -> str:
        """Return the most stable available unique device identifier."""
        if self.data.device_serial_number:
            return self.data.device_serial_number

        if stored_serial := self.config_entry.data.get(CONF_DEVICE_SERIAL_NUMBER):
            return stored_serial

        return self.config_entry.entry_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device metadata for entity registry."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_device_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=self.config_entry.title or DEFAULT_NAME,
            serial_number=self.data.device_serial_number
            or self.config_entry.data.get(CONF_DEVICE_SERIAL_NUMBER),
        )

    async def async_shutdown(self) -> None:
        """Close connections held by the client."""
        await self.hass.async_add_executor_job(self.api.close)

    async def _async_update_data(self) -> EcoflowRiver3Data:
        """Fetch the latest telemetry from the power station."""
        try:
            data = await self.hass.async_add_executor_job(self.api.update)
        except EcoflowRiver3Error as err:
            if not self._unavailable_logged:
                _LOGGER.info("Device is unavailable: %s", err)
                _LOGGER.info(
                    "Check USB passthrough and confirm both serial and HID interfaces "
                    "are available inside Home Assistant"
                )
                self._unavailable_logged = True
            raise UpdateFailed(err) from err

        if self._unavailable_logged:
            _LOGGER.info("Device is back online")
            self._unavailable_logged = False

        if (
            data.device_serial_number
            and self.config_entry.data.get(CONF_DEVICE_SERIAL_NUMBER)
            != data.device_serial_number
        ):
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={
                    **self.config_entry.data,
                    CONF_DEVICE_SERIAL_NUMBER: data.device_serial_number,
                },
            )

        return data
