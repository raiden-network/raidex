import { Component, OnInit } from '@angular/core';
import { Subscription } from 'rxjs/Subscription';
import { RaidexService } from '../services/raidex.service';
import { Offer } from '../model/offer';

@Component({
    selector: 'rex-offers-table',
    templateUrl: 'offers-table.component.html',
})
export class OffersTableComponent implements OnInit {
    public buys: Offer[];
    public sells: Offer[];
    private raidexSubscription: Subscription;

    constructor(private raidexService: RaidexService) {}

    public ngOnInit(): void {
        this.getOrderBook();
    }

    public getOrderBook(): void {
        this.raidexSubscription = this.raidexService.getOffers().subscribe(
            (offers) => {
                this.buys = offers.buys;
                this.sells = offers.sells;
            },
        );
    }
}
