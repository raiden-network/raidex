export class Order {
    public type: string;
    public amount: string;
    public price: string;
    public id: string;
    public filledAmount: number;
    public cancel: number;
    constructor(type?: string, amount?: string, price?: string,
                id?: string, filledAmount?: number, cancel?: number) {
        this.type = type;
        this.amount = amount;
        this.price = price;
        this.id = id;
        this.filledAmount = filledAmount;
        this.cancel = cancel;
    }
}
