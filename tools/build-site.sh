#!/usr/bin/env bash
# Build the status website exactly as Upptime's Static Site CI does (uptime-monitor
# src/site.ts), into ./site/status-page/__sapper__/export, for a local preview:
#
#   tools/build-site.sh
#   npx serve site/status-page/__sapper__/export      # data still comes from GitHub
#
# It installs the latest @upptime/status-page, as the workflow does, and prints its version.
# ./site is ignored by git.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf site
mkdir site
cd site
npm init -y >/dev/null
npm i @upptime/status-page --no-audit --no-fund --loglevel=error
version=$(node -p "require('./node_modules/@upptime/status-page/package.json').version")
cp -r node_modules/@upptime/status-page/* .
npm i --no-audit --no-fund --loglevel=error || true   # cypress's binary download may fail offline
npm run export
mkdir -p status-page/__sapper__/export
cp -r __sapper__/export/* status-page/__sapper__/export
cp -r ../assets/* status-page/__sapper__/export
echo "Built with @upptime/status-page ${version}: site/status-page/__sapper__/export"
