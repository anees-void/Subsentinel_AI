import pandas as pd


def create_features(df):

    if df is None or df.empty:

        return pd.DataFrame()


    data = df.copy()


    data["tilt"] = pd.to_numeric(
        data["tilt"],
        errors="coerce"
    ).fillna(0)


    data["vibration"] = pd.to_numeric(
        data["vibration"],
        errors="coerce"
    ).fillna(0)


    data["temperature"] = pd.to_numeric(
        data.get("temperature", 0),
        errors="coerce"
    ).fillna(0)


    data["humidity"] = pd.to_numeric(
        data.get("humidity", 0),
        errors="coerce"
    ).fillna(0)


    data["activity"] = (
        data["tilt"] +
        data["vibration"]
    )


    data["activity_5"] = (
        data["activity"]
        .rolling(5)
        .sum()
        .fillna(0)
    )


    data["tilt_5"] = (
        data["tilt"]
        .rolling(5)
        .sum()
        .fillna(0)
    )


    data["vibration_5"] = (
        data["vibration"]
        .rolling(5)
        .sum()
        .fillna(0)
    )


    return data