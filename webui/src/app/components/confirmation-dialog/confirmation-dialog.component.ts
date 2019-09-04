import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { RaidexService } from '../../services/raidex.service';
import { ActionInformation } from '../../model/actioninformation'

@Component({
    selector: 'app-confirmation-dialog',
    templateUrl: './confirmation-dialog.component.html',
    styleUrls: ['./confirmation-dialog.component.css']
})
export class ConfirmationDialogComponent {
    readonly title: string;
    readonly message: string;
    readonly actionInformation : ActionInformation
    confirmed: boolean;
    readonly waiting = "WAITING . . ."



    constructor(
        public dialogRef: MatDialogRef<ConfirmationDialogComponent>,
        private raidexService: RaidexService,
        @Inject(MAT_DIALOG_DATA) data
    ) {
        console.log(data)
        this.title = data.title;
        this.message = data.message;
        this.actionInformation = data.actionInformation;
        this.confirmed = false;
    }



    confirm() {
        this.confirmed = true;
        this.raidexService.makeChannelAndDeposit(
        this.actionInformation.partner_address,
        this.actionInformation.token_address,
        this.actionInformation.deposit,
        ).subscribe(
            (id) => {console.log(id);}
        );

    }

}
