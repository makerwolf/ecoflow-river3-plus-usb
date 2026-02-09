"""Constants for the EcoFlow River 3 Plus integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN = "ecoflow_river3_plus"
DEFAULT_NAME = "EcoFlow River 3 Plus"
MANUFACTURER = "EcoFlow"
MODEL = "River 3 Plus"

CONF_VENDOR_ID = "vendor_id"
CONF_PRODUCT_ID = "product_id"
CONF_USB_SERIAL_NUMBER = "usb_serial_number"
CONF_DEVICE_SERIAL_NUMBER = "device_serial_number"

DEFAULT_VENDOR_ID: Final = 0x3746
DEFAULT_PRODUCT_ID: Final = 0xFFFF
HID_AC_IN_LIVE_BIT: Final = 10

UPDATE_INTERVAL = timedelta(seconds=10)
