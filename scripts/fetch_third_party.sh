#!/bin/bash
# Fetch the two external code bases used ONLY as benchmark baselines. Neither is
# redistributed in this repository.
#   third_party/metis   adhyan-jain/Metis at the audited commit (no licence file: fetched, not copied)
#   third_party/phmap   greg7mdp/parallel-hashmap v1.4.1 (Apache-2.0), a header-only Swiss-table port
set -e
cd "$(dirname "$0")/.."
mkdir -p third_party
METIS_COMMIT=7b3dacfa5405ec3e6a03b718f485b473d779123d
if [ ! -d third_party/metis/.git ]; then
  git clone -q https://github.com/adhyan-jain/Metis third_party/metis
fi
git -C third_party/metis checkout -q "$METIS_COMMIT"
if [ ! -d third_party/phmap/.git ]; then
  git clone -q --depth 1 --branch v1.4.1 https://github.com/greg7mdp/parallel-hashmap third_party/phmap
fi
# A tag can be moved; the commit it named when the baselines were measured cannot.
PHMAP_COMMIT=22a7f6ca7205aaa7d3929277103d5cf94c2e480c
if [ "$(git -C third_party/phmap rev-parse HEAD)" != "$PHMAP_COMMIT" ]; then
  echo "parallel-hashmap v1.4.1 is not at the expected commit $PHMAP_COMMIT" >&2
  exit 1
fi
echo "metis: $(git -C third_party/metis rev-parse HEAD)"
echo "phmap: $(git -C third_party/phmap describe --tags) $(git -C third_party/phmap rev-parse HEAD)"
