# ClaimGuard

ClaimGuard is a full-stack claims-intake application for card benefits. It receives successful Stripe payments, stores normalized transactions in Supabase, determines which synthetic card benefit applies, and lets users review or start a claim through a Next.js dashboard.

> This project uses **synthetic eligibility rules** for demonstration. It is not a production benefit-administration system or a source of insurance coverage decisions.

## What it does

1. Stripe sends a signed `payment_intent.succeeded` webhook.
2. The API verifies the signature and records the event as `processing`.
3. The payment intent becomes a transaction in Supabase.
4. A user can request an eligibility decision for the transaction.
5. The API applies the benefit rules on the server and creates a claim only when eligible.
6. The dashboard shows transactions and claims through a same-origin Next.js proxy.

## Architecture

```text
Stripe ──signed webhook──> FastAPI API ──> Supabase Postgres
                                │
                                └──> eligibility evaluator ──> claim creation

Browser ──> Next.js dashboard ──proxy──> FastAPI API
```

The browser calls `/api/claimguard/*` on the Next.js app. That route forwards requests to `NEXT_PUBLIC_API_BASE_URL`, so the browser does not need direct cross-origin access to the API.

## Tech stack

| Area | Technology |
| --- | --- |
| Backend API | FastAPI and Uvicorn |
| Persistence | Supabase / Postgres |
| Payment events | Stripe webhooks |
| Web UI | Next.js 15, React 19, TypeScript |
| Styling | Tailwind CSS |
| Tests | pytest |

## Repository layout

```text
app/
├── api/routes/                 HTTP endpoint definitions
├── core/                       Stripe setup and domain exception type
├── db/                         Supabase client initialization
├── middleware/                 Request-ID middleware
├── schemas/                    Pydantic input and output models
├── services/                   Business and persistence logic
└── main.py                     FastAPI application entry point
frontend/
├── src/app/                    Dashboard pages and Next.js proxy route
├── src/components/             Shared UI components
└── src/lib/                    API client, types, and formatting helpers
tests/                          Backend unit tests
```

## Prerequisites

- Python 3.10 or later
- Node.js 20 or later
- npm
- A Supabase project
- A Stripe account; install the Stripe CLI for local webhook testing

## Environment configuration

### Backend

Create `.env` at the repository root. It is ignored by Git and must never contain production secrets in source control.

```env
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_KEY=<supabase-service-or-project-key>
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

| Variable | Used for | Required |
| --- | --- | --- |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase client authentication | Yes |
| `STRIPE_SECRET_KEY` | Stripe Python SDK configuration | Yes for Stripe work |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signature validation | Yes for webhooks |

### Frontend

Copy the supplied template and use the local API address:

```bash
cp frontend/.env.example frontend/.env.local
```

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Install and run locally

### 1. Set up the API

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi "uvicorn[standard]" python-dotenv supabase stripe pytest
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`.

- Health check: `http://localhost:8000/health`
- Interactive OpenAPI documentation: `http://localhost:8000/docs`

### 2. Set up the dashboard

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### 3. Verify the API

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Database setup

ClaimGuard expects three tables: `transactions`, `claims`, and `webhook_events`. The following baseline SQL can be run in the Supabase SQL editor.

```sql
create table public.transactions (
  id uuid primary key default gen_random_uuid(),
  stripe_payment_id text not null unique,
  customer_id text not null,
  merchant text not null,
  amount numeric(12, 2) not null check (amount >= 0),
  currency text not null,
  transaction_date timestamptz not null,
  created_at timestamptz not null default now()
);

create table public.claims (
  id uuid primary key default gen_random_uuid(),
  transaction_id uuid not null references public.transactions(id),
  benefit_type text not null,
  amount numeric(12, 2) not null check (amount >= 0),
  status text not null default 'created',
  created_at timestamptz not null default now(),
  unique (transaction_id, benefit_type)
);

create table public.webhook_events (
  stripe_event_id text primary key,
  event_type text not null,
  status text not null check (status in ('processing', 'processed', 'ignored')),
  created_at timestamptz not null default now()
);
```

The service uses the unique constraints to make duplicate transaction and claim attempts return conflict errors. If Row Level Security is enabled, configure policies appropriate for the key and deployment model you choose.

## Eligibility model

The evaluator accepts a transaction's amount, currency, and merchant. A transaction must use USD. The first eligible benefit in the following priority order is selected:

| Priority | Benefit | Requirements | Eligible amount |
| --- | --- | --- | --- |
| 1 | `PURCHASE_PROTECTION` | Amount is at least $100 and merchant is present | Lesser of transaction amount and $500 |
| 2 | `TRAVEL_DELAY` | Amount is at least $50 and merchant is United Airlines, Delta, American Airlines, Air India, or Emirates | Lesser of transaction amount and $300 |
| 3 | `RETURN_PROTECTION` | Amount is at least $50 | Lesser of transaction amount and $250 |

