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
module: bigip_software
short_description: Manage BIG-IP software versions and hotfixes
description:
   - Manage BIG-IP software versions and hotfixes
version_added: "2.0"
options:
  connection:
    description:
      - The connection used to interface with the BIG-IP
    required: false
    default: icontrol
    choices: [ "rest", "icontrol" ]
  force:
    description:
      - If C(yes) will upload the file every time and replace the file on the
        device. If C(no), the file will only be uploaded if it does not already
        exist. Generally should be C(yes) only in cases where you have reason
        to believe that the image was corrupted during upload.
    required: false
    default: no
    choices:
      - yes
      - no
  hotfix:
    description:
      - The path to an optional Hotfix to install. This parameter requires that
        the C(software) parameter be specified.
    required: false
    default: None
    aliases:
      - hotfix_image
  password:
    description:
      - BIG-IP password
    required: true
  server:
    description:
      - BIG-IP host
    required: true
  state:
    description:
      - When C(installed), ensures that the software is uploaded and installed,
        on the system. The device is not, however, rebooted into the new software.
        When C(activated), ensures that the software is uploaded, installed, and
        the system is rebooted to the new software. When C(present), ensures
        that the software is uploaded. When C(absent), only the uploaded image
        will be removed from the system
    required: false
    default: activated
    choices:
      - absent
      - activated
      - installed
      - present
  software:
    description:
      - The path to the software (base image) to install. The parameter must be
        provided if the C(state) is either C(installed) or C(activated).
    required: false
    aliases:
      - base_image
  user:
    description:
      - BIG-IP username
    required: false
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be
        used on personally controlled sites using self-signed certificates.
    required: false
    default: true
  volume:
    description:
      - The volume to install the software and, optionally, the hotfix to. This
        parameter is only required when the C(state) is either C(activated) or
        C(installed).
    required: false

notes:
   - Requires the bigsuds Python package on the host if using the iControl
     interface. This is as easy as pip install bigsuds
   - Requires the lxml Python package on the host. This can be installed
     with pip install lxml
   - https://devcentral.f5.com/articles/icontrol-101-06-file-transfer-apis

