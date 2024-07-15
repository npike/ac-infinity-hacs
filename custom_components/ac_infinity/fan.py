"""The ac_infinity fan platform."""
from __future__ import annotations
import logging
import math
from typing import Any

from ac_infinity_ble import ACInfinityController

from homeassistant.components.fan import FanEntity, FanEntityFeature

from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothCoordinatorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_platform

from homeassistant.util.percentage import (
    int_states_in_range,
    ranged_value_to_percentage,
    percentage_to_ranged_value,
)

import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from .const import DEVICE_MODEL, DOMAIN
from .coordinator import ACInfinityDataUpdateCoordinator
from .models import ACInfinityData

SPEED_RANGE = (1, 10)

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_WORK_TYPE_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("type"): vol.In(["AUTO", "ON", "OFF", "CYCLE", "TIMER"]),
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform for LEDBLE."""
    data: ACInfinityData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ACInfinityFan(data.coordinator, data.device, entry.title)])
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "set_device_work_type", SERVICE_SET_WORK_TYPE_SCHEMA, "set_device_work_type"
    )


class ACInfinityFan(
    PassiveBluetoothCoordinatorEntity[ACInfinityDataUpdateCoordinator], FanEntity
):
    """Representation of AC Infinity sensor."""

    _attr_speed_count = int_states_in_range(SPEED_RANGE)
    _attr_supported_features = FanEntityFeature.SET_SPEED

    def __init__(
        self,
        coordinator: ACInfinityDataUpdateCoordinator,
        device: ACInfinityController,
        name: str,
    ) -> None:
        """Initialize an AC Infinity sensor."""
        super().__init__(coordinator)
        self._device = device
        self._attr_name = f"{name} Fan"
        self._attr_unique_id = f"{self._device.address}_fan"
        self._attr_device_info = DeviceInfo(
            name=device.name,
            model=DEVICE_MODEL[device.state.type],
            manufacturer="AC Infinity",
            sw_version=device.state.version,
            connections={(dr.CONNECTION_BLUETOOTH, device.address)},
        )
        self._async_update_attrs()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        speed = 0
        if percentage > 0:
            speed = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))

        await self._device.set_speed(speed)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        speed = None
        if percentage is not None:
            speed = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        await self._device.turn_on(speed)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        await self._device.turn_off()

    async def set_device_work_type(self, type):
        """Handle service request to change work type."""
        work_type = type
        _LOGGER.debug("Service request to set work type to %s", work_type)

        # Translate the mode to the raw value
        if work_type == "CYCLE":
            raw_mode = 6
        elif work_type == "TIMER":
            raw_mode = 4
        elif work_type == "AUTO":
            raw_mode = 3
        elif work_type == "ON":
            raw_mode = 2
        elif work_type == "OFF":
            raw_mode = 1

        _LOGGER.debug("Work type set to %s", raw_mode)
        await self._device.set_type(raw_mode)

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        self._attr_is_on = self._device.is_on
        self._attr_percentage = ranged_value_to_percentage(
            SPEED_RANGE, self._device.state.fan
        )

    @callback
    def _handle_coordinator_update(self, *args: Any) -> None:
        """Handle data update."""
        self._async_update_attrs()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            self._device.register_callback(self._handle_coordinator_update)
        )
        return await super().async_added_to_hass()
