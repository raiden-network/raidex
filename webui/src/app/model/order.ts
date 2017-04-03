export class Order {
    public type: string;
    public amount: string;
    public price: string;
    constructor(type?:string, amount?:string, price?:string){
        this.type = type;
        this.amount = amount;
        this.price = price;
    }
}