requirements: [ "bigsuds", "lxml" ]
author: Tim Rupp <caphrim007@gmail.com> (@caphrim007)
'''

EXAMPLES = """
- name: Remove uploaded hotfix
  bigip_software:
      server: "bigip.localhost.localdomain"
      user: "admin"
      password: "admin"
      hotfix: "/root/Hotfix-BIGIP-11.6.0.3.0.412-HF3.iso"
      state: "absent"
  delegate_to: localhost

- name: Upload hotfix
  bigip_software:
      server: "bigip.localhost.localdomain"
      user: "admin"
      password: "admin"
      hotfix: "/root/Hotfix-BIGIP-11.6.0.3.0.412-HF3.iso"
      state: "present"
  delegate_to: localhost

- name: Remove uploaded base image
  bigip_software:
      server: "bigip.localhost.localdomain"
      user: "admin"
      password: "admin"
      software: "/root/BIGIP-11.6.0.0.0.401.iso"
      state: "absent"
  delegate_to: localhost

- name: Upload base image
  bigip_software:
      server: "bigip.localhost.localdomain"
      user: "admin"
      password: "admin"
      software: "/root/BIGIP-11.6.0.0.0.401.iso"
      state: "present"
  delegate_to: localhost

- name: Upload base image and hotfix
  bigip_software:
      server: "bigip.localhost.localdomain"
      user: "admin"
      password: "admin"
      software: "/root/BIGIP-11.6.0.0.0.401.iso"
      hotfix: "/root/Hotfix-BIGIP-11.6.0.3.0.412-HF3.iso"
      state: "present"
  delegate_to: localhost

- name: Remove uploaded base image and hotfix
  bigip_software:
      server: "bigip.localhost.localdomain"
      user: "admin"
      password: "admin"
      software: "/root/BIGIP-11.6.0.0.0.401.iso"
      hotfix: "/root/Hotfix-BIGIP-11.6.0.3.0.412-HF3.iso"
      state: "absent"
  delegate_to: localhost

- name: Install (upload, install) base image. Create volume if not exists
  bigip_software:
      server: "bigip.localhost.localdomain"
      user: "admin"
      password: "admin"
      software: "/root/BIGIP-11.6.0.0.0.401.iso"
      volume: "HD1.1"
      state: "installed"
  delegate_to: localhost

- name: Install (upload, install) base image and hotfix. Create volume if not exists
  bigip_software:
      server: "bigip.localhost.localdomain"
      user: "admin"
      password: "admin"
      software: "/root/BIGIP-11.6.0.0.0.401.iso"
      hotfix: "/root/Hotfix-BIGIP-11.6.0.3.0.412-HF3.iso"
      volume: "HD1.1"
      state: "installed"

- name: Activate (upload, install, reboot) base image. Create volume if not exists
  bigip_software:
      server: "bigip.localhost.localdomain"
      user: "admin"
      password: "admin"
      software: "/root/BIGIP-11.6.0.0.0.401.iso"
      volume: "HD1.1"
      state: "activated"
  delegate_to: localhost

- name: Activate (upload, install, reboot) base image and hotfix. Create volume if not exists
  bigip_software:
      server: "bigip.localhost.localdomain"
      user: "admin"
      password: "admin"
      software: "/root/BIGIP-11.6.0.0.0.401.iso"
      hotfix: "/root/Hotfix-BIGIP-11.6.0.3.0.412-HF3.iso"
      volume: "HD1.1"
      state: "activated"
"""

import base64
import socket
import os
import time
import subprocess
import io
import urllib
import struct
import datetime

from lxml import etree

try:
    import bigsuds
    BIGSUDS_AVAILABLE = True
except ImportError:
    BIGSUDS_AVAILABLE = False

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

SECTOR_SIZE = 2048
TRANSPORTS = ['rest', 'soap']
STATES = ['absent', 'activated', 'installed', 'present']

# Size of chunks of data to read and send via the iControl API
CHUNK_SIZE = 512 * 1024


class ActiveVolumeError(Exception):
    pass


class NoVolumeError(Exception):
    pass


class NoBaseImageError(Exception):
    pass


class SoftwareInstallError(Exception):
    pass


class ISO9660IOError(IOError):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return "Path not found: %s" % self.path


class ISO9660(object):
    def __init__(self, url):
        self._buff  = None #input buffer
        self._root  = None #root node
        self._pvd   = {}   #primary volume descriptor
        self._paths = []   #path table

        self._url   = url
        if not hasattr(self, '_get_sector'): #it might have been set by a subclass
            self._get_sector = self._get_sector_file

        ### Volume Descriptors
        sector = 0x10
        while True:
            self._get_sector(sector, SECTOR_SIZE)
            sector += 1
            ty = self._unpack('B')

            if ty == 1:
                self._unpack_pvd()
            elif ty == 255:
                break
            else:
                continue

        ### Path table
        l0 = self._pvd['path_table_size']
        self._get_sector(self._pvd['path_table_l_loc'], l0)

        while l0 > 0:
            p = {}
            l1 = self._unpack('B')
            l2 = self._unpack('B')
            p['ex_loc'] = self._unpack('<I')
            p['parent'] = self._unpack('<H')
            p['name']   = self._unpack_string(l1)
            if p['name'] == '\x00':
                p['name'] = ''

            if l1%2 == 1:
                self._unpack('B')

            self._paths.append(p)

            l0 -= 8 + l1 + (l1 % 2)

        assert l0 == 0

    ##
    ## Retrieve file contents as a string
    ##
    def get_file(self, path):
        path = path.upper().strip('/').split('/')
        path, filename = path[:-1], path[-1]

        if len(path)==0:
            parent_dir = self._root
        else:
            try:
                parent_dir = self._dir_record_by_table(path)
            except ISO9660IOError:
                parent_dir = self._dir_record_by_root(path)

        f = self._search_dir_children(parent_dir, filename)

        self._get_sector(f['ex_loc'], f['ex_len'])
        return self._unpack_raw(f['ex_len'])

    def _get_sector_file(self, sector, length):
        with open(self._url, 'rb') as f:
            f.seek(sector*SECTOR_SIZE)
            self._buff = StringIO(f.read(length))

    ##
    ## Return the record for final directory in a path
    ##
    def _dir_record_by_table(self, path):
        for e in self._paths[::-1]:
            search = list(path)
            f = e
            while f['name'] == search[-1]:
                search.pop()
                f = self._paths[f['parent']-1]
                if f['parent'] == 1:
                    e['ex_len'] = SECTOR_SIZE #TODO
                    return e
        raise ISO9660IOError(path)

    def _dir_record_by_root(self, path):
        current = self._root
        remaining = list(path)

        while remaining:
            current = self._search_dir_children(current, remaining[0])

            remaining.pop(0)

        return current

    ##
    ## Unpack the Primary Volume Descriptor
    ##
    def _unpack_pvd(self):
        self._pvd['type_code']                     = self._unpack_string(5)
        self._pvd['standard_identifier']           = self._unpack('B')
        self._unpack_raw(1)                        #discard 1 byte
        self._pvd['system_identifier']             = self._unpack_string(32)
        self._pvd['volume_identifier']             = self._unpack_string(32)
        self._unpack_raw(8)                        #discard 8 bytes
        self._pvd['volume_space_size']             = self._unpack_both('i')
        self._unpack_raw(32)                       #discard 32 bytes
        self._pvd['volume_set_size']               = self._unpack_both('h')
        self._pvd['volume_seq_num']                = self._unpack_both('h')
        self._pvd['logical_block_size']            = self._unpack_both('h')
        self._pvd['path_table_size']               = self._unpack_both('i')
        self._pvd['path_table_l_loc']              = self._unpack('<i')
        self._pvd['path_table_opt_l_loc']          = self._unpack('<i')
        self._pvd['path_table_m_loc']              = self._unpack('>i')
        self._pvd['path_table_opt_m_loc']          = self._unpack('>i')
        _, self._root = self._unpack_record()      #root directory record
        self._pvd['volume_set_identifer']          = self._unpack_string(128)
        self._pvd['publisher_identifier']          = self._unpack_string(128)
        self._pvd['data_preparer_identifier']      = self._unpack_string(128)
        self._pvd['application_identifier']        = self._unpack_string(128)
        self._pvd['copyright_file_identifier']     = self._unpack_string(38)
        self._pvd['abstract_file_identifier']      = self._unpack_string(36)
        self._pvd['bibliographic_file_identifier'] = self._unpack_string(37)
        self._pvd['volume_datetime_created']       = self._unpack_vd_datetime()
        self._pvd['volume_datetime_modified']      = self._unpack_vd_datetime()
        self._pvd['volume_datetime_expires']       = self._unpack_vd_datetime()
        self._pvd['volume_datetime_effective']     = self._unpack_vd_datetime()
        self._pvd['file_structure_version']        = self._unpack('B')

    ##
    ## Unpack a directory record (a listing of a file or folder)
    ##
    def _unpack_record(self, read=0):
        l0 = self._unpack('B')

        if l0 == 0:
            return read+1, None

        l1 = self._unpack('B')

        d = dict()
        d['ex_loc']               = self._unpack_both('I')
        d['ex_len']               = self._unpack_both('I')
        d['datetime']             = self._unpack_dir_datetime()
        d['flags']                = self._unpack('B')
        d['interleave_unit_size'] = self._unpack('B')
        d['interleave_gap_size']  = self._unpack('B')
        d['volume_sequence']      = self._unpack_both('h')

        l2 = self._unpack('B')
        d['name'] = self._unpack_string(l2).split(';')[0]
        if d['name'] == '\x00':
            d['name'] = ''

        if l2 % 2 == 0:
            self._unpack('B')

        t = 34 + l2 - (l2 % 2)

        e = l0-t
        if e>0:
            extra = self._unpack_raw(e)

        return read+l0, d

    #Assuming d is a directory record, this generator yields its children
    def _unpack_dir_children(self, d):
        sector = d['ex_loc']
        read = 0
        self._get_sector(sector, 2048)

        read, r_self = self._unpack_record(read)
        read, r_parent = self._unpack_record(read)

        while read < r_self['ex_len']: #Iterate over files in the directory
            if read % 2048 == 0:
                sector += 1
                self._get_sector(sector, 2048)
            read, data = self._unpack_record(read)

            if data == None: #end of directory listing
                to_read = 2048 - (read % 2048)
                self._unpack_raw(to_read)
                read += to_read
            else:
                yield data

    #Search for one child amongst the children
    def _search_dir_children(self, d, term):
        for e in self._unpack_dir_children(d):
            if e['name'] == term:
                return e

        raise ISO9660IOError(term)
    ##
    ## Datatypes
    ##
    def _unpack_raw(self, l):
        return self._buff.read(l)

    #both-endian
    def _unpack_both(self, st):
        a = self._unpack('<'+st)
        b = self._unpack('>'+st)
        assert a == b
        return a

    def _unpack_string(self, l):
        return self._buff.read(l).rstrip(' ')

    def _unpack(self, st):
        if st[0] not in ('<','>'):
            st = '<' + st
        d = struct.unpack(st, self._buff.read(struct.calcsize(st)))
        if len(st) == 2:
            return d[0]
        else:
            return d

    def _unpack_vd_datetime(self):
        return self._unpack_raw(17) #TODO

    def _unpack_dir_datetime(self):
        epoch = datetime.datetime(1970, 1, 1)
        date = self._unpack_raw(7)
        t = [struct.unpack('<B', i)[0] for i in date[:-1]]
        t.append(struct.unpack('<b', date[-1])[0])
        t[0] += 1900
        t_offset = t.pop(-1) * 15 * 60.    # Offset from GMT in 15min intervals, converted to secs
        t_timestamp = (datetime.datetime(*t) - epoch).total_seconds() - t_offset
        t_datetime = datetime.datetime.fromtimestamp(t_timestamp)
        t_readable = t_datetime.strftime('%Y-%m-%d %H:%M:%S')
        return t_readable


class BigIpApiFactory(object):
    def factory(module):
        type = module.params.get('connection')

        if type == "rest":
            module.fail_json(msg='The REST connection is currently not supported')
        elif type == "soap":
            if not BIGSUDS_AVAILABLE:
                raise Exception("The python bigsuds module is required")
            return BigIpSoapApi(check_mode=module.check_mode, **module.params)

    factory = staticmethod(factory)


class BigIpCommon(object):
    def __init__(self, *args, **kwargs):
        self.result = dict(changed=False, changes=dict())

        self.current = dict()

        if kwargs['hotfix']:
            kwargs['photfix'] = self.iso_info(kwargs['hotfix'])

        if kwargs['software']:
            kwargs['psoftware'] = self.iso_info(kwargs['software'])

        self.params = kwargs

    def iso_info(self, iso):
        result = dict(
            product=None,
            version=None,
            build=None
        )

        cd = ISO9660(iso)
        content = cd.get_file('/METADATA.XML')
        content = io.BytesIO(content)

        context = etree.iterparse(content)
        for action, elem in context:
            if elem.text:
                text = elem.text

            if elem.tag == 'productName':
                result['product'] = text
            elif elem.tag == 'version':
                result['version'] = text
            elif elem.tag == 'buildNumber':
                result['build'] = text
        return result

    def flush(self):
        result = dict()
        state = self.params['state']
        volume = self.params['volume']
        software = self.params['software']

        if state == 'activated' or state == 'installed':
            if not volume:
                raise NoVolumeError
            elif not software:
                raise NoBaseImageError

        if state == "activated":
            changed = self.activated()
        elif state == "installed":
            changed = self.installed()
        elif state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        if state in ['activated', 'installed', 'present']:
            if not self.params['check_mode']:
                current = self.read()
                result.update(current)

        result.update(dict(changed=changed))
        return result


class BigIpSoapApi(BigIpCommon):
    def __init__(self, *args, **kwargs):
        super(BigIpSoapApi, self).__init__(*args, **kwargs)

        self.api = bigip_api(kwargs['server'],
                             kwargs['user'],
                             kwargs['password'],
                             kwargs['validate_certs'])

    def read(self):
        result = dict(
            software=[],
            hotfix=[]
        )

        try:
            images = self.api.System.SoftwareManagement.get_software_image_list()
            for image in images:
                info = self.api.System.SoftwareManagement.get_software_image(
                    imageIDs=[image]
                )
                result['software'].append(info[0])

            hotfixes = self.api.System.SoftwareManagement.get_software_hotfix_list()
            for hotfix in hotfixes:
                info = self.api.System.SoftwareManagement.get_software_hotfix(
                    imageIDs=[hotfix]
                )
                result['hotfix'].append(info[0])
        except bigsuds.ServerError:
            pass

        return result

    def get_active_volume(self):
        softwares = self.api.System.SoftwareManagement.get_all_software_status()
        for software in softwares:
            if software['active']:
                return software['installation_id']['install_volume']
        return None

    def upload(self, filename):
        done = False
        first = True

        with open(filename, 'rb') as fh:
            remote_path = "/shared/images/%s" % os.path.basename(filename)

            while not done:
                text = base64.b64encode(fh.read(CHUNK_SIZE))

                if first:
                    if len(text) < CHUNK_SIZE:
                        chain_type = 'FILE_FIRST_AND_LAST'
                    else:
                        chain_type = 'FILE_FIRST'
                    first = False
                else:
                    if len(text) < CHUNK_SIZE:
                        chain_type = 'FILE_LAST'
                        done = True
                    else:
                        chain_type = 'FILE_MIDDLE'

                self.api.System.ConfigSync.upload_file(
                    file_name=remote_path,
                    file_context=dict(
                        file_data=text,
                        chain_type=chain_type
                    )
                )

    def is_hotfix_available(self, hotfix):
        hotfix = os.path.basename(hotfix)
        images = self.api.System.SoftwareManagement.get_software_hotfix_list()
        for image in images:
            if image['filename'] == hotfix:
                return True
        return False

    def is_software_available(self, software):
        software = os.path.basename(software)
        images = self.api.System.SoftwareManagement.get_software_image_list()
        for image in images:
            if image['filename'] == software:
                return True
        return False

    def delete(self, software):
        software = os.path.basename(software)
        self.api.System.SoftwareManagement.delete_software_image(
            image_filenames=[software]
        )

    def is_activated(self):
        return self.software_active(True)

    def is_installed(self):
        volume = self.params['volume']
        result = self.software_active(False)
        if result:
            softwares = self.api.System.SoftwareManagement.get_all_software_status()
            for software in softwares:
                if software['installation_id']['install_volume'] == volume:
                    return True
        return False

    def software_active(self, activity):
        result = False
        images = self.api.System.SoftwareManagement.get_all_software_status()

        hotfix = self.params['hotfix']
        software = self.params['software']

        if hotfix:
            photfix = self.params['photfix']

        if software:
            psoftware = self.params['psoftware']

        for image in images:
            ibuild = image['base_build']
            iver = image['version']
            iprod = image['product']

            if image['active'] == activity:
                if hotfix:
                    pbuild = photfix['build']
                    pver = photfix['version']
                    pprod = photfix['product']

                    if pbuild == ibuild and pver == iver and pprod == iprod:
                        result = True

                if software:
                    pbuild = psoftware['build']
                    pver = psoftware['version']
                    pprod = psoftware['product']

                    if pbuild == ibuild and pver == iver and pprod == iprod:
                        result = True

        return result

    def wait_for_software_install(self):
        while True:
            time.sleep(5)
            status = self.api.System.SoftwareManagement.get_all_software_status()
            progress = [x['status'] for x in status if not x['active']]
            if 'complete' in progress:
                break
            elif 'failed' in progress:
                raise SoftwareInstallError(progress)

    def wait_for_reboot(self):
        volume = self.params['volume']

        while True:
            time.sleep(5)

            try:
                status = self.api.System.SoftwareManagement.get_all_software_status()
                volumes = [x['installation_id']['install_volume'] for x in status if x['active']]
                if volume in volumes:
                    break
            except:
                # Handle all exceptions because if the system is offline (for a
                # reboot) the SOAP client will raise exceptions about connections
                pass

    def wait_for_images(self, count):
        while True:
            # Waits for the system to settle
            images = self.read()
            ntotal = sum(len(v) for v in images.itervalues())
            if ntotal == count:
                break
            time.sleep(1)

    def install_software(self, pvb, reboot=False, create=False):
        volume = self.params['volume']

        self.api.System.SoftwareManagement.install_software_image_v2(
            volume=volume,
            product=pvb['product'],
            version=pvb['version'],
            build=pvb['build'],
            create_volume=create,
            reboot=reboot,
            retry=False
        )

    def activated(self):
        """Ensures a base image and optionally a hotfix are activated

        Activated means that the current active boot location contains
        the base image + hotfix(optional).

        If the image is uploaded to the "Available Images" list but has not yet
        been made active, this method will activate it.

        If the image is not uploaded to the "Available Images" list, but is
        listed as activated, this method will return true

        If the image is not uploaded to the "Available Images" list, and is not
        in the active list, this method will upload the image and activate it.
        """

        changed = False
        force = self.params['force']
        software = self.params['software']
        hotfix = self.params['hotfix']
        psoftware = self.params['psoftware']
        volume = self.params['volume']

        if self.is_activated() and volume == self.get_active_volume():
            return False
        elif self.is_installed() and volume != self.get_active_volume():
            self.api.System.SoftwareManagement.set_cluster_boot_location(volume)
            self.api.System.Services.reboot_system(seconds_to_reboot=1)
            self.wait_for_reboot()
            return True
        elif volume == self.get_active_volume():
            raise ActiveVolumeError

        images = self.read()
        total = sum(len(v) for v in images.itervalues())

        if force:
            if hotfix:
                self.delete(hotfix)
                total -= 1
                changed = True

            if software:
                self.delete(software)
                total -= 1
                changed = True

        if changed:
            self.wait_for_images(total)
            changed = False

        if hotfix:
            if not self.is_hotfix_available(hotfix):
                self.upload(hotfix)
                total += 1
                changed = True

        if not self.is_software_available(software):
            self.upload(software)
            total += 1
            changed = True

        if changed:
            self.wait_for_images(total)

        status = self.api.System.SoftwareManagement.get_all_software_status()
        volumes = [x['installation_id']['install_volume'] for x in status]

        if volume in volumes:
            create_volume = False
        else:
            create_volume = True

        if hotfix:
            photfix = self.params['photfix']

            # We do not want to reboot after installation of the base image
            # because we can install the hotfix image right away and reboot
            # the system after that happens instead
            self.install_software(psoftware, reboot=False, create=create_volume)
            self.wait_for_software_install()
            self.install_software(photfix, reboot=True, create=False)
        else:
            self.install_software(psoftware, reboot=True, create=create_volume)

        self.wait_for_software_install()

        # We need to wait for the system to reboot so that we can check the
        # active volume to ensure it is the volume that was specified to the
        # module
        self.wait_for_reboot()
        return True

    def installed(self):
        """Ensures a base image and optionally a hotfix are installed

        """

        changed = False
        force = self.params['force']
        hotfix = self.params['hotfix']
        psoftware = self.params['psoftware']
        software = self.params['software']
        volume = self.params['volume']

        if self.is_installed():
            return False
        elif volume == self.get_active_volume():
            raise ActiveVolumeError

        images = self.read()
        total = sum(len(v) for v in images.itervalues())

        if force:
            if hotfix:
                self.delete(hotfix)
                total -= 1
                changed = True

            if software:
                self.delete(software)
                total -= 1
                changed = True

            if changed:
                self.wait_for_images(total)
                changed = False

        images = self.read()
        total = sum(len(v) for v in images.itervalues())

        if hotfix:
            if not self.is_hotfix_available(hotfix):
                self.upload(hotfix)
                total += 1
                changed = True

        if not self.is_software_available(software):
            self.upload(software)
            total += 1
            changed = True

        if changed:
            self.wait_for_images(total)

        status = self.api.System.SoftwareManagement.get_all_software_status()
        volumes = [x['installation_id']['install_volume'] for x in status]

        if volume in volumes:
            self.install_software(psoftware, reboot=False, create=False)
            self.wait_for_software_install()
        else:
            self.install_software(psoftware, reboot=False, create=True)
            self.wait_for_software_install()

        if hotfix:
            photfix = self.params['photfix']
            self.install_software(photfix, reboot=False, create=False)

        self.wait_for_software_install()

        return True

    def present(self):
        changed = False

        force = self.params['force']
        hotfix = self.params['hotfix']
        software = self.params['software']

        images = self.read()
        total = sum(len(v) for v in images.itervalues())

        if force:
            if hotfix:
                self.delete(hotfix)
                total -= 1
                changed = True

            if software:
                self.delete(software)
                total -= 1
                changed = True

            if changed:
                self.wait_for_images(total)

        # I check for existence after the 'force' check because an image can
        # be incompletely uploaded and broken, but would be listed as "present"
        # so forcing the deletion beforehand allows you to handle those cases.
        #
        # Note though that in the forced re-upload, the uploading could again
        # fail (for some reason) and this module would still report success if
        # it found the "broken" image.
        #
        # A better approach would be to compare checksums, however the checksum
        # stored by the BIG-IP is not the actual checksum of the ISO, but
        # instead is the checksum of the files _inside_ the ISO.
        if hotfix and software:
            if self.is_software_available(software) and self.is_hotfix_available(hotfix):
                return False
        elif hotfix:
            if self.is_hotfix_available(hotfix):
                return False
        elif software:
            if self.is_software_available(software):
                return False

        if hotfix:
            self.upload(hotfix)
            total += 1

        if software:
            self.upload(software)
            total += 1

        self.wait_for_images(total)

        return True

    def absent(self):
        hotfix = self.params['hotfix']
        software = self.params['software']

        images = self.read()
        total = sum(len(v) for v in images.itervalues())

        if hotfix and software:
            if not self.is_software_available(software) and not self.is_hotfix_available(hotfix):
                return False
        elif hotfix:
            if not self.is_hotfix_available(hotfix):
                return False
        elif software:
            if not self.is_software_available(software):
                return False

        if hotfix:
            self.delete(hotfix)
            total -= 1

        if software:
            self.delete(software)
            total -= 1

        self.wait_for_images(total)

        return True


def main():
    argument_spec = f5_argument_spec()

    meta_args = dict(
        connection=dict(default='soap', choices=TRANSPORTS),
        state=dict(default='activated', choices=STATES),
        force=dict(required=False, type='bool', default='no'),
        hotfix=dict(required=False, aliases=['hotfix_image'], default=None),
        software=dict(required=False, aliases=['base_image']),
        volume=dict(required=False)
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    try:
        obj = BigIpApiFactory.factory(module)
        result = obj.flush()

        module.exit_json(**result)
    except bigsuds.ConnectionError:
        module.fail_json(msg='Could not connect to BIG-IP host')
    except ActiveVolumeError:
        module.fail_json(msg='Cannot install software or hotfixes to active volumes')
    except NoVolumeError:
        module.fail_json(msg='You must specify a volume')
    except NoBaseImageError:
        module.fail_json(msg='You must specify a base image')
    except SoftwareInstallError, e:
        module.fail_json(msg=str(e))
    except ISO9660IOError:
        module.fail_json(msg='Failed checking the version metadata in the ISO')
    except socket.timeout:
        module.fail_json(msg='Timed out connecting to the BIG-IP')

    module.exit_json(changed=changed)

from ansible.module_utils.basic import *
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
