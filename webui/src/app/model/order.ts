export class Order {
    constructor(public type: string, public amount: string, public price: string,
                public id: number, public filledAmount: string) {}

    get filled(): String {
        return String(Number(this.filledAmount) / Number(this.amount) * 100.) + '%';
    }
}
