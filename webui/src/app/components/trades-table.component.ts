import { Component, OnInit } from '@angular/core';
import { Subscription } from 'rxjs/Subscription';
import { RaidexService } from '../services/raidex.service';
import * as util from '../services/util.service';
import { Trade } from '../model/trade';

@Component({
    selector: 'rex-trades-table',
    templateUrl: 'trades-table.component.html',
})
export class TradesTableComponent implements OnInit {

    public trades: Trade[];
    private raidexSubscription: Subscription;

    constructor(private raidexService: RaidexService) { }

    public ngOnInit(): void {
        this.getTrades();
    }

    public getTrades(): void {
        this.raidexSubscription = this.raidexService.getTrades().subscribe(
            (data) => {
                this.trades = util.preprocessTrades(data);
            },
        );
    }
}
