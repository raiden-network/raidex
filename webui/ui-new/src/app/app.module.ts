import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { AgGridModule} from 'ag-grid-ng2/main';

import { AppComponent } from './app.component';
import { OrderHistoryComponent } from './components/orderhistory.component';
import { OrderBookComponent } from './components/orderbook.component';


import { UserInteractionComponent } from './components/userinteraction.component';

import { OrderService } from './services/order.service';

import { ZingChartDirective } from './directives/zing-chart.directive';
import { ZingDepthChartComponent } from './components/zing-depthchart.component';
import { ZingPriceTimeSeriesComponent } from './components/zing-pricechart.component';

@NgModule({
    declarations: [
        AppComponent,
        ZingChartDirective,
        OrderHistoryComponent,
        OrderBookComponent,
        UserInteractionComponent,
        ZingDepthChartComponent,
        ZingPriceTimeSeriesComponent
    ],
    imports: [
        BrowserModule,
        FormsModule,
        HttpModule,
        AgGridModule.withNg2ComponentSupport(),
    ],
    providers: [ OrderService ],
    bootstrap: [AppComponent]
})


export class AppModule { }
