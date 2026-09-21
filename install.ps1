<#
.SYNOPSIS
    SushiStack one-script installer (Windows).

.DESCRIPTION
    Bootstraps Python and Git — using winget when available, direct downloads
    otherwise (no Microsoft Store required). Installs the `hub` CLI from PyPI with
    pipx, then runs `hub init` and `hub install` in the directory you choose.
    Nothing is cloned: a workspace is any directory `hub init` has marked, and Git
    is installed because `hub add` clones module checkouts with it. The portable
    CMake/Ninja lands in <workspace>\dependencies, so only Python and Git are
    bootstrapped here. `hub install` provisions what the present modules declare,
    which in a fresh workspace is the base build tools alone; to choose a different
    set, run `hub install --customize` after.

    An install made this way carries no desktop application; `hub gui` needs the
    SushiStack repository, which you clone yourself if you want it.

.PARAMETER Add
    Space- or comma-separated module list to clone into the workspace, e.g.
    -Add "sushiruntime sushiengine". Each module brings the toolchains it
    declares as it arrives. Default: none.

.PARAMETER NoAlias
    Skip the offer to append `function sh { hub @args }` to the PowerShell
    profile. The offer is skipped anyway when input is redirected.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File install.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File install.ps1 -Add "sushiruntime sushiengine"

.EXAMPLE
    irm https://sushisystems.io/install.ps1 | iex
#>
[CmdletBinding()]
param(
    [string]$Add = "",
    [switch]$DryRun,
    [switch]$NoAlias
)

$ErrorActionPreference = "Stop"

function Info($m) { Write-Host "[INFO] $m"  -ForegroundColor Cyan }
function Warn($m) { Write-Host "[WARN] $m"  -ForegroundColor Yellow }
function Fail($m) { Write-Host "[ERROR] $m" -ForegroundColor Red; exit 1 }

function Prompt-WorkspaceDir($defaultDir) {
    if ($env:SUSHISTACK_DIR) { return $env:SUSHISTACK_DIR }
    if (-not [Environment]::UserInteractive) { return $defaultDir }
    try {
        if ([Console]::IsInputRedirected) { return $defaultDir }
    } catch { return $defaultDir }

    Write-Host "[INFO] Install location [$defaultDir] (30s to answer, Enter to accept): " -ForegroundColor Cyan -NoNewline
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $buffer = ""
    while ($sw.Elapsed.TotalSeconds -lt 30) {
        if ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true)
            if ($key.Key -eq "Enter") {
                Write-Host ""
                if ([string]::IsNullOrWhiteSpace($buffer)) { return $defaultDir }
                return $buffer.Trim()
            } elseif ($key.Key -eq "Backspace") {
                if ($buffer.Length -gt 0) {
                    $buffer = $buffer.Substring(0, $buffer.Length - 1)
                    Write-Host "`b `b" -NoNewline
                }
            } elseif (-not [char]::IsControl($key.KeyChar)) {
                $buffer += $key.KeyChar
                Write-Host $key.KeyChar -NoNewline
            }
        } else {
            Start-Sleep -Milliseconds 100
        }
    }
    Write-Host ""
    Info "No input received, using default: $defaultDir"
    return $defaultDir
}

$AliasMarker = "# sushi hub alias"

# Ask once whether to append `function sh { hub @args }` to the profile, and append it if the answer is yes.
function Offer-Alias {
    if ($NoAlias) { return }
    if (-not [Environment]::UserInteractive) { return }
    try {
        if ([Console]::IsInputRedirected) { return }
    } catch { return }

    $profilePath = $PROFILE.CurrentUserAllHosts
    if ((Test-Path $profilePath) -and (Select-String -Path $profilePath -SimpleMatch $AliasMarker -Quiet)) { return }

    Info "The alias only changes what you type in an interactive shell; sh.exe and every #!/bin/sh script keep the real sh."
    Write-Host "[INFO] Add ``function sh { hub @args }`` to $profilePath ? [y/N] " -ForegroundColor Cyan -NoNewline
    $reply = Read-Host
    if ($reply -notmatch '^(y|yes)$') { return }

    $parent = Split-Path $profilePath -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Add-Content -Path $profilePath -Encoding utf8 -Value @("", $AliasMarker, 'function sh { hub @args }')
    Info "Alias written to $profilePath; open a new PowerShell to pick it up."
}

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path","User")
}

function GitHub-LatestUrl($repo, $assetGlob) {
    $rel = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest"
    $asset = $rel.assets | Where-Object { $_.name -like $assetGlob } | Select-Object -First 1
    if (-not $asset) { Fail "No asset matching '$assetGlob' in $repo latest release." }
    return $asset.browser_download_url
}

function Download($url, $dest) {
    Info "Downloading $(Split-Path $dest -Leaf)..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    (New-Object Net.WebClient).DownloadFile($url, $dest)
}

function Ensure-Python {
    Refresh-Path
    if (Get-Command python -ErrorAction SilentlyContinue) { return }

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Info "Installing Python via winget..."
        winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements --silent
        Refresh-Path
        if (Get-Command python -ErrorAction SilentlyContinue) { return }
    }

    $url  = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
    $dest = Join-Path $env:TEMP "python-setup.exe"
    Download $url $dest
    Info "Installing Python (user scope, prepend PATH)..."
    Start-Process -Wait -FilePath $dest -ArgumentList "/quiet","InstallAllUsers=0","PrependPath=1","Include_pip=1"
    Refresh-Path
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Fail "Python installation failed. Open a new terminal and re-run."
    }
}

