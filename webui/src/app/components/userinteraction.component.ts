import { Component, OnInit, Input } from '@angular/core';
import { Order } from '../model/order';
import { RaidexService } from '../services/raidex.service';
import { Message } from 'primeng/primeng';

@Component({
    selector: 'rex-user-interact',
    templateUrl: 'userinteraction.component.html',
    styleUrls: ['userinteraction.component.css']
})

export class UserInteractionComponent implements OnInit {

    @Input() public market: any;

    public buyOrder = new Order();
    public sellOrder = new Order();
    public tempBuyId: number;
    public tempSellId: number;
    public orderArray: Order[];
    public selectedOrder: Order;
    public msgs: Message[] = [];
    public selectedType: String;
    constructor(private raidexService: RaidexService) {}

    public ngOnInit(): void {
        this.buyOrder.type = 'BUY';
        this.sellOrder.type = 'SELL';
        this.selectedType = 'BUY';
        this.getOrders();
    }

    public selectType(type: string) {
        this.selectedType = type;
    }

    public submitOrder(type: string) {
        this.raidexService.submitLimitOrder(this.segregateOrder(type)).subscribe(
            (id) => {
                type === 'BUY' ? this.tempBuyId = id : this.tempSellId = id;
                this.clearModel();
                this.getOrders();
                this.showMessage(type);
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

    public showMessage(type: string) {
        this.msgs = [];
        if (type === 'BUY' && this.tempBuyId !== null) {
            this.msgs.push({severity: 'info',
                            summary: 'Buy Order Submitted',
                            detail: 'Your Buy Order has been submitted with id ' + this.tempBuyId
                          });
        } else if (type === 'SELL' && this.tempSellId !== null) {
            this.msgs.push({severity: 'info',
                            summary: 'Sell Order Submitted',
                            detail: 'Your Sell Order has been submitted with id ' +
                            this.tempSellId
                          });
        } else {
            this.msgs.push({severity: 'error',
                            summary: 'Error',
                            detail: 'Error in submitting orders please try again'});
        }


    }
    // TODO: Remove this when we're done
    get diagnostic() { return JSON.stringify(this.buyOrder); }
}
