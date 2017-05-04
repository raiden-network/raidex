import { Component, OnInit, Input } from '@angular/core';
import { Order } from '../model/order';
import { RaidexService } from '../services/raidex.service';

@Component({
    selector: 'rex-user-interact',
    templateUrl: 'userinteraction.component.html',

})

export class UserInteractionComponent implements OnInit {

    @Input() public market: any;

    public buyOrder = new Order();
    public sellOrder = new Order();
    public tempBuyId: number;
    public tempSellId: number;
    public orderArray: Order[];
    public selectedOrder: Order;
    constructor(private raidexService: RaidexService) {}

    public ngOnInit(): void {
        this.buyOrder.type = 'BUY';
        this.sellOrder.type = 'SELL';
        this.getOrders();
    }

    public submitOrder(type: string) {
        this.raidexService.submitLimitOrder(this.segregateOrder(type)).subscribe(
            (id) => {
                type === 'BUY' ? this.tempBuyId = id : this.tempSellId = id;
                this.clearModel();
                this.getOrders();
            },
        );
    }

    public getOrders() {
        this.raidexService.getLimitOrders().subscribe(
            (limitOrders) => {
                this.orderArray = <Order[]> limitOrders;
            },
        );
    }

    public cancelOrder() {
        if (this.selectedOrder) {
            this.raidexService.cancelLimitOrders(this.selectedOrder).subscribe(
                (value) => {
                    this.getOrders();
                },
            );
        }
    }
    private clearModel() {
        this.buyOrder.amount = '';
        this.buyOrder.price = '';
        this.sellOrder.amount = '';
        this.sellOrder.price = '';
    }

    private segregateOrder(type: string) {
        if (type === 'BUY') {
            return this.buyOrder;
        } else {
          return this.sellOrder;
        }
    }
    // TODO: Remove this when we're done
    get diagnostic() { return JSON.stringify(this.buyOrder); }
}
