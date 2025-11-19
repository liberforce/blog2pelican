#! /bin/bash

this_script=$(readlink -e "$0")
this_script_dir=$(realpath $(dirname "${this_script}"))

toplevel_dir=$(realpath "${this_script_dir}/..")

project="blog2pelican"
mypy --no-error-summary "${toplevel_dir}/${project}"
ruff check --quiet --output-format=concise "${toplevel_dir}/${project}"
isort --quiet "${toplevel_dir}/${project}"
black --quiet "${toplevel_dir}/${project}"
