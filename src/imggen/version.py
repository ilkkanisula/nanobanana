"""Version management and checking for imggen."""

import subprocess
import sys

__version__ = "1.0.1"

# Repository details
REPO_URL = "https://github.com/ilkkanisula/imggen"
REPO_NAME = "ilkkanisula/imggen"


def get_current_version():
    """Get the current installed version."""
    return __version__


def check_for_updates(verbose=False):
    """Check if a newer version is available on GitHub.

    Args:
        verbose: If True, print status messages

    Returns:
        tuple: (has_update, latest_version, message)
    """
    try:
        # Try to get the latest tag from the repo
        result = subprocess.run(
            ["git", "ls-remote", "--tags", REPO_URL],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            if verbose:
                print("Could not check for updates (git error)")
            return False, None, None

        # Parse tags and find the latest version
        # Format: hash refs/tags/v1.0.0 (with optional ^{} suffix)
        tags = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            # Remove ^{} suffix if present
            tag = line.split()[-1].replace('refs/tags/', '').rstrip('^{}')
            # Filter for version-like tags (v0.0.0)
            if tag.startswith('v') and tag[1:2].isdigit():
                tags.append(tag[1:])  # Remove 'v' prefix

        if not tags:
            if verbose:
                print("No version tags found in repository")
            return False, None, None

        # Sort versions (simple semantic version comparison)
        def parse_version(v):
            try:
                return tuple(map(int, v.split('.')))
            except (ValueError, AttributeError):
                return (0, 0, 0)

        latest = max(tags, key=parse_version)
        current = parse_version(get_current_version())
        latest_tuple = parse_version(latest)

        if latest_tuple > current:
            message = f"\n💾 Update available: {latest}\n"
            message += f"   Run: uv tool install --upgrade git+{REPO_URL}.git\n"
            return True, latest, message

        if verbose:
            print(f"✓ You're on the latest version ({get_current_version()})")

        return False, None, None

    except subprocess.TimeoutExpired:
        if verbose:
            print("Update check timed out")
        return False, None, None
    except Exception as e:
        if verbose:
            print(f"Update check failed: {e}")
        return False, None, None


def print_update_notice():
    """Print update notice if a new version is available."""
    has_update, latest, message = check_for_updates(verbose=False)
    if has_update:
        print(message, file=sys.stderr)
