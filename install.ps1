<#
.SYNOPSIS
    SushiStack one-script installer (Windows).

.DESCRIPTION
    Bootstraps Python and Git — using winget when available, direct downloads
    otherwise (no Microsoft Store required). Clones the SushiStack workspace,
    installs the `hub` CLI, then provisions the shared dependency tree with
    `hub install`. The portable CMake/Ninja lands in <workspace>\dependencies, so
    only Python and Git are bootstrapped here. `hub install` provisions what the
    present modules declare, which in a fresh workspace is the base build tools
    alone; to choose a different set, run `hub install --customize` after.

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

$RepoUrl = if ($env:SUSHISTACK_REPO_URL) { $env:SUSHISTACK_REPO_URL } else { "https://github.com/sushisystems/sushistack.git" }

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

# Locate or clone the workspace. The SushiStack repo is identified by its
# sushihub\cli\manifests tree (it ships no CMakeLists.txt).
$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { $null }
if ($ScriptDir -and (Test-Path (Join-Path $ScriptDir "sushihub\cli\manifests"))) {
    $WorkspaceDir = $ScriptDir
} else {
    $DefaultWorkspaceDir = Join-Path $HOME "sushistack"
    $WorkspaceDir = Prompt-WorkspaceDir $DefaultWorkspaceDir
    if (-not (Test-Path (Join-Path $WorkspaceDir ".git"))) {
        Info "Cloning $RepoUrl -> $WorkspaceDir"
        git clone $RepoUrl $WorkspaceDir
    }
}
Set-Location $WorkspaceDir
Info "Workspace: $WorkspaceDir"

# Install the hub CLI.
Info "Installing the hub CLI..."
python sushihub/cli/install.py

$PipxBinDir = python -m pipx environment --value PIPX_BIN_DIR

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
