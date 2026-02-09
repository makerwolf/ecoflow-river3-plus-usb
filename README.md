# EcoFlow River 3 Plus USB for Home Assistant

Home Assistant custom integration for reading EcoFlow River 3 Plus data over
USB (serial + HID), without MQTT.

## Features

- Local USB communication (no cloud, no MQTT broker)
- Config flow with USB device selection
- Sensors for charge level, input/output power, and temperatures
- Binary sensor for AC input state

## Installation (HACS custom repository)

1. Open HACS in Home Assistant
2. Go to `Integrations`
3. Open the menu (`⋮`) and select `Custom repositories`
4. Add this repository URL and choose `Integration`
5. Install `EcoFlow River 3 Plus USB`
6. Restart Home Assistant

## Requirements

- Home Assistant OS or supervised/container setup with USB passthrough
- Access to both USB serial and HID interfaces of the EcoFlow device

## Known target environment

- Proxmox VE host with Home Assistant OS VM
- Bare-metal Home Assistant OS

## Acknowledgments

This integration is based on the excellent work in
[`greyltc/r3pcomms`](https://github.com/greyltc/r3pcomms).
Credit where credit is due: without that project, this would have required
significantly more reverse engineering and development effort.
