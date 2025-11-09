#!/usr/bin/env bash

# Calls our patched version of pelican-import
this_script=$(readlink -e "$0")
this_script_dir=$(realpath $(dirname "${this_script}"))

export PATH="${PATH}:${this_script_dir}:${this_script_dir}/.."

blog2pelican.py --dotclear --markup markdown "$@"
