# DummyFastAPI

A minimal FastAPI app ready for deployment on [Railway](https://railway.app/).

## Running Locally

```sh
pip install -r requirements.txt
uvicorn main:app --reload
```

## Deploying to Railway

1. Push this repo to GitHub.
2. Create a new Railway project and link your repo.
3. Set the Railway service start command to:
   ```sh
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
4. Deploy!
