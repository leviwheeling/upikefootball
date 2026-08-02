#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail

python -m pip install -r requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build
mkdir -p backend/static
cp -R frontend/out/. backend/static/
