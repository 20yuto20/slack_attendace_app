# Function Warmup Setup Guide

To keep your Firebase Function instances warm and reduce cold starts, follow these steps to set up a Cloud Scheduler job.

## Step 1: Deploy the Updated Warmup Functions

The warmup solution has been improved to warm up both the `warmup_function` and the `slack_bot_function` with a single scheduler job. Deploy your Firebase functions:

```bash
firebase deploy --only functions
```

## Step 2: Create a Cloud Scheduler Job

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Make sure you're in your Firebase project: `slack-attendance-bot-4a3a5`
3. Navigate to Cloud Scheduler: https://console.cloud.google.com/cloudscheduler
4. Click "CREATE JOB"
5. Fill in the following details:
   - Name: `warmup-function-job`
   - Description: `Prevents cold starts by periodically warming up all functions`
   - Frequency: `*/5 * * * *` (Runs every 5 minutes)
   - Timezone: Select your timezone (e.g., "Asia/Tokyo")
   - Target type: `HTTP`
   - URL: `https://[REGION]-[PROJECT_ID].cloudfunctions.net/warmup_function`
     - Replace `[REGION]` with your function region (e.g., `us-central1`)
     - Replace `[PROJECT_ID]` with `slack-attendance-bot-4a3a5`
   - HTTP method: `GET`
   - Auth header: `None`
6. Click "CREATE"

## Step 3: Verify Operation

1. Wait for a few minutes after creating the job
2. Check Cloud Scheduler logs to ensure the job is executing
3. Check Firebase Function logs to look for these messages:
   - `***** Warmup function called to keep instances warm *****`
   - `***** Warmed up slack_bot_function - Status: 200 *****`
   - `***** Received warmup request for slack_bot_function *****`

## How This Works

This improved warmup solution works by:

1. The Cloud Scheduler calls the `warmup_function` every 5 minutes
2. The `warmup_function` then makes an HTTP request to the `slack_bot_function` with a special header
3. The `slack_bot_function` recognizes this as a warmup request and responds quickly
4. This keeps both functions warm and ready to respond quickly to user requests

## Troubleshooting

If you still experience cold starts:

1. Check if both functions are being warmed up correctly by examining the logs
2. Try increasing the frequency of the Cloud Scheduler job (e.g., every 3 minutes)
3. Ensure the requests library is correctly installed (it was added to requirements.txt)
4. Check if there are any errors in the function logs related to the warmup process