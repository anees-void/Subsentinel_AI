from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import sqlite3
from datetime import datetime, timedelta

import pandas as pd
from sklearn.ensemble import IsolationForest

import os
import json
import urllib.request
import threading
import time

from dotenv import load_dotenv
from twilio.rest import Client


# ============================================================
# SUBSENTINEL AI 2
# SERVER
# ============================================================

app = FastAPI(
    title="SUBSENTINEL AI 2",
    description="AI-enabled real-time mine subsidence monitoring prototype",
    version="2.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

DATABASE = "mine_data.db"


# ============================================================
# RASPBERRY PI PICO W GATEWAY
# ============================================================

PICO_API_URL = "http://192.168.4.1/api/data"

pico_last_seen = {}

pico_polling_started = False


# ============================================================
# TWILIO CONFIGURATION
# ============================================================

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv(
    "TWILIO_ACCOUNT_SID"
)

TWILIO_AUTH_TOKEN = os.getenv(
    "TWILIO_AUTH_TOKEN"
)

TWILIO_FROM_NUMBER = os.getenv(
    "TWILIO_PHONE_NUMBER"
)

# Keep your verified recipient number here
# or configure it through your .env file.
ALERT_TO_NUMBER = "+919003345004"


twilio_client = None


if (
    TWILIO_ACCOUNT_SID
    and TWILIO_AUTH_TOKEN
    and TWILIO_FROM_NUMBER
):

    twilio_client = Client(
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN
    )


# ============================================================
# SMS STATE
# ============================================================

last_alert_time = None

last_alert_risk = None

SMS_COOLDOWN_MINUTES = 10


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_database():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor_data (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp TEXT NOT NULL,

            node_id TEXT NOT NULL,

            tilt INTEGER NOT NULL,

            vibration INTEGER NOT NULL,

            temperature REAL DEFAULT 0,

            humidity REAL DEFAULT 0,

            crack REAL DEFAULT 0,

            sound REAL DEFAULT 0

        )
        """
    )

    conn.commit()

    conn.close()


# ============================================================
# ENSURE DATABASE COLUMNS
# ============================================================

def ensure_database_columns():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute(
        "PRAGMA table_info(sensor_data)"
    )

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    required_columns = {

        "temperature":
            "ALTER TABLE sensor_data ADD COLUMN temperature REAL DEFAULT 0",

        "humidity":
            "ALTER TABLE sensor_data ADD COLUMN humidity REAL DEFAULT 0",

        "crack":
            "ALTER TABLE sensor_data ADD COLUMN crack REAL DEFAULT 0",

        "sound":
            "ALTER TABLE sensor_data ADD COLUMN sound REAL DEFAULT 0"

    }

    for column, sql in required_columns.items():

        if column not in columns:

            try:

                cursor.execute(sql)

                print(
                    "Added database column:",
                    column
                )

            except Exception as e:

                print(
                    "DATABASE COLUMN ERROR:",
                    e
                )

    conn.commit()

    conn.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_database()

ensure_database_columns()


# ============================================================
# SEND SMS
# ============================================================

def send_sms(message):

    if twilio_client is None:

        print(
            "SMS ERROR: Twilio is not configured."
        )

        return False

    try:

        sms = twilio_client.messages.create(

            body=message,

            from_=TWILIO_FROM_NUMBER,

            to=ALERT_TO_NUMBER

        )

        print(
            "SMS SENT:",
            sms.sid
        )

        return True

    except Exception as e:

        print(
            "SMS ERROR:",
            e
        )

        return False


# ============================================================
# AUTOMATIC SMS ALERT
# ============================================================

def check_and_send_alert(
    node_id,
    risk_level,
    risk_score
):

    global last_alert_time

    global last_alert_risk

    if risk_level not in [
        "HIGH",
        "CRITICAL"
    ]:

        return


    now = datetime.now()


    if last_alert_time is not None:

        elapsed = (
            now - last_alert_time
        ).total_seconds() / 60

        if elapsed < SMS_COOLDOWN_MINUTES:

            print(
                "SMS cooldown active."
            )

            return


    message = (

        "SUBSENTINEL AI ALERT\n"

        f"Node: {node_id}\n"

        f"Risk: {risk_level}\n"

        f"Risk Score: {risk_score}\n"

        f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"

        "Prototype monitoring alert."
    )


    sent = send_sms(message)


    if sent:

        last_alert_time = now

        last_alert_risk = risk_level


# ============================================================
# GET NODE DATA
# ============================================================

def get_node_dataframe(node_id):

    conn = sqlite3.connect(
        DATABASE
    )

    query = """
        SELECT
            id,
            timestamp,
            node_id,
            tilt,
            vibration,
            temperature,
            humidity,
            crack,
            sound
        FROM sensor_data
        WHERE node_id = ?
        ORDER BY id ASC
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(node_id,)
    )

    conn.close()

    return df


