#!/usr/bin/env python
# VMware vSphere Python SDK
# Copyright (c) 2008-2013 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Python program for listing the vms on an ESX / vCenter host
"""

import atexit

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

import tools.cli as cli

import re

def print_vm_info(virtual_machine):
    """
    Print information for a particular virtual machine or recurse into a
    folder with depth protection
    """
    summary = virtual_machine.summary
    print("Name       : ", summary.config.name)
    print("Template   : ", summary.config.template)
    print("Path       : ", summary.config.vmPathName)
    print("Guest      : ", summary.config.guestFullName)
    print("Instance UUID : ", summary.config.instanceUuid)
    print("Bios UUID     : ", summary.config.uuid)
    print("Host name     : ", virtual_machine.runtime.host.name)
    annotation = summary.config.annotation
    if annotation:
        print("Annotation : ", annotation)
    print("State      : ", summary.runtime.powerState)
    if summary.guest is not None:
        ip_address = summary.guest.ipAddress
        tools_version = summary.guest.toolsStatus
        if tools_version is not None:
            print("VMware-tools: ", tools_version)
        else:
            print("Vmware-tools: None")
        if ip_address:
            print("IP         : ", ip_address)
        else:
            print("IP         : None")
    if summary.runtime.question is not None:
        print("Question  : ", summary.runtime.question.text)
    print("")

def print_vm_info_as_yaml(virtual_machine):
    """
    Print information for a particular virtual machine as yaml
    """
    summary = virtual_machine.summary
    path = summary.config.vmPathName
    p = re.compile(r'^\[(\w+)\].*$')
    m = p.match(path)
    datastore = m.group(1)
    print("  - { ",                                                       end="")
    print("id: ",        summary.config.name,               ", ", sep="", end="")
    print("host: ",      virtual_machine.runtime.host.name, ", ", sep="", end="")
    print("datastore: ", datastore,                         ", ", sep="", end="")
    print("uuid: ",      summary.config.instanceUuid,       ", ", sep="", end="")
    print("template: ",  summary.config.template,           ", ", sep="", end="")
    print("state: ",     summary.runtime.powerState,              sep="", end="")
    print(" } ")


def get_more_args():
    """
    Adds more args to tools func
    """
    parser = cli.build_arg_parser()

    parser.add_argument('-y', '--yaml',
                        required=False,
                        action='store_true',
                        help='print as yaml')

    args = parser.parse_args()

    return cli.prompt_for_password(args)

def main():
    """
    Simple command-line program for listing the virtual machines on a system.
    """

    args = get_more_args()

    try:
        if args.disable_ssl_verification:
            service_instance = connect.SmartConnectNoSSL(host=args.host,
                                                         user=args.user,
                                                         pwd=args.password,
                                                         port=int(args.port))
        else:
            service_instance = connect.SmartConnect(host=args.host,
                                                    user=args.user,
                                                    pwd=args.password,
                                                    port=int(args.port))

        atexit.register(connect.Disconnect, service_instance)

        content = service_instance.RetrieveContent()

        container = content.rootFolder  # starting point to look into
        viewType = [vim.VirtualMachine]  # object types to look for
        recursive = True  # whether we should look into it recursively
        containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive)

        children = containerView.view
        if args.yaml:
            print("---\n")
            print("pyvmomy_getallvms:\n")
        for child in children:
            if args.yaml:
                print_vm_info_as_yaml(child)
            else:
                print_vm_info(child)

    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0

# Start program
if __name__ == "__main__":
    main()
