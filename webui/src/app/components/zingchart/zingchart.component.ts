import { Component, Input, NgZone, AfterViewInit, HostBinding, OnDestroy } from '@angular/core';
import { ZingChartModel } from '../../model/zing-chart.model';

declare var zingchart: any;

@Component({
  selector: 'rex-zingchart',
  template: `<div id="{{chart.id}}"></div>`
})
export class ZingChartComponent implements AfterViewInit, OnDestroy {
    @Input()
    public chart: ZingChartModel;

    @HostBinding('id')
    public get something() {
        return this.chart.id;
    }
    constructor(private zone: NgZone) {}

    public ngAfterViewInit() {
        this.render();
    }

    public render() {
        this.zone.runOutsideAngular(() => {
            zingchart.render({
                id : this.chart['id'],
                data : this.chart['data'],
                width : this.chart['width'],
                height: this.chart['height']
            });

        });
    }

    public ngOnDestroy() {
        zingchart.exec(this.chart['id'], 'destroy');
    }

    public update() {
      this.zone.runOutsideAngular(() => {
        zingchart.exec(this.chart['id'], 'setdata', {
          data: this.chart['data']
        });
      });
    }

}
