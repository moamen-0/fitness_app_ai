# Deploying the Fitness App to Google Cloud Platform

This guide walks through the steps to deploy the WebSocket-enabled fitness application to Google Cloud Platform using the web interface.

## Prerequisites

1. [Create a Google Cloud account](https://cloud.google.com/) if you don't have one
2. A credit card for setting up billing (Google Cloud offers a free tier and credits for new users)
3. Your application code ready to deploy

## Deployment Steps

### 1. Set Up Your Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "New Project" 
4. Enter a name for your project and click "Create"
5. Wait for the project to be created, then select it from the dropdown
6. **Important**: Note your Project ID (not the project number) which appears under the project name. It typically looks like "my-project-12345" and is different from the numeric Project Number.

### 2. Enable Billing

1. In the navigation menu, click "Billing"
2. Follow the prompts to set up a billing account if you haven't already
3. Link your project to the billing account

### 3. Enable Required APIs

1. In the navigation menu, click "APIs & Services" > "Library"
2. Search for and enable the following APIs:
   - App Engine Admin API
   - Cloud Build API
   - Cloud Run API

### 4. Set Up IAM Permissions (Important)

Before deploying, you must ensure your user account has the necessary permissions:

1. In the navigation menu, click "IAM & Admin" > "IAM"
2. Look for your email account in the list of principals
3. If you need to add permissions, click the pencil icon to edit, or click "Grant Access" to add your account
4. Add the following roles to your account:
   - App Engine Deployer (`roles/appengine.deployer`)
   - App Engine Service Admin (`roles/appengine.serviceAdmin`)
   - Cloud Build Editor (`roles/cloudbuild.builds.editor`)
   - Storage Admin (`roles/storage.admin`)
   - Service Account User (`roles/iam.serviceAccountUser`)
5. Click "Save"

If you're the project owner, you should automatically have these permissions. If not, you'll need to ask the project owner to grant them to you.

### 5. Deploy to App Engine

1. In the navigation menu, click "App Engine"
2. Click "Create Application"
3. Select a region closest to your users
4. Select "Python" as the language and "Standard" as the environment
5. Click "Next" and "I'll do this later" when prompted about the first deployment

6. Once your App Engine instance is created, go to "Cloud Shell" by clicking the terminal icon in the top-right corner of the console
7. In Cloud Shell, upload your files by clicking the three-dot menu and selecting "Upload"
8. Or clone your repository using:
   ```bash
   git clone https://github.com/yourusername/your-repository.git
   ```

9. Navigate to your project directory:
   ```bash
   cd ~/your-project-directory
   ```

10. Get your project ID (not the project number):
    ```bash
    gcloud projects list
    ```
    Look for your project in the list and note the PROJECT_ID column value.

11. Deploy the app with:
    ```bash
    gcloud app deploy app.yaml --project=YOUR_PROJECT_ID
    ```
    Replace YOUR_PROJECT_ID with the ID (not the number) from step 10. For example:
    ```bash
    gcloud app deploy app.yaml --project=pure-highlander-456910
    ```
    
    If you see an error like:
    ```
    ERROR: (gcloud.app.deploy) The value of ``--project'' flag was set to Project number. 
    To use this command, set it to PROJECT ID instead.
    ```
    This means you used the numeric project number instead of the project ID. Project IDs are typically in the format of words with hyphens, like "pure-highlander-456910".

12. Type "Y" when prompted to confirm the deployment

### 6. View Your Application

1. After deployment completes, click on the generated URL in the console output
2. Or go to App Engine > Dashboard and click on the URL displayed at the top

## Testing WebSockets

1. After deployment, navigate to the `/websocket_test` route on your app
2. Verify that the WebSocket connection is established successfully
3. Test sending and receiving messages

## Alternative Deployment: Cloud Run (Better for WebSockets)

Cloud Run may provide better support for WebSockets than App Engine. Here's how to deploy using the web interface:

1. In the Google Cloud Console, navigate to "Cloud Run"
2. Click "Create Service"
3. You can choose either:
   - "Continuously deploy new revisions from a source repository" (connect to GitHub or other source)
   - "Deploy one revision from an existing container image" (if you have a Docker image)

4. For source code deployment:
   - Connect your GitHub repository
   - Configure the build settings (select Python as the runtime)
   - Under "Container, Networking, Security" settings:
     - Expand "Container" and set the container port to 8080
     - In "Advanced Settings" under "Connections", enable "Session affinity" which helps with WebSockets
   - Make sure your service account has necessary permissions

5. For container deployment, you'll need to build your Docker image first:
   - Use the Dockerfile in your project
   - Build and push to Google Container Registry or Artifact Registry
   - Select this image during deployment

6. Configure "Capacity" settings based on your needs (memory, CPU, etc.)
7. Enable "Allow unauthenticated invocations" if you want public access
8. Click "Create" to deploy your service

## Troubleshooting

### Project ID vs. Project Number

Google Cloud uses both Project IDs and Project Numbers:

1. **Project ID**: A user-defined, globally unique identifier (e.g., "pure-highlander-456910")
   - Used in most gcloud commands
   - Appears in URLs for your application
   - Can be custom or auto-generated during project creation

2. **Project Number**: A Google-assigned numeric identifier (e.g., "115514733643")
   - Not typically used in commands
   - Cannot be used in place of a Project ID for deployment

If you're unsure of your Project ID:
```bash
gcloud projects list
```
This will show all your projects with both IDs and numbers.

### Permission Issues

If you encounter permission errors:

1. Verify your user account has the following roles:
   - App Engine Deployer (`roles/appengine.deployer`)
   - App Engine Service Admin (`roles/appengine.serviceAdmin`)
   - Cloud Build Editor (`roles/cloudbuild.builds.editor`)
   - Storage Admin (`roles/storage.admin`)
   - Service Account User (`roles/iam.serviceAccountUser`)

2. If using Cloud Shell, you may need to authenticate:
   ```bash
   gcloud auth login
   ```

3. If problems persist, try activating your service account:
   ```bash
   gcloud auth activate-service-account --key-file=your-key-file.json
   ```

### WebSocket Issues

If you encounter WebSocket connection issues:

1. Make sure your application is configured to handle WebSockets properly
2. Verify your client code uses secure WebSockets (`wss://`) when connecting to the deployed app
3. For App Engine: Check your `app.yaml` includes `network: session_affinity: true`
4. For Cloud Run: Make sure you've enabled session affinity during setup
5. Check logs:
   - Go to "Logging" in Google Cloud Console
   - Filter logs by your service name

## Cost Management

1. Set budget alerts in Google Cloud Console:
   - Navigate to "Billing" > "Budgets & alerts"
   - Create a budget with notification thresholds

2. Use cost-effective configurations:
   - For App Engine: Use automatic scaling with min instances set to 0
   - For Cloud Run: Use the "CPU is only allocated during request processing" option

3. Monitor your usage:
   - Use the "Monitoring" section in Google Cloud Console
   - Set up alerts for high usage

## Important Notes

- The first connection to your app might be slow as the instance spins up
- WebSocket connections may time out after several minutes of inactivity
- The application is configured to use HTTPS by default, which is required for WebSocket connections in production
- Cloud Run may be more suitable for WebSocket applications than App Engine
- You may need to adjust timeout settings for long-lived WebSocket connections
