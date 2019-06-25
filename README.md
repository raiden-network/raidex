
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

### Overview
raidEX consists of several components
- Commitment Service
- Message Broker (Order Book)
- raidEX nodes
- Raiden nodes

> Insert diagram

### Commitment Service (CS)

When two parties want to engage in a trade the commitment service guides the communication between them. When signing the agreement the CS acts as a notary. Finally, it settles the trade by revealing the secret to the HTLC of the parties' payments via the raiden network.

### Message Broker (Order Book)

The message broker is a simple sub/pub model to send messages around. A public broadcast acts as the order book. 

### raidEX nodes
The raidEX node is the core instance implementing the raidEX protocol. When necessary it communicates with its respective raiden node, triggering payments and acknowledging when payments have been received. On the other end it communicates to other raidex nodes or the commitment service via the message broker. 

### Raiden nodes
Every raidEX node need an underlying raiden node to transfer value. It is used to exchange assets via the raiden network or to pay fees to the commitment service.


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

### Installation

Clone the repository from Github

`git clone git@github.com:raiden-network/raidex.git`

`cd raidex`

Create a virtualenv for Raidex (requires **python3.6**) and install all python dependencies there.

```
python3.6 -m venv venv
source venv/bin/activate
```

Install with 
`python setup.py develop`.

### Run

For the current version Raiden, the Message Broker and the Commitment Service need to run before starting the raidex node. Currently the Raidex Node is configured to be used in Kovan Testnet.

#### Start the Message Broker 

In your raidex directory..

```
#Activate the virtual environment
source  venv/bin/activate

#Run the Message Broker with 
python raidex/message_broker/server.py
```

#### Start Raiden

Start Raiden as described in the [Raiden Installation Guide](https://raiden-network.readthedocs.io/en/stable/overview_and_guide.html#firing-it-up).

> **Info:** Run Raiden with the same keystore file as your raidex node later on.

If you want to run the commitment service by yourself, you need to start a second raiden node for the commitment service. Please see below.

#### Start the Commitment Service

> **Info:** Run the Commitment Service with the same keystore file as Raiden

Run a Raiden Node for the commitment service as described above. Choose a different port and keystore for the commitment service.

Start the Commitment Service 

```
# go to raidex directory
cd raidex

# activate virtual environment
source venv/bin/activate

# run the commitment service
python raidex/commitment_service/__main__.py --trader-port *PATH_TO_RAIDEN_NODE* --keyfile *PATH_TO_KEYFILE* --pwfile *PATH_TO_PASSWORD_FILE*`
```

#### Create Raiden Channels to the Commitment Service

In order to be able to pay the fees to the Commitment Service a Raiden Channel from the user's node to the CS Node must be created and topped up. A convinient way to create channels is via accessing the Raiden WebUI (Default: http://localhost:5001). Currently fees are being payed in Raiden Testnet Token (RTT) (Please see General Notes).

Open a channel and deposit RTT as describen in https://raiden-network.readthedocs.io/en/stable/webui_tutorial.html


#### Start Raidex

After running the Raiden Node, the message broker and the commitment service you are good to go to start the raidex node. 

```
# go to raidex directory
cd raidex

# activate virtual environment
source venv/bin/activate

# start the Raidex Node
raidex --api --keyfile=*PATH_TO_KEYFILE* --pwfile=*PATH_TO_PASSWORD_FILE* --trader-port=*PORT_TO_RAIDEN_NODE*  --api-port=*RAIDEX_API_PORT*
```

#### Access the WebUI

> Remark: It is already included in Raiden (can we remove it?)

After installing all dependecies (see `./webui/README.md`), the WebUI can then be started
with:
 
```
cd webui
ng serve
```

Start the WebUI as described in the [Web Application Tutorial](https://raiden-network.readthedocs.io/en/stable/webui_tutorial.html)

### General Notes

The Raidex Project is currently configured to be used on the Kovan Testnet. It is recommended to test and play around there.

If you do not have Kovan Ether (KETH) you can get them here https://faucet.kovan.network/
To get Wrapped Eth (WETH) send the wished amount of KETH to the WETH contract address (see below)


Currently raidex supports the use of one trading pair. The default trading pair is set to be WETH and Raiden Testnet Token (RTT) on Kovan Testnet
- WETH Contract Address: `0xd0A1E359811322d97991E03f863a0C30C2cF029C`  
- RTT Contract Address: `0x92276aD441CA1F3d8942d614a6c3c87592dd30bb`
If you do want to use other trading pairs (not recommended yet) change the addresses in `*RAIDEX_DIR*/raidex/constants.py`

Fees to the commitment service are paid in Raiden Testnet Token (RTT) which can be minted. > link to how to mint token?



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



