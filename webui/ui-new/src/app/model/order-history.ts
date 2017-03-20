export class OrderHistory {
    public timestamp: number;
    public amount: string;
    public price: string;
    constructor(timestamp: number, amount: string, price: string) {
      this.timestamp = timestamp;
      this.amount = amount;
      this.price = price;
    }
}
