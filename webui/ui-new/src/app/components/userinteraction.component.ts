import { Component, OnInit, OnDestroy, Input } from '@angular/core';
import { Subscription } from 'rxjs/Subscription';
import * as util from '../services/util.service';
import { OrderBook } from '../model/order-book';

declare var BigNumber: any;
declare var Web3;


@Component({
    selector: 'rex-user-interact',
    templateUrl: 'userinteraction.component.html',
    styleUrls: ['material-tab.css']
})

export class UserInteractionComponent implements OnInit {

    @Input() market: any;

    buyOrder = new OrderBook();
    sellOrder = new OrderBook();
	  ngOnInit(): void {

    }
}
