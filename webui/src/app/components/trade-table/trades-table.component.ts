import { Component, OnInit } from '@angular/core';
import { Subscription } from 'rxjs';
import { RaidexService } from '../../services/raidex.service';
import { Trade } from '../../model/trade';
import { Order } from '../../model/order'

@Component({
    selector: 'rex-trades-table',
    templateUrl: 'trades-table.component.html',
})
export class TradesTableComponent implements OnInit {


    public orders: Order[] = [];
    private raidexSubscription: Subscription;
    private observe_window = 30;

    constructor(private raidexService: RaidexService) {
    }

    public ngOnInit(): void {
        this.getOrders();
    }

    public getOrders() {
        this.raidexService.getLimitOrders().subscribe(
            (limitOrders) => {
                this.orders = <Order[]>limitOrders.filter(order => {

                    return ! order.canceled && ! order.open;

                });
            },
        );
    }
}
