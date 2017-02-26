#!/usr/bin/env python3

# providers.py
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

from gi.repository import Gtd, Gio, Gdk, GLib, GObject

from todoist import TodoistAPI
from .accounts import Account, TODOIST

from re import match
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager
import locale


TODOIST_TIME_FORMAT = "%a %d %b %Y %X %z"
TODOIST_COLORS = [
    "#95ef63",
    "#ff8581",
    "#ffc471",
    "#f9ec75",
    "#a8c8e4",
    "#d2b8a3",
    "#e2a8e4",
    "#cccccc",
    "#fb886e",
    "#ffcc00",
    "#74e8d3",
    "#3bd5fb",
    "#dc4fad",
    "#ac193d",
    "#d24726",
    "#82ba00",
    "#03b3b2",
    "#008299",
    "#5db2ff",
    "#0072c6",
    "#000000",
    "#777777",
]


@contextmanager
def set_locale(name):
    saved = locale.setlocale(locale.LC_ALL)
    try:
        yield locale.setlocale(locale.LC_ALL, name)
    finally:
        locale.setlocale(locale.LC_ALL, saved)

def convert_to_todoist_datetime(datetime_object):
    with set_locale('C'):
        if datetime_object is None:
            return None
        date = datetime(
            year=datetime_object.get_year(),
            month=datetime_object.get_month(),
            day=datetime_object.get_day_of_month(),
            hour=datetime_object.get_hour(),
            minute=datetime_object.get_minute(),
            second=datetime_object.get_second(),
            microsecond=datetime_object.get_microsecond(),
            tzinfo=timezone(
                timedelta(microseconds=datetime_object.get_utc_offset())
            ),
        )
        return date.strftime(TODOIST_TIME_FORMAT)

def convert_from_todoist_datetime(datetime_string):
    with set_locale('C'):
        if datetime_string is None:
            return None
        date = datetime.strptime(datetime_string, TODOIST_TIME_FORMAT)
        return GLib.DateTime(
            tz=GLib.TimeZone(str(date.tzinfo.utc)[3:]),
            year=date.year,
            month=date.month,
            day=date.day,
            hour=date.hour,
            minute=date.minute,
            seconds=float(date.second),
        )

def convert_to_todoist_color(color):
    color.to_color()
    rep = color.to_string()
    rgb = match("rgb\((\d+),(\d+),(\d+)\)", rep).group(1,2,3)
    r = hex(int(rgb[0]))[2:]
    g = hex(int(rgb[1]))[2:]
    b = hex(int(rgb[2]))[2:]
    speck = "\#{}{}{}".format(r,g,b)
    try:
        color_code = TODOIST_COLORS.index(speck)
    except ValueError:
        color_code = 0
    return color_code

def convert_from_todoist_color(color_code):
    spec = TODOIST_COLORS[color_code]
    color = Gdk.RGBA()
    color.parse(spec)
    return color


def CreateProvider(account):
    if account.service == TODOIST:
        return TodoistProvider(account)


class TodoistTask(Gtd.Task):
    """The Todoist Task"""

    id = GObject.Property(type=int)

    def __init__(self, task, task_list, api):
        Gtd.Task.__init__(self)
        self.api = api
        self.import_from_todoist(task, task_list)

    def import_from_todoist(self, task, task_list):
        self.set_property('complete', task['checked'])
        # self.set_property(
        #     'creation-date',
        #     convert_from_todoist_datetime(task['date_added']),
        # )
        # self.set_property('depth', task['indent'])
        self.set_property('description', task['content'])
        self.set_property('list', task_list)
        # self.set_property('parent', None)
        self.set_property('priority', task['priority'])
        self.set_property('title', task['content'])
        self.set_property('id', task['id'])


