# Dockerfile
FROM pytorch/pytorch:2.1.2-cuda11.8-cudnn8-devel

ARG DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND=${DEBIAN_FRONTEND} TZ=Etc/UTC
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=$CUDA_HOME/bin:$PATH
ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
ENV TORCH_CUDA_ARCH_LIST=9.0

# --- Install System Dependencies ---
RUN apt-get update && \
    echo "tzdata tzdata/Areas select Etc" | debconf-set-selections && \
    echo "tzdata tzdata/Zones/Etc select UTC" | debconf-set-selections && \
    apt-get install -y --no-install-recommends \
      build-essential python3-dev git libgl1-mesa-glx libglib2.0-0 ffmpeg curl tzdata imagemagick && \
    rm -rf /var/lib/apt/lists/*
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml

# --- Install CUB Dependency ---
RUN curl -LO https://github.com/NVIDIA/cub/archive/1.10.0.tar.gz && \
    tar xzf 1.10.0.tar.gz && rm 1.10.0.tar.gz
ENV CUB_HOME=/workspace/cub-1.10.0

# --- Install Python Dependencies ---
RUN python3 -m pip install --upgrade pip setuptools wheel
RUN python3 -m pip install "protobuf==3.20.3"
RUN python3 -m pip install \
    tensorboard==2.13.0 pyspy==0.1.1 scipy==1.9.1 kornia==0.5.0 trimesh==3.22.0 \
    torchshow==0.5.1 imageio==2.31.1 imageio-ffmpeg==0.4.8 av==10.0.0 scikit-image==0.21.0 \
    moviepy==1.0.3 scikit-learn==1.3.0 lpips==0.1.4 timm==0.9.2 transformers==4.33.2 \
    pretrainedmodels==0.7.4 faiss-cpu==1.7.4 librosa==0.9.2 praat-parselmouth==0.4.3 \
    webrtcvad pyloudnorm pyworld-prebuilt pypinyin==0.42.0 ninja==1.11.1 gateloop-transformer \
    beartype==0.16.4 attr torchode==0.2.0 torchdiffeq==0.2.3 hydra-core==1.3.2 pandas==2.1.3 \
    pytorch-lightning==2.1.2 httpx==0.23.3 gradio==4.16.0 mediapipe==0.10.7 \
    gdown fvcore iopath openmim==0.3.9 einops \
    git+https://github.com/linto-ai/whisper-timestamped.git
RUN python3 -m pip install "huggingface_hub[hf_transfer]"
ENV HF_HUB_ENABLE_HF_TRANSFER=1

# --- Run Custom Installation and Patching Scripts ---
COPY src/helper/patch_torchshow.py /tmp/patch_torchshow.py
RUN python3 /tmp/patch_torchshow.py
COPY src/helper/install_mmcv.py /tmp/install_mmcv.py
RUN python3 /tmp/install_mmcv.py
COPY src/helper/install_pytorch3d.py /tmp/install_pytorch3d.py
RUN python3 /tmp/install_pytorch3d.py

# --- Pre-bake Models ---
COPY src/helper/download_models.py /tmp/download_models.py
RUN python3 /tmp/download_models.py

# --- Set Final Workdir ---
WORKDIR /workspace