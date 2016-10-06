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

    public gridOptions = <GridOptions>{}

    private orderhistorySubscription: Subscription;

	orderHistoryColumns = [
        {   headerName: "Timestamp", 
            field: "timestamp",
            sort:'asc',
            cellRenderer: function (params: any) {
                return (new Date(params.value)).toTimeString();
                }
            },
        {   headerName: "Amount", 
            field: "amount",
            sort:'asc',
            cellRenderer: function (params: any) {
                var wei = String(params.value);
                return new BigNumber(wei).dividedBy(new BigNumber('1000000000000000000'));
                }
            },
        {
            headerName: "Price",
            field: "price",
            sort:'asc',
            width: 100
        }
    ];


    constructor(private orderService: OrderService) { 

    }

    ngOnInit(): void {
    	this.getOrderHistory();
        this.gridOptions.enableSorting = true;
        this.gridOptions.paginationPageSize = 20;
        this.gridOptions.datasource = this.dataSource;
	}

    public ngOnDestroy(): void {
        this.orderhistorySubscription.unsubscribe();
    }

    dataSource = {

        pageSize:20,
        overflowSize: 100,
        getRows:(params: any) => {
            this.orderService.getOrderHistory().subscribe( rowData => {
                var rowsThisPage = rowData.slice(params.startRow, params.endRow);
                var lastRow = -1;
                params.successCallback(rowsThisPage, lastRow);
            });
        }


    }

	getOrderHistory(): void {
        this.orderhistorySubscription = this.orderService.getOrderHistory().subscribe(
            data => { this.orderHistory = data; }
        );

    }



}