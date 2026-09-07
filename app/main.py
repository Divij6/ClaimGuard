from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.routes.health import router as health_router
from app.api.routes.claims import router as claims_router
from app.core.exceptions import ClaimGuardException
from app.middleware.request_id import RequestIDMiddleware
from app.api.routes.transactions import router as transactions_router
from app.api.routes.webhooks import router as webhook_router

app =  FastAPI()
app.add_middleware(RequestIDMiddleware)


@app.exception_handler(ClaimGuardException)
async def claimguard_exception_handler(
    request: Request,
    exc: ClaimGuardException,
):
    request_id = request.state.request_id

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "requestId": request_id,
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    details = []

    for error in exc.errors():
        field = ".".join(str(location) for location in error["loc"])

        details.append(
            {
                "field": field,
                "message": error["msg"],
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
            "requestId": request.state.request_id,
            "details": details,
        },
    )

app.include_router(health_router)
app.include_router(claims_router)
app.include_router(transactions_router)
app.include_router(webhook_router)