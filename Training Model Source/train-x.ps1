param([int]$Epochs = 100, [int]$Batch = 8, [int]$Workers = 4, [int]$ImgSize = 640, [double]$LearningRate = 0.0001, [ValidateSet('bf16','fp32')][string]$Precision = 'bf16', [switch]$NoAmp)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$taskTrainArgs = @('train.py', '--data', '.\dataset-detect\data.yaml', '--epochs', "$Epochs", '--batch', "$Batch", '--workers', "$Workers", '--imgsz', "$ImgSize", '--cache', 'ram', '--nondeterministic', '--name', 'helmet-yolo11x', '--model', 'yolo11x.pt')
if ($NoAmp) { $Precision = 'fp32' }
$taskTrainArgs += @('--precision', $Precision)
$taskTrainArgs += @('--optimizer', 'AdamW', '--lr0', $LearningRate.ToString([System.Globalization.CultureInfo]::InvariantCulture))
& '.\.venv\Scripts\python.exe' @taskTrainArgs
if ($LASTEXITCODE -ne 0) { throw "YOLO11x training failed ($LASTEXITCODE)." }
