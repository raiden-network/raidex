import { Component, OnInit} from '@angular/core';
import { ZingChartModel } from '../model/zing-chart.model';
import { RaidexService } from '../services/raidex.service';
import { Subscription } from 'rxjs/Subscription';
import * as d3Array from 'd3-array';

@Component({
    selector: 'rex-zing-depthchart',
    template: `
        <rex-zingchart *ngFor="let chartObj of charts" [chart]="chartObj"></rex-zingchart>
    `
})
export class ZingDepthChartComponent implements OnInit {

    public charts: ZingChartModel[];
    public bidArray: any[] = [];
    public askArray: any[] = [];
    public raidexSubscription: Subscription;

    constructor(private raidexService: RaidexService) {}

    public ngOnInit(): void {
        setTimeout(() => this.initialiseOrderChart(), 1000);
    }

    public initialiseOrderChart(): void {
        this.raidexSubscription = this.raidexService.getOffers().subscribe(
            (offer) => {
                let tempArray = offer.buys;
                tempArray.sort(function(x, y) {
                    return d3Array.ascending(Number(x.price), Number(y.price));
                });
                this.bidArray = cumulativePoints(tempArray);
                tempArray = offer.sells;
                tempArray.sort(function(x, y) {
                    return d3Array.descending(Number(x.price), Number(y.price));
                });
                this.askArray = cumulativePoints(tempArray);
                this.populateChartData();
            });
    }

    public populateChartData(): void {
        this.charts = [{
            id: 'depth-chart',
            data: {
                'type': 'area',
                'plot': {
                    'line-width': 2,
                    'marker': {
                        'size': 1,
                        'visible': false
                    },
                    'tooltip': {
                        'text': '<table border="0" rules=none>' +
                        '<col width="150">' +
                        '<tr align="left">' +
                        '<td>Cumulative Volume</td>' +
                        '<td>%vt</td>' +
                        '</tr>' +
                        '<tr align="right">' +
                        '<td>Price</td>' +
                        '<td>%kt</td>' +
                        '</tr>' +
                        '</table>',
                        'html-mode': true,
                        'background-color': 'white',
                        'border-color': 'black',
                        'border-radius': '6px',
                        'font-color': 'black',
                        'alpha': 0.5,
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
                    'label': {
                        'text': 'Price'
                    }
                },
                'series': [
                    {
                        'values': this.bidArray,
                        'text': 'Red'
                    },
                    {
                        'values': this.askArray,
                        'text': 'Blue'
                    }
                ],
            },
            height: 300,
            width: '100%'
        }];
    }

}

function cumulativePoints(orderArray: Array<any>) {
    return orderArray.map((element, index, arr) => [
        parseFloat(element.price),
        d3Array.sum(arr.slice(index), function (d) {
            return parseFloat(d.amount);
        })
    ]);
}
