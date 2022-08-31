#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd ..
git pull
cd "$SCRIPT_DIR"
matlab -r run_experiment
ssh 10.0.0.10 "mkdir -p /media/azuredata/minion39"
scp -r ~/acc23matlab/minion39 10.0.0.10:/media/azuredata/minion39
pwsh ~/shutdown_self.ps1
