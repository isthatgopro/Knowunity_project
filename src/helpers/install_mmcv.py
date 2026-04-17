import subprocess
import sys

print("Attempting to install mmcv...")

# Command to install mmcv-full from the specified wheel index
install_full_cmd = [
    sys.executable, '-m', 'mim', 'install', 'mmcv==2.1.0',
    '-f', 'https://download.openmmlab.com/mmcv/dist/cu118/torch2.1.0/index.html'
]

# Execute the command
rc = subprocess.call(install_full_cmd)

# If the installation failed, fall back to mmcv-lite
if rc != 0:
    print("Installation of mmcv failed. Falling back to mmcv-lite.")
    install_lite_cmd = [sys.executable, '-m', 'pip', 'install', 'mmcv-lite']
    subprocess.check_call(install_lite_cmd)
else:
    print("mmcv-full installed successfully.")
