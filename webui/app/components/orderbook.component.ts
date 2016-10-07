import { Component, OnInit, OnDestroy } from "@angular/core";
import { Subscription } from "rxjs/Subscription";
import {AgGridNg2} from 'ag-grid-ng2/main';
import {GridOptions} from 'ag-grid/main';
import { OrderService } from '../services/order.service';

declare var BigNumber: any;
declare var Web3;
var web3 = new Web3();
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
                return web3.fromWei(String(params.value), 'ether');
            },
            width: 100
        },
        {
            headerName: "Price",
            field: "price",
            width: 100,
            cellRenderer: function(params){ 
                return '<div style="text-align: center;">'+params.value+'</div>';
            } 
        }
    ];

    orderAskColumns = [
        {   headerName: "Amount", 
            field: "amount",
            cellRenderer: function (params: any) {
                return web3.fromWei(String(params.value), 'ether');
            },
            width: 100
        },
        {
            headerName: "Price",
            field: "price",
            width: 100,
            cellRenderer: function(params){ 
                return '<div style="text-align: center;">'+params.value+'</div>';
            } 
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