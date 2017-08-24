import { Component, OnInit } from '@angular/core';
import { Subscription } from 'rxjs/Subscription';
import { RaidexService } from '../services/raidex.service';
import { Order } from '../model/order';
import {parseCurrency} from "../utils/format";

@Component({
    selector: 'rex-alt-trades-table',
    templateUrl: 'limit-order-table.component.html',
})
export class OrdersTableComponent implements OnInit {

    public orders: any[];
    private raidexSubscription: Subscription;

    constructor(private raidexService: RaidexService) { }

    public ngOnInit(): void {
        this.getOrders();
    }

    public parseOrders(orders: Order[]){
        return orders.map( order => {
            let amount = parseCurrency(order.amount);
            let filled = parseCurrency(order.filledAmount);
            // TODO proper type, proper rounding, should be int between 0-100
            let percentage = Math.round(filled / amount);
            return {'id': order.id,
                    'type': order.type,
                    'price': parseFloat(order.price),
                    'amount': amount,
                    'percentage': percentage,
            }
        })
    }

    public getOrders(): void {
      this.raidexSubscription = this.raidexService.getLimitOrders().subscribe(
          (orders) => {
              this.orders = this.parseOrders(orders);
              console.log(this.orders);
          },
      );
    }
}
