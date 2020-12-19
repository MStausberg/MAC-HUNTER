"""
AUTHOR: IPvZero
DATE: 21 Oct 2020

This script is intended to work on Cisco IOS and IOS-XE devices.
Due to an issue with the Genie parsers ensure your Nornir inventory
platform is set to 'cisco_xe' - even if the device is regular IOS.


19 Dec 2020 Ported to nornir 3 by paketb0te

"""

# Imports
from rich import print as rprint
from nornir import InitNornir
from nornir.core.task import Task
from nornir.core.plugins.connections import ConnectionPluginRegister
from nornir_netmiko.tasks import netmiko_send_command
from netaddr import EUI

# Register Plugins
ConnectionPluginRegister.register("connection-name", netmiko_send_command)


def get_interface_info(task: Task, target: EUI) -> None:
    """
    Get MAC addresses of all interfaces and compare to target.
    If present, identify Device and Interface
    """
    interfaces = task.run(
        task=netmiko_send_command, command_string="show interfaces", use_genie=True
    ).result

    for intf in interfaces:
        mac_addr = EUI(interfaces[intf]["mac_address"])
        if target == mac_addr:
            print_info(task, intf, target)


def print_info(task: Task, intf: str, target: EUI) -> None:

    """
    Execute show cdp neighbor and show version commands
    on target device. Parse information and return output
    """

    rprint("\n[green]*** TARGET IDENTIFIED ***[/green]")
    print(f"MAC ADDRESS: {target} is present on {task.host}'s {intf}")
    rprint("\n[cyan]GENERATING DETAILS...[/cyan]")
    cdp_result = task.run(
        task=netmiko_send_command, command_string="show cdp neighbors", use_genie=True
    )
    task.host["cdpinfo"] = cdp_result.result
    index = task.host["cdpinfo"]["cdp"]["index"]
    intf_neighbors = {}
    for num in index:
        if intf == index[num]["local_interface"]:
            dev_id = index[num]["device_id"]
            port_id = index[num]["port_id"]
            intf_neighbors[dev_id] = port_id
    ver_result = task.run(
        task=netmiko_send_command, command_string="show version", use_genie=True
    )
    task.host["verinfo"] = ver_result.result
    version = task.host["verinfo"]["version"]
    serial_num = version["chassis_sn"]
    uptime = version["uptime"]
    version_long = version["os"] + " " + version["version"]
    print(f"DEVICE MGMT IP: {task.host.hostname}")
    print(f"DEVICE SERIAL NUMBER: {serial_num}")
    print(f"DEVICE OS: {version_long}")
    print(f"DEVICE UPTIME: {uptime}\n")
    if intf_neighbors:
        rprint("[cyan]REMOTE CONNECTION DETAILS...[/cyan]")
        for neighbor in intf_neighbors:
            print(f"Connected to {neighbor}'s {intf_neighbors[neighbor]}")
        print()


def main():
    """
    Main Function, execution starts here.
    """
    nornir = InitNornir(config_file="config.yaml")
    target = EUI(input("Enter the MAC address you wish to find: "))
    nornir.run(task=get_interface_info, target=target)


if __name__ == "__main__":
    main()
