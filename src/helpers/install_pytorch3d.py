import os
import sys
import subprocess
import torch

# Force PyTorch3D to compile with CUDA support, even if a GPU is not visible at build time.
os.environ["FORCE_CUDA"] = "1"

# Add the CUB_HOME to the include path for the compiler
cub_home = os.environ.get("CUB_HOME", None)
if cub_home is None:
    print("Warning: CUB_HOME is not set. Compilation might fail.")
    include_args = []
else:
    include_args = ["-I", cub_home]

try:
    pyt_ver = torch.__version__.split('+')[0].replace('.', '')
    cuda_ver = torch.version.cuda.replace('.', '')
    py_ver_minor = sys.version_info.minor
    version_str = f"py3{py_ver_minor}_cu{cuda_ver}_pyt{pyt_ver}"
    
    print(f"Attempting PyTorch3D wheel for: {version_str}")
    wheel_url = f"https://dl.fbaipublicfiles.com/pytorch3d/packaging/wheels/{version_str}/download.html"
    
    rc = subprocess.call([
        sys.executable, "-m", "pip", "install", "--no-index", "--no-cache-dir", "pytorch3d", "-f", wheel_url
    ])
    
    if rc != 0:
        raise Exception("Wheel installation failed. Falling back to source.")

except Exception as e:
    print(f"Wheel installation failed or was skipped: {e}. Falling back to build PyTorch3D from source with FORCE_CUDA.")
    
    # Build from source, passing CUB include path to the compiler
    build_env = os.environ.copy()
    build_env["CPLUS_INCLUDE_PATH"] = cub_home
    build_env["C_INCLUDE_PATH"] = cub_home
    
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "git+https://github.com/facebookresearch/pytorch3d.git@stable"],
        env=build_env
    )

print("PyTorch3D installation successful.")
