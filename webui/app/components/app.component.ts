import {Component} from '@angular/core';
import {AgGridNg2} from 'ag-grid-ng2/main';
import {GridOptions} from 'ag-grid/main';
import { OnInit } from '@angular/core';
import { OrderService } from '../services/order.service';



@Component({
    moduleId: module.id,
    selector: 'app',
    templateUrl: 'app.component.html'
})
export class AppComponent implements OnInit{

    title = 'Raidex Decentralized Exchange';  
    ngOnInit(): void {
        
    }

}
