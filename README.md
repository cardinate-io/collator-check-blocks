# Astar/Shiden Collator Block Check Script

This scripts interrogates an Astar/Shiden collator for the last block it has successfully built
and restarts it if it is trailing behind the head of the chain too far.

## Installation

### Requirements 

* Python3
* pip
* virtualenv

On Debian/Ubuntu based systems the following should be enough to get those:

```sh
sudo apt-get install -qy python3-pip python3-virtualenv
```

### Install the script

```sh
set -eu
git clone https://github.com/cardinate-io/collator-check-blocks.git
cd collator-check-blocks
sudo python3 -m venv /usr/local/lib/collator-check-blocks
sudo /usr/local/lib/collator-check-blocks/bin/pip -r requirements.txt
sudo cp collator-check-blocks.py /usr/local/lib/collator-check-blocks/bin/
echo "COLLATOR_ADDRESS=$YOUR_COLLATOR_WALLET_ADDRESS" | sudo tee /etc/default/collator-check-blocks
echo "*/5 * * * * root /usr/local/lib/collator-check-blocks/bin/python /usr/local/lib/collator-check-blocks/bin//collator-check-blocks.py >/dev/null 2>&1" | sudo tee /etc/cron.d/collator-check-blocks
```

This installs the script and its Python dependencies into a virtualenv and creates a cron job
that runs every 5 minutes. Make sure to substitute `$YOUR_COLLATOR_WALLET_ADDRESS` with the
on-chain account of the collator.


## Configuration

The script can be configured through environment variables or through an env file at `/etc/default/collator-check-blocks`. The following settings are available. Usually, it should be
sufficient to specify `COLLATOR_ADDRESS` (and potentially tweak `COLLATOR_BLOCK_DELTA_FAIL_THRESHOLD`)


| variable | meaning | default |
|----------|---------|---------|
| `COLLATOR_ADDRESS` | On chain address of the collator wallet | | 
| `COLLATOR_WS_URL`  | WS URL where the collator can be reached | `ws://127.0.0.1:9944` |
| `COLLATOR_JSONRPC_URL` | JSON-RPC URL where the collator can be reached | `ws://127.0.0.1:9933` |
| `COLLATOR_RESTART_OFFSET` | Amount of seconds to wait between collator restarts | 1,800 |
| `COLLATOR_RESTART_COMMAND` | The command to run in a subshell in order to restart the collator. The calling process needs to have sufficient privileges | `systemctl restart astar.service` |
| `COLLATOR_RESTART_SENTINEL` | The script will write the last restart time to the file named here | `/tmp/collator-check-blocks` |
| `COLLATOR_LOG_FILE` | The file where the script will write logs to | `/var/log/collator-check-blocks.log` |
| `COLLATOR_BLOCK_DELTA_FAIL_THRESHOLD` | The number of blocks that the last block built by the collator is allowed to fall behind the head of the chain | 150 |