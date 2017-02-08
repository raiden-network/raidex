import { Component, OnInit, OnChanges, Input, SimpleChanges } from '@angular/core';
import { ZingChartDirective } from '../directives/zing-chart.directive';
import { ZingChartModel } from '../model/zing-chart.model';
import { OrderService } from '../services/order.service';
import { Subscription } from 'rxjs/Subscription';
import * as util from '../services/util.service';
import * as d3Array from 'd3-array';

@Component({
    selector: 'rex-zing-pricechart-component',
    template: `
        <zing-chart *ngFor="let chartObj of charts" [chart]="chartObj"></zing-chart>
    `
})
export class ZingPriceTimeSeriesComponent implements OnInit, OnChanges {

    charts: ZingChartModel[];

    @Input() priceTimeSeriesArray: any[] = [];
    @Input() volumeTimeSeriesArray: any[] = [];
    private orderhistorySubscription: Subscription;

    constructor(private orderService: OrderService) {

    }

    ngOnInit(): void {
      setTimeout(() => this.initialisePriceChart(), 1000);
    }
    ngOnChanges(changes: SimpleChanges) {

    }

    initialisePriceChart(): void {
        this.orderhistorySubscription = this.orderService.getOrderHistory().subscribe(
            data => {
                let tempArray = data;
                tempArray.sort(function(x, y) {
                    return d3Array.ascending(x.timestamp, y.timestamp);
                });
                this.priceTimeSeriesArray = util.formatIntoPriceTimeSeries(tempArray);
                this.volumeTimeSeriesArray = util.formatIntoVolumeTimeSeries(tempArray);
                console.log(this.priceTimeSeriesArray.length+",,,"+
                this.volumeTimeSeriesArray.length);
                let length = this.priceTimeSeriesArray.length - 1;
                this.populateChartData(this.priceTimeSeriesArray[0][0],
                                  this.priceTimeSeriesArray[length][0]);
            }
        );
    }

    populateChartData(minValue: number, maxValue: number): void {
      this.charts = [{
          id : 'price-chart',
          data : {
              'type' : 'mixed',
              'title': {
                'text': 'Price Volume Time Series',
                'font-size': 14,
                'offset-x': -200,
                'offset-y': -10
              },
              'plotarea': {
                'adjust-layout': true /* For automatic margin adjustment. */
              },
              'scale-x': {
                'auto-fit': true,
                'min-value': minValue,
                'max-value': maxValue,
                'step': '1second',
                'transform':{
                  'type':'date',
                  'all':'%g:%i'
                },
                'items-overlap': true,
                'max-items': 6,
                'label': {
                  'text': 'Time'
                }
              },
              'crosshair-x':{
                'plot-label':{
                  'multiple':true
                },
                'scale-label': {
                  'text': '%v',
                  'transform': {
                    'type': 'date',
                    'all': '%g:%i'
                  }
                }
              },
                'scale-y': {
                  'offset-start': '20%', //to adjust scale offsets.

                  'format': '$%v',
                  'label': {
                    'text': 'Prices'
                  },
                  'guide':{
                    'line-style': 'solid'
                  },
                  'item': {
                    'font-size': 10
                  }
                },
                'scale-y-2': {
                  'placement': 'default', //to move scale to default (left) side.
                  'blended': true, //to bind the scale to "scale-y".
                  'offset-end': '75%', //to adjust scale offsets.

                  'format': '%v',
                  'label': {
                    'text': 'Volume'
                  },
                  'guide':{

                  },
                  'item':{
                    'font-size': 10
                  }
                },
              'series': [
                {
                  'type':'scatter',
                  'scales': 'scale-x,scale-y',
                  'guide-label': { //for crosshair plot labels
                    'text': 'Price: %vt',
                    'decimals': 2
                  },
                  'marker': {
                    'type': 'circle',
                    'size':3
                  },
                  'values': this.priceTimeSeriesArray
                },
                {
                  'type': 'vbar',
                  'bar-width': '5%',
                  'scales': "scale-x,scale-y-2",
                  'guide-label': { //for crosshair plot labels
                    'text': 'Volume: %vt',
                    'decimals': 2,
                  },
                  "background-color":"#6666FF",

                  "values": this.volumeTimeSeriesArray
                }
              ],
          },
          height: 400,
          width: '100%'
      }];
    }

}
