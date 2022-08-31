#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd ..
git pull
cd "$SCRIPT_DIR"
matlab -r run_experiment
ssh 10.0.0.10 "mkdir -p /media/azuredata/minion26"
scp ~/acc_code/minion26 10.0.0.10:/media/azuredata/minion26
pwsh ~/shutdown_self.ps1
