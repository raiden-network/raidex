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

    public getOrders(): void {
      this.raidexSubscription = this.raidexService.getLimitOrders().subscribe(
          (orders) => {
              this.orders = orders;
          },
      );
    }

    public lookupRowStyleClass(rowData: Order, rowIndex: number): string{
        console.log(rowData, rowIndex);
        if (rowData.type == 'BUY'){
            return 'buy-row'
        }
        else {
            return 'sell-row'
        }
}


}
