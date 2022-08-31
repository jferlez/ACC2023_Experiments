#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd ..
git pull
cd "$SCRIPT_DIR"
matlab -r run_experiment
ssh 10.0.0.10 "mkdir -p /media/azuredata/minion25"
scp -r ~/acc23matlab/minion25 10.0.0.10:/media/azuredata/minion25
pwsh ~/shutdown_self.ps1
