# EcoFlow River 3 Plus USB — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/makerwolf/ecoflow-river3-plus-usb?include_prereleases)](https://github.com/makerwolf/ecoflow-river3-plus-usb/releases)
[![License](https://img.shields.io/github/license/makerwolf/ecoflow-river3-plus-usb)](LICENSE)

A **local, cloud-free Home Assistant integration for the EcoFlow River 3 Plus**
portable power station. It reads battery, power and temperature data directly
over **USB** (serial + HID) — **no EcoFlow cloud account, no MQTT broker, no
internet connection required**.

If you want to monitor your EcoFlow River 3 Plus in Home Assistant 100% locally,
this is for you.

> **Keywords:** EcoFlow River 3 Plus, Home Assistant, HACS, local USB, no cloud,
> no MQTT, portable power station, battery monitoring, solar, energy dashboard.

---

## ✨ Features

- 🔌 **100% local USB communication** — no cloud, no MQTT, no internet
- ⚙️ **Easy setup via the UI** — config flow with automatic USB device discovery
- 🔋 **Battery monitoring** — charge level, time remaining, charge/discharge ETA
- ⚡ **Power monitoring** — total in/out, AC, solar/DC, USB-A and USB-C loads
- 🌡️ **Temperature sensors** — system and battery temperature
- 🟢 **AC input state** as a binary sensor
- 📈 **Energy Dashboard ready** — power sensors with proper device classes

## 📊 Provided entities

| Entity | Type | Default |
|---|---|---|
| Charge level (%) | Sensor (Battery) | ✅ |
| Discharge time remaining (min) | Sensor (Duration) | ✅ |
| Output power (W) | Sensor (Power) | ✅ |
| AC input active | Binary sensor (Power) | ✅ |
| Input power (W) | Sensor (Power) | Diagnostic |
| AC input power (W) | Sensor (Power) | Diagnostic |
| Solar/DC input power (W) | Sensor (Power) | Diagnostic |
| AC output power (W) | Sensor (Power) | Diagnostic |
| DC output power (W) | Sensor (Power) | Diagnostic |
| USB-A output power (W) | Sensor (Power) | Diagnostic |
| USB-C output power (W) | Sensor (Power) | Diagnostic |
| Charge time remaining (min) | Sensor (Duration) | Diagnostic |
| System temperature (°C) | Sensor (Temperature) | Diagnostic |
| Battery temperature (°C) | Sensor (Temperature) | Diagnostic |

Entities marked *Diagnostic* are disabled by default — enable them in the entity
settings if you need them.

## 📦 Installation

### Option A — HACS (recommended)

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=makerwolf&repository=ecoflow-river3-plus-usb&category=integration)

1. Open **HACS** in Home Assistant
2. Click the menu (`⋮`) → **Custom repositories**
3. Add `https://github.com/makerwolf/ecoflow-river3-plus-usb` and choose
   category **Integration**
4. Install **EcoFlow River 3 Plus USB**
5. **Restart** Home Assistant
6. Go to **Settings → Devices & Services → Add Integration** and search for
   *EcoFlow River 3 Plus USB* (it is usually auto-discovered when the device is
   plugged in)

### Option B — Manual

1. Copy `custom_components/ecoflow_river3_plus` into your Home Assistant
   `config/custom_components/` directory
2. Restart Home Assistant
3. Add the integration via **Settings → Devices & Services**

## ✅ Requirements

- Home Assistant **2025.12.0** or newer
- The EcoFlow River 3 Plus connected via **USB** to the Home Assistant host
- Access to **both** the USB serial and HID interfaces of the device
  (USB passthrough on VMs/containers)

### Tested environments

- Proxmox VE host with a Home Assistant OS VM (USB passthrough)
- Bare-metal Home Assistant OS

## 🛠️ Troubleshooting

- **No compatible HID interface found** — make sure both USB interfaces are
  passed through to Home Assistant and that the user running Home Assistant has
  permission to access the HID device. On a VM, verify the USB device is mapped
  to the VM and not claimed by the host.
- **Device not auto-discovered** — add the integration manually via
  *Settings → Devices & Services → Add Integration*.

## 🙏 Acknowledgments

This integration is based on the excellent reverse-engineering work in
[`greyltc/r3pcomms`](https://github.com/greyltc/r3pcomms).
Credit where credit is due — without that project this would have required
significantly more effort.

## 🤝 Contributing

Issues and pull requests are welcome on the
[issue tracker](https://github.com/makerwolf/ecoflow-river3-plus-usb/issues).

## ⚖️ Disclaimer

This is an unofficial, community-maintained integration and is **not affiliated
with, endorsed by, or supported by EcoFlow**. EcoFlow and River are trademarks
of their respective owners. Use at your own risk.
