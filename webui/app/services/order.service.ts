import { Injectable } from '@angular/core';
import { Http, Response} from "@angular/http";
import {Observable} from 'rxjs/Rx';
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

	 
	public getOrderHistory(): Promise<any>{
        return this.http.get('app/services/order-history.json')
                    .toPromise()
                    .then(response => response.json().order_history)
                    .catch((error) => this.handleError(error));
    }	

    public getOrderBook(): Observable<any> {
        return this.http.get('app/services/order-book.json')
        .map((res: Response) => res.json());
    }

    private extractData(res: Response) {
        let body = res.json();
        return body.data || { };
    }
    private handleError(error: any): Promise<any> {
        return Promise.reject(error.json().message || error);
    }

}