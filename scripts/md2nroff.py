#!/usr/bin/env python

# This script is friendly to both Python 2 and Python 3.

import os
import re
import tempfile
import argparse
import datetime
import subprocess

from pprint import pprint

#--------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True,
                    help="Source Markdown file")
parser.add_argument('--dest', required=True,
                    help="Destination nroff file")
parser.add_argument('--pandoc',
                    default='pandoc',
                    help='Location of pandoc executable')
parser.add_argument('--verbose', action='store_true',
                    help="Show additional information about processing")
args = parser.parse_args()

#--------------------------------------------------------------------------

# If the destination exists, read it in
if os.path.exists(args.dest):
    with open(args.dest) as f:
        dest_lines = f.readlines()
else:
    dest_lines = list()
dest_content = ''.join(dest_lines)

#--------------------------------------------------------------------------

# Read in the source
if not os.path.exists(args.source):
    print("Error: {file} does not exist".format(file=args.source))
    exit(1)

with open(args.source) as f:
    source_lines = f.readlines()
source_content = ''.join(source_lines)

#--------------------------------------------------------------------------

# Figure out the section of man page
result = re.search("(\d+).md$", args.source)
if not result:
    print("Error: Cannot figure out man page section from source filename")
    exit(1)
man_section = int(result.group(1))

shortfile = os.path.basename(args.source)
shortfile = re.sub('\.{man_section}.md$'.format(man_section=man_section),
                    '', shortfile)

#--------------------------------------------------------------------------

today = datetime.date.today().isoformat()

# Pandoc does not handle markdown links in output nroff properly, so just remove
# all links.  Some versions of Pandoc ignore the links, but others handle it
# badly.  So just remove all links.
source_content = re.sub(r'\[(.+)\]\((.+)\)', r'\1', source_content)

# Add the pandoc header
source_content = """---
section: {man_section}
title: {shortfile}
header: Open MPI
footer: {today}
---

{source_content}""".format(man_section=man_section, shortfile=shortfile,
                           today=today, source_content=source_content)

#--------------------------------------------------------------------------

if args.verbose:
    print("*** Processing: {source} --> {dest}".format(source=args.source,
                                                       dest=args.dest))

# This is friendly to both Python 2 and Python 3
cmd = [args.pandoc, '-s', '--from=markdown', '--to=man']
out = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
pandoc_rendered, pandoc_stderr = out.communicate(source_content.encode('utf-8'))
pandoc_rendered = pandoc_rendered.decode('utf-8')

if pandoc_rendered != dest_content:
    if args.verbose:
        print("Content has changed; writing new file {dest}"
               .format(dest=args.dest))
    with open(args.dest, 'w') as f:
        f.write(pandoc_rendered)
else:
    if args.verbose:
        print("Content has not changed; not writing new file {dest}"
              .format(dest=args.dest))

exit(0)
