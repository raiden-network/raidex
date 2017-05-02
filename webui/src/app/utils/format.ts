export function formatCurrency(value: any, decimals = 18, precision = 6) {
    return (Number(value) / Math.pow(10, decimals)).toFixed(precision);
}

export function parseCurrency(strToParse: string, decimals = 18): number {
    return Math.round(parseFloat(strToParse) * Math.pow(10, decimals));
}
