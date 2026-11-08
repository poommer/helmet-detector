param([string]$Python = '')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Run-Python { & $script:Exe @args; if ($LASTEXITCODE -ne 0) { throw "Python command failed ($LASTEXITCODE)." } }
if (!(Test-Path '.venv\Scripts\python.exe')) {
    if ($Python) { & $Python -m venv .venv } else { & py -3.12 -m venv .venv }
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 x64 or pass -Python with its executable path.' }
}
$script:Exe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
Run-Python -c "import sys; assert sys.version_info[:2] == (3,12), 'Python 3.12 required'"
Run-Python -m pip install --upgrade pip
$base = 'https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1'
Run-Python -m pip install --no-cache-dir "$base/rocm_sdk_core-7.2.1-py3-none-win_amd64.whl" "$base/rocm_sdk_devel-7.2.1-py3-none-win_amd64.whl" "$base/rocm_sdk_libraries_custom-7.2.1-py3-none-win_amd64.whl" "$base/rocm-7.2.1.tar.gz"
Run-Python -m pip install --no-cache-dir "$base/torch-2.9.1%2Brocm7.2.1-cp312-cp312-win_amd64.whl" "$base/torchvision-0.24.1%2Brocm7.2.1-cp312-cp312-win_amd64.whl"
Run-Python -m pip install -c constraints.txt 'ultralytics>=8.4,<9' pyyaml
Run-Python -m pip check
Run-Python check_gpu.py
Run-Python -m pip freeze | Out-File -Encoding utf8 environment-installed.txt
