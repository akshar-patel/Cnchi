#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  desktop_environments.py
#
#  Copyright © 2013,2014 Antergos
#
#  This file is part of Cnchi.
#
#  Cnchi is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  Cnchi is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Cnchi; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

""" DE information """

# Enabled desktops

DESKTOPS_DEV = ["cinnamon", "enlightenment", "gnome", "kde", "mate", "base", "openbox", "lxqt", "xfce"]
DESKTOPS = ["cinnamon", "gnome", "kde", "mate", "base", "openbox", "xfce"]

DESKTOP_ICONS_PATH = "/usr/share/cnchi/data/icons"

'''
MENU - Size appropriate for menus (16px).
SMALL_TOOLBAR - Size appropriate for small toolbars (16px).
LARGE_TOOLBAR - Size appropriate for large toolbars (24px)
BUTTON - Size appropriate for buttons (16px )
DND - Size appropriate for drag and drop (32px )
DIALOG - Size appropriate for dialogs (48px )
'''

# Descriptive names
NAMES = {
    'base' : "Base",
    'gnome' : "Gnome",
    'cinnamon' : "Cinnamon",
    'xfce' : "Xfce",
    'lxde' : "LXDE",
    'openbox' : "Openbox",
    'enlightenment' : "Enlightenment",
    'kde' : "KDE",
    'lxqt' : "LXQt",
    'mate' : "MATE"}

LIBS = {
    'gtk' : ["gnome", "cinnamon", "xfce", "openbox", "mate", "enlightenment"],
    'qt' : ["lxqt", "kde"]}

ALL_FEATURES = ["aur", "bluetooth", "cups", "fonts", "office", "visual", "firewall"]

# Each desktop has its own available features
FEATURES = {
    'cinnamon' : ["aur", "bluetooth", "cups", "fonts", "office", "firewall"],
    'gnome' : ["aur", "bluetooth", "cups", "fonts", "office", "firewall"],
    'kde' : ["aur", "bluetooth", "cups", "fonts", "office", "firewall"],
    'mate' : ["aur", "cups", "fonts", "office", "firewall"],
    'enlightenment' : ["aur", "bluetooth", "cups", "fonts", "office", "firewall"],
    'base' : ["aur", "bluetooth", "cups", "fonts", "firewall"],
    'openbox' : ["aur", "bluetooth", "cups", "fonts", "office", "visual", "firewall"],
    'lxqt' : ["aur", "bluetooth", "cups", "fonts", "office", "firewall"],
    'xfce' : ["aur", "bluetooth", "cups", "fonts", "office", "firewall"]}

# See http://docs.python.org/2/library/gettext.html "22.1.3.4. Deferred translations"
def _(message): return message

DESCRIPTIONS = {
    'gnome' : _("Gnome 3 is an easy and elegant way to use your "
                "computer. It features the Activities Overview which "
                "is an easy way to access all your basic tasks. GNOME 3 is "
                "the default desktop in Antergos."),

    'cinnamon' : _("Cinnamon is a fork of GNOME 3 developed "
                   "by (and for) Linux Mint. It provides users a more traditional desktop "
                   "interface along with the newest compositing techniques of GNOME 3. "
                   "Cinnamon is for users of all experience levels. "),

    'xfce' : _("Xfce is a lightweight desktop environment. It aims to "
               "be fast and low on system resources, while remaining visually "
               "appealing and user friendly. It is a great option for use "
               "on older computers or those with low hardware specifications. "),

    'lxde': _("LXDE is an extremely fast-performing and energy-saving desktop "
              "environment. It uses less CPU and RAM than other environments. "
              "LXDE is especially designed for cloud computers with low hardware "
              "specifications such as netbooks, mobile devices, and older computers."),

    'openbox' : _("Openbox is a highly configurable, next generation window "
                  "manager with extensive standards support. It's default theme "
                  "is well known for its minimalistic appearance and flexibility. "
                  "Your desktop becomes cleaner, faster."),

    'enlightenment' : _("Enlightenment is not just a window manager for Linux/X11 "
                        "and others, but also a whole suite of libraries to help "
                        "you create beautiful user interfaces with much less work"),

    'kde' : _("If you are looking for a familiar working environment, KDE's "
              "Plasma Desktop offers all the tools required for a modern desktop "
              "computing experience so you can be productive right from the start."),

    'lxqt' : _("LXQt is an advanced, easy-to-use, and fast desktop environment "
               "based on Qt technologies. It has been tailored for users who "
               "value simplicity, speed, and an intuitive interface."),

    'base' : _("This option will install Antergos as command-line only system, "
              "without any type of graphical interface. After the installation you can "
              "customize Antergos by installing packages with the command-line package manager."),

    'mate': _("MATE is a fork of GNOME 2. It provides an intuitive and attractive "
              "desktop environment using traditional metaphors for Linux and other Unix-like "
              "operating systems.")}

# Delete previous _() dummy declaration
del _

