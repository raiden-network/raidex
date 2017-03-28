import { Component, OnInit, Input } from '@angular/core';
import { Order } from '../model/order';


@Component({
    selector: 'rex-user-interact',
    templateUrl: 'userinteraction.component.html'
})

export class UserInteractionComponent implements OnInit {

    @Input() market: any;

    buyOrder = new Order();
    sellOrder = new Order();
    ngOnInit(): void {

    }

    // TODO: Remove this when we're done
    get diagnostic() { return JSON.stringify(this.buyOrder); }
}
