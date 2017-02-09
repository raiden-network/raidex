export class OrderHistory {
    public timestamp: number;
    public amount: number;
    public price: number;
    constructor(timestamp: number, amount: number, price: number) {
      this.timestamp = timestamp;
      this.amount = amount;
      this.price = price;
    }
}
