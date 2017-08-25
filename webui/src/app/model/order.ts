export class Order {
    constructor(public type: string, public amount: string, public price: string,
                public id: number, public filledAmount: string, public canceled: Boolean) {}

    get filled(): String {
        return String(Number(this.filledAmount) / Number(this.amount) * 100.) + '%';
    }

    get status(): String {
        return this.canceled ? 'canceling' : 'open';
    }
}
