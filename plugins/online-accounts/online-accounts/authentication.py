#!/usr/bin/env python3

# authentication.py
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

from gi.repository import Secret, Gtk, Gtd, GObject, WebKit

from urllib.parse import parse_qs, urlencode
from urllib.request import urlopen
from random import choice
from string import ascii_uppercase, digits
from os.path import join, dirname
from configparser import ConfigParser
from sys import exit
import json


BASE_URL = 'https://todoist.com/oauth'
TOKEN_URL = 'https://todoist.com/oauth/access_token'
CALLBACK_URL = 'https://wiki.gnome.org/Apps/Todo'

SCOPE = 'data:read_write,data:delete,project:delete'

CLIENT_ID = '7610743d7c504e9a9053ded63a8ce94b'
CLIENT_SECRET = '2b552cc87a724762bf709b9ab329474a'

ONLINE_ACCOUNTS_SCHEMA = Secret.Schema.new(
    'org.gnome.Todo.online-accounts',
    Secret.SchemaFlags.NONE,
    {
        'name': Secret.SchemaAttributeType.STRING,
        'service': Secret.SchemaAttributeType.STRING,
    },
)


class AuthWin(Gtk.Window):
    """Allows the user to authenticate to Todoist, returning the auth_code"""

    __gsignals__ = {
        'authenticated':(GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        """Create a Webkit WebView to the authentication url"""
        super(AuthWin, self).__init__()
        # Creates the required authentication url
        self.state = ''.join(choice(ascii_uppercase + digits) for _ in range(10))
        oauth_url = '{base}/authorize?client_id={client_id}&scope={scope}&state={state}'.format(
            base = BASE_URL,
            client_id = CLIENT_ID,
            scope = SCOPE,
            state = self.state,
        )
        # Creates the WebView and loads the uri
        self.web = WebKit.WebView()
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.add(self.web)
        self.add(self.scrolled)
        self.set_size_request(900, 640)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_title('Authorize')
        self.set_skip_taskbar_hint(True)
        self.set_resizable(False)
        self.set_default_size(900, 640)
        self.web.load_uri(oauth_url)
        self.show_all()
        self.web.connect(
            'navigation-policy-decision-requested',
            self.navigation_callback,
        )

    def navigation_callback(self, view, frame, request, action, decision):
        """Obtains the auth_code from the callback_url"""
        url = request.get_uri()
        if CALLBACK_URL in url:
            self.hide()
            qs = url.replace(CALLBACK_URL + '?', '')
            res = parse_qs(qs)
            state = res['state'][0]
            if state != self.state:
                raise Exception('Wrong state code, insecure comunication')
            auth_code = res['code'][0]
            self.emit('authenticated', auth_code)


class OAuth2(Gtd.Object):
    """Connect to the oauth2 server and obtains an authentication token"""

    token_type = GObject.Property(type=str)

    @GObject.Property(type=str)
    def access_token(self):
        ## FIXME:for some reason this crashes
        # Secret.password_lookup(
        #     ONLINE_ACCOUNTS_SCHEMA,
        #     {'name': self.account.name, 'service':self.account.service},
        #     None,
        #     self.callback_password_lookup,
        # )
        # password = Secret.password_lookup_sync(
        #     ONLINE_ACCOUNTS_SCHEMA,
        #     {'name': self.account.name, 'service':self.account.service},
        #     None,
        # )
        # if not password is None:
        #     self._access_token = password
        # else:
        #     self._access_token = ''
        # self.set_ready(True)
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        ## FIXME:for some reason this crashes
        # Secret.password_store(
        #     ONLINE_ACCOUNTS_SCHEMA,
        #     {'name': self.account.name, 'service':self.account.service},
        #     Secret.COLLECTION_DEFAULT,
        #     'Access Token for account {0[name] in service {0[service]}'.format(
        #         self.account.name,
        #     ),
        #     value,
        #     None,
        #     self.callback_password_stored,
        # )
        # Secret.password_store_sync(
        #     ONLINE_ACCOUNTS_SCHEMA,
        #     {'name': self.account.name, 'service':self.account.service},
        #     Secret.COLLECTION_DEFAULT,
        #     'Access Token for account {0[name] in service {0[service]}'.format(
        #         self.account.name,
        #     ),
        #     value,
        #     None,
        # )
        self._access_token = value

    def __init__(self, account):
        Gtd.Object.__init__(self)
        self.account = account
        self._access_token = None
        self.set_ready(False)

    def load(self):
        """Securely search for the password in libSecret"""
        self._access_token = 'eca89d5f1ba5bb6d88cd64454d598f96cfb9016f'
        self.set_ready(True)

    # def callback_password_lookup(self, source, result):
    #     password = Secret.password_lookup_finish(result)
    #     if not password is None:
    #         self._access_token = password
    #     else:
    #         self._access_token = ''
    #     self.set_ready(True)

    # def callback_password_stored(self, source, result):
    #     Secret.password_store_finish(result)

    def request_auth_code(self):
        auth_win = AuthWin()
        auth_win.connect('authenticated', self.on_request_token)
        auth_win.show_all()

    def on_request_token(self, manager, auth_code):
        data = {
            'client_id':CLIENT_ID,
            'client_secret':CLIENT_SECRET,
            'code':auth_code,
        }
        qs = urlencode(data)
        response = urlopen(TOKEN_URL, qs.encode())
        auth_info = json.loads(response.read().decode())
        self.access_token = auth_info['access_token']
        self.token_type = auth_info['token_type']
