import { Component, OnInit} from "@angular/core";
import {GoogleChart} from '../directives/angular2-google-chart.directive';
import { OrderService } from '../services/order.service';
import { Subscription } from "rxjs/Subscription";
import * as util from '../services/util.service';
declare var Web3;
var web3 = new Web3();
@Component({
	moduleId: module.id,
	selector : 'order-history-chart',
	template:`
    	<div id="history_price" [chartData]="historyprice_ChartData"  [chartOptions] = "historyprice_ChartOptions" chartType="ScatterChart" GoogleChart></div>
      <div id="history_volume" [chartData]="historyvolume_ChartData" [chartOptions]= "historyvolume_ChartOptions" chartType="ColumnChart" GoogleChart></div>
			`
})
export class OrderHistoryChartComponent implements OnInit {
	
  public historyprice_ChartData: any[]; 

  public historyvolume_ChartData: any[];

  private orderhistorySubscription: Subscription;

	constructor(private orderService: OrderService) {
    
  }
	ngOnInit(): void {
      this.historyprice_ChartData =[ ['Time', 'Price'] ];
      this.historyvolume_ChartData =[ ['Time', 'Volume'] ]
    	this.getOrderHistory();
	}
	
  public historyprice_ChartOptions = {
          legend: 'none',
          title: 'Trade History Price Time Series',
          hAxis: {title: 'Time', format: ['HH:mm']},
          vAxis: {title: 'Price'},
          pointShape: 'circle',
          pointSize: 1
       };	

  public historyvolume_ChartOptions = {
      title: 'Trade History Volume Time Series',
      legend: 'none',
      hAxis: {title: 'Time', format: ['HH:mm']},
      vAxis: {title: 'Volume'}
    };

  public getOrderHistory(): void {
    	this.orderhistorySubscription = this.orderService.getOrderHistory().subscribe(
            data => {  
            	for(let entry in data){
            		this.historyprice_ChartData.push([
            			new Date(data[entry].timestamp),
            			parseFloat(data[entry].price)/1000
            		]);
                this.historyvolume_ChartData.push([
                  new Date(data[entry].timestamp),
                  parseFloat(web3.fromWei(String(data[entry].amount), 'ether'))
                ])
            	}
            }
        );

    }

}