# ============================================================
# AI RISK ANALYSIS
# ============================================================

def analyze_risk(node_id):

    df = get_node_dataframe(
        node_id
    )


    if df.empty:

        return {

            "risk_level": "LOW",

            "risk_score": 0,

            "anomaly_score": 0,

            "activity": 0,

            "activity_5": 0,

            "tilt_5": 0,

            "vibration_5": 0

        }


    df["activity"] = (
        df["tilt"].astype(int)
        +
        df["vibration"].astype(int)
    )


    latest = df.iloc[-1]


    activity = int(
        latest["activity"]
    )


    recent = df.tail(5)


    activity_5 = int(
        recent["activity"].sum()
    )


    tilt_5 = int(
        recent["tilt"].sum()
    )


    vibration_5 = int(
        recent["vibration"].sum()
    )


    # ========================================================
    # ISOLATION FOREST
    # ========================================================

    anomaly_score = 0


    if len(df) >= 5:

        try:

            features = df[
                [
                    "tilt",
                    "vibration",
                    "temperature",
                    "humidity"
                ]
            ].fillna(0)


            model = IsolationForest(

                n_estimators=100,

                contamination="auto",

                random_state=42

            )


            predictions = model.fit_predict(
                features
            )


            anomaly_score = int(
                predictions[-1] == -1
            )

        except Exception as e:

            print(
                "AI anomaly error:",
                e
            )


    # ========================================================
    # RISK RULES
    # ========================================================

    risk_level = "LOW"

    risk_score = 0


    if (
        vibration_5 >= 4
        and
        tilt_5 >= 4
    ):

        risk_level = "CRITICAL"

        risk_score = 90


    elif vibration_5 >= 3:

        risk_level = "HIGH"

        risk_score = 75


    elif tilt_5 >= 4:

        risk_level = "WARNING"

        risk_score = 55


    elif activity >= 1:

        risk_level = "WARNING"

        risk_score = 40


    if anomaly_score == 1:

        risk_score += 10


    if risk_score > 100:

        risk_score = 100


    return {

        "risk_level":
            risk_level,

        "risk_score":
            risk_score,

        "anomaly_score":
            anomaly_score,

        "activity":
            activity,

        "activity_5":
            activity_5,

        "tilt_5":
            tilt_5,

        "vibration_5":
            vibration_5

    }


# ============================================================
# PROCESS SENSOR DATA
# ============================================================

def receive_data(data):

    node_id = str(
        data.get(
            "node_id",
            "NODE_01"
        )
    )


    try:

        tilt = int(
            data.get(
                "tilt",
                0
            )
        )

    except:

        tilt = 0


    try:

        vibration = int(
            data.get(
                "vibration",
                0
            )
        )

    except:

        vibration = 0


    try:

        temperature = float(
            data.get(
                "temperature",
                0
            )
        )

    except:

        temperature = 0


    try:

        humidity = float(
            data.get(
                "humidity",
                0
            )
        )

    except:

        humidity = 0


    try:

        crack = float(
            data.get(
                "crack",
                0
            )
        )

    except:

        crack = 0


    try:

        sound = float(
            data.get(
                "sound",
                0
            )
        )

    except:

        sound = 0


    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO sensor_data
        (
            timestamp,
            node_id,
            tilt,
            vibration,
            temperature,
            humidity,
            crack,
            sound
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            node_id,
            tilt,
            vibration,
            temperature,
            humidity,
            crack,
            sound
        )
    )


    conn.commit()

    conn.close()


    ai = analyze_risk(
        node_id
    )


    check_and_send_alert(

        node_id,

        ai["risk_level"],

        ai["risk_score"]

    )


    print()
    print(
        "================================"
    )

    print(
        "DATA RECEIVED"
    )

    print(
        "Node:",
        node_id
    )

    print(
        "Tilt:",
        tilt
    )

    print(
        "Vibration:",
        vibration
    )

    print(
        "Temperature:",
        temperature
    )

    print(
        "Humidity:",
        humidity
    )

    print(
        "Risk:",
        ai["risk_level"]
    )

    print(
        "Score:",
        ai["risk_score"]
    )

    print(
        "================================"
    )


    return {

        "status":
            "success",

        "node_id":
            node_id,

        "timestamp":
            timestamp,

        "ai":
            ai

    }


