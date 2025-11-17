# Instructions for Restarting the Backend

I have now fixed the backend code to truncate the password during verification, which was the root cause of the `ValueError` and the 500 Internal Server Error you were seeing during login attempts.

Please **restart your backend** by stopping the `uvicorn` process (if it's still running) and then running it again:

```bash
cd backend
source venv/bin/activate
uvicorn api.main:socket_app --host 0.0.0.0 --port 8000 --reload
```

After restarting the backend, please try to register and/or log in again from the frontend. This time, it should work without any errors.
