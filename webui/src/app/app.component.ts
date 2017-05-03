import { Component } from '@angular/core';

@Component({
    selector: 'rex-app-root',
    templateUrl: 'app.component.html',
    styleUrls: ['app.component.css']
})

export class AppComponent {
    public altText = 'raidEX';
    public imageUrl = 'raidexlogo.png';
    public title = 'Decentralised Exchange based on Raiden';
    public markets = ['ETH/USD', 'ETC/USD'];
    public selectedMarket = 'ETH/USD';
}
