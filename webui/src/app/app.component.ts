import { Component , Input } from '@angular/core';
import { Subscription, timer } from 'rxjs';
import { finalize } from 'rxjs/operators';
import {
    ConfirmationDialogComponent
} from './components/confirmation-dialog/confirmation-dialog.component';
import { MatDialog, MatDialogConfig } from '@angular/material';
import { Channel } from './model/channel'
import { RaidexService } from './services/raidex.service';

@Component({
    selector: 'rex-app-root',
    templateUrl: 'app.component.html',
    styleUrls: ['app.component.css']
})

export class AppComponent {
    public altText = 'raidEX';
    public imageUrl = 'raidexlogo.png';
    public title = 'Decentralised Exchange based on Raiden';
    public markets = ['RTT/WETH'];
    public selectedMarket = 'RTT/WETH';
    public cs_address = '0xEDC5f296a70096EB49f55681237437cbd249217A';
    @Input() public channels: Channel[];
    private raidexSubscription: Subscription;
    private dialogRef;


    constructor(private raidexService: RaidexService, public dialog: MatDialog ) {
        this.channels = []
        this.dialogRef = undefined
    }

    public ngOnInit(): void {
        this.getChannels()
    }



    public getChannels(): void {
        this.raidexSubscription = this.raidexService.getChannels().subscribe(
            (channels) => {
                this.channels = channels;

                if(!this.has_cs_channel() && !this.dialogRef)
                    this.showDialog();
                if(this.has_cs_channel() && this.dialogRef)
                    this.dialogRef.close(true);
            },
        );
    }

    has_cs_channel(): boolean {

        let has_cs_channel = false

        this.channels.forEach((channel) =>{
                if(channel.partner_address == this.cs_address)
                    has_cs_channel = true
            });
        return has_cs_channel
    }

    showDialog(): void {

        const dialogConfig = new MatDialogConfig();

            dialogConfig.disableClose = true;
            dialogConfig.autoFocus = true;

            dialogConfig.data = {
                title: 'Connection To Commitment Service',
                message:
                    `There is no Channel to the commitment service open. <b>${
                        (this.cs_address)}</b>
                        ` + `Do you want to open a channel and deposit 10 Token?</b>.`,
                actionInformation: {
                    partner_address: this.cs_address,
                    token_address: '0x92276aD441CA1F3d8942d614a6c3c87592dd30bb',
                    deposit: '10000'
                    }
                };

        this.dialogRef = this.dialog.open(ConfirmationDialogComponent, dialogConfig);
        this.dialogRef.afterClosed().pipe(
            finalize(() => this.dialogRef = undefined)
        );
    }

}
