import { Component, OnInit, OnDestroy, OnChanges, SimpleChanges, Input } from '@angular/core';
import { Subscription } from 'rxjs/Subscription';
import { AgGridNg2 } from 'ag-grid-ng2/main';
import { GridOptions } from 'ag-grid/main';
import { OrderService } from '../services/order.service';
import * as util from '../services/util.service';


declare var BigNumber: any;
declare var Web3;
let web3 = new Web3();


@Component({
    selector: 'rex-order-history',
    templateUrl: 'orderhistory.component.html'
})

export class OrderHistoryComponent implements OnInit, OnChanges {

    public orderHistory = [];
    public gridOptions = <GridOptions>{};
    private orderhistorySubscription: Subscription;
    @Input() market: String;
	  public orderHistoryColumns = [
        {
            headerName: 'Timestamp',
            field: 'timestamp',
            sort: 'asc',
            width: 100,
            cellRenderer: function (params: any) {
                return (new Date(params.value)).toLocaleTimeString();
            }
        },
        {
            headerName: 'Amount',
            field: 'amount',
            sort: 'asc',
            width: 100,
            cellRenderer: function (params: any) {
                return util.convertToEther(params.value);
            }
        },
        {
            headerName: 'Price',
            field: 'price',
            sort: 'asc',
            width: 70,
            cellRenderer: function(params){
                return '<div style="text-align: center;">' + util.formatCurrency(params.value) + '</div>';
            }

        }
    ];
    public dataSource = {

        pageSize: 25,
        overflowSize: 100,
        getRows: (params: any) => {
            this.orderService.getOrderHistory().subscribe( rowData => {
                let rowsThisPage = rowData.slice(params.startRow, params.endRow);
                let lastRow = -1;
                params.successCallback(rowsThisPage, lastRow);
            });
        }
    };


    constructor(private orderService: OrderService) {

    }

    public ngOnInit(): void {
        this.getOrderHistory();
        this.gridOptions.enableSorting = true;
        this.gridOptions.paginationPageSize = 19;
        this.gridOptions.datasource = this.dataSource;
    }

    public ngOnDestroy(): void {
        this.orderhistorySubscription.unsubscribe();
    }


	  getOrderHistory(): void {
        this.orderhistorySubscription = this.orderService.getOrderHistory().subscribe(
            data => { this.orderHistory = data; }
        );
    }

    ngOnChanges(changes: SimpleChanges) {
        for (let propName in changes) {
            let chng = changes[propName];
            let cur  = JSON.stringify(chng.currentValue);
            let prev = JSON.stringify(chng.previousValue);
            console.log('Current Value ==' + cur + ' Previous Value==' + prev);
        }
    }
    get diagnostic() { return this.market; }

}
