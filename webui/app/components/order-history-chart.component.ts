import { Component, OnInit} from "@angular/core";
import {GoogleChart} from '../directives/angular2-google-chart.directive';
import { OrderService } from '../services/order.service';
import { Subscription } from "rxjs/Subscription";
@Component({
	moduleId: module.id,
	selector : 'order-history-chart',
	template:`
    	<div id="scatter_chart" [chartData]="scatter_ChartData"  [chartOptions] = "scatter_ChartOptions" chartType="ScatterChart" GoogleChart></div>
			`
})
export class OrderHistoryChartComponent implements OnInit {
	
	constructor(private orderService: OrderService) { 

    }
	ngOnInit(): void {
    	this.getOrderHistory();
	}
	private orderhistorySubscription: Subscription;

	public scatter_ChartData =  [
              ['Date', 'Price'],
            ];
    public scatter_ChartOptions = {
         legend: { position: 'bottom'
                  },
           title: 'Trade History Chart',
       };	


    public getOrderHistory(): void {
    	this.orderhistorySubscription = this.orderService.getOrderHistory().subscribe(
            data => {  
            	for(let entry in data){
            		this.scatter_ChartData.push([
            			new Date(data[entry].timestamp),
            			data[entry].price
            		])
            	}
            }
        );

    }

}
