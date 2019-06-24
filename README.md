## Decentralized Token Exchange on Raiden

1) please install raiden as stated in github.com/raiden-network/raiden/blob/master/docs/overview_and_guide.rst
2) `git clone git@github.com:raiden-network/raidex.git`
3) `cd raidex`

It’s advised to create a virtualenv for Raidex (requires **python3.6**) and install all python dependencies there.

4) Install with `python setup.py develop`.


### Getting started

For the current version, seperate programs need to be run before starting raidex.


**Raiden**

1) Run Raiden as described in https://raiden-network.readthedocs.io/en/stable/overview_and_guide.html#firing-it-up

Notes:
- Run Raiden with the same keystore file as your raidex node later on.

**Message Broker** 

1) Open your raidex directory 
2) Run the Message Broker with `python raidex/message_broker/server.py`

Notes: 
- activate the virtual environment beforehand
 
 **Commitment Service**

If you want to run the Commitment Service by yourself.. 
1) Run Raiden with the same keystore file for the Commitment Service.
2) Start the Commitment Service with `python raidex/commitment_service/__main__.py --trader-port *PATH_TO_RAIDEN_NODE* --keyfile *PATH_TO_KEYFILE* --pwfile *PATH_TO_PASSWORD_FILE*`

If you do have a Commitment Service instance running, you can skip the above steps.

Notes:
- make sure you have an open raiden channel with the commitment service address. Top up the channel to be able to pay the fees.
- activate the virtual environment before running the step 2)

**Raidex**

1) Start Raidex Node with `raidex --api --keyfile=*PATH_TO_KEYFILE* --pwfile=*PATH_TO_PASSWORD_FILE* --trader-port=*PORT_TO_RAIDEN_NODE*  --api-port=*RAIDEX_API_PORT*`

Notes:

- Run a Raiden instance with the same keystore
- Run the programs as stated above
- activate the virtual environment before starting raidex

**WebUI**

After installing all dependecies (see `./webui/README.md`), the WebUI can then be started
with:
 
```
cd webui
ng serve
```


### General Notes

- Currently only 1 trading pair is supported. The default trading pair is set to be WETH and Raiden Testnet Token (RTT) on Kovan Testnet.  
WETH Contract Address: `0xd0A1E359811322d97991E03f863a0C30C2cF029C`  
RTT Contract Address: `0x92276aD441CA1F3d8942d614a6c3c87592dd30bb`  
If you do want to use other trading pairs (not recommended yet) change the addresses in `*RAIDEX_DIR*/raidex/constants.py`