# ============================================================
# PICO W — READ API
# ============================================================

def read_pico_data():

    try:

        with urllib.request.urlopen(

            PICO_API_URL,

            timeout=3

        ) as response:

            raw_data = (
                response
                .read()
                .decode("utf-8")
            )


            return json.loads(
                raw_data
            )


    except Exception as e:

        print(
            "PICO CONNECTION ERROR:",
            e
        )

        return None


# ============================================================
# PROCESS ONE PICO NODE
# ============================================================

def process_pico_node(
    node_data,
    fallback_node_id
):

    if not isinstance(
        node_data,
        dict
    ):

        return


    node_id = (

        node_data.get(
            "node_id"
        )

        or

        node_data.get(
            "nodeID"
        )

        or

        fallback_node_id

    )


    if node_data.get(
        "online"
    ) is False:

        return


    try:

        tilt = int(
            node_data.get(
                "tilt",
                0
            )
        )

    except:

        tilt = 0


    try:

        vibration = int(
            node_data.get(
                "vibration",
                0
            )
        )

    except:

        vibration = 0


    try:

        temperature = float(
            node_data.get(
                "temperature",
                28.0
            )
        )

    except:

        temperature = 28.0


    try:

        humidity = float(
            node_data.get(
                "humidity",
                60.0
            )
        )

    except:

        humidity = 60.0


    try:

        crack = float(
            node_data.get(
                "crack",
                0.0
            )
        )

    except:

        crack = 0.0


    try:

        sound = float(
            node_data.get(
                "sound",
                35.0
            )
        )

    except:

        sound = 35.0


    # ========================================================
    # PREVENT DUPLICATE INSERTS
    # ========================================================

    last_seen = (

        node_data.get(
            "lastSeen"
        )

        or

        node_data.get(
            "last_seen"
        )

    )


    if last_seen is not None:

        last_seen_key = str(
            last_seen
        )


        if (
            pico_last_seen.get(
                node_id
            )
            ==
            last_seen_key
        ):

            return


        pico_last_seen[
            node_id
        ] = last_seen_key


    data = {

        "node_id":
            node_id,

        "tilt":
            tilt,

        "vibration":
            vibration,

        "temperature":
            temperature,

        "humidity":
            humidity,

        "crack":
            crack,

        "sound":
            sound

    }


    print()
    print(
        "================================"
    )

    print(
        "PICO W -> FASTAPI"
    )

    print(
        "================================"
    )

    print(
        "Node:",
        node_id
    )

    print(
        "Tilt:",
        tilt
    )

    print(
        "Vibration:",
        vibration
    )

    print(
        "Temperature:",
        temperature
    )

    print(
        "Humidity:",
        humidity
    )


    try:

        receive_data(
            data
        )

        print(
            "Data saved to SQLite"
        )


    except Exception as e:

        print(
            "PICO DATA PROCESSING ERROR:",
            e
        )


    print(
        "================================"
    )


# ============================================================
# PICO W POLLING LOOP
# ============================================================

def pico_polling_loop():

    print()
    print(
        "================================"
    )

    print(
        "PICO W GATEWAY POLLING"
    )

    print(
        "================================"
    )

    print(
        "Pico API:",
        PICO_API_URL
    )

    print(
        "Status: STARTED"
    )

    print(
        "================================"
    )


    while True:

        pico_data = read_pico_data()


        if pico_data is not None:


            # =================================================
            # NODE 1
            # =================================================

            if "node1" in pico_data:

                process_pico_node(

                    pico_data["node1"],

                    "NODE_01"

                )


            # =================================================
            # NODE 2
            # =================================================

            if "node2" in pico_data:

                process_pico_node(

                    pico_data["node2"],

                    "NODE_02"

                )


            # =================================================
            # OPTIONAL ARRAY FORMAT
            # =================================================

            nodes = pico_data.get(
                "nodes"
            )


            if isinstance(
                nodes,
                list
            ):

                for index, node in enumerate(
                    nodes
                ):

                    if index == 0:

                        fallback = "NODE_01"

                    else:

                        fallback = "NODE_02"


                    process_pico_node(

                        node,

                        fallback

                    )


        time.sleep(2)