function Ensure-Git {
    Refresh-Path
    if (Get-Command git -ErrorAction SilentlyContinue) { return }

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Info "Installing Git via winget..."
        winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements --silent
        Refresh-Path
        if (Get-Command git -ErrorAction SilentlyContinue) { return }
    }

    $url  = GitHub-LatestUrl "git-for-windows/git" "*64-bit.exe"
    $dest = Join-Path $env:TEMP "git-setup.exe"
    Download $url $dest
    Info "Installing Git..."
    Start-Process -Wait -FilePath $dest -ArgumentList "/VERYSILENT","/NORESTART","/NOCANCEL","/SP-","/CLOSEAPPLICATIONS","/RESTARTAPPLICATIONS","/COMPONENTS=icons,ext\reg\shellhere,assoc,assoc_sh"
    Refresh-Path
}

# Bootstrap only what `hub` itself needs to run and clone: Python and Git. CMake,
# Ninja, and the SYCL toolchains are downloaded portably into the shared
# <workspace>\dependencies by `hub install` and `hub add`.
Ensure-Python
Ensure-Git

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { Fail "python not on PATH after install. Open a new terminal and re-run." }

# Choose the workspace directory. It need not exist and need not be a checkout;
# `hub init` marks whatever directory it is run in.
$DefaultWorkspaceDir = Join-Path $HOME "sushistack"
$WorkspaceDir = Prompt-WorkspaceDir $DefaultWorkspaceDir
if (-not (Test-Path $WorkspaceDir)) { New-Item -ItemType Directory -Path $WorkspaceDir -Force | Out-Null }
Set-Location $WorkspaceDir
Info "Workspace: $WorkspaceDir"

# Name a command that runs pipx: its own shim when PATH carries one, otherwise
# the module under whichever python has it. Refresh-Path has already rebuilt PATH
# by now, so `python` is not necessarily the interpreter this shell started with,
# and `python -m pipx` alone is not safe to assume.
function Resolve-Pipx {
    if (Get-Command pipx -ErrorAction SilentlyContinue) { return @("pipx", @()) }
    return @("python", @("-m", "pipx"))
}

# Install the hub CLI from PyPI. pipx is bootstrapped here rather than reused
# from the repository's install.py, because that file arrives with a checkout and
# this script no longer makes one.
if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
    Info "pipx not found; installing it with pip..."
    python -m pip install --user pipx
    python -m pipx ensurepath
    Refresh-Path
}
$PipxExe, $PipxPre = Resolve-Pipx

# Remove any existing sushihub venv first. `pipx install --force` reuses the venv
# it finds, which fails when that venv was built another way -- an editable
# install from a checkout is the common case, and it is exactly what a
# contributor upgrading to the published package has.
if ((& $PipxExe @PipxPre list --short) -match "^sushihub") {
    Info "Replacing the existing sushihub install"
    & $PipxExe @PipxPre uninstall sushihub
}

Info "Installing the hub CLI from PyPI..."
& $PipxExe @PipxPre install sushihub
if ($LASTEXITCODE -ne 0) { Fail "Could not install sushihub from PyPI." }

$PipxBinDir = & $PipxExe @PipxPre environment --value PIPX_BIN_DIR

# An install made before 2026-09-22 published the same CLI under another
# distribution name, whose venv keeps its own `hub` shim.
if ((& $PipxExe @PipxPre list --short) -match "^sushistack-cli") {
    Info "Removing the sushistack-cli install this package was renamed from"
    & $PipxExe @PipxPre uninstall sushistack-cli
}

# An install from before the rename left a shim named ss.exe.
$StaleShim = Join-Path $PipxBinDir "ss.exe"
if (Test-Path $StaleShim) {
    Info "Removing the ss shim an earlier install left in $PipxBinDir"
    Remove-Item $StaleShim -Force -Confirm:$false
}

$HubCmd = Join-Path $PipxBinDir "hub.exe"
if (-not (Test-Path $HubCmd)) { $HubCmd = "hub" }

# Mark the workspace, then provision what it declares today: the base tools.
& $HubCmd init

$flags = @("install")
if ($DryRun) { $flags += "--dry-run" }
Info "Running: hub $($flags -join ' ')"
& $HubCmd @flags
$hubExit = $LASTEXITCODE
if ($hubExit -ne 0) { exit $hubExit }

# Optionally clone the requested modules; `hub add` provisions what each needs.
$modules = ($Add -replace ',', ' ').Split(' ', [StringSplitOptions]::RemoveEmptyEntries)
if ($modules.Count -gt 0) {
    Info "Adding modules: $($modules -join ' ')"
    & $HubCmd add @modules
}

Offer-Alias

Info "Done. Workspace ready at $WorkspaceDir"
if ($modules.Count -eq 0) {
    Info "Next: hub add sushiruntime   (then: cd sushiruntime; sr build)"
}
