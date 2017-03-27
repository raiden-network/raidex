import { Component, Input, NgZone, AfterViewInit, HostBinding, OnDestroy } from '@angular/core';
import { ZingChartModel } from '../model/zing-chart.model';

declare var zingchart: any;

@Component({
  selector: 'zingchart',
  template: `<div id="{{chart.id}}"></div>`
})
export class ZingChart implements AfterViewInit, OnDestroy {
    @Input()
    chart: ZingChartModel;

    @HostBinding('id')
    get something() {
        return this.chart.id;
    }
    constructor(private zone: NgZone) {}

    ngAfterViewInit() {
        this.render();
    }

    render() {
        this.zone.runOutsideAngular(() => {
            zingchart.render({
                id : this.chart['id'],
                data : this.chart['data'],
                width : this.chart['width'],
                height: this.chart['height']
            });

        });
    }

    ngOnDestroy() {
        zingchart.exec(this.chart['id'], 'destroy');
    }

    update() {
      this.zone.runOutsideAngular(() => {
        zingchart.exec(this.chart['id'], 'setdata', {
          data: this.chart['data']
        });
      });
    }

}
