# Flatscan Kodi repository

Kodi add-on repository for [Flatscan Widgets](https://github.com/flatscan/flatscanwidgets), served by GitHub Pages at https://flatscan.github.io/kodi-repo/.

## Install in Kodi

1. Enable **Settings → System → Add-ons → Unknown sources**.
2. **Settings → File manager → Add source**, enter `https://flatscan.github.io/kodi-repo/` and name it `flatscan`.
3. **Settings → Add-ons → Install from zip file → flatscan** and pick `repository.flatscan-<version>.zip`.
4. **Install from repository → Flatscan Repository** and install the add-ons you want. Kodi updates them automatically from then on.

## Releasing an update

1. In the add-on's repository, bump `version` in `addon.xml` (Kodi only offers an update when it goes up), update `<news>`, and merge to `master`.
2. Here, run `python build.py`. It packages each add-on with `git archive` from its `master` branch (committed files only, minus its `export-ignore` entries), then regenerates `addons.xml`, `addons.xml.md5` and `index.html`.
3. Commit and push. Pages updates within a minute or two.
4. Publish a GitHub release on the add-on's repository with the same zip, for example:

   ```
   gh release create v1.0.1 --repo flatscan/flatscanwidgets --target master --title "Flatscan Widgets 1.0.1" --notes-file notes.md zips/script.flatscan.widgets/script.flatscan.widgets-1.0.1.zip
   ```

   Always pass `--repo`: in the flatscanwidgets folder `gh` otherwise picks its `upstream` remote (Embuary Helper).

To change the repository add-on itself, edit `repository.flatscan/addon.xml` and bump its version too.

## Layout

```
build.py                      Build script (desktop Python, no dependencies)
repository.flatscan/          Source of the repository add-on
addons.xml, addons.xml.md5    Generated: what Kodi reads to find add-ons and updates
index.html                    Generated: link page Kodi's file manager browses
repository.flatscan-*.zip     Generated: copy of the repository add-on for Install from zip
zips/<id>/<id>-<version>.zip  Generated: add-on packages (old versions are kept for rollback)
```
