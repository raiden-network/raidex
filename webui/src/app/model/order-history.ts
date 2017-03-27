export class OrderHistoryEntry {
    public timestamp: number;
    public amount: string;
    public price: string;
    public type: number;
    constructor(timestamp: number, amount: string, price: string, type?: number) {
      this.timestamp = timestamp;
      this.amount = amount;
      this.price = price;
      this.type = type;
    }
}
