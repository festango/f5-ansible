#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: bigip_device_dns
short_description: Manage BIG-IP device DNS settings
description:
   - Manage BIG-IP device DNS settings
version_added: "2.1"
options:
  append:
    description:
      - If C(yes), will only add specific servers to the device configuration,
        not set them to just the list in C(nameserver), C(nameservers),
        C(forwarder), C(forwarders), C(search_domain) or C(search_domains).
    choices: ['yes', 'no']
    default: no
  server:
    description:
      - BIG-IP host
    required: true
  password:
    description:
      - BIG-IP password
    required: true
  cache:
    description:
      - Specifies whether the system caches DNS lookups or performs the
        operation each time a lookup is needed. Please note that this applies
        only to Access Policy Manager features, such as ACLs, web application
        rewrites, and authentication.
    required: false
    default: disable
    choices: ['enable', 'disable']
  nameserver:
    description:
      - A single name server that the system uses to validate DNS lookups, and
        resolve host names. At least one of C(nameservers) or C(nameserver) are
        required.
    required: false
    default: None
  nameservers:
    description:
      - A list of name servers that the system uses to validate DNS lookups,
        and resolve host names. At least one of C(nameservers) or C(nameserver)
        are required.
    required: false
    default: []
  forwarder:
    description:
      - A single BIND servers that the system can use to perform DNS lookups.
        BIND allows you to cache and store DNS requests and responses on a
        local server and minimize DNS server requests, and bandwidth. At least
        one of C(forwarders) or C(forwarder) are required.
    required: false
    default: None
  forwarders:
    description:
      - A list of BIND servers that the system can use to perform DNS lookups.
        BIND allows you to cache and store DNS requests and responses on a
        local server and minimize DNS server requests, and bandwidth. At least
        one of C(forwarders) or C(forwarder) are required.
    required: false
    default: []
  search_domain:
    description:
      - A single domain that the system searches for local domain lookups, to
        resolve local host names. At least one of C(search_domains) or
        C(search_domain) are required.
    required: false
    default: None
  search_domains:
    description:
      - A list of domains that the system searches for local domain lookups, to
        resolve local host names. At least one of C(search_domains) or
        C(search_domain) are required.
    required: false
    default: []
  ip_version:
    description:
      - Specifies whether the DNS specifies IP addresses using IPv4 or IPv6.
    required: false
    default: 4
    choices: [4, 6]
  state:
    description:
      - The state of the variable on the system. When C(present), guarantees
        that an existing variable is set to C(value).
    required: false
    default: present
    choices: ['absent', 'present']
  user:
    description:
      - BIG-IP username
    required: true
    aliases:
      - username
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be
        used on personally controlled sites using self-signed certificates.
    required: false
    default: true

notes:
   - Requires the requests Python package on the host. This is as easy as pip
     install requests

