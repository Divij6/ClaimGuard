export function formatMoney(value: string | number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(Number(value));
}

export function formatBenefit(benefit: string): string {
  return benefit
    .split("_")
    .map((word) => word[0] + word.slice(1).toLowerCase())
    .join(" ");
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

export function sumMoney(values: Array<string | number>): string {
  const totalCents = values.reduce((total, value) => total + toCents(value), BigInt(0));
  const whole = totalCents / BigInt(100);
  const cents = (totalCents % BigInt(100)).toString().padStart(2, "0");

  return `${whole}.${cents}`;
}

function toCents(value: string | number): bigint {
  const [whole = "0", decimal = ""] = String(value).split(".");
  const cents = decimal.padEnd(2, "0").slice(0, 2);

  return BigInt(whole) * BigInt(100) + BigInt(cents);
}