# ============================================================
# START PICO POLLING
# ============================================================

@app.on_event(
    "startup"
)
def start_pico_polling():

    global pico_polling_started


    if pico_polling_started:

        return


    pico_polling_started = True


    thread = threading.Thread(

        target=pico_polling_loop,

        daemon=True

    )


    thread.start()


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {

        "project":
            "SUBSENTINEL AI 2",

        "status":
            "ONLINE",

        "gateway":
            "Raspberry Pi Pico W",

        "pico_api":
            PICO_API_URL,

        "message":
            "Mine monitoring backend is running."

    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {

        "status":
            "healthy",

        "project":
            "SUBSENTINEL AI 2",

        "database":
            DATABASE,

        "pico_gateway":
            PICO_API_URL

    }


# ============================================================
# RECEIVE DATA
# ============================================================

@app.post("/data")
def data_endpoint(data: dict):

    return receive_data(
        data
    )


# ============================================================
# GET ALL SENSOR DATA
# ============================================================

@app.get("/data")
def get_data():

    conn = sqlite3.connect(
        DATABASE
    )

    query = """
        SELECT
            id,
            timestamp,
            node_id,
            tilt,
            vibration,
            temperature,
            humidity,
            crack,
            sound
        FROM sensor_data
        ORDER BY id DESC
    """


    cursor = conn.cursor()

    cursor.execute(
        query
    )


    rows = cursor.fetchall()


    conn.close()


    result = []


    for row in rows:

        result.append({

            "id":
                row[0],

            "timestamp":
                row[1],

            "node_id":
                row[2],

            "tilt":
                row[3],

            "vibration":
                row[4],

            "temperature":
                row[5],

            "humidity":
                row[6],

            "crack":
                row[7],

            "sound":
                row[8]

        })


    return {

        "status":
            "success",

        "count":
            len(result),

        "data":
            result

    }


# ============================================================
# STATUS
# ============================================================

@app.get("/status")
def status():

    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            timestamp,
            node_id,
            tilt,
            vibration,
            temperature,
            humidity
        FROM sensor_data
        ORDER BY id DESC
        LIMIT 1
        """
    )


    row = cursor.fetchone()


    conn.close()


    if row is None:

        return {

            "status":
                "NO_DATA"

        }


    ai = analyze_risk(
        row[1]
    )


    return {

        "status":
            "ONLINE",

        "timestamp":
            row[0],

        "node_id":
            row[1],

        "tilt":
            row[2],

        "vibration":
            row[3],

        "temperature":
            row[4],

        "humidity":
            row[5],

        "risk":
            ai

    }


# ============================================================
# NODES
# ============================================================

@app.get("/nodes")
def nodes():

    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            node_id,
            timestamp,
            tilt,
            vibration,
            temperature,
            humidity
        FROM sensor_data
        WHERE id IN (
            SELECT MAX(id)
            FROM sensor_data
            GROUP BY node_id
        )
        ORDER BY node_id
        """
    )


    rows = cursor.fetchall()


    conn.close()


    result = []


    for row in rows:

        ai = analyze_risk(
            row[0]
        )


        result.append({

            "node_id":
                row[0],

            "timestamp":
                row[1],

            "tilt":
                row[2],

            "vibration":
                row[3],

            "temperature":
                row[4],

            "humidity":
                row[5],

            "risk_level":
                ai["risk_level"],

            "risk_score":
                ai["risk_score"],

            "anomaly_score":
                ai["anomaly_score"]

        })


    return {

        "count":
            len(result),

        "nodes":
            result

    }


# ============================================================
# EVENTS
# ============================================================

