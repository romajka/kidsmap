# Illustrated choices across parent guides — 2026-11-05

Scope: user-approved local extension of the Baku guide's illustrated cards to parks, museums, play centres and sport, in AZ/RU/EN.

Workspace: `/home/ramin/.codex/worktrees/baku-guide-choice/kidsmap`, base HEAD `5ff3da4540cc61ea74cb71538f4799190574776b`. Changes are uncommitted. No push, production write or deployment.

## Result

- Shared pastel card styling, decorative floating images, hover lift and a native animation checkbox; reduced-motion CSS disables continuous movement and transitions.
- Existing planning copy and checklists moved before venue cards for parks, museums and play centres. No duplicated planning sections.
- Six sports directions use their existing localized descriptions and taxonomy-derived catalog links. Each has its own illustration.
- TOC order follows the new layout. Parks district directory, public venue selection, SEO metadata and hero images remain intact.
- Nine original transparent illustrations generated with built-in `image_gen.imagegen`, encoded as WebP without creative modification. Exact prompts and workspace paths: `docs/reports/parent-guides-art-prompts-2026-11-05.json`. Assets: `static/img/guides/choice-*.webp`.

## Verification

PASS — isolated Django regression corpus, 89 tests:

```sh
/home/ramin/kidsmap/.venv/bin/python .tmp/baku-guide/runner.py test catalog.testcases.test_baku_guide_choices catalog.testcases.test_parent_guides catalog.testcases.test_parks_guide catalog.testcases.test_museums_guide catalog.testcases.test_play_centers_guide catalog.testcases.test_home_parent_intent catalog.testcases.test_public_age_notes catalog.testcases.test_current_pricing_contract --noinput --keepdb
```

PASS — four image/schema/production-static-manifest tests, rerun after TOC changes:

```sh
/home/ramin/kidsmap/.venv/bin/python .tmp/baku-guide/runner.py test catalog.testcases.test_parent_guide_images --noinput --keepdb
```

PASS — nine JavaScript hash-navigation tests:

```sh
NODE_PATH="$PWD/.tmp/baku-guide/node/node_modules" node --test scripts/tests/parent_guide_links.test.cjs
```

PASS — rendered browser, four guides × three languages × 320/768/1440px: 36 states, no document overflow or clipped cards. Additional 375px mobile review. All nine new images loaded in rendered pages. Pause/resume verified on all four guides; keyboard Space also verified. OS reduced-motion emulation was unavailable; CSS and existing JS reduced-motion tests cover the implementation, not an OS-level browser run.

PASS — HTTP verification: 12 localized guide pages; 33 unique sport-page catalog links; nine new image URLs. No missing anchors or duplicate HTML IDs. No browser console errors in the final interaction check. `git diff --check` passes.

Evidence under `.tmp/baku-guide/`: `all-guide-tests.log`, `all-guide-image-tests.log`, `all-guide-responsive.json`, `all-guide-http.json`, `all-guides-sport.jpg`, `all-guides-museums.jpg`.

Known test limitation: SQLite warns that SpecialistEmployment nulls-distinct constraints are unsupported; unrelated to this visual change. No full-project or production test run.

## Preview

Persistent isolated server: `http://127.0.0.1:8774`. Paths: `/ru/parents/parks/`, `/ru/parents/museums/`, `/ru/parents/play-centers/`, `/ru/parents/sport/` (also AZ root and EN).

Preview contains 19 public-only venue fixtures, not the complete live inventory. Nine additional records were read from public KidsMap pages for sport/play-centre preview; no private database or production credentials were used. Candidate 31 was not imported because its public subcategory could not be confirmed. Earlier fixture import stopped on that validation; existing fixtures were retained.

## Follow-up: animation checkbox removed

At the user's request, removed the illustration animation checkbox from all five guides and all locales. Removed unused labels/control CSS. Automatic float now runs once for 4.8 seconds and settles at its base position; hover effects and reduced-motion support remain. Verified HTTP rendering of all 15 localized pages, absence of the control, presence of illustration cards, and browser computed animation duration/iteration count. This supersedes the checkbox behavior described above.

## Follow-up: continuous floating restored

The user explicitly requested the illustrations to float as before while keeping the checkbox removed. Restored the shared 5-second infinite float and staggered phases. Reduced-motion CSS remains. Rendered browser checks across all five RU guides confirm 16 illustrations with infinite/running animation and zero removed controls. The CSS is shared across locales. This supersedes the 4.8-second single-cycle change above. `git diff --check` passes.
