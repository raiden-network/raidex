import { throwError as observableThrowError, Observable, timer } from 'rxjs';
import { delay, mergeMap, retryWhen, map, catchError } from 'rxjs/operators';
import { Injectable } from '@angular/core';
import { Order } from '../model/order';
import { Trade } from '../model/trade';
import { PriceBin } from '../model/pricebin';
import { Offer } from '../model/offer';
import { Channel } from '../model/channel'
import * as format from '../utils/format';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { ApiResponse, OffersData, OrderResponse, ChannelResponse } from '../model/responses';

@Injectable()
export class RaidexService {

    constructor(private http: HttpClient) {

    }

    api = '/raidex/api/v01';

    private static handleError(error: Response | any) {
        let errMsg: string;
        if (error instanceof Response) {
            const body = error.json() || '';
            const err = body['error'] || JSON.stringify(body);
            errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
        } else {
            errMsg = error.message ? error.message : error.toString();
        }
        console.error(errMsg);
        return observableThrowError(errMsg);
    }

    public getNewTrades(chunk_size: number): Observable<Array<Trade>> {
        return timer(0, 1000).pipe(
            mergeMap(() => {
                const params: HttpParams = new HttpParams().set('chunk_size', chunk_size.toString());
                const resp = this.http.get<ApiResponse<Array<Trade>>>(`${this.api}/markets/dummy/trades`, {params: params});
                return resp.pipe(map((response) => {
                    const data = response.data;
                    return data.map((elem) => {
                            return new Trade(
                                elem.timestamp,
                                format.formatCurrency(elem.amount, 18, 1),
                                format.formatCurrency(elem.price, 18, 4),
                                elem.type,
                            );
                        }
                    );
                }));
            }), retryWhen((errors) => this.printErrorAndRetry('Could not get OrderHistory', errors)));
    }

    public getPriceChart(nof_buckets: number, interval: number): Observable<Array<PriceBin>> {
        return timer(0, 10000).pipe(
            mergeMap(() => {
                const params: HttpParams = new HttpParams()
                    .set('nof_buckets', (nof_buckets).toString())
                    .set('interval', (interval).toString());

                return this.http.get<ApiResponse<Array<PriceBin>>>(`${this.api}/markets/dummy/trades/price-chart`, {params: params}).pipe(
                    map((response) => {
                        const data = response.data;
                        return data.map((elem) => {
                                return new PriceBin(
                                    elem.timestamp,
                                    format.formatCurrency(elem.amount),
                                    format.formatCurrency(elem.open),
                                    format.formatCurrency(elem.close),
                                    format.formatCurrency(elem.max),
                                    format.formatCurrency(elem.min),
                                );
                            }
                        );
                    }));
            }), retryWhen((errors) => this.printErrorAndRetry('Could not get PriceChart', errors)));
    }

    public getOffers(): Observable<any> {
        return timer(0, 1000).pipe(
            mergeMap(() => this.http.get<ApiResponse<OffersData>>(`${this.api}/markets/dummy/offers`).pipe(
                map((response) => {
                    const data = response.data;
                    const buys = data.buys;
                    const sells = data.sells;
                    return {
                        buys: buys.map((elem) =>
                            new Offer(
                                format.formatCurrency(elem.amount),
                                format.formatCurrency(elem.price)
                            )),
                        sells: sells.map((elem) =>
                            new Offer(
                                format.formatCurrency(elem.amount),
                                format.formatCurrency(elem.price)
                            ))
                    };
                }))),
            retryWhen((errors) => this.printErrorAndRetry('Could not get OrderBook', errors)));
    }

    public submitLimitOrder(limitOrder: Order): Observable<number> {
        const data = {
            'type': limitOrder.type,
            'amount': format.parseCurrency(limitOrder.amount),
            'base_token': '0xA0195E88F732ff6379642eB702302dFae6EA7bC4',
            'price': format.parseCurrency(limitOrder.price, 18-3)
        };
        const options = new HttpHeaders().set('Content-Type', 'application/json');
        return this.http.post<ApiResponse<number>>(`${this.api}/markets/dummy/orders/limit`, data, {headers: options}).pipe(
            map((response) => response.data), catchError(RaidexService.handleError)
        );
    }

    public getLimitOrders() {
        return timer(0, 500).pipe(
            mergeMap(() => this.http.get<ApiResponse<Array<OrderResponse>>>(`${this.api}/markets/dummy/orders/limit`).pipe(
                map((response) => {
                    const data = response.data;

                    return data.map((elem) => new Order(
                        elem.type,
                        format.formatCurrency(elem.amount),
                        format.formatCurrency(elem.price),
                        elem.order_id,
                        format.formatCurrency(elem.filledAmount),
                        elem.open,
                        elem.canceled
                    ));
                }))),
            retryWhen((errors) => this.printErrorAndRetry('Could not get Limitorders', errors)));
    }

    public cancelLimitOrders(limitOrder: Order): Observable<number> {
        return this.http.delete<ApiResponse<number>>(`${this.api}/markets/dummy/orders/limit/${limitOrder.id}`).pipe(
            map((response) => response.data),
            catchError(RaidexService.handleError)
        );
    }

    private printErrorAndRetry(message: string, errors: Observable<any>): Observable<any> {
        return errors.pipe(
            map((error) => console.error(message + (error.message || error))),
            delay(20000)
        );
    }

    public getChannels() {
        return timer(0, 500).pipe(
            mergeMap(() => this.http.get<ApiResponse<Array<ChannelResponse>>>(`${this.api}/markets/dummy/channels`).pipe(
                map((response) => {
                    const data = response.data;

                    return data.map((elem) => new Channel(
                        elem.partner_address,
                        elem.token_address,
                        elem.total_deposit
                    ));
                }))),
            retryWhen((errors) => this.printErrorAndRetry('Could not get Channels', errors)));
    }

    public makeChannelAndDeposit(address: string, token_address: string, deposit: number): Observable<boolean> {
        const data = {
            'partner_address': address,
            'token_address': '0x92276aD441CA1F3d8942d614a6c3c87592dd30bb',
            'deposit': deposit,
        };
        const options = new HttpHeaders().set('Content-Type', 'application/json');
        return this.http.post<ApiResponse<boolean>>(`${this.api}/markets/dummy/channels`, data, {headers: options}).pipe(
            map((response) => response.data), catchError(RaidexService.handleError)
        );
    }

}
