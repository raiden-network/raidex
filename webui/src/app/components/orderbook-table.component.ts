import { Component, OnInit } from '@angular/core';
import { Subscription } from 'rxjs/Subscription';
import { OrderService } from '../services/order.service';
import * as util from '../services/util.service';
import { OrderBookEntry } from '../model/order-book';


@Component({
    selector: 'rex-orderbook-table',
    templateUrl: 'orderbook-table.component.html'
})
export class OrderBookTableComponent implements OnInit {
    public bids: OrderBookEntry[];
    public asks: OrderBookEntry[];
    private orderbookSubscription: Subscription;

    constructor(private orderService: OrderService) {}

    public ngOnInit(): void {
        this.getOrderBook();
    }

    getOrderBook(): void {
        this.orderbookSubscription = this.orderService.getOrderBook().subscribe(
            order => {
                this.bids = util.preprocessOrderBook(order.data.buys);
                this.asks = util.preprocessOrderBook(order.data.sells);
            }
        );
    }
}
