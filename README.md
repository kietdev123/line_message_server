# LINE Message Server

A FastAPI server that integrates with LINE Messaging API to handle user account linking and message sending.

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- ngrok (for testing webhook locally)

## Setup Instructions

1. Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

- Copy `.env-example` to `.env`
- Fill in the following variables:
  - `LINE_CHANNEL_SECRET`: Your LINE Channel Secret
  - `LINE_CHANNEL_ACCESS_TOKEN`: Your LINE Channel Access Token
  - `BASE_URL`: Your server URL (use ngrok URL for local testing)
  - Database credentials (default values work with provided Docker setup)

4. Start MySQL database:

```bash
docker-compose up -d
```

5. Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

6. Set up ngrok for webhook testing:

```bash
ngrok http 8000
```

## Testing Account Linking

1. Visit `http://localhost:8000/login` in your browser
2. Enter a username
3. You will be redirected to the LINE account linking page
4. Complete the linking process in LINE

## API Endpoints

- `GET /login`: Display login form
- `POST /login`: Handle login and generate nonce
- `GET /link`: Get LINE account linking URL
- `POST /webhook`: Handle LINE webhook events
- `POST /send-message`: Send message to linked user
- `GET /users`: List all users and their linking status

## Webhook Events

The server handles two types of webhook events:

1. Account Link events:

- Triggered when a user completes account linking
- Updates user's LINE ID in database
- Sends confirmation message

2. Message events:

- Handles incoming messages from users
- Provides linking URL for unlinked users
- Confirms link status for linked users
