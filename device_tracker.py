"""Device tracker platform for the Pivot API integration."""

from __future__ import annotations
from typing import Any
from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pivot API device trackers from a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for imei, device_data in entry_data.items():
        coordinator = device_data["coordinator"]
        device_info = device_data["device_info"]
        entities.append(PivotEndTowerTracker(coordinator, device_info, entry.entry_id))
        entities.append(PivotCenterTracker(coordinator, device_info, entry.entry_id))
    async_add_entities(entities)


class PivotEndTowerTracker(CoordinatorEntity, TrackerEntity):
    """Representation of the end tower location."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_info: dict[str, Any],
        entry_id: str,
    ) -> None:
        """Initialize the end tower tracker."""
        super().__init__(coordinator)
        self._device_info = device_info
        imei = device_info["imei"]
        self._attr_unique_id = f"{entry_id}_{imei}_end_tower"
        self._attr_name = "End tower"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, imei)},
            name=imei,
            model="Center Pivot Monitor",
            manufacturer="Stickman Solutions LLC",
        )

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return latitude."""
        if self.coordinator.data is None or self.coordinator.data["reported"] is None:
            return None
        return self.coordinator.data["reported"]["latitude"]

    @property
    def longitude(self) -> float | None:
        """Return longitude."""
        if self.coordinator.data is None or self.coordinator.data["reported"] is None:
            return None
        return self.coordinator.data["reported"]["longitude"]

    @property
    def location_accuracy(self) -> float:
        """Return location HDOP."""
        if self.coordinator.data is None or self.coordinator.data["reported"] is None:
            return 0
        return self.coordinator.data["reported"]["hdop"]


class PivotCenterTracker(CoordinatorEntity, TrackerEntity):
    """Representation of the pivot center location."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_info: dict[str, Any],
        entry_id: str,
    ) -> None:
        """Initialize the center tracker."""
        super().__init__(coordinator)
        self._device_info = device_info
        imei = device_info["imei"]
        self._attr_unique_id = f"{entry_id}_{imei}_center"
        self._attr_name = "Center"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, imei)},
            name=imei,
            model="Center Pivot Monitor",
            manufacturer="Stickman Solutions LLC",
        )

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return center latitude."""
        if self.coordinator.data is None or self.coordinator.data["derived"] is None:
            return None
        return self.coordinator.data["derived"]["center_latitude"]

    @property
    def longitude(self) -> float | None:
        """Return center longitude."""
        if self.coordinator.data is None or self.coordinator.data["derived"] is None:
            return None
        return self.coordinator.data["derived"]["center_longitude"]

    @property
    def location_accuracy(self) -> int:
        """Return fixed accuracy for derived center point."""
        return 0
