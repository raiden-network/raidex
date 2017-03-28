import { Component, OnInit } from '@angular/core';
import { Subscription } from 'rxjs/Subscription';
import { RaidexService } from '../services/raidex.service';
import * as util from '../services/util.service';
import { Offer } from '../model/offer';


@Component({
    selector: 'rex-offers-table',
    templateUrl: 'offers-table.component.html'
})
export class OffersTableComponent implements OnInit {
    public bids: Offer[];
    public asks: Offer[];
    private raidexSubscription: Subscription;

    constructor(private raidexService: RaidexService) {}

    public ngOnInit(): void {
        this.getOrderBook();
    }

    getOrderBook(): void {
        this.raidexSubscription = this.raidexService.getOffers().subscribe(
            order => {
                this.bids = util.preprocessOffers(order.data.buys);
                this.asks = util.preprocessOffers(order.data.sells);
            }
        );
    }
}
