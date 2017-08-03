import { Injectable } from '@angular/core';
import { Http, Headers, RequestOptions, Response } from '@angular/http';
import { Observable } from 'rxjs/Observable';
import { TimerObservable} from 'rxjs/observable/TimerObservable';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';
import 'rxjs/add/observable/throw';
import 'rxjs/add/operator/catch';
import 'rxjs/add/operator/retryWhen';
import 'rxjs/add/operator/delay';
import 'rxjs/add/operator/mergeMap';
import { Order } from '../model/order';
import { Trade } from '../model/trade';
import { Offer } from '../model/offer';
import * as format from '../utils/format';

@Injectable()
export class RaidexService {

    api = 'http://127.0.0.1:5002/api/v01';

    constructor(private http: Http) {

    }

    public getTrades(): Observable<Array<Trade>> {
        return TimerObservable.create(0, 1000)
            .flatMap(() => this.http.get(`${this.api}/markets/dummy/trades`)
                .map((response) => {
                    let data = response.json().data;
                    return data.map((elem) => new Trade(
                        elem.timestamp,
                        format.formatCurrency(elem.amount),
                        format.formatCurrency(elem.price, 2),
                        elem.type
                    ));
                }))
                .retryWhen((errors) => this.printErrorAndRetry('Could not get OrderHistory', errors));
    }

    public getOffers(): Observable<any> {
        return TimerObservable.create(0, 1000)
            .flatMap(() => this.http.get(`${this.api}/markets/dummy/offers`)
                .map((response) => {
                    let data = response.json().data;
                    let buys = data.buys;
                    let sells = data.sells;
                    return {
                        'buys': buys.map((elem) =>
                            new Offer(
                                format.formatCurrency(elem.amount),
                                format.formatCurrency(elem.price, 2)
                            )),
                        'sells': sells.map((elem) =>
                            new Offer(
                                format.formatCurrency(elem.amount),
                                format.formatCurrency(elem.price, 2)
                            ))
                    };
                }))
            .retryWhen((errors) => this.printErrorAndRetry('Could not get OrderBook', errors));
    }

    public submitLimitOrder(limitOrder: Order) {
        let data = {
            'type': limitOrder.type,
            'amount': format.parseCurrency(limitOrder.amount),
            'price': format.parseCurrency(limitOrder.price, 2)
        };
        const headers = new Headers({ 'Content-Type': 'application/json' });
        const options = new RequestOptions({ headers: headers });
        return this.http.post(`${this.api}/markets/dummy/orders/limit`,
            data, options).map((response) => response.json().data).catch(this.handleError);
    }

    public getLimitOrders() {
        return TimerObservable.create(0, 1000)
            .flatMap(() => this.http.get(`${this.api}/markets/dummy/orders/limit`).
            map((response) => {
                let data = response.json().data;
                return data.map((elem) => new Order(
                    elem.type,
                    format.formatCurrency(elem.amount),
                    format.formatCurrency(elem.price, 2),
                    elem.order_id,
                    format.formatCurrency(elem.filledAmount),
                    elem.canceled
                ));
            }))
            .retryWhen((errors) => this.printErrorAndRetry('Could not get Limitorders', errors));
    }

    public cancelLimitOrders(limitOrder: Order) {
        return this.http.delete(`${this.api}/markets/dummy/orders/limit/${limitOrder.id}`)
            .map((response) => response.json().data).catch(this.handleError);
    }

    private printErrorAndRetry(message: string, errors: Observable<any>): Observable<any> {
        return errors
            .map((error) => console.error(message + (error.json().message || error)))
            .delay(20000);
    }

    private handleError(error: Response | any) {
      let errMsg: string;
      if (error instanceof Response) {
          const body = error.json() || '';
          const err = body.error || JSON.stringify(body);
          errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
      } else {
          errMsg = error.message ? error.message : error.toString();
      }
      console.error(errMsg);
      return Observable.throw(errMsg);
}

}
