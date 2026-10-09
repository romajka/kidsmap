#!/bin/bash
set -o pipefail
cd /home/ramin/kidsmap
.venv/bin/python .tmp/place-acceptance-20261009-8792/run_unit.py catalog.testcases.test_task33_place_continuous catalog.testcases.permanent_place_wizard catalog.testcases.test_place_json_and_pricing_modes catalog.testcases.test_content_entry_final.CandidateMediaTests catalog.testcases.test_content_entry_final.AdminCandidateGalleryTests catalog.testcases.test_content_entry_final.LegacyReviewProjectionTests catalog.testcases.test_content_entry_final.SourceLanguageDisplayTests catalog.testcases.test_admin_candidate_cover > .tmp/place-acceptance-20261009-8792/server-tests.log 2>&1
