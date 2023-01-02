#!/usr/bin/env python3
import os

from sys import exit

from vyos.config import Config
from vyos.configdict import dict_merge
from vyos.configverify import verify_vrf
from vyos.util import call
from vyos.template import render
from vyos import ConfigError
from vyos import airbag
from jinja2 import Template


airbag.enable()

config_file = r'/etc/default/node_exporter'

def get_config(config=None):
    if config:
        conf = config
    else:
        conf = Config()
    base = ['service', 'monitoring', 'node-exporter']
    if not conf.exists(base):
        return None

    node_exporter = conf.get_config_dict(base, get_first_key=True)

    return node_exporter

def verify(node_exporter):
    if node_exporter is None:
        return None

    # upstream configuration is required for zia to work as expected
    if "upstream" not in zia_server:
        print("ZIA-Server upstream configuration is required!")
        exit(1)
        
    # upstream configuration requires address and port
    error = False
    if "address" not in zia_server["upstream"]:
        print("Missing ZIA-Server upstream address!")
        error = True
    if "port" not in zia_server["upstream"]:
        print("Missing ZIA-Server upstream port!")
        error = True
    if error:
        exit(1)
    
    verify_vrf(node_exporter)
    return None

def generate(node_exporter):
    if node_exporter is None:
        if os.path.isfile(config_file):
            os.unlink(config_file)
        return None

    # merge web/listen-address with subelement web/listen-address/port
    if 'web' in node_exporter:
        # {'listen-address': {'0.0.0.0': {'port': '8080'}}
        if 'listen-address' in node_exporter['web']:
            address = list(node_exporter['web']['listen-address'].keys())[0]
            port = node_exporter['web']['listen-address'][address].get("port", 9100)
            node_exporter['web']['listen-address'] = f"{address}:{port}"
            del node_exporter['web']['listen-address']['port']

    with open('/opt/vyatta-node_exporter/config.j2', 'r') as tmpl, open(config_file, 'w') as out:
        template = Template(tmpl.read()).render(data=node_exporter)
        out.write(template)

    # Reload systemd manager configuration
    call('systemctl daemon-reload')

    return None

def apply(node_exporter):
    if node_exporter is None:
        # node_exporter is removed in the commit
        call('systemctl stop node_exporter.service')
        return None

    call('systemctl restart node_exporter.service')
    return None

if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        exit(1)
