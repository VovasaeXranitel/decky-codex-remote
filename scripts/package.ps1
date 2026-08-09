$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$pluginName = "CodexRemote"
$buildRoot = Join-Path $root "build"
$packageRoot = Join-Path $buildRoot $pluginName
$zipPath = Join-Path $buildRoot "$pluginName.zip"

Set-Location $root

pnpm run build

if (Test-Path $packageRoot) {
  Remove-Item -LiteralPath $packageRoot -Recurse -Force
}

New-Item -ItemType Directory -Path (Join-Path $packageRoot "dist") -Force | Out-Null

Copy-Item -LiteralPath (Join-Path $root "plugin.json") -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $root "package.json") -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $root "main.py") -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $root "codex_app_client.py") -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $root "codex_remote") -Destination (Join-Path $packageRoot "codex_remote") -Recurse
Copy-Item -LiteralPath (Join-Path $root "README.md") -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $root "LICENSE") -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $root "dist/index.js") -Destination (Join-Path $packageRoot "dist/index.js")

Get-ChildItem -LiteralPath $packageRoot -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -LiteralPath $packageRoot -Recurse -File -Filter "*.pyc" | Remove-Item -Force

if (Test-Path $zipPath) {
  Remove-Item -LiteralPath $zipPath -Force
}

@"
import pathlib
import zipfile

package_root = pathlib.Path(r"$packageRoot")
zip_path = pathlib.Path(r"$zipPath")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in package_root.rglob("*"):
        if path.is_file():
            archive.write(path, path.relative_to(package_root.parent).as_posix())
"@ | python -

Write-Host "Packaged $pluginName at $packageRoot"
Write-Host "Zip: $zipPath"
