## Decentralized Token Exchange on Raiden

1) please install raiden as stated in github.com/raiden-network/raiden/blob/master/docs/overview_and_guide.rst
2) `git clone https://github.com/brainbot-com/raidex.git`
3) `cd raidex`
4) Install with `python setup.py develop`.


###Getting started

The easiest way to test the functionality of raidex is achieved with a special command that mocks all 
the networking activity as well as the commitment-service in one process.
Additionally, different types of bots can be started, to introduce some trading activity.

```
raidex --mock-networking --api --bots liquidity random manipulator
```

After installing all dependecies (see `./webui/README.md`), the WebUI can than be started
with:
 
```
cd webui
ng serve
```