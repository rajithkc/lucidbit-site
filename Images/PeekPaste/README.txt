PeekPaste page assets.

Already here:
  • Icon-macOS-Default-1024x1024@1x.webp — generated from the app's own
    AppIcon (PeekPaste-macOS-Dark-1024x1024@1x.png in Assets.xcassets).

Slots the page expects. All optional — a CSS placeholder renders in each
spot until the file exists, so nothing breaks if you ship without them:

  • pp_edge.mp4             — Feature row 1: the panel sliding in at the edge  ✅
  • CardTypes.webp          — Feature row 2: code / link / colour / file cards  ✅
  • pp_preview.mp4          — Feature row 3: a clip opening in the preview
                              sheet, looping  ✅
  • pp_search.mp4           — Feature row 4: searching text inside a screenshot,
                              as a looping video rather than a still  ✅
  • pp_filter.mp4           — Feature row 5: filtering the Library, looping  ✅
  • Settings.webp           — Feature row 6: Settings › General — edge, shortcut,
                              permission, theme  ✅
  • Privacy.webp            — Feature row 7: App Rules — blur / ignore per app  ✅

All seven rows are filled. The only thing still unreferenced in this folder is
peekpaste_preview.mp4 (6.1 MB) — the hero video slot it was made for is still a
placeholder in peekpaste.html. Wire it in or delete it.
  • peekpaste_preview.mp4   — Optional looping hero video

The App Store screenshots are the obvious source for these, with one caveat:
crop the caption off first. Each feature row already carries its own headline
and paragraph, so an image with "Private by design." baked into it prints the
same words twice on the same row.

To use a feature image, replace the matching
    <div class="feature-image placeholder">…</div>
in peekpaste.html with
    <div class="feature-image"><img src="../Images/PeekPaste/NAME.webp" alt="…" loading="lazy"></div>

For the hero video, swap the .pp-video-placeholder div for the <video>
block used on the PeekFocus page.

Also still needed:
  • ../og/og-peekpaste.png  — 1200×630 social card (referenced by OG tags)
  • ../../downloads/PeekPaste.dmg — direct download
