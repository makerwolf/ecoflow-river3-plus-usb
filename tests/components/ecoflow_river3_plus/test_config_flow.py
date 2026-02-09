"""Test the EcoFlow River 3 config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from homeassistant.components.ecoflow_river3_plus.client import (
    EcoflowRiver3NoHidDeviceError,
)
from homeassistant.components.ecoflow_river3_plus.const import (
    CONF_DEVICE_SERIAL_NUMBER,
    CONF_PRODUCT_ID,
    CONF_USB_SERIAL_NUMBER,
    CONF_VENDOR_ID,
    DEFAULT_PRODUCT_ID,
    DEFAULT_VENDOR_ID,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USB, SOURCE_USER
from homeassistant.const import CONF_DEVICE, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import DISCOVERY_INFO, TEST_DEVICE


@pytest.mark.usefixtures("mock_comports", "mock_setup_entry")
async def test_flow_user_success(
    hass: HomeAssistant,
    mock_ecoflow_client: MagicMock,
) -> None:
    """Test successful user initiated flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_DEVICE: TEST_DEVICE}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_DEVICE] == TEST_DEVICE
    assert result["data"][CONF_VENDOR_ID] == DEFAULT_VENDOR_ID
    assert result["data"][CONF_PRODUCT_ID] == DEFAULT_PRODUCT_ID
    assert result["data"][CONF_USB_SERIAL_NUMBER] == DISCOVERY_INFO.serial_number
    assert result["data"][CONF_DEVICE_SERIAL_NUMBER]
    mock_ecoflow_client.update.assert_called_once()


@pytest.mark.usefixtures("mock_setup_entry")
async def test_flow_user_no_devices(hass: HomeAssistant) -> None:
    """Test user flow when no compatible devices are found."""
    with patch(
        "homeassistant.components.ecoflow_river3_plus.config_flow.comports",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={CONF_SOURCE: SOURCE_USER}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


@pytest.mark.usefixtures("mock_setup_entry")
async def test_flow_usb_no_hid(
    hass: HomeAssistant,
    mock_ecoflow_client: MagicMock,
) -> None:
    """Test USB flow aborts when no HID interface is available."""
    mock_ecoflow_client.update.side_effect = EcoflowRiver3NoHidDeviceError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USB},
        data=DISCOVERY_INFO,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_hid_device"


@pytest.mark.usefixtures("mock_setup_entry")
async def test_flow_usb_success(
    hass: HomeAssistant,
    mock_ecoflow_client: MagicMock,
) -> None:
    """Test successful USB initiated flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USB},
        data=DISCOVERY_INFO,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_DEVICE] == TEST_DEVICE
    assert result["data"][CONF_VENDOR_ID] == DEFAULT_VENDOR_ID
    assert result["data"][CONF_PRODUCT_ID] == DEFAULT_PRODUCT_ID
    assert result["data"][CONF_USB_SERIAL_NUMBER] == DISCOVERY_INFO.serial_number
    assert result["data"][CONF_DEVICE_SERIAL_NUMBER]
    mock_ecoflow_client.update.assert_called_once()
