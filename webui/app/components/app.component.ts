import {Component} from '@angular/core';
import {AgGridNg2} from 'ag-grid-ng2/main';
import {GridOptions} from 'ag-grid/main';
import { OnInit } from '@angular/core';
import { OrderService } from '../services/order.service';

declare var BigNumber: any;

@Component({
    selector: 'app',
    template: `<h1>Order History</h1>
                <ag-grid-ng2 class="ag-fresh" style="height: 300px; width: 600px;" 
                [columnDefs]="columnDefs"  
                [rowData] = "rowData">
                </ag-grid-ng2>
                `
})
export class AppComponent implements OnInit{

    public rowData = [];
    columnDefs = [
        {   headerName: "Timestamp", 
            field: "timestamp"
            cellRenderer: function (params: any) {
                return (new Date(params.value)).toUTCString();
                }
            },
        {   headerName: "Amount", 
            field: "amount",
            cellRenderer: function (params: any) {
                // the precision is wrong needs to be corrected
                var wei = String(params.value);
                return new BigNumber(wei).dividedBy(10e18);
                
                }
            },
        {
            headerName: "Price",
            field: "price",
            cellClass: 'centerJustify'
        }
    ];
    constructor(private orderService: OrderService) { }


    
    

    ngOnInit(): void {
        this.getOrderHistory();


    }

    getOrderHistory(): void {
        this.orderService.getOrderHistory()
        .then((order_history) => this.rowData = order_history)
    }


    // put data directly onto the controller
    /**
    rowData = [
        {make: "Toyota", model: "Celica", price: 35000},
        {make: "Ford", model: "Mondeo", price: 32000},
        {make: "Porsche", model: "Boxter", price: 72000}
    ];
    */
    // gridOptions: GridOptions = {
    //     columnDefs: this.columnDefs,
    //     rowData: this.rowData
    // }
}
