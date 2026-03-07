#!/bin/bash
set -e

# Configuration - Keywords for version bumping
MAJOR_KEYWORDS="BREAKING CHANGE|BREAKING|!:"
MINOR_KEYWORDS="^feat:|^feature:"
PATCH_KEYWORDS="^fix:|^chore:|^docs:|^style:|^refactor:|^perf:|^test:|^ci:|^build:"

# Get inputs from environment variables
BRANCH_NAME="${BRANCH_NAME}"
COMMIT_MSG="${COMMIT_MSG}"
COMMIT_SHA="${COMMIT_SHA}"

echo "Branch: $BRANCH_NAME"
echo "Commit SHA: $COMMIT_SHA"
echo "Commit Message: $COMMIT_MSG"

# Determine tag based on branch
if [ "$BRANCH_NAME" == "main" ]; then
  echo "Main branch detected - using semantic versioning"

    # Check if THIS commit already has a tag
  EXISTING_TAG=$(git tag --points-at HEAD | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -n1)
  
  if [ -n "$EXISTING_TAG" ]; then
    echo "This commit already has tag: $EXISTING_TAG"
    IMAGE_TAG="$EXISTING_TAG"
    echo "IMAGE_TAG=$IMAGE_TAG" >> $GITHUB_ENV
    echo "Final IMAGE_TAG: $IMAGE_TAG"
    exit 0  # ← Skip version calculation
  fi
  
  # Fetch all tags
  git fetch --tags --unshallow 2>/dev/null || git fetch --tags
  
  # Get latest semantic version tag
  LATEST_TAG=$(git tag -l "v*.*.*" | sort -V | tail -n1)
  LATEST_TAG=${LATEST_TAG:-v0.0.0}
  
  echo "Latest tag: $LATEST_TAG"
  
  # Parse version components
  MAJOR=$(echo $LATEST_TAG | cut -d. -f1 | sed 's/v//')
  MINOR=$(echo $LATEST_TAG | cut -d. -f2)
  PATCH=$(echo $LATEST_TAG | cut -d. -f3)
  
  echo "Current version: $MAJOR.$MINOR.$PATCH"
  
  # Determine version bump based on commit message
  if echo "$COMMIT_MSG" | grep -qE "$MAJOR_KEYWORDS"; then
    echo "MAJOR bump detected"
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
  elif echo "$COMMIT_MSG" | grep -qE "$MINOR_KEYWORDS"; then
    echo "MINOR bump detected"
    MINOR=$((MINOR + 1))
    PATCH=0
  elif echo "$COMMIT_MSG" | grep -qE "$PATCH_KEYWORDS"; then
    echo "PATCH bump detected"
    PATCH=$((PATCH + 1))
  else
    echo "No keyword matched, defaulting to PATCH bump"
    PATCH=$((PATCH + 1))
  fi
  
  # New version
  IMAGE_TAG="v${MAJOR}.${MINOR}.${PATCH}"
  echo "New version: $IMAGE_TAG"
  
  # Output to GitHub Environment
  echo "IMAGE_TAG=$IMAGE_TAG" >> $GITHUB_ENV
  echo "NEW_GIT_TAG=$IMAGE_TAG" >> $GITHUB_ENV
  
  # Create Git tag with re-run protection
  if ! git rev-parse $IMAGE_TAG >/dev/null 2>&1; then
    echo "Creating Git tag: $IMAGE_TAG"
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git tag $IMAGE_TAG
    git push origin $IMAGE_TAG
    echo "Git tag created and pushed: $IMAGE_TAG"
  else
    echo "Git tag $IMAGE_TAG already exists, skipping tag creation"
  fi
  
else
  # For dev/staging branches
  echo "Dev/Staging branch detected - using branch-sha format"
  SHORT_SHA=$(echo "$COMMIT_SHA" | cut -c1-7)
  IMAGE_TAG="${BRANCH_NAME}-${SHORT_SHA}"
  echo "Image tag: $IMAGE_TAG"
  
  # Output to GitHub Environment
  echo "IMAGE_TAG=$IMAGE_TAG" >> $GITHUB_ENV
fi

echo "Final IMAGE_TAG: $IMAGE_TAG"