class TodoistTaskList(Gtd.TaskList):
    """The Todoist Task List"""

    id = GObject.Property(type=int)

    def __init__(self, project, provider, api):
        Gtd.TaskList.__init__(self)
        self.api = api
        self.import_from_todoist(project, provider)

    def import_from_todoist(self, project, provider):
        self.set_property('color', convert_from_todoist_color(project['color']))
        self.set_property('is-removable', False)
        self.set_property('name', project['name'])
        self.set_property('provider', provider)
        self.set_property('id', project['id'])
        self.tasks = []
        for task in self.api.items.all():
            if task['project_id'] == project['id']:
                task = TodoistTask(task, self, self.api)
                self.save_task(task)

    # def save_task(self, task):
    #     if task in self.task:
    #         item = self.api.items.get_by_id(task.get_id())
    #         item.update(
    #             content=task.get_title(),
    #             project_id=task.get_list().get_id(),
    #             priority=task.get_priority(),
    #             indent=task.get_date(),
    #         )
    #         self.api.commit()
    #         self.emit('task-updated', self, task, None)
    #     else:
    #         item = self.api.items.add(
    #             content=task.get_title(),
    #             project_id=task.get_list().get_id(),
    #             priority=task.get_priority(),
    #             indent=task.get_date(),
    #         )
    #         self.api.commit()
    #         task = TodoistTask(item, self)
    #         self.tasks.append(task)
    #         self.emit('task-added', self, task, None)

    # def remove_task(self, task):
    #     item = self.api.items.get_by_id(task.get_id())
    #     item.delete()
    #     self.api.commit()
    #     self.tasks.remove(task)
    #     self.emit('task-removed', self, task, None)

    # def contains(self, task):
    #     return task in self.tasks


class TodoistProvider(Gtd.Object, Gtd.Provider):
    """Interface between Gnome Todo and Todoist"""

    _description = 'On Todoist'
    _enabled = True
    _icon = Gio.ThemedIcon(name='todoist')
    _id = None
    _name = 'Todoist'
    _account = None
    _default_task_list = None

    @GObject.Property(type=str, default=None)
    def description(self):
        return self._description

    @GObject.Property(type=bool, default=False)
    def enabled(self):
        return self._enabled

    @GObject.Property(type=Gio.ThemedIcon)
    def icon(self):
        return self._icon

    @GObject.Property(type=str, default=None)
    def id(self):
        return self._id

    @GObject.Property(type=str, default=None)
    def name(self):
        return self._name

    @GObject.Property(type=Account)
    def account(self):
        return self._account

    @GObject.Property(type=TodoistTaskList)
    def default_task_list(self):
        return self._default_task_list

    def __init__(self, account):
        Gtd.Object.__init__(self)
        self.set_ready(False)
        self._account = account
        self.task_lists = []
        self.api = TodoistAPI(self.account.auth.access_token)
        self._helper_import_data()

    def _helper_import_data(self):
        projects = self.api.projects.all()
        self.task_lists = [TodoistTaskList(p, self, self.api) for p in projects]
        for task_list in self.task_lists:
            if task_list.get_property('name') == 'Inbox':
                self._default_task_list = task_list
        self.set_ready(True)

    def do_get_description(self):
        return self.get_property('description')

    def do_get_enabled(self):
        return self.get_property('enabled')

    def do_get_icon(self):
        return self.get_property('icon')

    def do_get_id(self):
        return self.get_property('id')

    def do_get_name(self):
        return self.get_property('name')

    def do_create_task(self, task):
        self.default_task_list.save_task(task)

    def do_update_task(self, task):
        self.default_task_list.save_task(task)

    def do_remove_task(self, task):
        self.default_task_list.remove_task(task)

    def do_create_task_list(self, task_list):
        print(task_list)
        info = {
            'name':task_list.get_name(),
            'color':convert_to_todoist_color(task_list.get_color()),
        }
        project = self.api.projects.add(**info)
        self.api.commit()
        task_list = TodoistTaskList(project, self)
        self.task_lists.append(task_list)
        self.emit('list-added', self, task_list, None)

    def do_update_task_list(self, task_list):
        print(task_list)
        project = self.api.projects.get_by_id(task_list.get_id())
        info = {
            'name':task_list.get_name(),
            'color':convert_to_todoist_color(task_list.get_color()),
        }
        project.update(**info)
        self.api.commit()
        self.emit('list-changed', self, task_list, None)

    def do_remove_task_list(self, task_list):
        print(task_list)
        project = self.api.projects.get_by_id(task_list.get_id())
        project.delete()
        self.api.commit()
        self.task_lists.remove(task_list)
        self.emit('list-removed', self, task_list, None)

    def do_get_task_lists(self):
        return self.task_lists

    def do_get_default_task_list(self):
        return self.default_task_list

    def do_get_edit_panel(self):
        #TODO: ask what should be returned
        pass