requirements: [ "requests" ]
author: Tim Rupp <caphrim007@gmail.com> (@caphrim007)
'''

EXAMPLES = """
- name: Set the boot.quiet DB variable on the BIG-IP
  bigip_sysdb:
      server: "big-ip"
      key: "boot.quiet"
      value: "disable"
  delegate_to: localhost
"""

import json
import socket

try:
    import requests
except ImportError:
    requests_found = False
else:
    requests_found = True


class BigIpCommon(object):
    def __init__(self, user, password, server, nameservers=[], forwarders=[],
                 search_domains=[], cache=None, ip_version=None, append=False,
                 validate_certs=True):

        self._username = user
        self._password = password
        self._hostname = server

        if isinstance(nameservers, list):
            self._nameservers = nameservers
        else:
            self._nameservers = [nameservers]

        if isinstance(forwarders, list):
            self._forwarders = forwarders
        else:
            self._forwarders = [forwarders]

        if isinstance(search_domains, list):
            self._search_domains = search_domains
        else:
            self._search_domains = [search_domains]

        self._cache = cache
        self._append = append
        self._ip_version = str(ip_version)

        self._validate_certs = validate_certs


class BigIpRest(BigIpCommon):
    def __init__(self, user, password, server, nameservers=[], forwarders=[],
                 search_domains=[], cache=None, ip_version=None, append=False,
                 validate_certs=True):

        """Handles manipulating the DNS settings on a device via REST interface

        The REST data structure looks like this

        {
          "kind": "tm:sys:dns:dnsstate",
          "selfLink": "https://localhost/mgmt/tm/sys/dns?ver=12.0.0",
          "description": "configured-by-dhcp",
          "include": "options inet6",
          "nameServers": [
            "10.2.1.254"
          ],
          "search": [
            "hype.f5net.com"
          ]
        }
        """

        super(BigIpRest, self).__init__(user, password, server, nameservers,
                                        forwarders, search_domains, cache,
                                        ip_version, append, validate_certs)

        self._headers = dict()
        self._headers['Content-Type'] = 'application/json'

    def dhcp_enabled(self):
        uri = 'https://%s/mgmt/tm/sys/db/dhclient.mgmt' % (self._hostname)
        resp = requests.get(uri,
                            auth=(self._username, self._password),
                            verify=self._validate_certs)

        if resp.status_code == 200:
            res = resp.json()
            if res['value'] == 'enable':
                return True
            else:
                return False
        else:
            raise Exception()

    def _read_dns(self):
        result = {}

        uri = 'https://%s/mgmt/tm/sys/dns' % (self._hostname)
        resp = requests.get(uri,
                            auth=(self._username, self._password),
                            verify=self._validate_certs)

        if resp.status_code == 200:
            res = resp.json()
            if 'nameServers' in res:
                result['nameservers'] = res['nameServers']
            else:
                result['nameservers'] = []

            if 'search' in res:
                result['search_domains'] = res['search']
            else:
                result['search_domains'] = []

            if 'include' in res and 'options inet6' in res['include']:
                result['ip_version'] = '6'
            else:
                result['ip_version'] = '4'

        return result

    def _read_cache(self):
        uri = 'https://%s/mgmt/tm/sys/db/dns.cache' % (self._hostname)
        resp = requests.get(uri,
                            auth=(self._username, self._password),
                            verify=self._validate_certs)

        if resp.status_code == 200:
            res = resp.json()
            return res['value']

    def _read_forwarders(self):
        uri = 'https://%s/mgmt/tm/sys/db/dns.proxy.__iter__' % (self._hostname)
        resp = requests.get(uri,
                            auth=(self._username, self._password),
                            verify=self._validate_certs)

        if resp.status_code == 200:
            res = resp.json()
            return res['value'].split(' ')

    def read(self):
        result = dict()

        cache = self._read_cache()
        forwarders = self._read_forwarders()
        dns = self._read_dns()

        result.update({'cache': cache})
        result.update({'forwarders': forwarders})
        result.update(dns)

        return result

    def _present_dns(self, current):
        payload = dict()

        # DNS servers can be set independently
        if self._nameservers and self._append:
            if 'nameservers' in current:
                current_servers = current['nameservers']
                if not set(self._nameservers).issubset(set(current_servers)):
                    current_servers += self._nameservers
                    payload['nameServers'] = list(set(current_servers))
            else:
                payload['nameServers'] = self._nameservers
        elif self._nameservers:
            if 'nameservers' in current and current['nameservers'] != self._nameservers:
                payload['nameServers'] = self._nameservers
            elif 'nameservers' not in current:
                payload['nameServers'] = self._nameservers

        # Search domains can be set independently
        if self._search_domains and self._append:
            if 'search_domains' in current:
                current_servers = current['search_domains']
                if not set(self._search_domains).issubset(set(current_servers)):
                    current_servers += self._search_domains
                    payload['search'] = list(set(current_servers))
            else:
                payload['search'] = self._search_domains
        elif self._search_domains:
            if 'search_domains' in current and current['search_domains'] != self._search_domains:
                payload['search'] = self._search_domains
            elif 'search_domains' not in current:
                payload['search'] = self._search_domains

        # IP version can be set independently
        if self._ip_version:
            if 'ip_version' in current and current['ip_version'] != self._ip_version:
                if self._ip_version == '6':
                    payload['include'] = 'options inet6'
                elif self._ip_version == '4':
                    payload['include'] = ''

        if payload:
            uri = 'https://%s/mgmt/tm/sys/dns' % (self._hostname)
            resp = requests.patch(uri,
                                  auth=(self._username, self._password),
                                  data=json.dumps(payload),
                                  verify=self._validate_certs)
            if resp.status_code == 200:
                return True
            else:
                res = resp.json()
                raise Exception(res['message'])
        else:
            return False

    def _present_forwarders(self, current):
        payload = dict()
        forwarders = list()

        # Forwarders can be set independently
        if self._forwarders and self._append:
            if 'forwarders' in current:
                current_servers = current['forwarders']
                if not set(self._forwarders).issubset(set(current_servers)):
                    current_servers += self._forwarders
                    forwarders = list(set(current_servers))
            else:
                forwarders = self._forwarders
        elif self._forwarders:
            if 'forwarders' in current and current['forwarders'] != self._forwarders:
                forwarders = self._forwarders
            elif 'forwarders' not in current:
                forwarders = self._forwarders

        if forwarders:
            payload['value'] = ' '.join(forwarders)
            uri = 'https://%s/mgmt/tm/sys/db/dns.proxy.__iter__' % (self._hostname)
            resp = requests.put(uri,
                                auth=(self._username, self._password),
                                data=json.dumps(payload),
                                verify=self._validate_certs)
            if resp.status_code == 200:
                return True
            else:
                res = resp.json()
                raise Exception(res['message'])
        else:
            return False

    def _present_cache(self, current):
        payload = dict()

        if self._cache:
            if 'cache' in current and current['cache'] != self._cache:
                payload['value'] = self._cache

        if payload:
            uri = 'https://%s/mgmt/tm/sys/db/dns.cache' % (self._hostname)
            resp = requests.patch(uri,
                                  auth=(self._username, self._password),
                                  data=json.dumps(payload),
                                  verify=self._validate_certs)
            if resp.status_code == 200:
                return True
            else:
                res = resp.json()
                raise Exception(res['message'])
        else:
            return False

    def _absent_forwarders(self, current):
        payload = dict()
        forwarders = list()

        if self._forwarders and 'forwarders' in current:
            set_current = set(current['forwarders'])
            set_new = set(self._forwarders)

            forwarders = set_current - set_new
            if forwarders != set_current:
                forwarders = list(forwarders)
                payload['value'] = ' '.join(forwarders)

        if payload:
            uri = 'https://%s/mgmt/tm/sys/db/dns.proxy.__iter__' % (self._hostname)
            resp = requests.patch(uri,
                                  auth=(self._username, self._password),
                                  data=json.dumps(payload),
                                  verify=self._validate_certs)
            if resp.status_code == 200:
                return True
            else:
                res = resp.json()
                raise Exception(res['message'])
        else:
            return False

    def _absent_dns(self, current):
        payload = dict()

        if self._nameservers and 'nameservers' in current:
            set_current = set(current['nameservers'])
            set_new = set(self._nameservers)

            nameservers = set_current - set_new
            if nameservers != set_current:
                payload['nameServers'] = list(nameservers)

        if self._search_domains and 'search_domains' in current:
            set_current = set(current['search_domains'])
            set_new = set(self._search_domains)

            search_domains = set_current - set_new
            if search_domains != set_current:
                payload['search'] = list(search_domains)

        if payload:
            uri = 'https://%s/mgmt/tm/sys/dns' % (self._hostname)
            resp = requests.patch(uri,
                                  auth=(self._username, self._password),
                                  data=json.dumps(payload),
                                  verify=self._validate_certs)
            if resp.status_code == 200:
                return True
            else:
                res = resp.json()
                raise Exception(res['message'])
        else:
            return False

    def present(self):
        changed = False
        result = False
        current = self.read()

        result = self._present_dns(current)
        if result:
            changed = True

        result = self._present_forwarders(current)
        if result:
            changed = True

        result = self._present_cache(current)
        if result:
            changed = True

        if changed:
            self.save()

        return changed

    def absent(self):
        changed = False
        result = False
        current = self.read()

        result = self._absent_dns(current)
        if result:
            changed = True

        result = self._absent_forwarders(current)
        if result:
            changed = True

        if changed:
            self.save()

        return changed

    def save(self):
        payload = dict(command='save')
        uri = 'https://%s/mgmt/tm/sys/config' % (self._hostname)
        resp = requests.post(uri,
                             auth=(self._username, self._password),
                             data=json.dumps(payload),
                             verify=self._validate_certs)
        if resp.status_code == 200:
            return True
        else:
            res = resp.json()
            raise Exception(res['message'])


def main():
    changed = False

    module = AnsibleModule(
        argument_spec=dict(
            append=dict(default='no', type='bool'),
            cache=dict(required=False, choices=['disable', 'enable'], default=None),
            server=dict(required=True),
            password=dict(required=True),
            state=dict(default='present', choices=['absent', 'present']),
            user=dict(required=True, aliases=['username']),
            nameserver=dict(required=False, type='str', default=None),
            nameservers=dict(required=False, type='list', default=[]),
            forwarder=dict(required=False, type='str', default=None),
            forwarders=dict(required=False, type='list', default=[]),
            search_domain=dict(required=False, type='str', default=None),
            search_domains=dict(required=False, type='list', default=[]),
            ip_version=dict(required=False, default=None, choices=['4', '6']),
            validate_certs=dict(default='yes', type='bool')
        ),
        required_one_of=[[
            'nameserver', 'nameservers', 'search_domain', 'search_domains',
            'forwarder', 'forwarders', 'ip_version', 'cache'
        ]],
        mutually_exclusive=[
            ['nameserver', 'nameservers'],
            ['forwarder', 'forwarders'],
            ['search_domain', 'search_domains']
        ]
    )

    hostname = module.params.get('server')
    password = module.params.get('password')
    username = module.params.get('user')
    state = module.params.get('state')
    append = module.params.get('append')
    cache = module.params.get('cache')
    nameserver = module.params.get('nameserver')
    nameservers = module.params.get('nameservers')
    forwarder = module.params.get('forwarder')
    forwarders = module.params.get('forwarders')
    search_domain = module.params.get('search_domain')
    search_domains = module.params.get('search_domains')
    ip_version = module.params.get('ip_version')
    validate_certs = module.params.get('validate_certs')

    try:
        if not requests_found:
            raise Exception("The python requests module is required")

        if nameserver:
            nameservers = nameserver
        if forwarder:
            forwarders = forwarder
        if search_domain:
            search_domains = search_domain

        if append and not (nameservers or forwarders or search_domains):
            mesg = "The 'append' parameter requires at least one of 'nameservers', 'forwarders', or 'search_domains'"
            module.fail_json(msg=mesg)

        obj = BigIpRest(username, password, hostname, nameservers, forwarders,
                        search_domains, cache, ip_version, append, validate_certs)

        if obj.dhcp_enabled():
            module.fail_json(msg="DHCP on the mgmt interface must be disabled to make use of this module")

        if state == "present":
            changed = obj.present()
        elif state == "absent":
            if not (nameservers or forwarders or search_domains):
                mesg = "State 'absent' requires at least one of 'nameservers', 'forwarders', or 'search_domains'"
                module.fail_json(msg=mesg)

            changed = obj.absent()
    except socket.timeout, e:
        module.fail_json(msg="Timed out connecting to the BIG-IP")
    except socket.timeout, e:
        module.fail_json(msg=str(e))

    module.exit_json(changed=changed)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
