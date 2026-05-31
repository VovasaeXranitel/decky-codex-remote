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
Copy-Item -LiteralPath (Join-Path $root "README.md") -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $root "LICENSE") -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $root "dist/index.js") -Destination (Join-Path $packageRoot "dist/index.js")

if (Test-Path $zipPath) {
  Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive -LiteralPath $packageRoot -DestinationPath $zipPath -Force

Write-Host "Packaged $pluginName at $packageRoot"
Write-Host "Zip: $zipPath"
