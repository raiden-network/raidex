export class OrderBookEntry {
    public amount: string;
    public price: string;
    constructor(amount?:string, price?:string){
        this.amount = amount;
        this.price = price;
    }
}
