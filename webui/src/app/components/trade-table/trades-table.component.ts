import { Component, OnInit } from '@angular/core';
import { Subscription } from 'rxjs';
import { RaidexService } from '../../services/raidex.service';
import { Trade } from '../../model/trade';

@Component({
    selector: 'rex-trades-table',
    templateUrl: 'trades-table.component.html',
})
export class TradesTableComponent implements OnInit {

    public trades: Trade[] = [];
    private raidexSubscription: Subscription;
    private observe_window = 30;

    constructor(private raidexService: RaidexService) {
    }

    public ngOnInit(): void {
        this.getTrades();
    }

    public getTrades(): void {
        this.raidexSubscription = this.raidexService.getNewTrades(this.observe_window).subscribe(
            (trades) => {
                this.trades = trades;
            },
        );
    }
}
