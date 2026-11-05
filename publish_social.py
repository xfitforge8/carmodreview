#!/usr/bin/env python3
"""Publish the shorts to docs/social/ so Instagram's API can fetch them.

The Instagram Graph API does not accept a file upload -- it takes a video_url
and fetches the mp4 itself. So the shorts have to be publicly reachable before
they can be posted, and on GitHub Pages that means committing them.

This copies the renders into docs/social/ and rewrites the queue entries' URLs
accordingly. It does NOT commit; decide that yourself after looking at the
diff, because these are binaries going into the site repo.

  python3 publish_social.py
  git add docs/social && git commit -m "Publish shorts" && git push
"""
import json
import os
import shutil

ROOT = os.path.expanduser('~/carmodreview')
SOCIAL = os.path.join(ROOT, 'social')
# The master copies live at the repo root, not in docs/. build.py runs
# shutil.rmtree(docs) at the top of every build, so anything parked under
# docs/ that is not generated is deleted on the next `python3 build.py` --
# which is exactly what happened to a first attempt at docs/social/.
MASTER = os.path.join(ROOT, 'social', 'public')
DEST = os.path.join(ROOT, 'docs', 'social')


def main():
    os.makedirs(MASTER, exist_ok=True)
    os.makedirs(DEST, exist_ok=True)
    n = 0
    for f in sorted(os.listdir(SOCIAL)):
        if f.endswith(('-short.mp4', '-cover.jpg')):
            shutil.copy(os.path.join(SOCIAL, f), os.path.join(MASTER, f))
            shutil.copy(os.path.join(SOCIAL, f), os.path.join(DEST, f))
            n += 1
    print(f'copied {n} files to docs/social/ and {MASTER}')


if __name__ == '__main__':
    main()