@app.get("/events")
def events():

    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            id,
            timestamp,
            node_id,
            tilt,
            vibration,
            temperature,
            humidity
        FROM sensor_data
        WHERE
            tilt = 1
            OR vibration = 1
        ORDER BY id DESC
        LIMIT 100
        """
    )


    rows = cursor.fetchall()


    conn.close()


    result = []


    for row in rows:

        ai = analyze_risk(
            row[2]
        )


        result.append({

            "id":
                row[0],

            "timestamp":
                row[1],

            "node_id":
                row[2],

            "tilt":
                row[3],

            "vibration":
                row[4],

            "temperature":
                row[5],

            "humidity":
                row[6],

            "risk_level":
                ai["risk_level"],

            "risk_score":
                ai["risk_score"]

        })


    return {

        "count":
            len(result),

        "events":
            result

    }


# ============================================================
# ANALYTICS
# ============================================================

@app.get("/analytics")
def analytics():

    conn = sqlite3.connect(
        DATABASE
    )

    query = """
        SELECT
            timestamp,
            node_id,
            tilt,
            vibration,
            temperature,
            humidity
        FROM sensor_data
        ORDER BY id ASC
    """


    df = pd.read_sql_query(
        query,
        conn
    )


    conn.close()


    if df.empty:

        return {

            "status":
                "NO_DATA"

        }


    df["activity"] = (
        df["tilt"]
        +
        df["vibration"]
    )


    return {

        "status":
            "success",

        "total_records":
            int(len(df)),

        "total_nodes":
            int(
                df["node_id"]
                .nunique()
            ),

        "tilt_events":
            int(
                df["tilt"].sum()
            ),

        "vibration_events":
            int(
                df["vibration"].sum()
            ),

        "average_temperature":
            float(
                df["temperature"]
                .mean()
            ),

        "average_humidity":
            float(
                df["humidity"]
                .mean()
            ),

        "total_activity":
            int(
                df["activity"].sum()
            )

    }


# ============================================================
# 7-DAY ANALYTICS
# ============================================================

@app.get("/analytics/7days")
def analytics_7days():

    conn = sqlite3.connect(
        DATABASE
    )

    query = """
        SELECT
            timestamp,
            node_id,
            tilt,
            vibration,
            temperature,
            humidity
        FROM sensor_data
        ORDER BY id ASC
    """


    df = pd.read_sql_query(
        query,
        conn
    )


    conn.close()


    if df.empty:

        return {

            "status":
                "NO_DATA",

            "data":
                []

        }


    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )


    cutoff = (
        datetime.now()
        -
        timedelta(days=7)
    )


    df = df[
        df["timestamp"] >= cutoff
    ]


    if df.empty:

        return {

            "status":
                "NO_DATA",

            "data":
                []

        }


    df["date"] = (
        df["timestamp"]
        .dt
        .strftime("%Y-%m-%d")
    )


    grouped = (

        df.groupby("date")
        .agg({

            "tilt":
                "sum",

            "vibration":
                "sum",

            "node_id":
                "nunique"

        })
        .reset_index()

    )


    return {

        "status":
            "success",

        "data":
            grouped.to_dict(
                orient="records"
            )

    }


# ============================================================
# MINE
# ============================================================

@app.get("/mine")
def mine():

    return {

        "name":
            "SUBSENTINEL AI 2",

        "type":
            "Underground Coal Mine Monitoring Prototype",

        "gateway":
            "Raspberry Pi Pico W",

        "nodes":
            [

                "NODE_01",

                "NODE_02"

            ],

        "sensors":
            [

                "Tilt",

                "Vibration",

                "Temperature",

                "Humidity"

            ],

        "ai":
            "Isolation Forest + Rule Based Risk Engine"

    }


# ============================================================
# TEST SMS
# ============================================================

@app.get("/test-sms")
def test_sms():

    message = (

        "SUBSENTINEL AI 2 TEST ALERT\n"

        "This is a prototype SMS test."

    )


    sent = send_sms(
        message
    )


    return {

        "status":
            "sent"
            if sent
            else "failed"

    }


# ============================================================
# RUN INFORMATION
# ============================================================

@app.get("/system")
def system():

    return {

        "project":
            "SUBSENTINEL AI 2",

        "backend":
            "FastAPI",

        "database":
            "SQLite",

        "gateway":
            "Raspberry Pi Pico W",

        "gateway_ip":
            "192.168.4.1",

        "gateway_api":
            "/api/data",

        "nodes":
            2,

        "poll_interval":
            "2 seconds",

        "ai":
            "Isolation Forest",

        "risk_levels":
            [

                "LOW",

                "WARNING",

                "HIGH",

                "CRITICAL"

            ]

    }