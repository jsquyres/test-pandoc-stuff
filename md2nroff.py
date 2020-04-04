#!/usr/bin/env python3

import os
import re
import tempfile
import argparse
import subprocess

from pprint import pprint

#--------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True,
                    help="Source Markdown file")
parser.add_argument('--dest', required=True,
                    help="Destination nroff file")
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
    print(f"Error: {args.source} does not exist")
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
shortfile = re.sub(f'\.{man_section}.md$', '', shortfile)

#--------------------------------------------------------------------------

# Pandoc does not handle markdown links in output nroff properly, so just remove
# all links.  Some versions of Pandoc ignore the links, but others handle it
# badly.  So just remove all links.
source_content = re.sub(r'\[(.+)\]\((.+)\)', r'\1', source_content)

# Add the pandoc header
source_content = f"""% {shortfile}({man_section}) Libfoobar | OMPI_VERSION
% The Foo Organization
% OMPI_DATE

{source_content}"""

pprint(source_content)

#--------------------------------------------------------------------------

print(f"*** Processing: {args.source} --> {args.dest}")

cmd = ['pandoc', '-s', '--from=markdown', '--to=man']
out = subprocess.run(cmd, input=source_content.encode('utf-8'),
                     capture_output=True, check=True)
pandoc_rendered = out.stdout.decode('utf-8')

if pandoc_rendered != dest_content:
    print(f"Content has changed; writing new file {args.dest}")
    with open(args.dest, 'w') as f:
        f.write(pandoc_rendered)
else:
    print(f"Content has not changed; not writing new file {args.dest}")

exit(0)
