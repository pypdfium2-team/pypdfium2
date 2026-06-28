#! /usr/bin/env bash
set -exuo pipefail

TAG="$1"
git config user.email "geisserml@gmail.com"
git config user.name "geisserml"
git tag -a "$TAG" -m "Autorelease"
