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

@Injectable()
export class RaidexService {


    constructor(private http: Http) {

    }

    public getTrades(): Observable<any> {
        return TimerObservable.create(0, 60000)
                .flatMap(() =>  this.http.get('http://127.0.0.1:5000/api/version/markets/dummy/trades/')
                    .map((response) => response.json().data))
                .retryWhen((errors) => this.printErrorAndRetry('Could not get OrderHistory', errors));
    }


    public getOffers(): Observable<any> {
        return TimerObservable.create(0, 60000)
                .flatMap(() =>  this.http.get('/src/app/services/order-book.json')
                    .map((response) => response.json()))
                .retryWhen((errors) => this.printErrorAndRetry('Could not get OrderBook', errors));
    }

    public submitLimitOrder(limitOrder: Order) {
        let headers = new Headers({ 'Content-Type': 'application/json' });
        let options = new RequestOptions({ headers: headers });
        return this.http.post('http://127.0.0.1:5000/api/version/markets/dummy/orders/limit',
            limitOrder, options).delay(2000).map(response => response.json()).catch(this.handleError);
    }


    private extractData(res: Response) {
        let body = res.json();
        return body.data || { };
    }


    private printErrorAndRetry(message: string, errors: Observable<any>): Observable<any> {
        return errors
            .map(error => console.error(message + (error.json().message || error)))
            .delay(20000);
    }

    private handleError (error: Response | any) {
      // In a real world app, you might use a remote logging infrastructure
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
