export interface Transaction {
  id: string;
  stripe_payment_id: string;
  customer_id: string;
  merchant: string;
  amount: string | number;
  currency: string;
  transaction_date: string;
  created_at: string;
}

export interface EligibilityResponse {
  transactionId: string;
  eligible: boolean;
  benefitType: string | null;
  eligibleAmount: string | number;
  reason: string;
}

export interface Claim {
  id: string;
  transaction_id: string;
  benefit_type: string;
  amount: string | number;
  status: string;
  created_at: string;
}

export interface APIError {
  code: string;
  message: string;
  requestId?: string;
}
