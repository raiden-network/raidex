import { Component } from '@angular/core';


@Component({
    selector: 'rex-app-root',
    templateUrl: 'app.component.html'
})


export class AppComponent {
    altText = 'Raidex';
    imageUrl = 'raidexlogo.png';
    title = 'Decentralised Exchange based on Raiden';
    markets = ['ETH/USD', 'ETC/USD'];
    selectedMarket = 'ETH/USD';
}
