"""Client for EcoFlow River 3 USB communication."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
import logging
from operator import xor
import struct
from typing import Any

import serial

from .const import HID_AC_IN_LIVE_BIT

try:
    import hid
except ImportError:
    hid = None

_LOGGER = logging.getLogger(__name__)


SERIAL_BAUDRATE = 115200
SERIAL_TIMEOUT_SECONDS = 1
SERIAL_QUERY_OVERHEAD_BYTES = 14
SERIAL_RESPONSE_HEADER_BYTES = 4
SERIAL_RESPONSE_BASE_BYTES = 20
SERIAL_RESPONSE_CRC_BYTES = 2
SERIAL_MESSAGE_PREFIX = 0x03AA
SERIAL_METRICS_QUERY = "de2d00000000ffff220201016602"
SERIAL_METRICS_OFFSET = 22
SERIAL_XOR_OFFSET = 18
BATTERY_TIME_UNKNOWN = b"\x33\x17"


class EcoflowRiver3Error(Exception):
    """Base error for EcoFlow River 3 communication issues."""


class EcoflowRiver3DependencyError(EcoflowRiver3Error):
    """Raised when an optional dependency is missing."""


class EcoflowRiver3NoHidDeviceError(EcoflowRiver3Error):
    """Raised when no matching HID interface can be found."""


class EcoflowRiver3ConnectionError(EcoflowRiver3Error):
    """Raised when communication with the device fails."""


class EcoflowRiver3CrcError(EcoflowRiver3ConnectionError):
    """Raised when CRC validation fails for a serial packet."""


@dataclass(slots=True)
class EcoflowRiver3SerialMetrics:
    """Metrics read from the CDC serial interface."""

    device_serial_number: str | None = None
    system_temperature: int | None = None
    battery_temperature: int | None = None
    total_load: float | None = None
    total_draw: float | None = None
    ac_draw: float | None = None
    solar_dc_draw: float | None = None
    ac_load: float | None = None
    dc_load: float | None = None
    usb_a_load: float | None = None
    usb_c_load: float | None = None
    remaining_charge_time: int | None = None


@dataclass(slots=True)
class EcoflowRiver3HidMetrics:
    """Metrics read from the HID interface."""

    charge_level: int | None = None
    battery_time_remaining: int | None = None
    ac_input_active: bool | None = None


@dataclass(slots=True)
class EcoflowRiver3Data:
    """Combined EcoFlow River 3 telemetry."""

    device_serial_number: str | None = None
    charge_level: int | None = None
    battery_time_remaining: int | None = None
    remaining_charge_time: int | None = None
    system_temperature: int | None = None
    battery_temperature: int | None = None
    total_load: float | None = None
    total_draw: float | None = None
    ac_draw: float | None = None
    solar_dc_draw: float | None = None
    ac_load: float | None = None
    dc_load: float | None = None
    usb_a_load: float | None = None
    usb_c_load: float | None = None
    ac_input_active: bool | None = None


class EcoflowRiver3Client:
    """Blocking client for EcoFlow River 3 USB telemetry."""

    def __init__(
        self,
        serial_device: str,
        vendor_id: int,
        product_id: int,
        usb_serial_number: str | None,
    ) -> None:
        """Initialize the client."""
        self._serial_device = serial_device
        self._vendor_id = vendor_id
        self._product_id = product_id
        self._usb_serial_number = usb_serial_number

        self._serial: serial.Serial | None = None
        self._hid_device: Any | None = None
        self._hid_path: bytes | str | None = None
        self._sequence_number = 0

    def close(self) -> None:
        """Close all open interfaces."""
        if self._hid_device is not None:
            with suppress(OSError, RuntimeError, ValueError):
                self._hid_device.close()
            self._hid_device = None

        if self._serial is not None:
            with suppress(serial.SerialException, OSError, ValueError):
                self._serial.close()
            self._serial = None

    def update(self) -> EcoflowRiver3Data:
        """Read fresh telemetry from serial and HID."""
        try:
            self._ensure_connected()
            serial_metrics = self._read_serial_metrics()
            hid_metrics = self._read_hid_metrics()
        except (
            EcoflowRiver3Error,
            OSError,
            ValueError,
            serial.SerialException,
        ) as err:
            self.close()
            if isinstance(err, EcoflowRiver3Error):
                raise
            raise EcoflowRiver3ConnectionError(
                f"Communication failed for {self._serial_device}"
            ) from err

        return EcoflowRiver3Data(
            device_serial_number=serial_metrics.device_serial_number,
            charge_level=hid_metrics.charge_level,
            battery_time_remaining=hid_metrics.battery_time_remaining,
            remaining_charge_time=serial_metrics.remaining_charge_time,
            system_temperature=serial_metrics.system_temperature,
            battery_temperature=serial_metrics.battery_temperature,
            total_load=serial_metrics.total_load,
            total_draw=serial_metrics.total_draw,
            ac_draw=serial_metrics.ac_draw,
            solar_dc_draw=serial_metrics.solar_dc_draw,
            ac_load=serial_metrics.ac_load,
            dc_load=serial_metrics.dc_load,
            usb_a_load=serial_metrics.usb_a_load,
            usb_c_load=serial_metrics.usb_c_load,
            ac_input_active=hid_metrics.ac_input_active,
        )

    def _ensure_connected(self) -> None:
        """Connect to serial and HID interfaces if needed."""
        if self._serial is None:
            try:
                self._serial = serial.Serial(
                    port=self._serial_device,
                    baudrate=SERIAL_BAUDRATE,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=SERIAL_TIMEOUT_SECONDS,
                )
            except (serial.SerialException, OSError) as err:
                raise EcoflowRiver3ConnectionError(
                    f"Unable to open serial device {self._serial_device}: {err}"
                ) from err
            self._sequence_number = 0
            _LOGGER.debug("Opened serial device %s", self._serial_device)

        if self._hid_device is None:
            if hid is None:
                raise EcoflowRiver3DependencyError("hidapi is required")

            hid_path = self._find_hid_path()
            hid_device = hid.device()
            try:
                hid_device.open_path(hid_path)
            except TypeError:
                if isinstance(hid_path, bytes):
                    hid_device.open_path(hid_path.decode(errors="ignore"))
                else:
                    raise
            except OSError as err:
                raise EcoflowRiver3ConnectionError(
                    f"Unable to open HID interface for "
                    f"{self._vendor_id:04x}:{self._product_id:04x}: {err}"
                ) from err

            self._hid_path = hid_path
            self._hid_device = hid_device
            _LOGGER.debug(
                "Opened HID interface path=%s", self._hid_path_as_str(hid_path)
            )

    def _find_hid_path(self) -> bytes | str:
        """Resolve the matching HID path for the configured USB device."""
        if hid is None:
            raise EcoflowRiver3DependencyError("hidapi is required")

        devices: list[dict[str, Any]] = list(
            hid.enumerate(self._vendor_id, self._product_id)
        )
        _LOGGER.debug(
            "Enumerated %d HID candidates for %04x:%04x",
            len(devices),
            self._vendor_id,
            self._product_id,
        )

        serial_match = (
            self._usb_serial_number.casefold() if self._usb_serial_number else None
        )
        fallback_path: bytes | str | None = None

        for device in devices:
            path = device.get("path")
            if path is None:
                continue

            _LOGGER.debug(
                "HID candidate path=%s serial=%s interface=%s usage_page=%s usage=%s",
                self._hid_path_as_str(path),
                device.get("serial_number"),
                device.get("interface_number"),
                device.get("usage_page"),
                device.get("usage"),
            )

            if fallback_path is None:
                fallback_path = path

            if serial_match is None:
                continue

            device_serial = str(device.get("serial_number") or "").casefold()
            if device_serial == serial_match:
                return path

        if fallback_path is not None and serial_match is None:
            return fallback_path

        if fallback_path is not None and len(devices) == 1:
            _LOGGER.warning(
                "No HID serial match for usb serial %s, using only available HID "
                "candidate path=%s",
                self._usb_serial_number,
                self._hid_path_as_str(fallback_path),
            )
            return fallback_path

        raise EcoflowRiver3NoHidDeviceError(
            f"No HID interface found for {self._vendor_id:04x}:{self._product_id:04x}; "
            "for Proxmox, use full USB passthrough and verify HA OS sees hidraw/usb devices"
        )

    @staticmethod
    def _hid_path_as_str(path: bytes | str) -> str:
        """Convert HID path to a readable string."""
        if isinstance(path, bytes):
            return path.decode(errors="ignore")
        return path

    def _read_serial_metrics(self) -> EcoflowRiver3SerialMetrics:
        """Read and decode serial metrics."""
        response = self._query_serial(SERIAL_METRICS_QUERY)
        decoded = self._xor_payload(response)
        return self._parse_serial_metrics(decoded[SERIAL_METRICS_OFFSET:])

    def _read_hid_metrics(self) -> EcoflowRiver3HidMetrics:
        """Read and decode HID metrics."""
        charge_report = self._read_hid_feature_report(12)
        remaining_report = self._read_hid_feature_report(13)
        flags_report = self._read_hid_feature_report(7)

        charge_level = charge_report[0] if charge_report else None

        battery_time_remaining: int | None
        battery_payload = remaining_report[:2]
        if len(battery_payload) < 2:
            battery_time_remaining = None
        elif battery_payload == BATTERY_TIME_UNKNOWN:
            battery_time_remaining = -1
        else:
            battery_time_remaining = struct.unpack("<H", battery_payload)[0]

        flags = int.from_bytes(flags_report, byteorder="big", signed=False)
        ac_input_active = bool(flags & (1 << HID_AC_IN_LIVE_BIT))

        return EcoflowRiver3HidMetrics(
            charge_level=charge_level,
            battery_time_remaining=battery_time_remaining,
            ac_input_active=ac_input_active,
        )

    def _read_hid_feature_report(self, report_id: int, length: int = 16) -> bytes:
        """Read a HID feature report payload."""
        if self._hid_device is None:
            raise EcoflowRiver3ConnectionError("HID interface is not connected")

        try:
            raw = bytes(self._hid_device.get_feature_report(report_id, length))
        except OSError as err:
            raise EcoflowRiver3ConnectionError(
                f"Failed to read HID report {report_id}"
            ) from err

        if len(raw) < 2:
            raise EcoflowRiver3ConnectionError(
                f"Invalid HID report length for report {report_id}"
            )

        return raw[1:]

    def _query_serial(self, payload_hex: str) -> bytes:
        """Send a serial request and return response bytes."""
        self._serial_write(payload_hex)
        return self._serial_read_response()

    def _serial_write(self, payload_hex: str) -> None:
        """Send a framed serial request payload."""
        if self._serial is None:
            raise EcoflowRiver3ConnectionError("Serial interface is not connected")

        payload = bytes.fromhex(payload_hex)
        message_length = len(payload) - SERIAL_QUERY_OVERHEAD_BYTES
        sequence = struct.pack("<I", self._sequence_number)
        payload_with_sequence = payload[:2] + sequence + payload[6:]
        header = struct.pack("<HH", SERIAL_MESSAGE_PREFIX, message_length)
        framed = header + payload_with_sequence
        crc = self._crc16(framed)
        packet = framed + struct.pack("<H", crc)

        written = self._serial.write(packet)
        if written != len(packet):
            raise EcoflowRiver3ConnectionError(
                f"Wrote {written} of {len(packet)} serial bytes"
            )

        self._sequence_number += 1

    def _serial_read_response(self) -> bytes:
        """Read a framed serial response and validate CRC."""
        header = self._serial_read_exact(SERIAL_RESPONSE_HEADER_BYTES)
        _, variable_length = struct.unpack("<HH", header)

        payload_length = (
            SERIAL_RESPONSE_BASE_BYTES
            + variable_length
            - SERIAL_RESPONSE_HEADER_BYTES
            - SERIAL_RESPONSE_CRC_BYTES
        )
        if payload_length < 0:
            raise EcoflowRiver3ConnectionError(
                f"Invalid serial payload length {payload_length}"
            )

        payload = self._serial_read_exact(payload_length)
        crc = self._serial_read_exact(SERIAL_RESPONSE_CRC_BYTES)

        framed = header + payload + crc
        if self._crc16(framed) != 0:
            raise EcoflowRiver3CrcError("CRC check failed for serial response")

        return header + payload

    def _serial_read_exact(self, size: int) -> bytes:
        """Read an exact number of bytes from serial."""
        if self._serial is None:
            raise EcoflowRiver3ConnectionError("Serial interface is not connected")

        data = bytearray()
        while len(data) < size:
            chunk = self._serial.read(size - len(data))
            if not chunk:
                break
            data.extend(chunk)

        if len(data) != size:
            raise EcoflowRiver3ConnectionError(
                f"Read {len(data)} of {size} serial bytes"
            )

        return bytes(data)

    @staticmethod
    def _xor_payload(payload: bytes) -> bytes:
        """Decode serial payload bytes obfuscated with the sequence number."""
        if len(payload) <= SERIAL_XOR_OFFSET:
            return payload

        sequence = struct.unpack_from("<I", payload, offset=6)[0] & 0xFF
        decoded_payload = bytes(
            xor(value, sequence) & 0xFF for value in payload[SERIAL_XOR_OFFSET:]
        )
        return payload[:SERIAL_XOR_OFFSET] + decoded_payload

    @staticmethod
    def _crc16(data: bytes) -> int:
        """Calculate CRC-16/ARC checksum."""
        crc = 0x0000
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc & 0xFFFF

    @staticmethod
    def _parse_serial_metrics(payload: bytes) -> EcoflowRiver3SerialMetrics:
        """Parse serial segment payload into typed metrics."""
        metrics = EcoflowRiver3SerialMetrics()
        offset = 0

        while offset < len(payload):
            if offset + 3 > len(payload):
                raise EcoflowRiver3ConnectionError("Invalid serial segment header")

            segment_type, segment_length = struct.unpack_from("<HB", payload, offset)
            offset += 3

            if offset + segment_length > len(payload):
                raise EcoflowRiver3ConnectionError("Invalid serial segment length")

            segment_data = payload[offset : offset + segment_length]
            offset += segment_length

            match segment_type:
                case 4 if len(segment_data) >= 2:
                    metrics.system_temperature = segment_data[0]
                    metrics.battery_temperature = segment_data[1]
                case 7 if len(segment_data) == 4:
                    metrics.total_load = struct.unpack("<f", segment_data)[0]
                case 8 if len(segment_data) == 4:
                    metrics.total_draw = struct.unpack("<f", segment_data)[0]
                case 9 if len(segment_data) == 4:
                    metrics.ac_draw = struct.unpack("<f", segment_data)[0]
                case 12 if len(segment_data) == 4:
                    metrics.solar_dc_draw = struct.unpack("<f", segment_data)[0]
                case 14 if len(segment_data) == 4:
                    metrics.ac_load = abs(struct.unpack("<f", segment_data)[0])
                case 16 if len(segment_data) == 4:
                    metrics.dc_load = abs(struct.unpack("<f", segment_data)[0])
                case 17 if len(segment_data) == 4:
                    metrics.usb_a_load = abs(struct.unpack("<f", segment_data)[0])
                case 18 if len(segment_data) == 4:
                    metrics.usb_c_load = abs(struct.unpack("<f", segment_data)[0])
                case 22:
                    serial_number = segment_data.rstrip(b"\x00\xff").decode(
                        "ascii", errors="ignore"
                    )
                    metrics.device_serial_number = serial_number or None
                case 23 if len(segment_data) >= 2:
                    if segment_data[:2] == BATTERY_TIME_UNKNOWN:
                        metrics.remaining_charge_time = -1
                    else:
                        metrics.remaining_charge_time = struct.unpack_from(
                            "<H", segment_data
                        )[0]

        return metrics
