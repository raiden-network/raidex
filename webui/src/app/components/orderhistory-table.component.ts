import { Component, OnInit } from '@angular/core';
import { Subscription } from 'rxjs/Subscription';
import { OrderService } from '../services/order.service';
import * as util from '../services/util.service';
import { OrderHistoryEntry } from '../model/order-history';


@Component({
    selector: 'rex-orderhistory-table',
    templateUrl: 'orderhistory-table.component.html'
})
export class OrderHistoryTableComponent implements OnInit {

    orderHistory: OrderHistoryEntry[];
    private orderhistorySubscription: Subscription;

    constructor(private orderService: OrderService) { }

    public ngOnInit(): void {
        this.getOrderHistory();
    }

    getOrderHistory(): void {
        this.orderhistorySubscription = this.orderService.getOrderHistory().subscribe(
            data => {
                this.orderHistory = util.preprocessOrderHistory(data);
            }
        );
    }
}
