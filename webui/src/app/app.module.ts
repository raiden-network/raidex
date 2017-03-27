import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { DataTableModule, SharedModule } from 'primeng/primeng';
import { MaterialModule } from '@angular/material';

import { AppComponent } from './app.component';
import { UserInteractionComponent } from './components/userinteraction.component';
import { OrderService } from './services/order.service';

import { ZingChart } from './components/zingchart.component';
import { ZingDepthChartComponent } from './components/zing-depthchart.component';
import { ZingPriceTimeSeriesComponent } from './components/zing-pricechart.component';
import { ZingStockChartComponent } from './components/zing-stockchart.component';
import { OrderHistoryTableComponent } from './components/orderhistory-table.component';
import { OrderBookTableComponent } from './components/orderbook-table.component';



@NgModule({
    declarations: [
        AppComponent,
        ZingChart,
        UserInteractionComponent,
        ZingDepthChartComponent,
        ZingPriceTimeSeriesComponent,
        ZingStockChartComponent,
        OrderHistoryTableComponent,
        OrderBookTableComponent
    ],
    imports: [
        BrowserModule,
        FormsModule,
        HttpModule,
        DataTableModule,
        SharedModule,
        MaterialModule.forRoot()
    ],
    providers: [ OrderService ],
    bootstrap: [ AppComponent ]
})


export class AppModule { }
