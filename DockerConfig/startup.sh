#!/bin/bash
USER=$1
INTERACTIVE=$2
SERVER=$3
CORES=$4
PORTNUM=$5
MPIHOSTS=$6
MPIARGS="$7"
/usr/sbin/sshd -D &> /root/sshd_log.out &
if [ ! -d /home/$USER/.ssh ]
then
    sudo -u $USER mkdir /home/$USER/.ssh
fi
if [ -e /etc/ssh/ssh_host_rsa_key.pub ]; then
	echo "
****** SSH host key ******"
	cat /etc/ssh/ssh_host_rsa_key.pub
	echo "**************************
"
    sudo -u $USER mkdir -p /home/$USER/results/ssh_keys
    sudo -u $USER chown -R $USER:$USER /home/$USER/results/ssh_keys
    sudo -u $USER cp /etc/ssh/ssh_host_rsa_key.pub /home/$USER/results/ssh_keys
    HOSTKEY=`cat /etc/ssh/ssh_host_rsa_key.pub`
    sudo -u $USER sh -c "echo \"*:$PORTNUM $HOSTKEY\" > /home/$USER/.ssh/known_hosts"
fi
if [ -e /home/$USER/.ssh/id_rsa.pub ]; then
	echo "
****** SSH public key for user $USER ******"
    cat /home/$USER/.ssh/id_rsa.pub
    echo "***************************************
"
    sudo -u $USER mkdir -p /home/$USER/results/ssh_keys
    sudo -u $USER chown -R $USER:$USER /home/$USER/results/ssh_keys
    sudo -u $USER cp /home/$USER/.ssh/id_rsa.pub /home/$USER/results/ssh_keys/id_rsa_${USER}.pub
    sudo -u $USER sh -c "cat /home/$USER/.ssh/id_rsa.pub > /home/$USER/.ssh/authorized_keys"
fi

# Setup authorized_keys/known_hosts
for fname in authorized_keys known_hosts; do
    if [ -e /home/$USER/results/$fname ]
    then
        sudo -u $USER sh -c "cat /home/$USER/results/$fname >> /home/$USER/.ssh/${fname}_base"
        rm /home/$USER/results/$fname
    fi
    if [ -e /home/$USER/.ssh/${fname}_base ]
    then
        sudo -u $USER sh -c "cat /home/$USER/.ssh/${fname}_base >> /home/$USER/.ssh/${fname}"
    fi
    if [ -e /home/$USER/.ssh/${fname} ]
    then
        chmod 600 /home/$USER/.ssh/${fname} && chown $USER:$USER /home/$USER/.ssh/${fname}
    fi
done

#PYPATH="/home/$USER/tools/FastBATLLNN:/home/$USER/tools/FastBATLLNN/HyperplaneRegionEnum:/home/$USER/tools/FastBATLLNN/TLLnet:/home/$USER/tools/nnenum/src/nnenum"

if [ "$MPIHOSTS" != "" ]; then
    echo "$MPIHOSTS" | sed -e 's/,/\
/g' -e 's/:/    /g' >> /etc/hosts
    echo '#!/bin/bash' > /home/$USER/run_all.sh
    for vm in `echo "$MPIHOSTS" | sed -e 's/,/\n/g'`; do
        IFS=':' read -r -a array <<< "$vm"
        ip="${array[0]}"
        hostN="${array[1]}"
        echo "ssh -p 3000 $ip \"cd ~/acc23matlab/$hostN && bk ~/acc23matlab/$hostN/run_experiment.sh\"" >> /home/$USER/run_all.sh
        echo "sleep 2" >> /home/$USER/run_all.sh
    done
    chmod 755 /home/$USER/run_all.sh
fi

if [ "$SERVER" = "server" ]; then
	sudo -u $USER /usr/local/bin/charming /home/$USER/tools/FastBATLLNN/FastBATLLNNServer.py &> "/home/$USER/results/FastBATLLNN_server_log.out" &
fi
if [ "$INTERACTIVE" = "-d" ]; then
	wait -n
else
	sudo -u $USER /bin/bash
	killall sshd
fi
