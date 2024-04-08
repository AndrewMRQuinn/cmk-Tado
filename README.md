# Checkmk Tado Plugin

This plugin monitors the connectivity, calibration, and battery state of Tado devices using Tado's (unsupported) public API.

## Installation

Download the packaged MKP file and install it in Checkmk from **Setup > Maintenance > Extension packages** (Enterprise & Cloud editions only) or at the command line using `mkp install tado-1.0.0`

_Please refer to [Checkmk's documentation](https://docs.checkmk.com/latest/en/mkps.html) for further information about extension packages._

## Configuration

### Host

From **Setup > Hosts**, create a host to associate Tado devices with. This plugin is a "special agent" which runs on the Checkmk host. No checks will be executed on the selected host.

You may create a dummy host to act as a holder for Tado services by choosing `No IP` for the **IP address family** option and `Configured API integrations, no Checkmk agent` for the **Checkmk agent / API integrations** option; however a more preferable option may be to create a host with an IP address that represents your Tado Internet Bridge, and associate your Tado devices with this. This has the additional benefit of allowing Checkmk to monitor LAN connectivity to your Internet Bridge and alert should it drop off your local network. You will likely need to configure a DHCP reservation on your network to provide it with a predictable IP address.

### Tado Account

From **Setup > Agents > Other integrations > Hardware > Tado**, create a new rule with the following fields:

- Tado
  - Username: The username for your Tado account
  - Password: The password for your Tado account
  - Filter by Home: If the name of a home is specified here, Checkmk will only discover devices that are part of this home
  - Filter by Zone: If the name of a zone is specified here, Checkmk will only discover devices are part of this zone
- Conditions
  - Add conditions to select the host(s) you wish your Tado devices to be associated with

## Discovered Services

### Service Names

One Checkmk service will be created for each Tado device linked to your account.  
The services use the naming convention `Tado / {Home Name} / {Zone Name} / {Device Type} ({Device Serial Number})`.

E.g. `Tado / My Home / Bedroom / Radiator Thermostat (VA0123456789)`

For devices not assigned to a zone (e.g. an Internet Bridge), the zone name will be displayed as "Other".

### Service States

| State   | Conditions                                                                |
| ------- | ------------------------------------------------------------------------- |
| OK      | Good connectivity + no calibration/mounting errors +  good battery health |
| WARN    | Good connectivity + no calibration/mounting errors + battery low          |
| CRIT    | Loss of connectivity or a calibration/mounting error is reported          |

## Acknowledgments & Further Information

- [Checkmk](https://checkmk.com/)
  - Open source IT monitoring software
- [Tado](https://www.tado.com/)
  - Smart heating and energy management
- [openHAB](https://www.openhab.org/)
  - Open source home automation software
  - Used as a reference for information about Tado's unsupported public API
  