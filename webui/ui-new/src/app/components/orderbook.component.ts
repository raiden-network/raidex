import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs/Subscription';
import { AgGridNg2 } from 'ag-grid-ng2/main';
import { GridOptions } from 'ag-grid/main';
import { OrderService } from '../services/order.service';
import * as util from '../services/util.service';

declare var BigNumber: any;
declare var Web3;
let web3 = new Web3();


@Component({
    selector: 'rex-order-book',
    templateUrl: 'orderbook.component.html'
})

export class OrderBookComponent implements OnInit {

    public bids: any[];
    public asks: any[];
    private orderbookSubscription: Subscription;
    public gridOptions = <GridOptions>{};
    orderBidColumns = [
        {
            headerName: 'Amount',
            field: 'amount',
            cellRenderer: function (params: any) {
                return util.convertToEther(params.value);
            },
            sort: 'asc',
            cellStyle: { color: '#ff0000'},
            width: 80
        },
        {
            headerName: 'Price',
            field: 'price',
            width: 80,
            sort: 'asc',
            cellRenderer: function(params){
                return '<div style="text-align: center;">' + util.formatCurrency(params.value) + '</div>';
            }
        }
    ];
    orderAskColumns = [
        {   headerName: 'Amount',
            field: 'amount',
            cellRenderer: function (params: any) {
                return util.convertToEther(params.value);
            },
            sort: 'asc',
            cellStyle: { color: '#00ff00'},
            width: 80
        },
        {
            headerName: 'Price',
            field: 'price',
            width: 80,
            sort: 'asc',
            cellRenderer: function(params){
                return '<div style="text-align: center;">' + util.formatCurrency(params.value) + '</div>';
            }
        }
    ];


    constructor(private orderService: OrderService) {

    }

    public ngOnInit(): void {
        this.getOrderBook();
        this.gridOptions.enableSorting = true;
    }

    public ngOnDestroy(): void {
        this.orderbookSubscription.unsubscribe();
    }

    getOrderBook(): void {
        this.orderbookSubscription = this.orderService.getOrderBook().subscribe(
            data => {
                this.bids = data.order_book.bids;
                this.asks = data.order_book.asks;
            }
        );
    }

}
