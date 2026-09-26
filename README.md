# SUBSENTINEL AI

### AI-Enabled Real-Time Mine Subsidence Monitoring System

SUBSENTINEL AI is a prototype intelligent mine monitoring system designed to monitor underground mine conditions using sensor data and identify potentially dangerous conditions in real time.

The system collects data such as **tilt, vibration, temperature, humidity, crack activity, and sound**, stores the data locally using SQLite, analyzes sensor patterns using machine learning, and presents the results through a real-time web dashboard.

When a high or critical risk condition is detected, the system can also send an **SMS alert using Twilio**.

---

## Features

* Real-time mine sensor monitoring
* Multi-node sensor support
* Tilt and vibration monitoring
* Temperature and humidity monitoring
* Crack and sound sensor data support
* AI-based anomaly detection using **Isolation Forest**
* Automatic risk-level calculation
* Risk score from 0–100
* Five-sample activity analysis
* Real-time monitoring dashboard
* SQLite database for sensor data
* Raspberry Pi Pico W gateway integration
* Automatic SMS alerts using Twilio
* 10-minute SMS alert cooldown
* REST API using FastAPI
* CORS support for frontend communication
* System health and monitoring endpoints
* Analytics and event monitoring

---

## System Architecture

```text
        Mine Sensors
             │
             ▼
     Raspberry Pi Pico W
             │
             ▼
       FastAPI Backend
             │
       ┌─────┴─────┐
       ▼           ▼
    SQLite      AI Analysis
    Database    Isolation Forest
       │           │
       └─────┬─────┘
             ▼
       Risk Assessment
             │
       ┌─────┴─────┐
       ▼           ▼
   Web Dashboard  SMS Alert
                 (Twilio)
```

---

## Technologies Used

### Backend

* Python
* FastAPI
* Uvicorn
* Pandas
* Scikit-learn
* SQLite

### Machine Learning

* Isolation Forest
* Feature engineering
* Rolling-window activity analysis
* Sensor anomaly detection

### Frontend

* HTML5
* CSS3
* JavaScript
* Responsive dashboard interface

### Communication

* REST API
* Raspberry Pi Pico W
* Twilio SMS API

---

## Project Structure

```text
SUBSENTINEL_AI_2/
│
├── ai_features2.py
├── ai_risk2.py
├── server2.py
├── index2.html
│
└── mine_data.db
    └── Automatically created when the server starts
```

### File Description

| File              | Description                                                                          |
| ----------------- | ------------------------------------------------------------------------------------ |
| `server2.py`      | Main FastAPI backend, database handling, API endpoints, risk analysis and SMS alerts |
| `ai_features2.py` | Creates additional sensor features such as activity and rolling sensor values        |
| `ai_risk2.py`     | Performs AI anomaly detection and risk assessment                                    |
| `index2.html`     | Web-based mine monitoring dashboard                                                  |
| `mine_data.db`    | SQLite database automatically created by the backend                                 |

---

# Installation

## 1. Clone or download the project

Download the project and extract it to a suitable location.

Example:

```powershell
cd D:\SUBSENTINEL_AI\SUBSENTINEL_AI_2
```

---

## 2. Create a Python virtual environment

