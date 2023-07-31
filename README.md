# Rotadyne Customer Portal

### To run the application in production

`gunicorn3 --workers=3 app:app --preload`

--preload is required to get around a login loop error that became apparent when migrating from the flask development server to the gunicorn/nginx production server.
