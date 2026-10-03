# First two Fatiha ayahs: annotation visibility and color

The source has ten upper signs, five per ayah. r0-a9 and r0-a10 were present but withheld because the collision detector compared advance boxes including empty font side bearings. At 34px the boxes overlap about half a pixel, while the actual outlines have a positive gap.

For the opening row's catalogue symbols only, collision checks now use browser-measured horizontal ink extents. Their full vertical boxes are retained conservatively. An unattached measurement canvas reads font metrics; no canvas or image is displayed. All font sizes, text, positions and outlines are unchanged. Real collisions remain withheld and are regression-tested. The first row's ten upper signs now share source-like black ink and transparent backgrounds. Other rows retain the previous collision policy/style.

This fixes rendering omissions, not the unresolved semantic identity of individual letter anchors or full-Quran completeness.
