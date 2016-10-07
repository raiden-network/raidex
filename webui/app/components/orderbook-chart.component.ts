import { Component, OnInit} from "@angular/core";
import {GoogleChart} from '../directives/angular2-google-chart.directive';
import { OrderService } from '../services/order.service';
import { Subscription } from "rxjs/Subscription";
declare var google:any;
declare var googleLoaded:any;
@Component({
	moduleId: module.id,
	selector : 'order-book-chart',
	template:`
    	<div id="line_chart" [chartData]="line_ChartData" [chartOptions]= "line_ChartOptions" chartType="ColumnChart" GoogleChart></div>
			`
})

export class OrderBookChartComponent implements OnInit{
		
	constructor(private orderService: OrderService) { 

    }
    private orderbookSubscription: Subscription;

    ngOnInit(): void {
    	this.getOrderBook();
	}
    public line_ChartData = [
          ['Price', 'Volume'],
          ];	

    public columnChartData: any[];
    public line_ChartOptions = {
      title: 'Depth',
      legend: { position: 'bottom'
      }
    };

	public getOrderBook(): void {
		this.orderbookSubscription = this.orderService.getOrderBook().subscribe(
			data =>{
				var bidArray=data.order_book.bids;
				for(let entry in bidArray){
					this.line_ChartData.push([
						bidArray[entry].price,bidArray[entry].amount
					]);
				}
				
			}
		);
	}
}