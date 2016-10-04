import { Component, OnInit, OnDestroy } from "@angular/core";
import { Subscription } from "rxjs/Subscription";
import {AgGridNg2} from 'ag-grid-ng2/main';
import {GridOptions} from 'ag-grid/main';
import { OrderService } from '../services/order.service';

declare var BigNumber: any;

@Component({
    moduleId: module.id,
    selector: 'order-history',
    templateUrl: 'orderhistory.component.html'
})

export class OrderHistoryComponent implements OnInit{
	
	public orderHistory = [];

    private orderhistorySubscription: Subscription;

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

    public ngOnDestroy(): void {
        this.orderhistorySubscription.unsubscribe();
    }

	getOrderHistory(): void {
        this.orderhistorySubscription = this.orderService.getOrderHistory().subscribe(
            data => { this.orderHistory = data; }
        );

    }

}