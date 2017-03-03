## root of the api
everything in this api should be under
`/api/<version>/`
where <version> is the version number

## market
everything has to happen on a certain market
all following endpoints will be under
`markets/<market>/`
we need to aggree on how to do that, so lets skip it for now

### get_offer_book()
`(GET) offers/`
(before get_order_book)

returns: buys and sells

```
{
  data: {
          buys: offer[]
          sells: offer[]
        }
}
```
where offer is (to be extended)
```
{
  "amount": int,
  "price": double
}
```

### get_trade_history()
`(GET) trades/`

returns the list of trades that happend

```
{
  data: trade[]
}
```
where trade is (to be extended)
```
{
  "timestamp": int,
  "amount":int,
  "price": double
}
```
### make_limit_order()
`(POST) orders/limit`

creates a new order to buy or sell tokens
returns the id of this order
```
{
  data: int
}
```

parameters:
- type: BUY or SELL
- amount: amount of tokens
- price: the price limit

```
{
  type: string
  amount: int
  price: double
}
```
## errors
if an error occurs the code will be
`400` for a malformed request
`500` if there was a server error
`404` if the resource was not found

the error object looks like this
```
{
  'status': int,
  'message': string
}
```
maybe extend that with an application error_code
