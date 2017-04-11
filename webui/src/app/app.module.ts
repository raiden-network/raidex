import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { DataTableModule, SharedModule } from 'primeng/primeng';
import { MaterialModule } from '@angular/material';

import { AppComponent } from './app.component';
import { UserInteractionComponent } from './components/userinteraction.component';
import { RaidexService } from './services/raidex.service';

import { ZingChart } from './components/zingchart.component';
import { ZingDepthChartComponent } from './components/zing-depthchart.component';
import { ZingPriceTimeSeriesComponent } from './components/zing-pricechart.component';
import { ZingStockChartComponent } from './components/zing-stockchart.component';
import { TradesTableComponent } from './components/trades-table.component';
import { OffersTableComponent } from './components/offers-table.component';

@NgModule({
    declarations: [
        AppComponent,
        ZingChart,
        UserInteractionComponent,
        ZingDepthChartComponent,
        ZingPriceTimeSeriesComponent,
        ZingStockChartComponent,
        TradesTableComponent,
        OffersTableComponent
    ],
    imports: [
        BrowserModule,
        FormsModule,
        HttpModule,
        DataTableModule,
        SharedModule,
        MaterialModule.forRoot()
    ],
    providers: [ RaidexService ],
    bootstrap: [ AppComponent ]
})

export class AppModule { }
