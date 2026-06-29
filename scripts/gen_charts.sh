#!/usr/bin/env bash
# Regenerate the SVG/PNG Gantt charts under docs/. Run from the repo root.
# PNGs need rsvg-convert (librsvg2-bin); SVGs need only Python.
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p docs/svg docs/png

python3 -m rtsim compare examples/rm_fails_edf_ok.json --algos RM EDF \
    --gantt none --svg-dir docs/svg >/dev/null
python3 -m rtsim run examples/three_tasks.json --algo EDF \
    --gantt none --svg docs/svg/three_tasks_EDF.svg >/dev/null
python3 -m rtsim run examples/feasible.json --algo RM \
    --gantt none --svg docs/svg/feasible_RM.svg >/dev/null

if command -v rsvg-convert >/dev/null 2>&1; then
    for f in docs/svg/*.svg; do
        rsvg-convert -z 2 "$f" -o "docs/png/$(basename "${f%.svg}").png"
    done
    echo "SVGs and PNGs regenerated under docs/."
else
    echo "SVGs regenerated. Install librsvg2-bin (rsvg-convert) to also build PNGs."
fi
