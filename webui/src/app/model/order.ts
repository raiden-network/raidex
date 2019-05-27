import { formatCurrency } from '../utils/format';

export class Order {
    constructor(
        public type: string,
        public amount: string,
        public price: string,
        public id: number,
        public filledAmount: string,
        public open: Boolean,
        public canceled: Boolean
    ) {
    }

    // TODO price as a private attribute and provide getters for string repr.
    get shortPrice(): String {
        return formatCurrency(parseFloat(this.price), 0, 1);
    }

    get shortAmount(): String {
        return formatCurrency(Number(this.amount), 0, 1);
    }

    get filled(): String {
        return String(Math.round(Number(this.filledAmount) / Number(this.amount) * 100.)) + '%';
    }

    get status(): String {
        return this.canceled ? 'canceled' : this.open ? 'open' : 'closed';
    }

    get totalAmount(): String {
        return String(Number(this.amount) * Number(this.price))
    }
}
