#!/bin/bash

# This script solely exists for developers who do not have Pandoc installed.

cat <<EOF
.TH "Sad_day_for_you" "999" "Unreleased developer copy" "" "Open MPI"
.PP
This is a developer build of Open MPI (e.g., a git clone), and you apparently
do not have Pandoc installed.
.PP
As such, Open MPI was not able to generate man pages for you, and you got
these dummy man pages instead.
.PP
If you want real Open MPI man pages, you have two choices:
.IP "1." 3
Configure/build/install a distribution Open MPI tarball.
.IP "2." 3
Install Pandoc (see pandoc.org) and re-configure/build/install your
Open MPI developer's build.
.PP
Make today an Open MPI day!
EOF
