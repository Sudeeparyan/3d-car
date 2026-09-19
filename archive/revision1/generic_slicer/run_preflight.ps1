$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$taskSlicer = Join-Path $taskRoot 'tools\PrusaSlicer-2.9.6\PrusaSlicer-2.9.6\prusa-slicer-console.exe'
$taskConfig = Join-Path $PSScriptRoot 'generic_simulation.ini'
$taskSpecs = @(
    @{ Name = 'body'; File = '01_body_160mm.stl'; Output = '01_body_SIMULATION_DO_NOT_PRINT.gcode.txt' },
    @{ Name = 'wheel'; File = '02_wheel_front_left.stl'; Output = '02_wheel_SIMULATION_DO_NOT_PRINT.gcode.txt' },
    @{ Name = 'coupon'; File = '06_detail_test_1to1.stl'; Output = '06_coupon_SIMULATION_DO_NOT_PRINT.gcode.txt' }
)
$taskManifest = @()
foreach ($taskSpec in $taskSpecs) {
    $taskInput = Join-Path (Join-Path $taskRoot 'print') $taskSpec.File
    $taskBeforeHash = (Get-FileHash -LiteralPath $taskInput -Algorithm SHA256).Hash
    $taskInfo = & $taskSlicer --info $taskInput 2>&1
    $taskInfo | Set-Content -LiteralPath (Join-Path $PSScriptRoot ($taskSpec.Name + '_mesh_info.txt'))
    if ($LASTEXITCODE -ne 0) { throw ('Info failed: ' + $taskSpec.File) }
    & $taskSlicer --datadir (Join-Path $PSScriptRoot 'isolated_profile') --load $taskConfig --export-gcode --center '110,110' --threads 4 --loglevel 3 --output (Join-Path $PSScriptRoot $taskSpec.Output) $taskInput 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot ($taskSpec.Name + '_cli.log'))
    if ($LASTEXITCODE -ne 0) { throw ('Slice failed: ' + $taskSpec.File) }
    $taskAfterHash = (Get-FileHash -LiteralPath $taskInput -Algorithm SHA256).Hash
    if ($taskBeforeHash -ne $taskAfterHash) { throw ('Input changed while slicing: ' + $taskSpec.File) }
    $taskManifest += @{
        name = $taskSpec.Name
        file = $taskSpec.File
        output = $taskSpec.Output
        sha256 = $taskBeforeHash.ToLowerInvariant()
        input_modified_utc = (Get-Item -LiteralPath $taskInput).LastWriteTimeUtc.ToString('o')
        sliced_utc = [DateTime]::UtcNow.ToString('o')
        exit_code = 0
        note = 'Generic geometry simulation only. Unknown college printer. Toolpaths must not be printed.'
    }
}
$taskManifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'input_manifest.json') -Encoding utf8
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
& $taskPython (Join-Path $PSScriptRoot 'analyze_toolpaths.py')
if ($LASTEXITCODE -ne 0) { throw 'Toolpath analysis failed' }
