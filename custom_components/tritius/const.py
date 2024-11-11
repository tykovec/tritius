"""Constants for tritius."""

from enum import IntFlag, StrEnum
from logging import Logger, getLogger

_LOGGER: Logger = getLogger(__package__)

DOMAIN = "tritius"
SERVICE_RENEW_BORROWINGS = "renew_borrowings"


class TritiusEntityFeature(IntFlag):
    """Class for entity features."""

    RENEW_BORROWINGS = 1


class Url(StrEnum):
    """Urls used for data fetching."""

    BORROWINGS = "profile/borrowings/current"
    LOGIN = "process-login"
    PERSONAL_DATA = "profile/personal-data"
    RENEW_ALL = "profile/renew-all"


class Selector(StrEnum):
    """Selectors for data scrapping."""

    LOGIN_FORM = "form.login-form"
    REGISTRATION_EXPIRATION = "#navbar li.dropdown-user li.hidden-xs span.dropdown-text"
    PORTLET_PERSONAL_DATA = "#portlet-personal-data"
    PORTLET_BORROWINGS = "#borrowings-portlet"
    PORTLET_BORROWINGS_DATA = ".portlet-content table tbody tr"
    RENEW_ALL_FORM = f"form[action='/{Url.RENEW_ALL}']"
