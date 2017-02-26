#!/usr/bin/env python3

# accounts.py
#
# Copyright (C) 2016 Wolfang Torres <wolfang.torres@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import GObject, Gtd, Gio

from .authentication import OAuth2

from configparser import ConfigParser, ParsingError, MissingSectionHeaderError
from contextlib import contextmanager
from os.path import join, dirname, expanduser
from os import makedirs
from uuid import uuid4

CONF_DIR = expanduser(
    join('~','.local','share','gnome-todo','plugins','online-accounts')
)
makedirs(CONF_DIR, exist_ok=True)
CONF_FILE = join(CONF_DIR, 'accounts.conf')

TODOIST = 'TODOIST'
SERVICES = {
    TODOIST:('Todoist', 'goa-accounts-todoist'),
}


@contextmanager
def conf_handler(filename):
    config = ConfigParser()
    try:
        with open(filename) as conf_file:
            config.read_file(conf_file)
        yield config
    except (FileNotFoundError, ParsingError, MissingSectionHeaderError):
        with open(filename, 'w') as conf_file:
            ConfigParser().write(conf_file)
        yield config
    finally:
        with open(filename, 'w') as conf_file:
            config.write(conf_file)


class AccountsManager(Gio.ListStore):
    """Manages the accounts stored in the configuration file

    Controls the creation, modification and deletion of all acocunts"""

    ready = GObject.Property(type=bool, default=True)

    def get_ready(self):
        return self.ready

    def set_ready(self, value):
        self.ready = value

    def __init__(self):
        Gio.ListStore.__init__(self)
        self.set_ready(False)

    def load(self):
        with conf_handler(CONF_FILE) as conf:
            for uid in conf.sections():
                self._helper_create_account(uid, **conf[uid])

    def _helper_create_account(self, uid, **kwarg):
        account = Account(uid, **kwarg)
        account.connect('notify::name', self.on_notify_property)
        account.connect('notify::service', self.on_notify_property)
        account.connect('notify::active', self.on_notify_property)
        account.connect('notify::ready', self.on_account_ready)
        self.append(account)
        account.load()
        return account

    def search_account(self, uid):
        for i in range(self.get_n_items()):
            if self.get_item(i).uid == uid:
                return i

    def on_notify_property(self, account, param):
        if param.name == 'name':
            val = account.name
        elif param.name == 'service':
            val = account.service if not account.service is None else ''
        elif param.name == 'active':
            val = str(int(account.active))
        with conf_handler(CONF_FILE) as conf:
            conf[str(account.uid)][param.name] = val

    def on_account_ready(self, account, param):
        """Check if all accounts are ready, managuer is ready if they are"""
        for i in range(self.get_n_items()):
            if not self.get_item(i).get_ready():
                self.set_ready(False)
                break
        else:
            self.set_ready(True)

    def create_account(self):
        uid = uuid4()
        with conf_handler(CONF_FILE) as config:
            config[uid] = {}
        return self._helper_create_account(uid)

    def delete_account(self, uid):
        with conf_handler(CONF_FILE) as conf:
            del conf[str(uid)]
        position = self.search_account(uid)
        self.remove(position)
        return self.get_item(position)


class Account(Gtd.Object):
    """Object that represent an account form a to-do service

    Depends on the creator AccountsManager to store changes made to it"""

    name = GObject.Property(type=str)
    service = GObject.Property(type=str)
    active = GObject.Property(type=bool, default=False)

    @GObject.Property(type=OAuth2)
    def auth(self):
        return self._auth

    def __init__(self, uid, **kwarg):
        """Search for the access token in gnome-keyring"""
        Gtd.Object.__init__(self)
        self.uid = uid
        self.name = kwarg.get('name', '')
        self.active = bool(int(kwarg.get('active', False)))
        self.service = (
            kwarg['service']
            if ('service' in kwarg and kwarg['service'] != '')
            else None
        )
        self.set_ready(False)
        self._auth = OAuth2(self)
        self._auth.connect('notify::ready', self.on_auth_ready)

    def load(self):
        self._auth.load()

    def on_auth_ready(self, auth_obj, param):
        if auth_obj.get_ready():
            self.set_ready(True)

    def __eq__(self, other):
        return self.uid == other.uid

    def __str__(self):
        return '<Account {} on {}>'.format(self.name, self.service)
