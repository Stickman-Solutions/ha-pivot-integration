"""Sensor platform for the Pivot API integration."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfTemperature,
    PERCENTAGE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from datetime import datetime, timezone

from .const import DOMAIN


@dataclass(frozen=True)
class PivotSensorEntityDescription(SensorEntityDescription):
    """Describes a Pivot API sensor entity."""

    data_source: str = "reported"  # "reported" or "derived"
    value_fn: callable = None


SENSOR_DESCRIPTIONS: tuple[PivotSensorEntityDescription, ...] = (
    # Reported data
    PivotSensorEntityDescription(
        key="nickname",
        name="Nickname",
        data_source="reported",
        value_fn=lambda d: d["device"]["nickname"],
    ),
    PivotSensorEntityDescription(
        key="latitude",
        name="Latitude",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["latitude"],
    ),
    PivotSensorEntityDescription(
        key="longitude",
        name="Longitude",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["longitude"],
    ),
    PivotSensorEntityDescription(
        key="altitude",
        name="Altitude",
        native_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["altitude"],
    ),
    PivotSensorEntityDescription(
        key="satellites",
        name="Satellites",
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["sats"],
    ),
    PivotSensorEntityDescription(
        key="hdop",
        name="HDOP",
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["hdop"],
    ),
    PivotSensorEntityDescription(
        key="temperature",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["temperature"],
    ),
    PivotSensorEntityDescription(
        key="humidity",
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["humidity"],
    ),
    PivotSensorEntityDescription(
        key="v_bat",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["v_bat"],
    ),
    PivotSensorEntityDescription(
        key="v_in",
        name="Input Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["v_in"],
    ),
    PivotSensorEntityDescription(
        key="i_in",
        name="Input Current",
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["i_in"],
    ),
    PivotSensorEntityDescription(
        key="v_rail",
        name="Rail Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["v_rail"],
    ),
    PivotSensorEntityDescription(
        key="accel_x",
        name="Accelerometer X",
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["accel_x"],
    ),
    PivotSensorEntityDescription(
        key="accel_y",
        name="Accelerometer Y",
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["accel_y"],
    ),
    PivotSensorEntityDescription(
        key="accel_z",
        name="Accelerometer Z",
        state_class=SensorStateClass.MEASUREMENT,
        data_source="reported",
        value_fn=lambda d: d["reported"]["accel_z"],
    ),
    # Derived data
    PivotSensorEntityDescription(
        key="center_latitude",
        name="Center Latitude",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        data_source="derived",
        value_fn=lambda d: d["derived"]["center_latitude"],
    ),
    PivotSensorEntityDescription(
        key="center_longitude",
        name="Center Longitude",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        data_source="derived",
        value_fn=lambda d: d["derived"]["center_longitude"],
    ),
    PivotSensorEntityDescription(
        key="azimuth",
        name="Azimuth",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        data_source="derived",
        value_fn=lambda d: d["derived"]["azimuth"],
    ),
    PivotSensorEntityDescription(
        key="datetime",
        name="Last Report",
        device_class=SensorDeviceClass.TIMESTAMP,
        data_source="reported",
        value_fn=lambda d: datetime.fromisoformat(d["reported"]["datetime"]).replace(
            tzinfo=timezone.utc
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pivot API sensors from a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for imei, device_data in entry_data.items():
        coordinator = device_data["coordinator"]
        device_info = device_data["device_info"]

        for description in SENSOR_DESCRIPTIONS:
            entities.append(
                PivotSensor(coordinator, description, device_info, entry.entry_id)
            )

    async_add_entities(entities)


class PivotSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Pivot API sensor."""

    entity_description: PivotSensorEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        description: PivotSensorEntityDescription,
        device_info: dict[str, Any],
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device_info = device_info
        imei = device_info["imei"]
        self._attr_unique_id = f"{entry_id}_{imei}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, imei)},
            name=imei,
            model="Center Pivot Monitor",
            manufacturer="Stickman Solutions LLC",
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        try:
            return self.entity_description.value_fn(self.coordinator.data)
        except KeyError, TypeError:
            return None
