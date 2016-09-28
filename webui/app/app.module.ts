import { NgModule }      from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import {AgGridModule} from 'ag-grid-ng2/main';
import { Ng2BootstrapModule } from 'ng2-bootstrap/ng2-bootstrap';
import { HttpModule }    from '@angular/http';

import { OrderService } from './services/order.service';
import { AppComponent }  from './components/app.component';
import { OrderHistoryComponent } from './components/orderhistory.component';
import { OrderBookComponent } from './components/orderbook.component';

@NgModule({
    imports: [ 	BrowserModule, 
    			AgGridModule, 
    			HttpModule,
                Ng2BootstrapModule
    		 ],
    declarations:[ AppComponent,
    			   OrderHistoryComponent, 
    			   OrderBookComponent
    			 ],
    bootstrap:    [ AppComponent ],
    providers:	  [ OrderService ],
})
export class AppModule { }