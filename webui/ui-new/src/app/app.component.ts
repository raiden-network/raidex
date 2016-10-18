import {Component} from '@angular/core';
import {AgGridNg2} from 'ag-grid-ng2/main';
import {GridOptions} from 'ag-grid/main';
import { OnInit } from '@angular/core';
import { OrderService } from './services/order.service';



@Component({
    selector: 'app-root',
    templateUrl: 'app.component.html'
})
export class AppComponent implements OnInit{

    title = 'Raidex Decentralized Exchange';
    altText = 'Raidex'
    imageUrl = 'raidexlogo.png';  
    markets = ['ETH/USD', 'ETC/USD']
    selectedMarket = 'ETH/USD';
    ngOnInit(): void {
        
    }
    get diagnostic() { return this.selectedMarket; }


}