It is recommended to use a virtual environment.

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.\venv\Scripts\Activate.ps1
```

---

## 3. Install dependencies

Run:

```powershell
pip install fastapi uvicorn pandas scikit-learn python-dotenv twilio
```

Alternatively, create a `requirements.txt` file:

```text
fastapi
uvicorn
pandas
scikit-learn
python-dotenv
twilio
```

Then install everything with:

```powershell
pip install -r requirements.txt
```

---

# Running the Application

Start the FastAPI server using:

```powershell
uvicorn server2:app --reload
```

The backend will normally be available at:

```text
http://127.0.0.1:8000
```

Open the application in your browser:

```text
http://127.0.0.1:8000
```

FastAPI documentation is also available at:

```text
http://127.0.0.1:8000/docs
```

---

# Database

SUBSENTINEL AI uses **SQLite** to store sensor information.

The database file is:

```text
mine_data.db
```

The system automatically creates the database when the server starts.

The main `sensor_data` table stores:

* ID
* Timestamp
* Node ID
* Tilt
* Vibration
* Temperature
* Humidity
* Crack
* Sound

No separate database server is required.

---

# AI Risk Detection

The system uses **Isolation Forest**, an unsupervised machine-learning algorithm, to identify unusual sensor patterns.

The model analyzes sensor features including:

```text
Tilt
Vibration
Temperature
Humidity
```

The latest sensor reading is classified as either normal or anomalous.

The system also calculates recent activity using the last five sensor readings.

### Activity

```text
Activity = Tilt + Vibration
```

The system calculates:

```text
activity_5
tilt_5
vibration_5
```

These values are used together with anomaly detection to determine the overall risk condition.

---

# Risk Levels

The system currently uses the following risk categories:

| Risk Level | Description                               |
| ---------- | ----------------------------------------- |
| LOW        | No significant abnormal activity detected |
| WARNING    | Increased activity or tilt detected       |
| HIGH       | Significant vibration activity detected   |
| CRITICAL   | High vibration and tilt activity detected |

The system generates a risk score between:

```text
0 – 100
```

Anomaly detection can increase the calculated risk score.

---

# Sensor Data API

Sensor data can be submitted through the backend API.

### Endpoint

```http
POST /data
```

Example JSON:

```json
{
    "node_id": "NODE_01",
    "tilt": 1,
    "vibration": 2,
    "temperature": 32.5,
    "humidity": 65,
    "crack": 0,
    "sound": 40
}
```

The server stores the received sensor data in SQLite and uses it for risk analysis.

---

# API Endpoints

| Endpoint           | Method | Purpose                      |
| ------------------ | ------ | ---------------------------- |
| `/`                | GET    | Main application             |
| `/health`          | GET    | Backend health check         |
| `/data`            | POST   | Receive sensor data          |
| `/data`            | GET    | Retrieve sensor data         |
| `/status`          | GET    | System status                |
| `/nodes`           | GET    | Retrieve monitoring nodes    |
| `/events`          | GET    | Retrieve monitoring events   |
| `/analytics`       | GET    | Retrieve analytics           |
| `/analytics/7days` | GET    | Retrieve seven-day analytics |
| `/mine`            | GET    | Mine monitoring information  |
| `/test-sms`        | GET    | Test SMS functionality       |
| `/system`          | GET    | System information           |

Interactive API documentation can be accessed through:

```text
http://127.0.0.1:8000/docs
```

---

# Raspberry Pi Pico W Integration

The backend supports communication with a Raspberry Pi Pico W gateway.

The configured Pico API endpoint is:

```text
http://192.168.4.1/api/data
```

The Pico W can provide sensor readings to the backend, which can then store and analyze the incoming data.

For deployment in an actual mine environment, the gateway address and communication configuration should be updated according to the deployed network.

---

# SMS Alerts

SUBSENTINEL AI supports SMS notifications through **Twilio**.

SMS alerts are triggered for:

```text
HIGH
CRITICAL
```

risk levels.

A cooldown period is implemented to prevent repeated alerts:

```text
10 minutes
```

---

# Twilio Configuration

Create a `.env` file in the project directory:

```text
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
```

Do not commit your `.env` file to GitHub.

Add this to `.gitignore`:

```text
.env
venv/
__pycache__/
*.pyc
mine_data.db
```

---

# Example Alert

A generated alert contains information similar to:

```text
SUBSENTINEL AI ALERT

Node: NODE_01
Risk: HIGH
Risk Score: 75
Time: 2026-XX-XX XX:XX:XX

Prototype monitoring alert.
```

---

# Dashboard

The frontend provides a centralized monitoring interface for viewing:

* Current mine status
* Connected monitoring nodes
* Sensor telemetry
* Risk level
* Risk score
* Activity levels
* Vibration levels
* Tilt levels
* Recent events
* Analytics
* System status

The dashboard is designed with a dark monitoring-center interface suitable for continuous monitoring.

---

# Machine Learning Workflow

```text
Sensor Data
     │
     ▼
Data Validation
     │
     ▼
Feature Creation
     │
     ├── Tilt
     ├── Vibration
     ├── Temperature
     ├── Humidity
     ├── Activity
     ├── 5-Sample Activity
     ├── 5-Sample Tilt
     └── 5-Sample Vibration
     │
     ▼
Isolation Forest
     │
     ▼
Anomaly Detection
     │
     ▼
Risk Assessment
     │
     ▼
Risk Score
     │
     ├── Dashboard
     │
     └── SMS Alert
```

---

# Important Note

SUBSENTINEL AI is currently a **prototype monitoring and anomaly-detection system**.

The risk rules and machine-learning model are intended for demonstration and development purposes. They should not be treated as a certified mine-safety system without extensive validation, field testing, sensor calibration, fail-safe design, and approval under applicable mining safety standards.

---

# Future Enhancements

* Real-time WebSocket communication
* More advanced time-series machine-learning models
* Sensor calibration and validation
* GPS/location-based monitoring
* Mine map visualization
* More sensor types
* Automatic incident reports
* Email and mobile notifications
* Improved anomaly detection using historical mine data
* Predictive subsidence modeling
* Cloud-based data storage
* Role-based authentication
* Multi-mine monitoring
* Hardware-level emergency shutdown mechanisms

---

# License

This project is developed as a prototype for educational, research, and demonstration purposes.

---

# Author

**Anees Ahmed A,Vignesh R, Sivagnanasubramaniyam, Harini Elangovan, Shanmathi A, Vishwa K**

SUBSENTINEL AI — AI-Enabled Mine Intelligence and Subsidence Monitoring System
