# Checkmk Tado Plugin

This plugin monitors the connectivity, calibration, and battery state of Tado devices using Tado's (unsupported) public API.

## Compatibility
Note: From 21st March 2025 Tado's API will require the use of the device code grant flow. Usernames and passwords stored in Checkmk can no longer be used.<br>
Versions of the plugin prior to 1.3.0 will not work after this date. Review the **Updating** section below for more details.

| Tado Plugin Version | Checkmk Versions |
| ------------------- | ---------------- |
| 1.0.0               | 2.1.0, 2.2.0     |
| 1.1.0 - 1.3.0       | 2.3.0, 2.4.0     |

## Installation

Download the packaged MKP file and install it in Checkmk from **Setup > Maintenance > Extension packages** (Enterprise & Cloud editions only) or at the command line using `mkp install tado-1.3.0`

_Please refer to [Checkmk's documentation](https://docs.checkmk.com/latest/en/mkps.html) for further information about extension packages._

## Updating
v1.3.0 uses a new type of authentication called "device code grant flow", as required by Tado from 21st March 2025.<br>
When upgrading from older versions is it necessary to delete and recreate existing rules under **Setup > Agents > Other integrations > Hardware > Tado**.<br>
A username and password can no longer be provided to access the Tado API. Instead, after creating the new rules navigate to **Setup > Hosts > _Your host_** and perform a service rescan.
You will be prompted with a link to log in to Tado and authorise Checkmk to access your account. Complete the login and rescan services once more. Your Tado devices should now be discovered.

## Configuration

### Host

From **Setup > Hosts**, create a host to associate Tado devices with. This plugin is a "special agent" which runs on the Checkmk host. No checks will be executed on the selected host.

You may create a dummy host to act as a holder for Tado services by choosing `No IP` for the **IP address family** option and `Configured API integrations, no Checkmk agent` for the **Checkmk agent / API integrations** option; however a more preferable option may be to create a host with an IP address that represents your Tado Internet Bridge, and associate your Tado devices with this. This has the additional benefit of allowing Checkmk to monitor LAN connectivity to your Internet Bridge and alert should it drop off your local network. You will likely need to configure a DHCP reservation on your network to provide it with a predictable IP address.

### Monitoring Rule

From **Setup > Agents > Other integrations > Hardware > Tado**, create one or more rules to enable Tado monitoring.

- **Conditions**
  - Add conditions to select the host(s) you wish your Tado devices to be associated with.
- **Tado (Advanced)** - These fields are optional
  - Filter by Home: If the name of a home is specified here, Checkmk will only discover devices that are part of this home.
  - Filter by Zone: If the name of a zone is specified here, Checkmk will only discover devices are part of this zone.
  - Custom Token ID: If you have multiple Tado rules targeting the same host, they will share the same access token.
  Give the rules custom token IDs if you need them to use different Tado accounts. It doesn't matter what you choose as an ID
  as long as each Tado account on a host uses a different one.

Once the rule has been added, navigate to the host and rescan services. Wait for a message to appear with a verification link. Clicking this link will take you to the Tado website where you can log in to grant Checkmk access to your Tado account. Complete the login and rescan services once more. Your Tado devices should now be discovered.

## Discovered Services

### Service Names

One Checkmk service will be created for each Tado device linked to your account.  
The services use the naming convention `Tado / {Home Name} / {Zone Name} / {Device Type} ({Device Serial Number})`.

E.g. `Tado / My Home / Bedroom / Radiator Thermostat (VA0123456789)`

For devices not assigned to a zone (e.g. an Internet Bridge), the zone name will be displayed as "Other".

### Service States

| State   | Conditions                                                               |
| ------- | ------------------------------------------------------------------------ |
| OK      | Good connectivity + no calibration/mounting errors + good battery health |
| WARN    | Good connectivity + no calibration/mounting errors + battery low         |
| CRIT    | Loss of connectivity or a calibration/mounting error is reported         |

## Acknowledgments & Further Information

- [Checkmk](https://checkmk.com/)
  - Open source IT monitoring software
- [Tado](https://www.tado.com/)
  - Smart heating and energy management
- [openHAB](https://www.openhab.org/)
  - Open source home automation software
  - Used as a reference for information about Tado's unsupported public API
  
