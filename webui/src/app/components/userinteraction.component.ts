import { Component, OnInit, Input } from '@angular/core';
import { Order } from '../model/order';
import { RaidexService } from '../services/raidex.service';

@Component({
    selector: 'rex-user-interact',
    templateUrl: 'userinteraction.component.html',

})

export class UserInteractionComponent implements OnInit {

    @Input() market: any;

    buyOrder = new Order();
    sellOrder = new Order();
    tempBuyId: number;
    tempSellId: number;
    constructor(private raidexService: RaidexService) {}

    ngOnInit(): void {
        this.buyOrder.type = "BUY";
        this.sellOrder.type = "SELL";
    }


    submitOrder(type: string) {
        this.raidexService.submitLimitOrder(this.orderType(type)).subscribe(
            id => {
                type == "BUY" ? this.tempBuyId = id.data : this.tempSellId = id.data;
                this.clearModel();
            }
        );
    }

    clearModel() {
      this.buyOrder.amount = "";
      this.buyOrder.price = "";
      this.sellOrder.amount = "";
      this.sellOrder.price = "";
    }

    orderType(type: string) {
        if (type == "BUY") return this.buyOrder;
        else return this.sellOrder;
    }
    // TODO: Remove this when we're done
    get diagnostic() { return JSON.stringify(this.buyOrder); }
}
