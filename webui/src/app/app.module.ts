import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DataTableModule, SharedModule, GrowlModule } from 'primeng/primeng';
import { AppComponent } from './app.component';
import { UserInteractionComponent } from './components/userinteraction/userinteraction.component';
import { RaidexService } from './services/raidex.service';
import { ZingChartComponent } from './components/zingchart/zingchart.component';
import { ZingDepthChartComponent } from './components/zing-depthchart/zing-depthchart.component';
import { ZingStockChartComponent } from './components/zing-stockchart/zing-stockchart.component';
import { TradesTableComponent } from './components/trade-table/trades-table.component';
import { OffersTableComponent } from './components/offers-table/offers-table.component';
import { OrdersTableComponent } from './components/limit-order-table/limit-order-table.component';
import { HttpClientModule } from '@angular/common/http';
import { MaterialComponentModule } from './modules/material-components/material-component.module';
import { ZingPriceTimeSeriesComponent } from './components/zing-pricechart/zing-pricechart.component';

@NgModule({
    declarations: [
        AppComponent,
        ZingChartComponent,
        UserInteractionComponent,
        ZingDepthChartComponent,
        ZingStockChartComponent,
        ZingPriceTimeSeriesComponent,
        TradesTableComponent,
        OffersTableComponent,
        OrdersTableComponent
    ],
    imports: [
        BrowserModule,
        BrowserAnimationsModule,
        FormsModule,
        HttpClientModule,
        DataTableModule,
        SharedModule,
        GrowlModule,
        MaterialComponentModule
    ],
    providers: [RaidexService],
    bootstrap: [AppComponent]
})

export class AppModule {
}
