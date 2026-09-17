#!/usr/bin/env bash

# Cut a release. With no arguments, the next CalVer version for this month
# (YEAR.MONTH.MICRO); with --pre, a pre-release of it (YEAR.MONTH.MICROrcN).
#
# Pre-releases skip CHANGELOG.md — git-cliff ignores rc tags, so their commits
# roll into the final release's notes — and the workflow publishes them as
# Docker images only, never to PyPI, and never moves the :latest tags.

set -efu -o pipefail

PRERELEASE=0
for arg in "$@"; do
    case "$arg" in
        --pre) PRERELEASE=1 ;;
        *)
            echo "Usage: $0 [--pre]"
            exit 2
            ;;
    esac
done

function check_command {
    if ! command -v "$1" &> /dev/null; then
        echo "$1 not found. Exiting."
        exit 1
    fi
}

check_command git
check_command git-cliff
check_command uv
check_command npm

# Get current date components
YEAR=$(date +%Y)
MONTH=$(date +%-m)  # %-m removes zero padding

# Latest *final* version for the current year and month. Pre-release tags
# (2026.9.1rc1) are filtered out: they are not releases, and their suffix
# would break the arithmetic below.
LATEST_TAG=$(git tag -l "${YEAR}.${MONTH}.*" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -n 1 || true)

if [ -z "$LATEST_TAG" ]; then
    # No version for current year/month exists, start at 0
    MICRO=0
else
    # Extract micro version and increment
    MICRO=$(echo "$LATEST_TAG" | cut -d. -f3)
    MICRO=$((MICRO + 1))
fi

BASE_VERSION="${YEAR}.${MONTH}.${MICRO}"

if [ "$PRERELEASE" -eq 1 ]; then
    # Number the candidate after the ones already tagged for this version.
    RC=$(git tag -l "${BASE_VERSION}rc*" | wc -l | tr -d ' ')
    RC=$((RC + 1))
    # PEP 440 for Python and the tag; npm insists on semver for its own file.
    NEXT_VERSION="${BASE_VERSION}rc${RC}"
    NPM_VERSION="${BASE_VERSION}-rc.${RC}"
else
    NEXT_VERSION="$BASE_VERSION"
    NPM_VERSION="$BASE_VERSION"
fi

CURRENT_VERSION=$(uv version --short)

echo " > Current version is $CURRENT_VERSION"
echo " > Setting new version to $NEXT_VERSION"

# Manually update version in pyproject.toml and frontend/package.json
sed -i '' "s/^version = .*/version = \"${NEXT_VERSION}\"/" pyproject.toml
(cd frontend && npm version "$NPM_VERSION" --no-git-tag-version --allow-same-version > /dev/null)

echo " > Version bumped to $NEXT_VERSION"

FILES=(pyproject.toml frontend/package.json frontend/package-lock.json uv.lock)
if [ "$PRERELEASE" -eq 1 ]; then
    echo " > Pre-release: leaving CHANGELOG.md for the final release"
else
    echo "Updating CHANGELOG.md"
    git-cliff --unreleased --tag "$NEXT_VERSION" --prepend CHANGELOG.md > /dev/null
    FILES+=(CHANGELOG.md)
fi

echo "Locking dependencies"
uv lock

echo " > Commiting changes and adding git tag"
git add "${FILES[@]}"
git commit -m "chore(ci): Bump version to $NEXT_VERSION"
git tag -a "$NEXT_VERSION" -m "$NEXT_VERSION"

read -p " > Are you sure you want to push the changes and tags to the remote repository? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo " > Pushing changes and tags to the remote repository"
    git push
    git push --tags
else
    echo " > Changes and tags were not pushed to the remote repository"
fi
