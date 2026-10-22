$ErrorActionPreference = 'Stop'
$runtime = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $runtime)) { $runtime = 'python' }
& $runtime (Join-Path $PSScriptRoot 'research.py')
if ($LASTEXITCODE -ne 0) { throw 'Research failed; outputs may be incomplete.' }
& $runtime (Join-Path $PSScriptRoot 'make_report.py')
if ($LASTEXITCODE -ne 0) { throw 'Report generation failed.' }
