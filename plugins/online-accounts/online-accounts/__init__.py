#!/usr/bin/env python3

# __init__.py
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


import gi
gi.require_version('Gtd', '1.0')
gi.require_version('Secret', '1')
gi.require_version('WebKit', '3.0')
from gi.repository import Gtd, Gtk, GObject

from .accounts import AccountsManager, Account, SERVICES
from .providers import CreateProvider

from os import path


SERVICES_LIST = Gtk.ListStore(str, str)
for service in SERVICES:
    SERVICES_LIST.append([service, SERVICES[service][0]])

def get_local_file(filename):
    return path.join(path.dirname(path.abspath(__file__)), filename)


class HeaderButton(Gtk.Button):

    def __init__(self, callback):
        Gtk.Button.__init__(self)
        self.set_halign(Gtk.Align.END)
        self.set_label('↻')
        self.show_all()
        self.get_style_context().add_class('image-button')
        self.connect("clicked", callback)


class AccountRow(Gtk.ListBoxRow):

    __gsignals__ = {
        'delete-account': (GObject.SIGNAL_RUN_FIRST, None, (Account,)),
    }
    _ui_file = get_local_file("account-row.ui")

    def __init__(self, account):
        Gtk.ListBoxRow.__init__(self)
        self.set_selectable(False)
        account.connect('notify::name', self.on_account_changed)
        account.connect('notify::service', self.on_account_changed)
        account.connect('notify::active', self.on_account_changed)
        self.account = account
        self.builder = Gtk.Builder.new_from_file(self._ui_file)
        self.builder.connect_signals(self)
        self._helper_build_ui()

    def _helper_build_ui(self):
        _get = self.builder.get_object
        self.box_row = _get('box_row')
        self.add(self.box_row)
        self.label_name = _get('label_name')
        self.label_service = _get('label_service')
        self.image_service = _get('image_service')
        self._helper_write_data()

    def _helper_write_data(self):
        self.label_name.set_label(
            self.account.name
            if self.account.name
            else '<empty>'
        )
        self.label_service.set_label(
            SERVICES[self.account.service][0]
            if self.account.service
            else '<empty>'
        )
        self.image_service.set_from_icon_name(
            (SERVICES[self.account.service][1]
             if self.account.service
             else 'goa-panel'),
            32,
        )

    def on_account_changed(self, account, param):
        self._helper_write_data()
        self.changed()

    def on_delete(self, obj):
        self.emit('delete-account', self.account)


class PreferencesPanel(Gtk.Stack):

    _ui_file = get_local_file("preferences-panel.ui")
    _selected_account = None

    def __init__(self, accounts_manager):
        Gtk.Stack.__init__(self)
        self.set_transition_type(Gtk.StackTransitionType.SLIDE_UP)
        self.accounts_manager = accounts_manager
        self.builder = Gtk.Builder.new_from_file(self._ui_file)
        self.builder.connect_signals(self)
        self._helper_build_ui()

    def _helper_build_ui(self):
        _get = self.builder.get_object
        self.box_accounts_manager = _get('box_accounts_manager')
        self.box_accounts_manager.show()
        self.box_account_handler = _get('box_account_handler')
        self.box_account_handler.show()
        self.add(self.box_accounts_manager)
        self.add(self.box_account_handler)

        self.image_service = _get('image_service')
        self.entry_name = _get('entry_name')
        self.switch_active = _get('switch_active')
        self.combo_service = _get('combo_service')
        self.combo_service.connect("changed", self.on_service_changed)
        self.combo_service.set_model(SERVICES_LIST)
        self.combo_service.set_id_column(0)
        renderer_text = Gtk.CellRendererText()
        self.combo_service.pack_start(renderer_text, True)
        self.combo_service.add_attribute(renderer_text, "text", 1)

        self.listbox_accounts = _get('listbox_accounts')
        self.listbox_accounts.connect('row-activated', self.on_select_account)
        self.listbox_accounts.bind_model(
            self.accounts_manager,
            self.callback_create_row,
        )

    def callback_create_row(self, account):
        row = AccountRow(account)
        row.connect('delete-account', self.on_delete_account)
        row.show()
        return row

    def _helper_write_data(self, account):
        self.entry_name.set_text(account.name)
        self.combo_service.set_active_id(account.service)
        self.switch_active.set_active(account.active)
        self._helper_change_image(account.service)

    def _helper_change_image(self, service=None):
        self.image_service.set_from_icon_name(
            (SERVICES[service][1]
             if (service and service in SERVICES)
             else 'goa-panel'),
            64,
        )

    def _helper_clear_data(self):
        self.entry_name.set_text('')
        self.combo_service.set_active_id(None)
        self.switch_active.set_active(False)
        self.image_service.set_from_icon_name('goa-panel', 64)

    def _helper_save_data(self):
        account = self._selected_account
        account.name = self.entry_name.get_text()
        account.service = self.combo_service.get_active_id()
        account.active = self.switch_active.get_active()

    def on_service_changed(self, combo):
        tree_iter = combo.get_active_iter()
        service = SERVICES_LIST[tree_iter][0] if tree_iter != None else None
        self._helper_change_image(service)

    def on_select_account(self, obj, row):
        self._selected_account = row.account
        self._helper_write_data(row.account)
        self.set_visible_child(self.box_account_handler)

    def on_add_account(self, obj):
        account = self.accounts_manager.create_account()
        self._selected_account = account
        self._helper_write_data(account)
        self.set_visible_child(self.box_account_handler)

    def on_delete_account(self, obj, account):
        self.accounts_manager.delete_account(account.uid)
        self._selected_account = None

    def on_return(self, obj):
        self._helper_save_data()
        self._selected_account = None
        self._helper_clear_data()
        self.set_visible_child(self.box_accounts_manager)

    def on_authenticate(self, obj):
        # TODO: todo
        pass


class Plugin(GObject.Object, Gtd.Activatable):

    preferences_panel = GObject.Property(type=Gtk.Widget, default=None)

    @property
    def providers(self):
        return self._providers

    def __init__(self):
        GObject.Object.__init__(self)
        self._providers = []
        self.header_button = HeaderButton(self.manually_sync)
        self.accounts_manager = AccountsManager()
        self.accounts_manager.connect(
            'notify::ready',
            self.on_accounts_manager_ready,
            )
        self.preferences_panel = PreferencesPanel(self.accounts_manager)

    def on_accounts_manager_ready(self, accounts_manager, param):
        if accounts_manager.get_ready():
            for i in range(accounts_manager.get_n_items()):
                account = accounts_manager.get_item(i)
                provider = CreateProvider(account)
                self.add_provider(provider)

    def add_provider(self, provider):
        self.providers.append(provider)
        self.emit('provider-added', provider)

    def manually_sync(self, button):
        #TODO: make general sync function
        pass

    def do_activate(self):
        self.accounts_manager.load()

    def do_deactivate(self):
        pass

    def do_get_header_widgets(self):
        return [self.header_button]

    def do_get_preferences_panel(self):
        return self.preferences_panel

    def do_get_panels(self):
        return None

    def do_get_providers(self):
        return self.providers
