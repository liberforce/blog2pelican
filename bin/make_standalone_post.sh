#! /bin/env bash

cat \
tests/data/dotclear/headers/dotclear.txt \
tests/data/dotclear/partial/categories/categories.txt \
tests/data/dotclear/headers/posts.txt \
tests/data/dotclear/raw/posts/you-like-linux-tell-it-to-the-world.txt \
> tests/data/dotclear/standalone/posts/you-like-linux-tell-it-to-the-world.txt
