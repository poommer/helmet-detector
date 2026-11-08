param([int]$Epochs = 100, [int]$Batch = 4, [string]$Model = 'yolo11n.pt')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& '.\.venv\Scripts\python.exe' train.py --data '.\dataset-detect\data.yaml' --epochs $Epochs --batch $Batch --model $Model
if ($LASTEXITCODE -ne 0) { throw "Training failed ($LASTEXITCODE)." }
