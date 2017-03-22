import { Component, OnInit } from '@angular/core';
import { Subscription } from 'rxjs/Subscription';
import { OrderService } from '../services/order.service';
import * as util from '../services/util.service';
import { OrderBook } from '../model/order-book';
declare var BigNumber: any;
declare var Web3;

@Component({
    selector: 'rex-orderbook-table',
    templateUrl: 'orderbook-table.component.html'
})
export class OrderBookTableComponent implements OnInit {
    public bids: OrderBook[];
    public asks: OrderBook[];
    private orderbookSubscription: Subscription;

    constructor(private orderService: OrderService) {}

    public ngOnInit(): void {
        this.getOrderBook();
    }

    getOrderBook(): void {
        this.orderbookSubscription = this.orderService.getOrderBook().subscribe(
            data => {
                this.bids = util.preprocessOrderBook(data.order_book.bids);
                this.asks = util.preprocessOrderBook(data.order_book.asks);
            }
        );
    }
}
