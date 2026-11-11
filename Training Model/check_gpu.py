import os

# Avoid slow solver benchmarking/timing errors in the native Windows MIOpen build.
# Override externally if you want to benchmark other solver modes.
os.environ.setdefault('MIOPEN_FIND_MODE', 'FAST')
import torch

def check():
    print('PyTorch:', torch.__version__, 'HIP:', torch.version.hip)
    if not torch.version.hip or not torch.cuda.is_available():
        raise RuntimeError('AMD ROCm GPU unavailable. Check AMD driver and setup.ps1; CPU fallback is disabled.')
    print('GPU:', torch.cuda.get_device_name(0))
    print('VRAM GiB:', round(torch.cuda.get_device_properties(0).total_memory / 2**30, 2))
    x = torch.randn(128, 128, device='cuda', requires_grad=True)
    (x @ x.T).square().mean().backward()
    torch.cuda.synchronize()
    print('GPU forward/backward: PASS') 

if __name__ == '__main__':
    check()
