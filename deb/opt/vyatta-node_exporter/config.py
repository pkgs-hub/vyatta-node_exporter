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

    node_exporter = conf.get_config_dict(base, key_mangling=('-', '_'), get_first_key=True)
    node_exporter['config_file'] = config_file

    return ssh

def verify(node_exporter):
    if not node_exporter:
        return None

    verify_vrf(node_exporter)
    return None

def generate(node_exporter):
    if not node_exporter:
        if os.path.isfile(config_file):
            os.unlink(config_file)
        if os.path.isfile(systemd_override):
            os.unlink(systemd_override)

        return None

    render(config_file, '/opt/vyatta-node_exporter/config.j2', node_exporter)
    # Reload systemd manager configuration
    call('systemctl daemon-reload')

    return None

def apply(node_exporter):
    if not node_exporter:
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
