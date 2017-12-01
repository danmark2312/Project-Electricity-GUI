# -*- coding: utf-8 -*-
"""
Created on Wed Oct  4 17:04:20 2017

A setup script that creates an .exe file of the project inside the "build" folder

USAGE:
    From cmd, write:
        python setup.py bdist_msi <- for windows installer

IMPORTANT:
    It does not always work on macs due to errors in the source code of cx_freeze

Emil Ballermann (s174393) & Simon Moe Sørensen (s174420)
"""

from cx_Freeze import setup, Executable
from sys import platform as _platform
import os

#Dependencies are automatically detected, but it might need fine tuning.
additional_mods = ['numpy.core._methods', 'numpy.lib.format',
                   'matplotlib.backends.backend_qt5agg']

include_files = ["functions","resources"]

packages = ["numpy","matplotlib","csv","PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets","pandas"]

build_exe_options = {"packages": packages, "excludes": ["tkinter"],
                     "includes":additional_mods, "include_files":include_files}

if _platform == "darwin":
    base = None
else:
    base = "Win32GUI"

setup(  name = "Analysis of household electricity consumption project",
        version = "1.0",
        author = "Simon Moe Sørensen",
        description = "This program analyses data from household electricity usage",
        options = {"build_exe": build_exe_options},
        executables = [Executable("GUI.py", base=base, icon="resources/Icon.ico")])
