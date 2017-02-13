import { Component } from '@angular/core';
import { OnInit } from '@angular/core';


@Component({
    selector: 'rex-app-root',
    templateUrl: 'app.component.html'
})


export class AppComponent implements OnInit {

    title = 'Decentralised Exchange based on Raiden';
    altText = 'Raidex';
    imageUrl = 'raidexlogo.png';
    markets = ['ETH/USD', 'ETC/USD'];
    selectedMarket = 'ETH/USD';

    ngOnInit(): void {

    }


    get diagnostic() { return this.selectedMarket; }

}
