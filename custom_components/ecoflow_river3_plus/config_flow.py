"""Config flow for EcoFlow River 3."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo
import voluptuous as vol

from homeassistant.components import usb
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_DEVICE
from homeassistant.core import callback
from homeassistant.helpers.service_info.usb import UsbServiceInfo

from .client import (
    EcoflowRiver3Client,
    EcoflowRiver3Data,
    EcoflowRiver3Error,
    EcoflowRiver3NoHidDeviceError,
)
from .const import (
    CONF_DEVICE_SERIAL_NUMBER,
    CONF_PRODUCT_ID,
    CONF_USB_SERIAL_NUMBER,
    CONF_VENDOR_ID,
    DEFAULT_NAME,
    DEFAULT_PRODUCT_ID,
    DEFAULT_VENDOR_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class EcoflowRiver3Connection:
    """Connection details for an EcoFlow River 3 device."""

    device: str
    vendor_id: int
    product_id: int
    usb_serial_number: str | None


def _format_id(value: int | str | None) -> str:
    """Format USB IDs to a stable uppercase string."""
    if isinstance(value, str):
        return value.removeprefix("0x").upper().zfill(4)
    return f"{value or 0:04X}"


def _parse_id(value: int | str | None, fallback: int) -> int:
    """Parse USB ID values from discovery payloads."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 16)
    return fallback


def _generate_unique_id(port: ListPortInfo | UsbServiceInfo) -> str:
    """Generate a unique ID from USB metadata."""
    return (
        f"{_format_id(port.vid)}:{_format_id(port.pid)}_{port.serial_number}_"
        f"{port.manufacturer}_{port.description}"
    )


def _build_entry_data(
    connection: EcoflowRiver3Connection,
    telemetry: EcoflowRiver3Data | None = None,
) -> dict[str, Any]:
    """Build config entry data for the selected device."""
    data: dict[str, Any] = {
        CONF_DEVICE: connection.device,
        CONF_VENDOR_ID: connection.vendor_id,
        CONF_PRODUCT_ID: connection.product_id,
    }

    if connection.usb_serial_number:
        data[CONF_USB_SERIAL_NUMBER] = connection.usb_serial_number

    if telemetry and telemetry.device_serial_number:
        data[CONF_DEVICE_SERIAL_NUMBER] = telemetry.device_serial_number

    return data


def _entry_title(telemetry: EcoflowRiver3Data | None) -> str:
    """Generate the config entry title."""
    if telemetry and telemetry.device_serial_number:
        return f"{DEFAULT_NAME} {telemetry.device_serial_number}"
    return DEFAULT_NAME


def _is_supported_port(port: ListPortInfo) -> bool:
    """Check if a serial port can belong to an EcoFlow River 3."""
    return port.vid == DEFAULT_VENDOR_ID and port.pid == DEFAULT_PRODUCT_ID


def _validate_device(connection: EcoflowRiver3Connection) -> EcoflowRiver3Data:
    """Try reading one telemetry sample from the selected device."""
    _LOGGER.debug(
        "Validating device=%s vid=%04x pid=%04x usb_serial=%s",
        connection.device,
        connection.vendor_id,
        connection.product_id,
        connection.usb_serial_number,
    )
    client = EcoflowRiver3Client(
        serial_device=connection.device,
        vendor_id=connection.vendor_id,
        product_id=connection.product_id,
        usb_serial_number=connection.usb_serial_number,
    )
    try:
        return client.update()
    finally:
        client.close()


def _discover_ports() -> dict[str, ListPortInfo]:
    """Discover compatible USB serial ports."""
    devices = {
        usb.get_serial_by_id(port.device): port
        for port in comports()
        if _is_supported_port(port)
    }
    _LOGGER.debug("Discovered %d compatible serial port(s)", len(devices))
    return devices


class EcoflowRiver3ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle an EcoFlow River 3 config flow."""

    VERSION = 1

    @callback
    def _connection_from_port(
        self,
        device: str,
        port: ListPortInfo,
    ) -> EcoflowRiver3Connection:
        """Build connection details from a serial port."""
        return EcoflowRiver3Connection(
            device=device,
            vendor_id=port.vid or DEFAULT_VENDOR_ID,
            product_id=port.pid or DEFAULT_PRODUCT_ID,
            usb_serial_number=port.serial_number,
        )

    async def _async_validate(
        self, connection: EcoflowRiver3Connection
    ) -> EcoflowRiver3Data:
        """Validate connectivity for a selected device."""
        return await self.hass.async_add_executor_job(_validate_device, connection)

    async def async_step_usb(self, discovery_info: UsbServiceInfo) -> ConfigFlowResult:
        """Handle USB discovery."""
        connection = EcoflowRiver3Connection(
            device=await self.hass.async_add_executor_job(
                usb.get_serial_by_id, discovery_info.device
            ),
            vendor_id=_parse_id(discovery_info.vid, DEFAULT_VENDOR_ID),
            product_id=_parse_id(discovery_info.pid, DEFAULT_PRODUCT_ID),
            usb_serial_number=discovery_info.serial_number,
        )

        base_data = _build_entry_data(connection)
        await self.async_set_unique_id(usb.usb_unique_id_from_service_info(discovery_info))
        self._abort_if_unique_id_configured(updates=base_data)

        try:
            telemetry = await self._async_validate(connection)
        except EcoflowRiver3NoHidDeviceError as err:
            _LOGGER.warning("USB discovery failed: %s", err)
            return self.async_abort(reason="no_hid_device")
        except EcoflowRiver3Error as err:
            _LOGGER.warning("USB discovery failed: %s", err)
            return self.async_abort(reason="cannot_connect")

        return self.async_create_entry(
            title=_entry_title(telemetry),
            data=_build_entry_data(connection, telemetry),
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        if self._async_in_progress():
            return self.async_abort(reason="already_in_progress")

        all_ports = await self.hass.async_add_executor_job(_discover_ports)
        configured_devices = {
            entry.data[CONF_DEVICE] for entry in self._async_current_entries()
        }
        available_ports = {
            device: port
            for device, port in all_ports.items()
            if device not in configured_devices
        }

        if not available_ports:
            _LOGGER.debug("No unconfigured compatible devices found")
            return self.async_abort(reason="no_devices_found")

        errors: dict[str, str] = {}
        if user_input is not None:
            selected_device = user_input[CONF_DEVICE]
            selected_port = available_ports[selected_device]
            connection = self._connection_from_port(selected_device, selected_port)
            base_data = _build_entry_data(connection)

            unique_id = _generate_unique_id(selected_port)
            await self.async_set_unique_id(unique_id)

            try:
                self._abort_if_unique_id_configured(updates=base_data)
                telemetry = await self._async_validate(connection)
            except EcoflowRiver3NoHidDeviceError as err:
                _LOGGER.warning("Validation failed for %s: %s", selected_device, err)
                errors["base"] = "no_hid_device"
            except EcoflowRiver3Error as err:
                _LOGGER.warning("Validation failed for %s: %s", selected_device, err)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=_entry_title(telemetry),
                    data=_build_entry_data(connection, telemetry),
                )

        options = {
            device: usb.human_readable_device_name(
                port.device,
                port.serial_number,
                port.manufacturer,
                port.description,
                port.vid,
                port.pid,
            )
            for device, port in available_ports.items()
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE): vol.In(options)}),
            errors=errors,
        )
