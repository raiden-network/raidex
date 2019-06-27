
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

> **INFO** The current raidEX version is a work in progress proof-of-concept to investigate how a DEX could be built on top of Raiden. 

## Fixing the custodian issue

While there are already decentralized exchanges, they are built on the blockchain and inherit the performance restrictions of the global consensus systems, i.e. especially latency and limited transaction throughput. This results in a low liquidity for these exchanges. 

## High throughput & low latency

The mentioned performance restrictions are overcome by off-chain state technology, i.e. the Raiden Network for Ethereum. As raidEX is based on the Ethereum platform and the Raiden Network, it is fully interoperable and leverages synergies with tokens and apps in the Ethereum ecosystem.

## Table of Contents
- [How the raidEX protocol works](#how-the-raidex-protocol-works)
- [Architecture](#architecture)
  * [Overview](#overview)
  * [Commitment Service](#commitment-service)
  * [Order Book](#order-book)
  * [raidEX nodes](#raidex-nodes)
  * [Raiden nodes](#raiden-nodes)
  * [Message Broker](#message-broker)
- [Getting Started](#getting-started)
  * [Learn about Raiden](#learn-about-raiden)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
  * [Run](#run)
    + [Start the Message Broker](#start-the-message-broker)
    + [Start Raiden](#start-raiden)
    + [Start the Commitment Service](#start-the-commitment-service)
    + [Create Raiden Channels to the Commitment Service](#create-raiden-channels-to-the-commitment-service)
    + [Start raidEX](#start-raidex)
    + [Access the raidEX WebUI](#access-the-raidex-webui)
    + [Access the Raiden WebUI](#access-the-raiden-webui)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## How the raidEX protocol works

A high level introduction to the raidEX protocol can be found in [the following issue](https://github.com/raiden-network/raidex/issues/82).

## Architecture

### Overview
raidEX consists of several components
- Commitment Service
- Order Book
- raidEX nodes
- Raiden nodes
- Message Broker

<h2 align="center">
  <br/>
  <img 
      width='600px' 
      alt='raidEX architecture' 
      src="https://user-images.githubusercontent.com/35398162/60109644-06081a80-976b-11e9-9042-87e1ec8909f9.png" />
</h2>

### Commitment Service

When two parties want to engage in a trade the commitment service synchronizes the communication between them from the order creation until the settlement of a trade.

It is a trusted third party depository where traders provide a security that they are intending to engage in an exchange. On misbehavior this deposit could get slashed by the commitment service. 

It acts as a notary upon commitment signing and settles the trade eventually by revealing the secret to the HTLC of the parties' payments via the raiden network.  

In the happy case the commitment service returns the deposits minus a little fee for the service.  

The intended goal is to reduce as much influence as possible from the commitment service. In the end it should only synchronize the communication and penalize on misbehavior.  

### Order Book

Each raidEX node builds its own decentralized order book. It receives and publishes new orders from/to a public broadcast channel distributed via the message broker.

### raidEX nodes
The raidEX node is the core instance implementing the raidEX protocol. It communicates with its respective raiden node, triggering payments and acknowledging when payments have been received. On the other end it communicates to other raidEX nodes or the commitment service via the message broker. 

### Raiden nodes
Every raidEX node as well as the commitment service need an underlying raiden node to transfer value. It is used to exchange assets via the raiden network or to deposit to the commitment service.

### Message Broker

The message broker is a simple sub/pub model to exchange messages. raidEX nodes communicate via the message broker with the commitment service and to other raidEX nodes. It also reads and writes to/from the order book broadcast.

## Getting Started

### Learn about Raiden

Raiden is the base layer of the raidEX protocol.

If you didn't use Raiden before, you can

* Checkout the [developer portal](http://developer.raiden.network)
* Look at the [documentation](https://raiden-network.readthedocs.io/en/stable/index.html)
* Learn more by watching explanatory [videos](https://www.youtube.com/channel/UCoUP_hnjUddEvbxmtNCcApg)
* Read the blog posts on [Medium](https://medium.com/@raiden_network)

### Prerequisites

To run the code in this repository, you need to 
* [Install Raiden](https://raiden-network.readthedocs.io/en/stable/overview_and_guide.html)

The raidEX project is currently configured to be used on the Kovan Testnet.

To run Raiden on Kovan, you need to

* Get Kovan Ether (KETH) on the following [Kovan Faucet](https://faucet.kovan.network/).

* Send KETH to the WETH contract address (`0xd0A1E359811322d97991E03f863a0C30C2cF029C`) to get Wrapped Eth (WETH)

Currently raidEX supports one trading pair. The default trading pair is set to be WETH and Raiden Testnet Token (RTT) on the Kovan Testnet:
- WETH Contract Address: `0xd0A1E359811322d97991E03f863a0C30C2cF029C`  
- RTT Contract Address: `0x92276aD441CA1F3d8942d614a6c3c87592dd30bb`

Fees to the commitment service are paid in Raiden Testnet Token (RTT) which can be minted. You can adapt the [following utility](https://github.com/raiden-network/raiden-contracts/blob/master/raiden_contracts/utils/mint_tokens.py) to mint RTTs.

### Installation

Clone the repository from Github

```
git clone git@github.com:raiden-network/raidex.git`
```

Create a virtualenv for raidEX (requires **python3.6**) and install all python dependencies there.

```
# go to the raidex directory
cd raidex

# create virtual environment
python3.6 -m venv venv

#activate virtual environment
source venv/bin/activate
```

Install with 
```
python setup.py develop
```

### Run

For the current version, Raiden, the Message Broker and the Commitment Service need to run before starting the raidEX node. Currently the raidEX Node is configured to be used in Kovan Testnet.

> **Info:** In order to have a full trading experience it is necessary to run at least two raidEX nodes (traders). Each node relies on its own raiden node instance. Also the commitment service needs its own raiden node running. Please make sure to use different port settings for all instances and use unique keystores for every raidEX node including the commitment service.

#### Start the Message Broker 

```
# go to the raidex directory
cd raidex

#Activate the virtual environment
source  venv/bin/activate

#Run the Message Broker with 
python raidex/message_broker/server.py
```

#### Start Raiden

Start Raiden as described in the [Raiden Installation Guide](https://raiden-network.readthedocs.io/en/stable/overview_and_guide.html#firing-it-up).

> **Info:** Run Raiden with the same keystore file as your corresponding raidEX node later on.

If you want to run the commitment service by yourself, you need to start a new Raiden Node for the commitment service.

#### Start the Commitment Service

> **Info:** Run the Commitment Service with the same keystore file as the corresponding Raiden Node.

Run a Raiden Node for the commitment service as described above. Choose a different port and keystore for the commitment service.

Start the Commitment Service 

```
# go to the raidex directory
cd raidex

# activate the virtual environment
source venv/bin/activate

# run the commitment service
python raidex/commitment_service/__main__.py --trader-port *PATH_TO_RAIDEN_NODE* --keyfile *PATH_TO_KEYFILE* --pwfile *PATH_TO_PASSWORD_FILE*`
```

#### Create Raiden Channels to the Commitment Service

In order to be able to pay the fees to the Commitment Service a Raiden Channel from the user's node to the commitment service node must be created and topped up. A convinient way to create channels is using the Raiden WebUI (by default http://localhost:5001). Currently fees are getting payed in Raiden Testnet Token (RTT).

Open a channel to the CS and deposit RTT as described in [Raiden WebUI Tutorial](https://raiden-network.readthedocs.io/en/stable/webui_tutorial.html)

#### Start raidEX

After running the Raiden Node, the message broker and the commitment service you can start the raidEX Node. 

```
# go to the raidex directory
cd raidex

# activate virtual environment
source venv/bin/activate

# start the Raidex Node
raidex --api --keyfile=*PATH_TO_KEYFILE* --pwfile=*PATH_TO_PASSWORD_FILE* --trader-port=*PORT_TO_RAIDEN_NODE*  --api-port=*RAIDEX_API_PORT*
```

#### Access the raidEX WebUI

Install all dependecies (see `./webui/README.md`) of the raidEX WebUI.

Start the raidEX WebUI.
 
```
cd webui
ng serve
```

#### Access the Raiden WebUI

Start the WebUI as described in the [Web Application Tutorial](https://raiden-network.readthedocs.io/en/stable/webui_tutorial.html)


## Testing
For testing please use pytest

```
# go to the raidex directory
cd raidex

# activate virtual environment
source venv/bin/activate

# run tests
pytest raidex/tests/
```

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
