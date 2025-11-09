#!/usr/bin/env bash

this_script=$(readlink -e "$0")
this_script_dir=$(realpath $(dirname "${this_script}"))

export PATH="${PATH}:${this_script_dir}"

pelican-import --dotclear --markup markdown "$@"
