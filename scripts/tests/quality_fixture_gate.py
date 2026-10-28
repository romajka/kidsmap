"""Offline miniature gate: real worker processes, no application or database."""
from pathlib import Path
import sys

import quality_test_support  # noqa: F401
from django.conf import settings
settings.QA_ROOT = Path(sys.argv[1])
settings.MEDIA_ROOT = settings.QA_ROOT/'media'
settings.PRIVATE_MEDIA_ROOT = settings.QA_ROOT/'private-media'
sys.path.append(str(Path(__file__).resolve().parents[2]))
from scripts.run_isolated_quality import run_quality_lanes

failure = sys.argv[2]
labels = ['quality_fixture_cases.WorkerPass',
          'quality_fixture_cases.WorkerFailure' if failure == 'parallel' else 'quality_fixture_cases.OtherWorkerPass',
          'quality_fixture_cases.SerialFailure' if failure == 'serial' else 'quality_fixture_cases.SerialPass']
if failure == 'class_setup':
    labels[1] = 'quality_fixture_cases.ClassSetupFailure'
elif failure == 'empty':
    labels = ['quality_test_support']
report = run_quality_lanes(labels, Path(sys.argv[1]), execution='split', workers=2)
raise SystemExit(0 if report['successful'] else 1)
