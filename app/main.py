from fastapi import FastAPI

app =  FastAPI()


@app.get("/")
def root():
    return {"message":"ClaimGuard API is running"}


