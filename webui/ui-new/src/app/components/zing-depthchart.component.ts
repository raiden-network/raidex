import { Component, OnInit, OnChanges, Input, SimpleChanges } from '@angular/core';
import { ZingChartDirective } from '../directives/zing-chart.directive';
import { ZingChartModel } from '../model/zing-chart.model';
import { OrderService } from '../services/order.service';
import { Subscription } from 'rxjs/Subscription';
import * as util from '../services/util.service';
import * as d3Array from 'd3-array';

@Component({
    selector: 'rex-zing-depthchart-component',
    template: `
        <zing-chart *ngFor="let chartObj of charts" [chart]="chartObj"></zing-chart>
    `
})
export class ZingDepthChartComponent implements OnInit, OnChanges {

    charts: ZingChartModel[];
    @Input() bidArray: any[] = [];
    @Input() askArray: any[] = [];
    isLoaded: boolean = false;

    constructor(private orderService: OrderService) {

    }

    public orderbookSubscription: Subscription;

    ngOnInit(): void {
      setTimeout(() => this.initialiseOrderChart(), 1000);
    }

    ngOnChanges(changes: SimpleChanges) {

    }

    initialiseOrderChart(): void {
        this.orderbookSubscription = this.orderService.getOrderBook().subscribe(
          data => {
              let tempArray = data.order_book.bids;
              tempArray.sort(function(x, y) {
                  return d3Array.ascending(x.price, y.price);
              });
              tempArray = util.formatArray(tempArray);
              this.bidArray = util.cumulativePoints(tempArray);
              tempArray = data.order_book.asks;
              tempArray.sort(function(x, y){
                  return d3Array.descending(x.price, y.price);
              });
              tempArray = util.formatArray(tempArray);
              this.askArray = util.cumulativePoints(tempArray);
              this.populateChartData( this.bidArray[0][0],
                                      this.askArray[0][0],
                                      0.01);
          });
    }

    populateChartData(minValue: number, maxValue: number, step: number): void {
      this.charts = [{
          id : 'depth-chart',
          data : {
              'type' : 'area',
              'plot':{
                'tooltip':{
                  'text':
                    '<table border="0" rules=none>'+
                    '<col width="150">'+
                      '<tr align="left">'+
                        '<td>Cumulative Volume</td>'+
                        '<td>%kt</td>'+
                      '</tr>'+
                      '<tr align="right">'+
                        '<td>Price</td>'+
                        '<td>%vt</td>'+
                      '</tr>'+
                      '</table>',
                  'html-mode': true,
                  'background-color': 'white',
                  'border-color': 'black',
                  'border-radius': '6px',
                  'font-color': 'black',
                  'alpha' : 0.5,
                  'callout': true
                }
              },
              'title': {
                'text': 'Market Depth',
                'font-size': 14,
                'offset-x': -200,
                'offset-y': -10
              },
              'scaleY': {
                'label': {'text': 'Cumulative Volume'}
              },
              'plotarea': {
                'adjust-layout': true /* For automatic margin adjustment. */
              },
              'scale-x': {
                'auto-fit': true,
                'min-value': minValue,
                'max-value': maxValue,
                'step': .001,
                'decimals': 2,
                'label': {
                  'text': 'Price'
                }
              },
              'series': [
                {
                  'values': this.bidArray,
                  'text': 'Red'
                },
                { 'values': this.askArray,
                  'text': 'Blue'
                }
              ],
          },
          height: 300,
          width: '100%'
      }];
    }
}
