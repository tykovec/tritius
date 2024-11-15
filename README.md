# Tritius

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]

_Integration to integrate with [tritius](https://www.tritius.cz/), library system mainly used in Slovakia and Czechia._
_This is unofficial integration, do not contact system creator (Tritius Solutions) in case of issue._
_Links of instances / liraries can be found here [libraries](https://knihovny.net/wwwlnew/odkazy1t.htm)_

**This integration will set up the following platforms.**

Platform | Name | Description
-- | -- | --
`button` | `renew_borrowings` | Button for renewing all actual borrowings.
`binary_sensor` | `borrowings_alert` | Alerting when borrowing is about to expire (day before expiration).
`sensor` | `borrowings` | Sensor displaying borrowing count.
`sensor` | `registration_expiration` | Expiration of membership / registration in library.
`sensor` | `borrowing_expiration` | Nearest borrowing expiration.
`switch` | `auto_renew_borrowings` | Automatically renews when borrowings are about to expire.

Registration expiration sensor (registration_expiration) also contains info about borrowings with following format.

``` yaml

- borrowings:
    - author:
      title:
      id:
      expiration:

```
## Installation through HACS
To install the tritius integration using HACS:

1. Open Home Assistant, go to HACS > Integrations.
1. Search for tritius and install it.
1. After installation, add the necessary configuration to your configuration.yaml (see below).
1. Restart Home Assistant.

## Manual Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `tritius`.
1. Download _all_ the files from the `custom_components/tritius/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Tritius"

## Configuration
Through Home Assistant UI
1. Navigate to Configuration > Integrations.
2. Click the + Add Integration button.
3. Search fortritius and select it.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[tritius]: https://github.com/tykovec/home-assistant-tritius
[buymecoffee]: https://www.buymeacoffee.com/tykovec
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/tykovec/tritius.svg?style=for-the-badge
[commits]: https://github.com/tykovec/home-assistant-tritius/commits/main
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/tykovec/tritius.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Tomáš%20Lukáč%20%40tykovec-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/tykovec/tritius.svg?style=for-the-badge
[releases]: https://github.com/tykovec/home-assistant-tritius/releases
