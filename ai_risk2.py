import pandas as pd
from sklearn.ensemble import IsolationForest


def analyze_risk(df):

    if df is None or df.empty:

        return {
            "risk_level": "LOW",
            "risk_score": 0,
            "anomaly_score": 0,
            "activity": 0,
            "activity_5": 0,
            "tilt_5": 0,
            "vibration_5": 0
        }


    df = df.copy()


    df["tilt"] = pd.to_numeric(
        df["tilt"],
        errors="coerce"
    ).fillna(0)


    df["vibration"] = pd.to_numeric(
        df["vibration"],
        errors="coerce"
    ).fillna(0)


    df["activity"] = (
        df["tilt"] +
        df["vibration"]
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


    anomaly_score = 0


    if len(df) >= 5:

        try:

            features = df[
                [
                    "tilt",
                    "vibration"
                ]
            ].fillna(0)


            model = IsolationForest(
                n_estimators=100,
                contamination="auto",
                random_state=42
            )


            prediction = model.fit_predict(
                features
            )


            anomaly_score = int(
                prediction[-1] == -1
            )


        except Exception:

            anomaly_score = 0


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


    risk_score = min(
        risk_score,
        100
    )


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