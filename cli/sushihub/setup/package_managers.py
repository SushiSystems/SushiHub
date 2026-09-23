"""Re-export of :mod:`sushicore.provision.packages`; the implementation moved to sushicore."""

from __future__ import annotations

from sushicore.provision.packages import (  # noqa: F401
    WINGET_ID_TO_CMD,
    AptManager,
    DirectDownloadWindowsManager,
    DnfManager,
    IPackageManager,
    LinuxPackageManager,
    PacmanManager,
    VcpkgManager,
    WingetManager,
    YumManager,
    ZypperManager,
    download,
    ensure_intel_oneapi_repo,
    gh_latest_asset,
    gh_latest_asset_including_prerelease,
    gh_latest_release_asset,
    gh_tagged_asset,
    install_gpu_stack,
    prime_sudo,
    refresh_windows_path,
    run,
    tools_dir,
)

# Old private names some hub code and tests still import; kept as aliases so
# nothing in hub breaks now that the implementation lives in sushicore.
_download = download
_gh_latest_asset = gh_latest_asset
_gh_latest_asset_including_prerelease = gh_latest_asset_including_prerelease
_gh_latest_release_asset = gh_latest_release_asset
_gh_tagged_asset = gh_tagged_asset
_run = run
_tools_dir = tools_dir
