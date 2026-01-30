# KHWAISH: Lead Follow-Up Automation System

**KHWAISH** is a complete, runnable lead follow-up automation system built with **FastAPI** and **SQLite**. It automates the initial contact and reminder process via mock Email and WhatsApp webhooks, and provides a simple web dashboard for status tracking.

## 🚀 Setup and Installation

### 1. Clone and Navigate

The project structure is set up in the current directory.

### 2. Environment Setup

It is highly recommended to use a virtual environment.

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy the example environment file and fill in your details.

```bash
cp .env.example .env
# Open .env and edit the variables
```

**Key `.env` Variables to Configure:**

| Variable | Description | Notes |
| :--- | :--- | :--- |
| `SECRET_KEY` | Used for security purposes. | **MUST** be changed from the default. |
| `APP_BASE_URL` | The base URL where the app is running (e.g., `http://localhost:8000`). | Used to generate the "reply link" in emails. |
| `FROM_EMAIL` | The email address used as the sender. | Used in the mock email service. |
| `MAKE_ZAPIER_WEBHOOK_URL` | The URL provided by your Make.com or Zapier scenario. | **Required** for WhatsApp integration. |

### 4. Database Initialization

Create the SQLite database file and tables.

```bash
python3 scripts/init_db.py
```

### 5. Seed Demo Data (Optional)

Populate the database with 10 leads with mixed statuses for testing the dashboard and scheduler logic.

```bash
python3 scripts/seed_demo.py
```

## ⚙️ Running the System

The system consists of two main components: the API/Dashboard server and the Scheduler.

### 1. Start the API Server

This runs the web dashboard and exposes the API endpoints.

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The dashboard will be accessible at `http://localhost:8000`.

### 2. Run the Scheduler

The scheduler is responsible for checking for leads that need a reminder (no reply after 3 days).

**Note:** When the API server starts (`uvicorn app.main:app`), it automatically starts an in-process `APScheduler` to run the reminder check every hour.

If you need to run the check manually or as a separate cron job:

```bash
# Runs the reminder check logic once
python3 -m app.scheduler
```

## 🔗 WhatsApp Integration (Make/Zapier Instructions)

The system uses a simple outgoing webhook to trigger WhatsApp messages.

1.  **Create a Scenario/Zap:** In Make.com or Zapier, create a new scenario/zap that starts with a **Webhook** trigger.
2.  **Get the Webhook URL:** Copy the unique URL provided by the webhook trigger and paste it into the `MAKE_ZAPIER_WEBHOOK_URL` variable in your `.env` file.
3.  **Process the Payload:** The webhook will receive a JSON payload like this:

    ```json
    {
      "lead_id": 1,
      "name": "Alice Johnson",
      "phone": "123-456-7890",
      "email": "alice.j@example.com",
      "type": "FIRST_TOUCH", // or "REMINDER"
      "message": "Hello Alice Johnson, this is a first touch message from KHWAISH."
    }
    ```

4.  **Send WhatsApp Message:** Use the `phone` field and the `message` field to send the WhatsApp message via your chosen provider (e.g., WhatsApp Cloud API, Twilio).

## ✅ 10-Step Manual Test Plan

After setting up and running the API server, follow these steps to test the core functionality:

| Step | Action | Expected Result |
| :--- | :--- | :--- |
| 1 | **Access Dashboard:** Navigate to `http://localhost:8000`. | Dashboard loads, KPIs are visible, and the 10 demo leads are listed. |
| 2 | **Add New Lead (Web Form):** Click "Add Lead," fill in details for a new lead (e.g., `test@example.com`), and submit. | Lead is created, appears in the table with status **CONTACTED**. Mock email/WhatsApp logs appear in the console. |
| 3 | **Import CSV:** Click "Import CSV," create a simple CSV file (e.g., `name,email,phone,source\nTest User,test2@example.com,12345,csv_import`), and upload. | New leads are imported, appear in the table with status **CONTACTED**. |
| 4 | **View Lead Detail:** Click "View" on the lead created in Step 2. | Lead detail page loads, showing contact info and a timeline with "First Contact," "Email Sent," and "WhatsApp Sent." |
| 5 | **Mark as Replied (Manual):** On the lead detail page, click "Mark as Replied." | Status changes to **REPLIED**. A new "Lead Replied" entry appears in the timeline. |
| 6 | **Update Status:** On the lead detail page, click "Mark as Won." | Status changes to **WON**. KPI for "Won" increases on the dashboard. |
| 7 | **Manual Reminder:** Click "View" on a lead with status **CONTACTED** (e.g., Bob Smith from the seed data) and click "Send Reminder." | Status changes to **REMINDER\_SENT**. Mock reminder email/WhatsApp logs appear in the console. |
| 8 | **Test Reply Link:** Manually construct the reply link for a lead (e.g., `http://localhost:8000/api/leads/1/mark-replied`) and open it in a browser. | Lead #1's status changes to **REPLIED** (check dashboard). |
| 9 | **Test Scheduler Logic:** Check the console output for the scheduler. The lead created 3+ days ago (George Lucas from seed data) should have been automatically reminded if the server has been running for an hour, or if you run `python3 -m app.scheduler`. | Lead George Lucas's status changes to **REMINDER\_SENT** (if not already). |
| 10 | **Check Message Logs:** On the detail page for a lead that was reminded (Step 7 or 9), check the "Message Logs" section. | Logs show entries for both the initial contact and the reminder, with `success=True`. |
