import { Injectable } from '@angular/core';
import { Http, Response} from "@angular/http";
import {Observable} from 'rxjs/Rx';
import { TimerObservable} from "rxjs/observable/TimerObservable";
import "rxjs/add/operator/map";
import "rxjs/add/operator/toPromise";
import "rxjs/add/observable/throw";
import "rxjs/add/operator/catch";
import "rxjs/add/operator/retryWhen";
import "rxjs/add/operator/delay";


@Injectable()
export class OrderService{

	

	 constructor(private http: Http) {

	 }

	
	public getOrderHistory(): Observable<any>{
        return TimerObservable.create(0, 10000)
                .flatMap(()=>  this.http.get('app/services/order-history.json')
                    .map((response) => response.json().order_history))
                .retryWhen((errors) => this.printErrorAndRetry("Could not get OrderBook", errors));
    }	

    public getOrderBook(): Observable<any> {
        return TimerObservable.create(0, 10000)
                .flatMap(()=>  this.http.get('app/services/order-book.json')
                    .map((response) => response.json()))
                .retryWhen((errors) => this.printErrorAndRetry("Could not get OrderBook", errors));
    }

    private extractData(res: Response) {
        let body = res.json();
        return body.data || { };
    }
    private handleError(error: any): Promise<any> {
        return Promise.reject(error.json().message || error);
    }

    private printErrorAndRetry(message: string, errors: Observable<any>): Observable<any> {
        return errors
            .map(error => console.error(message + (error.json().message || error)))
            .delay(20000);
    }
}