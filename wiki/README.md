# Wiki source

These markdown files are the **source for the GitHub wiki**, kept in the main repo so the wiki is
version-controlled and reviewable. `Home.md` is the wiki landing page; `_Sidebar.md` is the nav.

GitHub serves the wiki from a separate git repo (`…/fungeom.wiki.git`) that **does not exist until
the first page is created once via the web UI**. After that one-time bootstrap, `publish.sh` syncs
these files to it.

## Publish (one-time bootstrap, then sync)

1. **Bootstrap once:** open <https://github.com/ryanrudes/fungeom/wiki>, click *Create the first
   page*, save anything (it will be overwritten). This initializes `fungeom.wiki.git`.
2. **Sync any time:**

   ```bash
   ./wiki/publish.sh
   ```

   It clones the wiki repo, copies these pages over it (dropping this `README.md`), commits, and
   pushes. Re-run whenever you edit a page here.

> This `README.md` is the only file *not* published as a wiki page.
