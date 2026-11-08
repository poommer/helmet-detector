param([int]$Epochs = 100, [int]$Batch = 16, [int]$Workers = 4, [int]$ImgSize = 640, [switch]$NoAmp)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$taskTrainArgs = @('train.py', '--data', '.\dataset-detect\data.yaml', '--epochs', "$Epochs", '--batch', "$Batch", '--workers', "$Workers", '--imgsz', "$ImgSize", '--cache', 'ram', '--nondeterministic', '--name', 'helmet-yolo11-l', '--model', 'yolo11l.pt')
if (!$NoAmp) { $taskTrainArgs += '--amp' }
& '.\.venv\Scripts\python.exe' @taskTrainArgs
if ($LASTEXITCODE -ne 0) { throw "Training failed ($LASTEXITCODE). Try -Batch 8, -Workers 0, or -NoAmp depending on the error." }
