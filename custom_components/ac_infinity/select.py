"""The ac_infinity select platform."""
from __future__ import annotations
import logging
from typing import Any

from ac_infinity_ble import ACInfinityController
from homeassistant.components.select import SelectEntity
from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothCoordinatorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_MODEL, DOMAIN
from .coordinator import ACInfinityDataUpdateCoordinator
from .models import ACInfinityData

_LOGGER = logging.getLogger(__name__)

WORK_TYPE_MAP = {
    1: "Off",
    2: "On",
    3: "Auto",
    4: "Timer",
    6: "Cycle",
}

WORK_TYPE_REVERSE_MAP = {v: k for k, v in WORK_TYPE_MAP.items()}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform."""
    data: ACInfinityData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ACInfinityWorkTypeSelect(data.coordinator, data.device, entry.title)])

class ACInfinityWorkTypeSelect(
    PassiveBluetoothCoordinatorEntity[ACInfinityDataUpdateCoordinator], SelectEntity
):
    """Representation of an AC Infinity work type select entity."""

    _attr_options = ["Auto", "On", "Off", "Cycle", "Timer"]
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: ACInfinityDataUpdateCoordinator,
        device: ACInfinityController,
        name: str,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._device = device
        self._attr_name = f"{name} Work Type"
        self._attr_unique_id = f"{self._device.address}_work_type"
        self._attr_device_info = DeviceInfo(
            name=device.name,
            model=DEVICE_MODEL[device.state.type],
            manufacturer="AC Infinity",
            sw_version=str(device.state.version) if device.state.version is not None else None,
            connections={(dr.CONNECTION_BLUETOOTH, device.address)},
        )
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        raw_state = self._device.state.work_type
        self._attr_current_option = WORK_TYPE_MAP.get(raw_state, "Unknown")

    @callback
    def _handle_coordinator_update(self, *args: Any) -> None:
        """Handle data update."""
        self._async_update_attrs()
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if (raw_value := WORK_TYPE_REVERSE_MAP.get(option)) is not None:
            _LOGGER.debug("Setting device work type to %s (%s)", option, raw_value)
            await self._device.set_type(raw_value)
            self._attr_current_option = option
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            self._device.register_callback(self._handle_coordinator_update)
        )
        return await super().async_added_to_hass()
