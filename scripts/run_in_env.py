#!/usr/bin/env python3
# run_in_env.py ---
#
# Filename: run_in_env.py
# Description:
# Author: Elric Milon
# Maintainer:
# Created: Fri Aug 23 17:37:32 2013 (+0200)

# Commentary:
# %*% Shell script to run commands inside the experiment environment. Enabling virtualenv if necessary, loading all the needed variables, etc.
# %*% Used by gumby, you shouldn't need to use it directly.
# %*% This script will make the following environment variables available to its subprocesses:
# %*%  - PROJECT_DIR: Absolute path to the root of the workspace where gumby and the rest of stuff is.
# %*%  - EXPERIMENT_DIR: Absolute path to the directory which contains the experiment config.
# %*%  - OUTPUT_DIR: Absolute path to the directory where all the data generated by the experiment execution should be written to.
#

# Change Log:
#
#
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street, Fifth
# Floor, Boston, MA 02110-1301, USA.
#
#

# Code:

from glob import glob
from os import path, chdir, environ, makedirs, execvpe, getcwd
from subprocess import call
from sys import stdout, stderr
import shlex
import sys


def extend_var(env, var, value, prepend=True):
    if var in env:
        if prepend:
            env[var] = value + ':' + env[var]
        else:
            env[var] = env[var] + value if env[var].endswith(':') else env[var] + ':' + value
    else:
        env[var] = value


def expand_var(var):
    return path.expanduser(path.expandvars(var))

# move to the project root dir, which is the parent of the one where this file is located (PROJECT_DIR/scripts/THIS_FILE)
project_dir = path.abspath(path.join(path.dirname(path.abspath(__file__)), '..', '..'))
print('Project root is:', project_dir)

scripts_dir = path.join(project_dir, "gumby/scripts")
r_scripts_dir = path.join(scripts_dir, "r")

sys.path.append(path.join(project_dir, "gumby"))
from gumby.settings import configToEnv, loadConfig

chdir(project_dir)

if len(sys.argv) >= 3:
    conf_path = path.abspath(sys.argv[1])
    if not path.exists(conf_path):
        print("Error: The specified configuration file (%s) doesn't exist." % conf_path)
        exit(2)
    config = loadConfig(conf_path)
    experiment_dir = path.abspath(path.dirname(path.abspath(conf_path)))
else:
    print("Usage:\n%s EXPERIMENT_CONFIG COMMAND" % sys.argv[0])
    exit(1)

environ.update(configToEnv(config))

environ['PROJECT_DIR'] = project_dir

environ['EXPERIMENT_DIR'] = experiment_dir

# Add project dir to PYTHONPATH
extend_var(environ, "PYTHONPATH", project_dir)

# Add gumby dir to PYTHONPATH
extend_var(environ, "PYTHONPATH", path.join(project_dir, "gumby"))

# Add tribler dir to PYTHONPATH
extend_var(environ, "PYTHONPATH", path.join(project_dir, "tribler", "src", "tribler-common"))
extend_var(environ, "PYTHONPATH", path.join(project_dir, "tribler", "src", "tribler-core"))

# Add IPv8 dir to PYTHONPATH
extend_var(environ, "PYTHONPATH", path.join(project_dir, "tribler", "src", "pyipv8"))

# Add gumby scripts dir to PATH
extend_var(environ, "PATH", scripts_dir)

# Add the experiment dir to PATH so we can call custom scripts from there
extend_var(environ, "PATH", experiment_dir)

# Add the gumby dir to PATH so we can launch the launch_scenario.py script
extend_var(environ, "PATH", path.join(project_dir, "gumby", "gumby"))

# Add ~/R to the R search path
extend_var(environ, "R_LIBS_USER", expand_var("$HOME/R"))
# Export the R scripts path
extend_var(environ, "R_SCRIPTS_PATH", r_scripts_dir)

# @CONF_OPTION VIRTUALENV_DIR: Virtual env to activate for the experiment (default is ~/venv)
# Enter virtualenv in case there's one
running_local_and_virtualenv_disabled = not (environ.get("USE_LOCAL_VENV", "False").lower() == environ.get("LOCAL_RUN", "False").lower() == "true")
if not running_local_and_virtualenv_disabled and "VIRTUALENV_DIR" in environ and path.exists(expand_var(environ["VIRTUALENV_DIR"])):
    venv_dir = path.abspath(expand_var(environ["VIRTUALENV_DIR"]))
    print("Activating virtualenv at", venv_dir)
    extend_var(environ, "LD_LIBRARY_PATH", path.join(venv_dir, "inst/lib"))
    extend_var(environ, "LD_LIBRARY_PATH", path.join(venv_dir, "lib"))  # TODO: Check if this one is needed
    extend_var(environ, "PATH", path.join(venv_dir, "inst/bin"))

    # This is a replacement for running venv/bin/activate
    environ["VIRTUAL_ENV"] = venv_dir
    extend_var(environ, "PATH", path.join(venv_dir, "bin"))
else:
    print("NOT activating virtualenv.")

# @CONF_OPTION OUTPUT_DIR: Dir where to write all the output generated from the experiment (default is workspace_dir/output)
# Create the experiment output dir if necessary
if 'OUTPUT_DIR' in environ:
    # Convert the output dir to an absolute path to make it easier for
    # the rest of scripts to write into it.
    output_dir = path.abspath(environ['OUTPUT_DIR'])
    environ['OUTPUT_DIR'] = output_dir
    if not path.exists(output_dir):
        makedirs(output_dir)

# Run the actual command
cmd = expand_var(" ".join(sys.argv[2:]))
print("Running", cmd)

argv = (shlex.split(cmd))

# Flush before calling exec
stdout.flush()
stderr.flush()

execvpe(argv[0], argv, environ)
#
# run_in_env.py ends here
