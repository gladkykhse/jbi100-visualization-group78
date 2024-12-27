import numpy as np
import pandas as pd

data = pd.read_parquet("datasets/processed_data.parquet")
data["incident_year"] = data["date_of_incident"].dt.year
data["incident_month"] = data["date_of_incident"].dt.month
data["incident_weekday"] = data["date_of_incident"].dt.weekday
data["death"] = data["date_of_death"].notna().astype(np.int32)


incident_types = sorted(data["type_of_incident"].unique())
state_codes = sorted(data["state_code"].unique())


def compute_agg_incident_rate_per_100k(df, column=None):
    agg_cols = ["state_code", column] if column is not None else ["state_code"]
    temp = df.groupby(agg_cols, observed=False).agg(
        {
            "case_number": "count",
            "total_hours_worked": "sum",
        }
    )

    temp.fillna(0, inplace=True)

    temp["incident_rate"] = np.where(
        temp["total_hours_worked"] == 0, 0, temp["case_number"] / temp["total_hours_worked"] * 100_000
    )

    temp.drop(columns=["case_number", "total_hours_worked"], inplace=True)

    return temp.reset_index()


def compute_agg_fatality_rate_per_100k(df, column=None):
    agg_cols = ["state_code", column] if column is not None else ["state_code"]
    temp = df.groupby(agg_cols, observed=False).agg(
        {
            "death": "sum",
            "total_hours_worked": "sum",
        }
    )

    temp.fillna(0, inplace=True)

    temp["fatality_rate"] = np.where(
        temp["total_hours_worked"] == 0, 0, temp["death"] / temp["total_hours_worked"] * 100_000
    )

    temp.drop(columns=["death", "total_hours_worked"], inplace=True)

    return temp.reset_index()


def compute_death_to_incident_ratio(df, column=None):
    agg_cols = ["state_code", column] if column is not None else ["state_code"]
    temp = df.groupby(agg_cols, observed=False).agg(
        {
            "death": "sum",
            "case_number": "count",
        }
    )

    temp.fillna(0, inplace=True)

    temp["death_to_incident"] = np.where(temp["case_number"] == 0, 0, temp["death"] / temp["case_number"])

    temp.drop(columns=["death", "case_number"], inplace=True)

    return temp.reset_index()


region_incident_rates = compute_agg_incident_rate_per_100k(data)
region_fatality_rates = compute_agg_fatality_rate_per_100k(data)
region_death_to_incident = compute_death_to_incident_ratio(data)

min_metric_values = {
    "incident_rate": region_incident_rates["incident_rate"].min(),
    "fatality_rate": region_fatality_rates["fatality_rate"].min(),
    "death_to_incident": region_death_to_incident["death_to_incident"].min(),
}

max_metric_values = {
    "incident_rate": region_incident_rates["incident_rate"].max(),
    "fatality_rate": region_fatality_rates["fatality_rate"].max(),
    "death_to_incident": region_death_to_incident["death_to_incident"].max(),
}

mean_metric_values = {
    "incident_rate": region_incident_rates["incident_rate"].mean(),
    "fatality_rate": region_fatality_rates["fatality_rate"].mean(),
    "death_to_incident": region_death_to_incident["death_to_incident"].mean(),
}


def prepare_radar_data(state_code):
    incident_rate = region_incident_rates[region_incident_rates["state_code"] == state_code]["incident_rate"].values[0]
    fatality_rate = region_fatality_rates[region_fatality_rates["state_code"] == state_code]["fatality_rate"].values[0]
    death_to_incident_rate = region_death_to_incident[region_death_to_incident["state_code"] == state_code][
        "death_to_incident"
    ].values[0]

    radar_data = {
        "kpi": ["incident_rate", "fatality_rate", "death_to_incident"],
        "value": [
            incident_rate,
            fatality_rate,
            death_to_incident_rate,
        ],
        "scaled_value": [
            (incident_rate - min_metric_values["incident_rate"])
            / (max_metric_values["incident_rate"] - min_metric_values["incident_rate"]),
            (fatality_rate - min_metric_values["fatality_rate"])
            / (max_metric_values["fatality_rate"] - min_metric_values["fatality_rate"]),
            (death_to_incident_rate - min_metric_values["death_to_incident"])
            / (max_metric_values["death_to_incident"] - min_metric_values["death_to_incident"]),
        ],
    }
    return pd.DataFrame(radar_data)


def prepare_state_data(start_date, end_date, filter_incident_types, agg_column="incident_month", kpi="incident_rate"):
    filtered_data = data[(data["date_of_incident"] >= start_date) & (data["date_of_incident"] <= end_date)]
    if filter_incident_types:
        filtered_data = filtered_data[filtered_data["type_of_incident"].isin(filter_incident_types)]

    if kpi == "incident_rate":
        stats = compute_agg_incident_rate_per_100k(filtered_data, agg_column)
    elif kpi == "fatality_rate":
        stats = compute_agg_fatality_rate_per_100k(filtered_data, agg_column)
    elif kpi == "death_to_incident":
        stats = compute_death_to_incident_ratio(filtered_data, agg_column)

    return stats


def prepare_bar_chart_data(state_code, feature, kpi):
    temp = data[data["state_code"] == state_code]

    if kpi == "incident_rate":
        temp = compute_agg_incident_rate_per_100k(temp, feature)
    elif kpi == "fatality_rate":
        temp = compute_agg_fatality_rate_per_100k(temp, feature)
    elif kpi == "death_to_incident":
        temp = compute_death_to_incident_ratio(temp, feature)

    return temp

