import { Component, OnInit, OnDestroy, Input} from "@angular/core";
import { Subscription } from "rxjs/Subscription";
import * as util from '../services/util.service';

declare var BigNumber: any;
declare var Web3;
@Component({
    selector: 'user-interact',
    templateUrl: 'userinteraction.component.html'
})
export class UserInteractionComponent implements OnInit{
	
	@Input() market:any;
	
	ngOnInit(): void {

	}
}