For example, a $150 USD purchase at Delta qualifies as `PURCHASE_PROTECTION`, because it is evaluated before travel delay. A non-USD transaction is always ineligible.

The `POST /transactions/{transaction_id}/claim` endpoint repeats this calculation server-side; it does not trust a benefit type or amount supplied by a client.

## API reference

FastAPI exposes the authoritative interactive schema at `/docs`. The endpoint summary below is useful for quick local testing.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health check |
| `POST` | `/transactions` | Insert a transaction |
| `GET` | `/transactions` | List transactions ordered by newest transaction date |
| `GET` | `/transactions/{id}/eligibility` | Return the current eligibility decision |
| `POST` | `/transactions/{id}/claim` | Start an eligible claim |
| `POST` | `/claims` | Create a claim directly |
| `GET` | `/claims` | List claims ordered by creation date |
| `GET` | `/claims/{id}` | Retrieve one claim |
| `POST` | `/webhooks/stripe` | Receive Stripe webhook events |

### Create a transaction

```bash
curl -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "stripe_payment_id": "pi_example_001",
    "customer_id": "cus_example_001",
    "merchant": "Example Electronics",
    "amount": 150.00,
    "currency": "usd",
    "transaction_date": "2026-09-07T10:30:00Z"
  }'
```

A successful response includes an ID used by the remaining endpoints:

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "stripe_payment_id": "pi_example_001",
  "customer_id": "cus_example_001",
  "merchant": "Example Electronics",
  "amount": 150.00,
  "currency": "usd",
  "transaction_date": "2026-09-07T10:30:00+00:00",
  "created_at": "2026-09-07T10:31:00+00:00"
}
```

### Check eligibility and create a claim

```bash
curl http://localhost:8000/transactions/<transaction-id>/eligibility

curl -X POST http://localhost:8000/transactions/<transaction-id>/claim
```

The eligibility response uses camelCase for the transaction and benefit fields:

```json
{
  "transactionId": "<transaction-id>",
  "eligible": true,
  "benefitType": "PURCHASE_PROTECTION",
  "eligibleAmount": 150.00,
  "reason": "Transaction qualifies for purchase protection."
}
```

### Direct claim creation

Direct claim creation is available for integrations that already know the benefit and amount:

```bash
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "<transaction-id>",
    "benefit_type": "PURCHASE_PROTECTION",
    "amount": 150.00
  }'
```

Prefer the transaction claim endpoint for user-facing flows so eligibility is always decided by the API.

## Errors and request IDs

Domain and validation errors return a structured JSON object. The API accepts an optional `X-Request-ID` request header; otherwise it generates one and returns it in the response header.

```json
{
  "code": "TRANSACTION_NOT_ELIGIBLE",
  "message": "Transaction amount is below the minimum purchase protection threshold.",
  "requestId": "req_..."
}
```

Common domain error codes include `TRANSACTION_NOT_FOUND`, `TRANSACTION_ALREADY_EXISTS`, `CLAIM_NOT_FOUND`, `CLAIM_ALREADY_EXISTS`, and `TRANSACTION_NOT_ELIGIBLE`. Invalid request bodies return HTTP 422 with a `details` array.

## Stripe webhook workflow

1. Configure a Stripe endpoint pointing to `/webhooks/stripe`.
2. Set its signing secret as `STRIPE_WEBHOOK_SECRET`.
3. ClaimGuard verifies the `Stripe-Signature` header before processing an event.
4. For `payment_intent.succeeded`, it creates a transaction from the intent details.
5. It records webhook state as `processed` or `ignored`, preventing repeat delivery from doing the work again.

Production payment intents must contain `customer_id` and `merchant` in their Stripe metadata. For Stripe test events only, the application fills absent metadata with development placeholders.

### Test Stripe locally

Start the API, then in another terminal run:

```bash
stripe listen --forward-to localhost:8000/webhooks/stripe
```

Copy the `whsec_...` value printed by the CLI into `.env`, restart Uvicorn, and trigger an event:

```bash
stripe trigger payment_intent.succeeded
```

## Testing and quality checks

Run backend tests from the project root after activating the virtual environment:

```bash
pytest
```

Run frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

## Troubleshooting

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| API fails during startup | Missing or invalid Supabase variables | Check `.env` and verify the URL/key match the project |
| Dashboard reports API configuration error | `NEXT_PUBLIC_API_BASE_URL` is unset | Create `frontend/.env.local` from the example and restart Next.js |
| Webhook returns 400 | Wrong signing secret or the request did not come through Stripe CLI | Use the currently displayed `whsec_...` value and restart the API |
| Transaction conflict | A transaction already exists for that Stripe payment ID | Use a new payment ID or treat the existing transaction as the source of truth |
| Claim conflict | The transaction already has a claim for that benefit | Fetch existing claims instead of retrying creation |
| Claim request returns 422 | Current eligibility rules do not allow the transaction | Call the eligibility endpoint and inspect its `reason` |

