#!/usr/bin/env python3
# coding: utf-8

"""
Build the Flatscan Kodi repository.

Runs with ordinary desktop Python (no Kodi, no extra packages). For each
add-on it writes zips/<id>/<id>-<version>.zip and the add-on's icon, then
regenerates addons.xml, addons.xml.md5 and index.html. Commit and push the
result; GitHub Pages serves it at https://flatscan.github.io/kodi-repo/.

Add-ons from git repositories are packaged with `git archive` from a branch,
so only committed files ship and `export-ignore` entries in the add-on's
.gitattributes are left out. Kodi only offers an update when the version in
addon.xml goes up; rebuilding an existing version just overwrites its zip.

Usage: python build.py
"""

import hashlib
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ZIPS = os.path.join(ROOT, 'zips')

# Add-ons kept in their own git repository, packaged from the given branch
GIT_ADDONS = [
    {'path': os.path.join(ROOT, '..', 'flatscanwidgets'), 'ref': 'master'},
]

# Add-ons whose source lives in this repository
LOCAL_ADDONS = ['repository.flatscan']

# The add-on people install by hand; its zip is also linked from index.html
REPOSITORY_ADDON = 'repository.flatscan'


def git(path, *args):
    """Run git in a repository and return its stdout as bytes."""
    return subprocess.run(['git', '-C', path, *args], check=True, capture_output=True).stdout


def addon_info(addon_xml):
    """Return (id, version, icon path) from an addon.xml string."""
    root = ET.fromstring(addon_xml)
    icon = root.find(".//extension[@point='xbmc.addon.metadata']/assets/icon")
    return root.get('id'), root.get('version'), icon.text.strip() if icon is not None else None


def strip_declaration(addon_xml):
    """Drop the <?xml ...?> line so the add-on can be embedded in addons.xml."""
    return re.sub(r'^\s*<\?xml[^>]*\?>\s*', '', addon_xml).rstrip()


def zip_path(addon_id, version):
    return os.path.join(ZIPS, addon_id, f'{addon_id}-{version}.zip')


def save_icon(addon_id, icon, data):
    """Kodi shows repository artwork from zips/<id>/<icon path>."""
    target = os.path.join(ZIPS, addon_id, *icon.split('/'))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, 'wb') as f:
        f.write(data)


def build_git_addon(path, ref):
    addon_xml = git(path, 'show', f'{ref}:addon.xml').decode('utf-8')
    addon_id, version, icon = addon_info(addon_xml)
    target = zip_path(addon_id, version)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    git(path, 'archive', '--format=zip', f'--prefix={addon_id}/', '-o', target, ref)
    if icon:
        save_icon(addon_id, icon, git(path, 'show', f'{ref}:{icon}'))
    print(f'{addon_id} {version} (from {ref})')
    return addon_xml


def build_local_addon(name):
    source = os.path.join(ROOT, name)
    with open(os.path.join(source, 'addon.xml'), encoding='utf-8') as f:
        addon_xml = f.read()
    addon_id, version, icon = addon_info(addon_xml)
    target = zip_path(addon_id, version)
    os.makedirs(os.path.dirname(target), exist_ok=True)

    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as zf:
        for folder, _, files in os.walk(source):
            for file in sorted(files):
                full = os.path.join(folder, file)
                arcname = os.path.relpath(full, source).replace(os.sep, '/')
                zf.write(full, f'{addon_id}/{arcname}')
    if icon:
        with open(os.path.join(source, *icon.split('/')), 'rb') as f:
            save_icon(addon_id, icon, f.read())
    print(f'{addon_id} {version}')
    return addon_xml


def write_index(repo_zip):
    """Kodi's file manager browses an HTTP source by following its links."""
    name = os.path.basename(repo_zip)
    shutil.copyfile(repo_zip, os.path.join(ROOT, name))
    for old in os.listdir(ROOT):
        if old.startswith(f'{REPOSITORY_ADDON}-') and old.endswith('.zip') and old != name:
            os.remove(os.path.join(ROOT, old))
    with open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(
            '<!DOCTYPE html>\n<html><head><meta charset="utf-8"><title>Flatscan Kodi repository</title></head>\n'
            '<body>\n<h1>Flatscan Kodi repository</h1>\n'
            '<p>Add this page as a source in Kodi\'s file manager, then use '
            '<em>Install from zip file</em> on the zip below.</p>\n'
            f'<a href="{name}">{name}</a>\n</body></html>\n'
        )


def main():
    addons = [build_git_addon(a['path'], a['ref']) for a in GIT_ADDONS]
    addons += [build_local_addon(name) for name in LOCAL_ADDONS]

    body = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    body += '\n'.join(strip_declaration(a) for a in addons)
    body += '\n</addons>\n'
    data = body.encode('utf-8')
    with open(os.path.join(ROOT, 'addons.xml'), 'wb') as f:
        f.write(data)
    with open(os.path.join(ROOT, 'addons.xml.md5'), 'w', encoding='ascii', newline='\n') as f:
        f.write(hashlib.md5(data).hexdigest())

    _, version, _ = addon_info(next(a for a in addons if addon_info(a)[0] == REPOSITORY_ADDON))
    write_index(zip_path(REPOSITORY_ADDON, version))
    print('Wrote addons.xml, addons.xml.md5 and index.html')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(f'git failed: {" ".join(e.cmd)}\n{e.stderr.decode(errors="replace")}')
