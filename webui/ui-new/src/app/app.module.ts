import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { AgGridModule} from 'ag-grid-ng2/main';

import { AppComponent } from './app.component';
import { OrderHistoryComponent } from './components/orderhistory.component';
import { OrderBookComponent } from './components/orderbook.component';
import { OrderHistoryChartComponent } from './components/order-history-chart.component';
import { OrderBookChartComponent } from './components/orderbook-chart.component';
import { UserInteractionComponent } from './components/userinteraction.component';

import { OrderService } from './services/order.service';
import {GoogleChart} from './directives/angular2-google-chart.directive';


@NgModule({
    declarations: [
        AppComponent,
        GoogleChart,
        OrderHistoryComponent,
        OrderBookComponent,
        OrderHistoryChartComponent,
        OrderBookChartComponent,
        UserInteractionComponent
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
