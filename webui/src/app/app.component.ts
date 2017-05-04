import { Component } from '@angular/core';

@Component({
    selector: 'rex-app-root',
    templateUrl: 'app.component.html',
})

export class AppComponent {
    public altText = 'Raidex';
    public imageUrl = 'raidexlogo.png';
    public title = 'Decentralised Exchange based on Raiden';
    public markets = ['ETH/USD', 'ETC/USD'];
    public selectedMarket = 'ETH/USD';
}
