#!/usr/bin/python3

from prometheus_client import Gauge
from prometheus_client import REGISTRY

registry = REGISTRY

# controller metrics
hpilo_controller_status_gauge = Gauge('hpilo_controller_status', 'HP iLO controller status 0 = OK 1 = OTHER', ["label","status","controller_status","serial_number","model","fw_version","product_name", "server_name"])
hpilo_controller_status_1_gauge = Gauge('hpilo_controller_status_1', 'HP iLO controller status 0 = OK 1 = OTHER', ["label","status","controller_status","serial_number","model","fw_version","product_name", "server_name"])
hpilo_controller_status_3_gauge = Gauge('hpilo_controller_status_3', 'HP iLO controller status 0 = OK 1 = OTHER', ["label","status","controller_status","serial_number","model","fw_version","product_name", "server_name"])
# controller metrics end


# hpilo_vrm_gauge = Gauge('hpilo_vrm', 'HP iLO vrm status', ["product_name", "server_name"])
# hpilo_drive_gauge = Gauge('hpilo_drive', 'HP iLO drive status', ["product_name", "server_name"])
hpilo_battery_gauge = Gauge('hpilo_battery', 'HP iLO battery status  0 = OK, 1 = DEGRADED; 2 = Other', ["product_name", "server_name"])
hpilo_battery1_gauge = Gauge('hpilo_battery1', 'HP iLO battery status  0 = OK, 1 = DEGRADED', ["label","present","status","model","spare","serial_number","capacity","firmware_version","product_name","server_name"])
hpilo_storage_gauge = Gauge('hpilo_storage', 'HP iLO storage status  0 = OK, 1 = DEGRADED; 2 = Other', ["product_name", "server_name"])
hpilo_fans_gauge = Gauge('hpilo_fans', 'HP iLO fans status  0 = OK, 1 = DEGRADED; 2 = Other', ["product_name", "server_name"])
hpilo_bios_hardware_gauge = Gauge('hpilo_bios_hardware', 'HP iLO bios_hardware status  0 = OK, 1 = DEGRADED; 2 = Other', ["product_name", "server_name"])
hpilo_memory_gauge = Gauge('hpilo_memory', 'HP iLO memory status  0 = OK, 1 = DEGRADED; 2 = Other', ["product_name", "server_name"])
hpilo_power_supplies_gauge = Gauge('hpilo_power_supplies', 'HP iLO power_supplies status  0 = OK, 1 = DEGRADED; 2 = Other', ["product_name",
                                                                                            "server_name"])
hpilo_power_supplies_detail_gauge = Gauge('hpilo_power_supplies_detail', 'HP iLO power_supplies detail', ["product_name","server_name", "psu_id", "label", "status", "capacity_w", "present"])
hpilo_processor_gauge = Gauge('hpilo_processor', 'HP iLO processor status  0 = OK, 1 = DEGRADED; 2 = Other', ["product_name", "server_name"])
hpilo_processor_detail_gauge = Gauge('hpilo_processor_detail', 'HP iLO processor detail', ["product_name", "server_name", "name", "status", "cpu_id", "speed"])
hpilo_network_gauge = Gauge('hpilo_network', 'HP iLO network status  0 = OK, 1 = DEGRADED; 2 = Other', ["product_name", "server_name"])
hpilo_temperature_gauge = Gauge('hpilo_temperature', 'HP iLO temperature status  0 = OK, 1 = DEGRADED; 2 = Other', ["product_name", "server_name"])
hpilo_firmware_version = Gauge('hpilo_firmware_version', 'HP iLO firmware version', ["product_name", "server_name", "management_processor", "license_type"])

hpilo_nic_status_gauge = Gauge('hpilo_nic_status', 'HP iLO nic status  0 = OK, 1 = Disabled, 2 = Unknown, 3 = Link Down', ["product_name", "server_name", "nic_name", "mac_address", "ip_address", "network_port"])


# no enty
# 'hpilo_vrm_gauge': hpilo_vrm_gauge,
# 'hpilo_drive_gauge': hpilo_drive_gauge,
gauges = {
    'hpilo_battery_gauge': hpilo_battery_gauge,
    'hpilo_storage_gauge': hpilo_storage_gauge,
    'hpilo_fans_gauge': hpilo_fans_gauge,
    'hpilo_bios_hardware_gauge': hpilo_bios_hardware_gauge,
    'hpilo_memory_gauge': hpilo_memory_gauge,
    'hpilo_power_supplies_gauge': hpilo_power_supplies_gauge,
    'hpilo_power_supplies_detail_gauge': hpilo_power_supplies_detail_gauge,
    'hpilo_processor_gauge': hpilo_processor_gauge,
    'hpilo_processor_detail_gauge': hpilo_processor_detail_gauge,
    'hpilo_network_gauge': hpilo_network_gauge,
    'hpilo_temperature_gauge': hpilo_temperature_gauge,
    'hpilo_firmware_version': hpilo_firmware_version,
    'hpilo_controller_status_gauge': hpilo_controller_status_gauge,
    'hpilo_controller_status_1_gauge': hpilo_controller_status_1_gauge,
    'hpilo_controller_status_3_gauge': hpilo_controller_status_3_gauge

}
