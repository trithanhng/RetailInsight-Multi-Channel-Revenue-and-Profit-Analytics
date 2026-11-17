param([ValidateSet('all','pipeline','benchmark','load-test','test','dashboard','report','package')][string]$Task = 'dashboard')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run .\setup.ps1 first' }
$env:PYTHONUTF8 = '1'
if (-not $env:JAVA_HOME) {
    $taskJava = 'C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot'
    if (Test-Path -LiteralPath (Join-Path $taskJava 'bin\java.exe')) { $env:JAVA_HOME = $taskJava }
}
function Invoke-TaskPython {
    & $taskPython @args
    if ($LASTEXITCODE -ne 0) { throw 'Python task failed; inspect output above' }
}
if ($Task -in @('all','pipeline')) { Invoke-TaskPython @('-m','src.pipeline.retail','--download') }
if ($Task -in @('all','benchmark')) { Invoke-TaskPython @('-m','src.pipeline.benchmark','--repeats','3') }
if ($Task -eq 'load-test') { Invoke-TaskPython @('-m','src.pipeline.benchmark','--scale','5','--repeats','3') }
if ($Task -in @('all','report')) { Invoke-TaskPython @('-m','src.utils.report') }
if ($Task -eq 'test') { Invoke-TaskPython @('-m','src.utils.delivery','--verify') }
if ($Task -eq 'package') { Invoke-TaskPython @('-m','src.utils.delivery','--package') }
if ($Task -eq 'all') { Invoke-TaskPython @('-m','src.utils.delivery','--verify','--package') }
if ($Task -eq 'dashboard') {
    Invoke-TaskPython @('-m','streamlit','run','dashboard/dashboard.py','--server.address','127.0.0.1','--server.headless','true','--browser.gatherUsageStats','false')
}
