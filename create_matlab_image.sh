#!/bin/bash

LIC="$1"

SYSTEM_TYPE=$(uname)
# Configure SHM size
if [ "$SYSTEM_TYPE" = "Darwin" ]; then
    ethif=en0
else
    ethif=eth0
fi

MAC="$(ifconfig $ethif | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}')"

docker create --mac-address "$MAC" -it --name matlab mathworks/matlab-deps:r2022a
docker start matlab
docker exec matlab sudo mkdir -p /opt/matlab/licenses
docker cp "$1" matlab:/opt/matlab/licenses
# docker exec matlab adduser --shell /bin/bash --disabled-password --gecos "" matlab && \
#     echo "matlab ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/matlab && \
#     chmod 0440 /etc/sudoers.d/matlab
# docker stop matlab
# docker start matlab
docker exec matlab sudo apt-get -y update
docker exec matlab sudo apt-get -y upgrade
docker exec matlab sudo apt-get -y install python3-pip python3.9 python3.9-dev cmake ssh git gfortran gfortran-10 gcc-10 clang-11 clang-12 vim emacs nano screen tmux ipython3 openssh-server sudo curl universal-ctags ripgrep psmisc locales clangd libpython3.9-dev

docker exec matlab sudo python3.9 -m pip install tensorflow tensorflow_probability onnx_tf onnxmltools

docker exec matlab wget -q "https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb"
docker exec matlab sudo dpkg -i packages-microsoft-prod.deb
docker exec matlab rm packages-microsoft-prod.deb
docker exec matlab sudo apt-get update
docker exec matlab sudo apt-get install -y powershell

docker exec matlab sh -c "wget https://www.mathworks.com/mpm/glnxa64/mpm && \
    chmod +x mpm && \
    sudo ./mpm install \
        --release=r2022a \
        --destination=/opt/matlab \
        --products MATLAB Computer_Vision_Toolbox Control_System_Toolbox Deep_Learning_Toolbox Image_Processing_Toolbox Optimization_Toolbox Parallel_Computing_Toolbox Symbolic_Math_Toolbox System_Identification_Toolbox Statistics_and_Machine_Learning_Toolbox && \
    sudo rm -f mpm /tmp/mathworks_root.log && \
    sudo ln -s /opt/matlab/bin/matlab /usr/local/bin/matlab"

docker commit matlab jferlez/matlab_docker:latest