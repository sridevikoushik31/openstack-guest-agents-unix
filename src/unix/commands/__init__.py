# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
#  Copyright (c) 2011 Openstack, LLC.
#  All Rights Reserved.
#
#     Licensed under the Apache License, Version 2.0 (the "License"); you may
#     not use this file except in compliance with the License. You may obtain
#     a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#     WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#     License for the specific language governing permissions and limitations
#     under the License.
#

"""
Main command module.  All command classes should subclass 'command'
"""

import logging
import sys

try:
    import anyjson
except ImportError:
    import json

    class anyjson(object):
        """Fake anyjson module as a class"""

        @staticmethod
        def serialize(buf):
            return json.write(buf)

        @staticmethod
        def deserialize(buf):
            return json.read(buf)


class CommandNotFoundError(Exception):

    def __init__(self, cmd):
        self.cmd = cmd

    def __str__(self):
        return "No such agent command '%s'" % self.cmd


class CommandMetaClass(type):

    def __init__(cls, cls_name, bases, attrs):
        if not hasattr(cls, '_cmd_classes'):
            cls._cmd_classes = []
        else:
            cls._cmd_classes.append(cls)


class CommandBase(object):
    """
    The class that all command classes should inherit from
    """

    # Set the metaclass
    __metaclass__ = CommandMetaClass

    _cmd_instances = []
    _cmds = {}
    _init_args = {}

    @classmethod
    def _get_commands(self, inst):
        cmds = {}
        for objname in dir(inst):
            obj = getattr(inst, objname)
            if getattr(obj, '_is_cmd', False):
                try:
                    cmds[obj._cmd_name] = obj
                except AttributeError:
                    # skip it if there's no _cmd_name
                    pass
        return cmds

    @classmethod
    def init(self, **kwargs):
        self._init_args.update(**kwargs)
        for cls in self._cmd_classes:
            inst = cls(**kwargs)
            self._cmd_instances.append(inst)
            self._cmds.update(self._get_commands(inst))
        return CommandBase

    @classmethod
    def command_names(self):
        return [x for x in self._cmds]

    @classmethod
    def run_command(self, cmd_name, arg):
        try:
            result = self._cmds[cmd_name](arg)
        except KeyError:
            raise CommandNotFoundError(cmd_name)

        return result


def command_add(cmd_name):
    """
    Decorator for command classes to use to add commands
    """

    def wrap(f):
        f._is_cmd = True
        f._cmd_name = cmd_name
        return f
    return wrap


class CommandModuleWrapper(object):

    def __init__(self, wrapped_module):
        self.wrapped_module = wrapped_module

    def __dir__(self):
        return dir(self.wrapped_module)

    def __getattr__(self, key):
        try:
            return getattr(self.wrapped_module, key)
        except AttributeError:
            return getattr(CommandBase, key)

if __name__ != "__main__":
    sys.modules[__name__] = CommandModuleWrapper(sys.modules[__name__])
