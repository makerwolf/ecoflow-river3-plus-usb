"""Common fixtures for EcoFlow River 3 tests."""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from serial.tools.list_ports_common import ListPortInfo

from homeassistant.components.ecoflow_river3_plus.client import EcoflowRiver3Data
from homeassistant.components.ecoflow_river3_plus.const import (
    CONF_DEVICE_SERIAL_NUMBER,
    CONF_PRODUCT_ID,
    CONF_USB_SERIAL_NUMBER,
    CONF_VENDOR_ID,
    DEFAULT_NAME,
    DEFAULT_PRODUCT_ID,
    DEFAULT_VENDOR_ID,
    DOMAIN,
)
from homeassistant.const import CONF_DEVICE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.service_info.usb import UsbServiceInfo

from tests.common import MockConfigEntry

TEST_DEVICE = "/dev/ttyACM42"
TEST_USB_SERIAL = "RIVER3-USB"
TEST_DEVICE_SERIAL = "RIVER3-DEVICE-1234"

DISCOVERY_INFO = UsbServiceInfo(
    device=TEST_DEVICE,
    vid=f"{DEFAULT_VENDOR_ID:04X}",
    pid=f"{DEFAULT_PRODUCT_ID:04X}",
    serial_number=TEST_USB_SERIAL,
    manufacturer="EcoFlow",
    description="EcoFlow River 3",
)

MOCK_DATA = EcoflowRiver3Data(
    device_serial_number=TEST_DEVICE_SERIAL,
    charge_level=76,
    battery_time_remaining=64,
    remaining_charge_time=120,
    system_temperature=30,
    battery_temperature=32,
    total_load=258.8,
    total_draw=29.2,
    ac_draw=0.0,
    solar_dc_draw=29.2,
    ac_load=258.8,
    dc_load=0.0,
    usb_a_load=6.1,
    usb_c_load=4.4,
    ac_input_active=True,
)

MOCK_DATA_RECOVERED = replace(MOCK_DATA, charge_level=75)


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.ecoflow_river3_plus.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_ecoflow_client() -> Generator[MagicMock]:
    """Mock the EcoFlow River 3 client in config flow and coordinator."""
    with (
        patch(
            "homeassistant.components.ecoflow_river3_plus.coordinator.EcoflowRiver3Client"
        ) as mock_client_class,
        patch(
            "homeassistant.components.ecoflow_river3_plus.config_flow.EcoflowRiver3Client",
            new=mock_client_class,
        ),
    ):
        client = mock_client_class.return_value
        client.update.return_value = MOCK_DATA
        client.close.return_value = None
        yield client


@pytest.fixture
def mock_comports() -> Generator[list[ListPortInfo]]:
    """Provide one compatible serial port."""
    port = ListPortInfo(TEST_DEVICE)
    port.device = TEST_DEVICE
    port.vid = DEFAULT_VENDOR_ID
    port.pid = DEFAULT_PRODUCT_ID
    port.serial_number = TEST_USB_SERIAL
    port.manufacturer = "EcoFlow"
    port.description = "EcoFlow River 3"

    with patch(
        "homeassistant.components.ecoflow_river3_plus.config_flow.comports",
        return_value=[port],
    ):
        yield [port]


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock EcoFlow River 3 config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=DEFAULT_NAME,
        data={
            CONF_DEVICE: TEST_DEVICE,
            CONF_VENDOR_ID: DEFAULT_VENDOR_ID,
            CONF_PRODUCT_ID: DEFAULT_PRODUCT_ID,
            CONF_USB_SERIAL_NUMBER: TEST_USB_SERIAL,
            CONF_DEVICE_SERIAL_NUMBER: TEST_DEVICE_SERIAL,
        },
        entry_id="ecoflow-river3-entry",
        unique_id=f"{DEFAULT_VENDOR_ID:04X}:{DEFAULT_PRODUCT_ID:04X}_{TEST_USB_SERIAL}",
    )
    entry.add_to_hass(hass)
    return entry
