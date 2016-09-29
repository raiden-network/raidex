import {Component} from '@angular/core';
import {AgGridNg2} from 'ag-grid-ng2/main';
import {GridOptions} from 'ag-grid/main';
import { OnInit } from '@angular/core';
import { OrderService } from '../services/order.service';

declare var BigNumber: any;

@Component({
    moduleId: module.id,
    selector: 'order-history',
    templateUrl: 'orderhistory.component.html'
})

export class OrderHistoryComponent implements OnInit{
	
	public orderHistory = [];

	orderHistoryColumns = [
        {   headerName: "Timestamp", 
            field: "timestamp",
            cellRenderer: function (params: any) {
                return (new Date(params.value)).toUTCString();
                }
            },
        {   headerName: "Amount", 
            field: "amount",
            cellRenderer: function (params: any) {
                var wei = String(params.value);
                return new BigNumber(wei).dividedBy(new BigNumber('1000000000000000000'));
                }
            },
        {
            headerName: "Price",
            field: "price",
            width: 100
        }
    ];

    constructor(private orderService: OrderService) { 

    }

    ngOnInit(): void {
    	this.getOrderHistory();
	}

	getOrderHistory(): void {
        this.orderService.getOrderHistory()
        .then((order_history) => this.orderHistory = order_history)
    }

}