import logging
import os
import random
from re import sub
from time import time
from typing import Optional

from dotenv import load_dotenv
import requests
from substrateinterface import SubstrateInterface

RESTART_SENTINEL = "/tmp/collator-check-blocks"

class Checker:

    last_id: int
    collator_address: Optional[str]
    substrate: SubstrateInterface
    jsonrpc_url: str
    restart_sentinel_file: str
    restart_offset: int

    def __init__(self, collator_address: Optional[str] = None):
        self.last_id = random.randint(1, 65536)
        self.collator_address = collator_address or os.getenv('COLLATOR_ADDRESS');
        try:
            self.substrate = SubstrateInterface(url=os.getenv('COLLATOR_WS_URL', "ws://127.0.0.1:9944"))
        except:
            self.substrate = None
        self.jsonrpc_url = os.getenv('COLLATOR_JSONRPC_URL', 'http://127.0.0.1:9933')
        self.restart_sentinel_file = os.getenv('COLLATOR_RESTART_SENTINEL', RESTART_SENTINEL)
        self.restart_offset = int(os.getenv('COLLATOR_RESTART_OFFSET', 30 * 60))
        self.restart_command = os.getenv('COLLATOR_RESTART_COMMAND', 'systemctl restart astar.service')

    def run_check(self):
        if self.substrate is None:
            logging.warning("Collator not (yet) running")
            return
        highest_block = 0
        blocks = self.rpc("system_syncState")
        highest_block = blocks['highestBlock']
        if not self.supports_collator_selection():
            return
        last_block = self.get_last_authored_block()
        block_delta = highest_block - last_block
        fail_threshold = os.getenv("COLLATOR_BLOCK_DELTA_FAIL_THRESHOLD", None)

        should_restart = False
        logging.info(f"Collator is {block_delta} blocks behind")
        if fail_threshold is not None and block_delta > int(fail_threshold):
            logging.warning("Considering restart")
            should_restart = True
            if os.path.exists(self.restart_sentinel_file):
                with open(self.restart_sentinel_file, "r") as f:
                    last_restart = int(f.readline())
                    current_time = int(time())
                    if ((current_time - last_restart) <= self.restart_offset):
                        should_restart = False
                        logging.info("Not running long enough")
        if should_restart:
            self.issue_restart()

    def issue_restart(self):
        logging.error("Restarting")
        with open(self.restart_sentinel_file, "w") as f:
            f.write(str(int(time())));
        os.system(self.restart_command)

        
    def supports_collator_selection(self) -> bool:
        metadata = list(self.substrate.get_metadata().value[1].values())[0]
        pallet_names = [x['name'] for x in metadata['pallets']]
        return 'CollatorSelection' in pallet_names
    
    def get_last_authored_block(self) -> int:
        return self.substrate.query("CollatorSelection", "LastAuthoredBlock", [self.collator_address]).value


    def rpc(self, method: str, params: Optional[list] = None):
        response = requests.post(self.jsonrpc_url, json={
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": self.get_id()
        })
        data = response.json()
        if 'error' in data:
            raise Exception(data['error']['message'])
        return data['result']

    def get_id(self) -> int:
        id = self.last_id
        self.last_id = id + 1
        return id

if __name__ == '__main__':
    load_dotenv("/etc/default/collator-check-blocks")
    logging.basicConfig(
        filename=os.getenv("COLLATOR_LOG_FILE", "/var/log/collator-check-blocks.log"),
        level=logging.INFO,
        format='%(asctime)s %(levelname)s:%(message)s'
        )
    Checker().run_check()
