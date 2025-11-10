#! /bin/bash

this_script=$(readlink -e "$0")
this_script_dir=$(realpath $(dirname "${this_script}"))

toplevel_dir=$(realpath "${this_script_dir}/..")

project="blog2pelican"
mypy "${toplevel_dir}/${project}"
ruff check "${toplevel_dir}/${project}"
isort "${toplevel_dir}/${project}"
black "${toplevel_dir}/${project}"
