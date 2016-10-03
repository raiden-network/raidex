import { Component, OnInit, OnDestroy } from "@angular/core";
import {AgGridNg2} from 'ag-grid-ng2/main';
import {GridOptions} from 'ag-grid/main';
import { OnInit } from '@angular/core';
import { OrderService } from '../services/order.service';

declare var BigNumber: any;
@Component({
    moduleId: module.id,
    selector: 'order-book',
    templateUrl: 'orderbook.component.html'
})

export class OrderBookComponent implements OnInit{

	public bids: any[];

	public asks: any[];

    private orderbookSubscription: Subscription;

	orderBidColumns = [
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

    orderAskColumns = [
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
    	this.getOrderBook();
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