
<!-- PROJECT SHIELDS -->

<h2 align="center">
  <br/>
  <a href='https://raidex.io/'><img 
      width='600px' 
      alt='' 
      src="https://user-images.githubusercontent.com/35398162/59664605-a7aecb00-91b1-11e9-9d61-44adaf4db0a2.jpeg" /></a>
  <br/>
   raidEX Proof of Concept
  <br/>
</h2>




<h4 align="center">
   POC for a decentralized exchange built on Raiden state channel technology
</h4>


<p align="center">
  <a href="#getting-started">Getting Started</a> ∙
  <a href='#contact'>Contact</a>
</p>

<p align="center">
  <a href="https://gitter.im/raiden-network/raiden">
    <img src="https://badges.gitter.im/gitterHQ/gitter.png" alt="Gitter Raiden Badge">
  </a>
</p>

> **INFO** The current raidEX version is a work in progress proof-of-concept to show how a DEX could be built on top of Raiden. 

## Fixing the custodian issue

While there are already decentralized exchanges, they are built on the blockchain and inherit the performance restrictions of the global consensus systems, i.e. especially latency and limited transaction throughput. This results in a low liquidity for these exchanges. 

## High throughput & low latency

The mentioned performance restrictions are overcome by off-chain state technology, i.e. the Raiden Network for Ethereum. As raidEX is based on the Ethereum platform and the Raiden Network, it is fully interoperable and leverages synergies with tokens and apps in the Ethereum ecosystem.


## Table of Contents


## Architecture

// TODO: Adapt

### Architecture diagram



## Getting Started

### Learn about Raiden

If you didn't use Raiden before, you can

* Checkout the [developer portal](http://developer.raiden.network)
* Look at the [documentation](https://raiden-network.readthedocs.io/en/stable/index.html)
* Learn more by watching explanatory [videos](https://www.youtube.com/channel/UCoUP_hnjUddEvbxmtNCcApg)
* Read the blog posts on [Medium](https://medium.com/@raiden_network)

### Prerequisites

To run the code in this repository, you must
* [Install Raiden](https://raiden-network.readthedocs.io/en/stable/overview_and_guide.html)
* [Create an account, get some testnet ETH and tokens](https://github.com/raiden-network/workshop/)

## Installation

1) please install raiden as stated in github.com/raiden-network/raiden/blob/master/docs/overview_and_guide.rst
2) `git clone git@github.com:raiden-network/raidex.git`
3) `cd raidex`

It’s advised to create a virtualenv for Raidex (requires **python3.6**) and install all python dependencies there.

4) Install with `python setup.py develop`.

## Run


For the current version, seperate programs need to be run before starting raidex.


### Raiden

1) Run Raiden as described in https://raiden-network.readthedocs.io/en/stable/overview_and_guide.html#firing-it-up

Notes:
- Run Raiden with the same keystore file as your raidex node later on.

### Message Broker 

1) Open your raidex directory 
2) Run the Message Broker with `python raidex/message_broker/server.py`

Notes: 
- activate the virtual environment beforehand
 
 ### Commitment Service
 
If you want to run the Commitment Service by yourself.. 
1) Run Raiden with the same keystore file for the Commitment Service.
2) Start the Commitment Service with `python raidex/commitment_service/__main__.py --trader-port *PATH_TO_RAIDEN_NODE* --keyfile *PATH_TO_KEYFILE* --pwfile *PATH_TO_PASSWORD_FILE*`

If you do have a Commitment Service instance running, you can skip the above steps.

Notes:
- make sure you have an open raiden channel with the commitment service address. Top up the channel to be able to pay the fees.
- activate the virtual environment before running the step 2)

### Raidex

1) Start Raidex Node with `raidex --api --keyfile=*PATH_TO_KEYFILE* --pwfile=*PATH_TO_PASSWORD_FILE* --trader-port=*PORT_TO_RAIDEN_NODE*  --api-port=*RAIDEX_API_PORT*`

Notes:

- Run a Raiden instance with the same keystore
- Run the programs as stated above
- activate the virtual environment before starting raidex

### WebUI

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


## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Also have a look at the [raidEX Development Guide](./CONTRIBUTING.md) for more info.

## License

Distributed under the [MIT License](./LICENSE).

## Contact

Dev Chat: [Gitter](https://gitter.im/raiden-network/raiden)

Twitter: [@raiden_network](https://twitter.com/raiden_network)

Website: [Raiden Network](https://raiden.network/)

Mail: contact@raiden.network 

*The Raiden project is led by brainbot labs Est.*

> Disclaimer: Please note, that even though we do our best to ensure the quality and accuracy of the information provided, this publication may contain views and opinions, errors and omissions for which the content creator(s) and any represented organization cannot be held liable. The wording and concepts regarding financial terminology (e.g. “payments”, “checks”, “currency”, “transfer” [of value]) are exclusively used in an exemplary way to describe technological principles and do not necessarily conform to the real world or legal equivalents of these terms and concepts.



