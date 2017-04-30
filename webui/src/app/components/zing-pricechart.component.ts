import { Component, OnInit } from '@angular/core';
import { ZingChartModel } from '../model/zing-chart.model';
import { RaidexService } from '../services/raidex.service';
import { Subscription } from 'rxjs/Subscription';
import * as d3Array from 'd3-array';

@Component({
    selector: 'rex-zing-pricechart',
    template: `
        <rex-zingchart *ngFor="let chartObj of charts" [chart]="chartObj"></rex-zingchart>
        `,
})
export class ZingPriceTimeSeriesComponent implements OnInit {

    public charts: ZingChartModel[];
    public priceTimeSeriesArray: any[] = [];
    public volumeTimeSeriesArray: any[] = [];
    private raidexSubscription: Subscription;

    constructor(private raidexService: RaidexService) {

    }

    public ngOnInit(): void {
        setTimeout(() => this.initialisePriceChart(), 1000);
    }

    public initialisePriceChart(): void {
        this.raidexSubscription = this.raidexService.getTrades().subscribe(
            (data) => {
                let tempArray = data;
                tempArray.sort(function (x, y) {
                    return d3Array.ascending(x.timestamp, y.timestamp);
                });
                this.priceTimeSeriesArray = formatIntoPriceTimeSeries(tempArray);
                this.volumeTimeSeriesArray = formatIntoVolumeTimeSeries(tempArray);
                this.populateChartData();
            }
        );
    }

    public populateChartData(): void {
        this.charts = [{
            id: 'price-chart',
            data: {
                'type': 'mixed',
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
                    'step': '10second',
                    'transform': {
                        'type': 'date',
                        'all': '%g:%i'
                    },
                    'items-overlap': true,
                    'max-items': 10,
                    'zooming': true,
                    'label': {
                        'text': 'Time'
                    }
                },
                'scroll-x': {},
                'crosshair-x': {
                    'plot-label': {
                        'multiple': true
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
                    'offset-start': '25%', // to adjust scale offsets.

                    'format': '$%v',
                    'label': {
                        'text': 'Prices'
                    },
                    'guide': {
                        'line-style': 'solid'
                    },
                    'item': {
                        'font-size': 10
                    }
                },
                'scale-y-2': {
                    'placement': 'default', // to move scale to default (left) side.
                    'blended': true, // to bind the scale to "scale-y".
                    'offset-end': '75%', // to adjust scale offsets.

                    'format': '%v',
                    'label': {
                        'text': 'Volume'
                    },
                    'guide': {
                        'line-style': 'solid'
                    },
                    'item': {
                        'font-size': 10
                    }
                },
                'series': [
                    {
                        'type': 'line',
                        'scales': 'scale-x,scale-y',
                        'guide-label': { // for crosshair plot labels
                            'text': 'Price: %vt',
                            'decimals': 2
                        },
                        'line-style': 'solid',
                        'marker': {
                            'type': 'circle',
                            'size': 3,
                            'background-color': '#03a9f4'
                        },
                        'values': this.priceTimeSeriesArray
                    },
                    {
                        'type': 'vbar',
                        'bar-width': '5%',
                        'scales': 'scale-x,scale-y-2',
                        'guide-label': { // for crosshair plot labels
                            'text': 'Volume: %vt',
                            'decimals': 2,
                        },
                        'background-color': '#6666FF',

                        'values': this.volumeTimeSeriesArray
                    }
                ],
            },
            height: 300,
            width: '100%'
        }];
    }

}

function formatIntoPriceTimeSeries(orderHistoryArray: Array<any>) {
    return orderHistoryArray.map((element) => [
            element.timestamp,
            parseFloat(element.price)
    ]);
}

function formatIntoVolumeTimeSeries(orderHistoryArray: Array<any>) {
    return orderHistoryArray.map((element) => [
        element.timestamp,
        parseFloat(element.amount)
    ]);
}
