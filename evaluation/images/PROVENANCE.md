# Evaluation image provenance and licensing

All photographs in this folder were downloaded from Wikimedia Commons, a
repository of freely-licensed media. Each file below links to its Commons
file page, which carries the authoritative license and author credit.
None of these images are AI-generated or synthetic; `images/synthetic/`
holds separate programmatically-drawn illustrations used only as pytest
fixtures (see that folder's note below).

| File | Source | License |
|---|---|---|
| `engagement_2carat_diamond.jpg` | [Engagement ring with a 2 Caret diamond.jpg](https://commons.wikimedia.org/wiki/File:Engagement_ring_with_a_2_Caret_diamond.jpg) | CC BY-SA 3.0 |
| `classic_diamond_engagement.jpg` | [Classic Diamond Engagement Ring.jpg](https://commons.wikimedia.org/wiki/File:Classic_Diamond_Engagement_Ring.jpg) | CC BY-SA 4.0 |
| `diamond_ring_top_down.jpg` | [Diamond ring (top down view) (2374464703).jpg](https://commons.wikimedia.org/wiki/File:Diamond_ring_(top_down_view)_(2374464703).jpg) | CC BY-SA 2.0 |
| `diamond_ring_on_hand.jpg` | [Diamond engagement ring on woman hand 6313.jpg](https://commons.wikimedia.org/wiki/File:Diamond_engagement_ring_on_woman_hand_6313.jpg) | CC BY-SA 2.5 |
| `engagement_ring_stephen_durham.jpg` | [Engagement ring photo by Stephen Durham.jpg](https://commons.wikimedia.org/wiki/File:Engagement_ring_photo_by_Stephen_Durham.jpg) | CC BY 2.0 |
| `citrine_silver_ring.jpg` | [Citrine and silver ring.jpg](https://commons.wikimedia.org/wiki/File:Citrine_and_silver_ring.jpg) (Mauro Cateb) | CC BY-SA 3.0 |
| `coil_silver_ring.jpg` | [Coil silver ring.jpg](https://commons.wikimedia.org/wiki/File:Coil_silver_ring.jpg) (Mauro Cateb) | CC BY-SA 3.0 |

All licenses above permit reuse and redistribution (including in this
local evaluation/demo project) provided attribution is given, which this
file provides. No image was altered from its source other than being
served as-is by the application.

## Why real photos, not studio-perfect ones

These seven images were deliberately chosen for variety rather than
uniform quality: different metals (white gold, yellow gold, silver),
different stones (diamond, citrine, none at all), different compositions
(clean product shot, on-hand lifestyle photo, angled macro, textured
background, pure reflective metal with no gemstone), and different
resolutions. Several of them are genuinely hard for a classical CV
pipeline -- that is the point. See `EVALUATION.md` for how the bundled
classical CV baseline actually performs on each one, including its
documented failures (e.g. filigree cutwork or polished-metal highlights
being mistaken for small stones).

## `images/synthetic/`

Separate, programmatically-drawn illustrations (`evaluation/generate_images.py`)
used exclusively as deterministic pytest fixtures in
`backend/tests/test_cv_pipeline.py`, where exact, by-construction ground
truth (e.g. "this image has exactly 0 stones" or "this image is below the
minimum usable resolution") is more valuable than photorealism. They are
not part of the labeled evaluation dataset or its reported metrics.
