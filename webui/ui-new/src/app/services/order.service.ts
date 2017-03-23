import { Injectable } from '@angular/core';
import { Http } from '@angular/http';
import { Observable } from 'rxjs/Observable';
import { TimerObservable} from 'rxjs/observable/TimerObservable';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';
import 'rxjs/add/observable/throw';
import 'rxjs/add/operator/catch';
import 'rxjs/add/operator/retryWhen';
import 'rxjs/add/operator/delay';
import 'rxjs/add/operator/mergeMap';

@Injectable()
export class OrderService {


    constructor(private http: Http) {

    }

    public getOrderHistory(): Observable<any> {
        return TimerObservable.create(0, 60000)
                .flatMap(() =>  this.http.get('http://127.0.0.1:5000/api/version/markets/dummy/trades/')
                    .map((response) => response.json().data))
                .retryWhen((errors) => this.printErrorAndRetry('Could not get OrderHistory', errors));
    }


    public getOrderBook(): Observable<any> {
        return TimerObservable.create(0, 60000)
                .flatMap(() =>  this.http.get('/src/app/services/order-book.json')
                    .map((response) => response.json()))
                .retryWhen((errors) => this.printErrorAndRetry('Could not get OrderBook', errors));
    }

    private printErrorAndRetry(message: string, errors: Observable<any>): Observable<any> {
        return errors
            .map(error => console.error(message + (error.json().message || error)))
            .delay(20000);
    }
}
