import { throwError as observableThrowError, Observable, timer } from 'rxjs';
import { delay, mergeMap, retryWhen, map, catchError } from 'rxjs/operators';
import { Injectable } from '@angular/core';
import { Order } from '../model/order';
import { Trade } from '../model/trade';
import { PriceBin } from '../model/pricebin';
import { Offer } from '../model/offer';
import * as format from '../utils/format';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { ApiResponse, OffersData, OrderResponse } from '../model/responses';

@Injectable()
export class RaidexService {

    constructor(private http: HttpClient) {

    }

    api = 'http://127.0.0.1:50001/api/v01';

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
                                format.formatCurrency(elem.price, 2, 4),
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
                                    format.formatCurrency(elem.open, 2),
                                    format.formatCurrency(elem.close, 2),
                                    format.formatCurrency(elem.max, 2),
                                    format.formatCurrency(elem.min, 2),
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
                                format.formatCurrency(elem.price, 2)
                            )),
                        sells: sells.map((elem) =>
                            new Offer(
                                format.formatCurrency(elem.amount),
                                format.formatCurrency(elem.price, 2)
                            ))
                    };
                }))),
            retryWhen((errors) => this.printErrorAndRetry('Could not get OrderBook', errors)));
    }

    public submitLimitOrder(limitOrder: Order): Observable<number> {
        const data = {
            'type': limitOrder.type,
            'amount': format.parseCurrency(limitOrder.amount),
            'price': format.parseCurrency(limitOrder.price, 2)
        };
        const options = new HttpHeaders().set('Content-Type', 'application/json');
        return this.http.post<ApiResponse<number>>(`${this.api}/markets/dummy/orders/limit`, data, {headers: options}).pipe(
            map((response) => response.data), catchError(RaidexService.handleError)
        );
    }

    public getLimitOrders() {
        return timer(0, 1000).pipe(
            mergeMap(() => this.http.get<ApiResponse<Array<OrderResponse>>>(`${this.api}/markets/dummy/orders/limit`).pipe(
                map((response) => {
                    const data = response.data;
                    return data.map((elem) => new Order(
                        elem.type,
                        format.formatCurrency(elem.amount),
                        format.formatCurrency(elem.price, 2),
                        elem.order_id,
                        format.formatCurrency(elem.filledAmount),
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

}
