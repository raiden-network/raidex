import { NgModule }      from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import {AgGridModule} from 'ag-grid-ng2/main';
import { OrderService } from './services/order.service';
import { AppComponent }  from './components/app.component';
import { HttpModule }    from '@angular/http';


@NgModule({
    imports: [ 	BrowserModule, 
    			AgGridModule, 
    			HttpModule],
    declarations: [ AppComponent ],
    bootstrap:    [ AppComponent ],
    providers:	  [ OrderService ],
})
export class AppModule { }