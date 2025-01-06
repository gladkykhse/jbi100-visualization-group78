import numpy as np
import pandas as pd
from datetime import datetime


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
        temp["total_hours_worked"] == 0,
        0,
        temp["case_number"] / temp["total_hours_worked"] * 1e6,
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
        temp["total_hours_worked"] == 0,
        0,
        temp["death"] / temp["total_hours_worked"] * 1e8,
    )

    temp.drop(columns=["death", "total_hours_worked"], inplace=True)

    return temp.reset_index()


# def compute_agg_lost_workday_rate(df, column=None):
#     agg_cols = ["state_code", column] if column is not None else ["state_code"]
#     temp = df.groupby(agg_cols, observed=False).agg(
#         {
#             "dafw_num_away": "sum",
#             "total_hours_worked": "sum",
#         }
#     )
#     temp.fillna(0, inplace=True)
#     # days to hours
#     # temp["dafw_num_away"] *= 8

#     temp["lost_workday_rate"] = np.where(
#         temp["total_hours_worked"] == 0, 0, temp["dafw_num_away"] / temp["total_hours_worked"] * 1_000
#     )

#     temp.drop(columns=["dafw_num_away", "total_hours_worked"], inplace=True)


#     return temp.reset_index()
def compute_agg_lost_workday_rate(df, column=None):
    agg_cols = ["state_code", column] if column is not None else ["state_code"]

    # Group and aggregate the relevant columns
    temp = df.groupby(agg_cols, observed=False).agg(
        {
            "dafw_num_away": "sum",  # Sum of days away from work
            "djtr_num_tr": "sum",  # Sum of days job transfer/restriction
            "case_number": "count",  # Count of cases
        }
    )

    # Replace missing values with 0
    temp.fillna(0, inplace=True)

    # Combine missed days
    temp["total_lost_days"] = temp["dafw_num_away"] + temp["djtr_num_tr"]

    # Compute the lost workday rate per case
    temp["lost_workday_rate"] = np.where(temp["case_number"] == 0, 0, temp["total_lost_days"] / temp["case_number"])

    # Drop intermediate columns
    temp.drop(columns=["dafw_num_away", "djtr_num_tr", "total_lost_days"], inplace=True)

    return temp.reset_index()


def compute_agg_severity_index(df, column=None):
    agg_cols = ["state_code", column] if column is not None else ["state_code"]
    temp = df.groupby(agg_cols, observed=False).agg(
        {
            "dafw_num_away": "sum",
            "case_number": "count",
        }
    )
    temp.fillna(0, inplace=True)

    temp["severity_index"] = np.where(temp["case_number"] == 0, 0, temp["dafw_num_away"] / temp["case_number"])

    temp.drop(columns=["dafw_num_away", "case_number"], inplace=True)

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


def compute_agg_safety_score(df, column=None):
    stats = compute_agg_incident_rate_per_100k(df, column)
    stats["fatality_rate"] = compute_agg_fatality_rate_per_100k(df, column)["fatality_rate"]
    stats["lost_workday_rate"] = compute_agg_lost_workday_rate(df, column)["lost_workday_rate"]
    stats["severity_index"] = compute_agg_severity_index(df, column)["severity_index"]
    stats["death_to_incident"] = compute_death_to_incident_ratio(df, column)["death_to_incident"]

    stats["safety_score"] = (
        1.0 * stats["incident_rate"]
        + 10 * stats["fatality_rate"]
        + 0.1 * stats["lost_workday_rate"]
        + 1.0 * stats["severity_index"]
        + 1000 * stats["death_to_incident"]
    )

    return stats


region_incident_rates = compute_agg_incident_rate_per_100k(data)
region_fatality_rates = compute_agg_fatality_rate_per_100k(data)
region_lost_workday_rate = compute_agg_lost_workday_rate(data)
region_severity_index = compute_agg_severity_index(data)
region_death_to_incident = compute_death_to_incident_ratio(data)
region_safety_score = compute_agg_safety_score(data)

min_metric_values = {
    "incident_rate": region_incident_rates["incident_rate"].min(),
    "fatality_rate": region_fatality_rates["fatality_rate"].min(),
    "lost_workday_rate": region_lost_workday_rate["lost_workday_rate"].min(),
    "severity_index": region_severity_index["severity_index"].min(),
    "death_to_incident": region_death_to_incident["death_to_incident"].min(),
    "safety_score": region_safety_score["safety_score"].min(),
}

max_metric_values = {
    "incident_rate": region_incident_rates["incident_rate"].max(),
    "fatality_rate": region_fatality_rates["fatality_rate"].max(),
    "lost_workday_rate": region_lost_workday_rate["lost_workday_rate"].max(),
    "severity_index": region_severity_index["severity_index"].max(),
    "death_to_incident": region_death_to_incident["death_to_incident"].max(),
    "safety_score": region_safety_score["safety_score"].max(),
}

mean_metric_values = {
    "incident_rate": region_incident_rates["incident_rate"].mean(),
    "fatality_rate": region_fatality_rates["fatality_rate"].mean(),
    "lost_workday_rate": region_lost_workday_rate["lost_workday_rate"].mean(),
    "severity_index": region_severity_index["severity_index"].mean(),
    "death_to_incident": region_death_to_incident["death_to_incident"].mean(),
    "safety_score": region_safety_score["safety_score"].mean(),
}


def prepare_radar_data(state_code, start_date, end_date, filter_incident_types):
    start_date = datetime.fromisoformat(start_date)
    end_date = datetime.fromisoformat(end_date)
    if start_date == data["date_of_incident"].min() and end_date == data["date_of_incident"].max() and not filter_incident_types:
        radar_region_incident_rates = region_incident_rates
        radar_region_fatality_rates = region_fatality_rates
        radar_region_lost_workday_rate = region_lost_workday_rate
        radar_region_severity_index = region_severity_index
        radar_region_death_to_incident = region_death_to_incident
        radar_region_safety_score = region_safety_score
    elif start_date == data["date_of_incident"].min() and end_date == data["date_of_incident"].max():
        filtered_data = data[data["type_of_incident"].isin(filter_incident_types)]

        radar_region_incident_rates = compute_agg_incident_rate_per_100k(filtered_data)
        radar_region_fatality_rates = compute_agg_fatality_rate_per_100k(filtered_data)
        radar_region_lost_workday_rate = compute_agg_lost_workday_rate(filtered_data)
        radar_region_severity_index = compute_agg_severity_index(filtered_data)
        radar_region_death_to_incident = compute_death_to_incident_ratio(filtered_data)
        radar_region_safety_score = compute_agg_safety_score(filtered_data)
    elif not filter_incident_types:
        filtered_data = data[(data["date_of_incident"] >= start_date) & (data["date_of_incident"] <= end_date)]

        radar_region_incident_rates = compute_agg_incident_rate_per_100k(filtered_data)
        radar_region_fatality_rates = compute_agg_fatality_rate_per_100k(filtered_data)
        radar_region_lost_workday_rate = compute_agg_lost_workday_rate(filtered_data)
        radar_region_severity_index = compute_agg_severity_index(filtered_data)
        radar_region_death_to_incident = compute_death_to_incident_ratio(filtered_data)
        radar_region_safety_score = compute_agg_safety_score(filtered_data)
    else:
        filtered_data = data[(data["date_of_incident"] >= start_date) & (data["date_of_incident"] <= end_date)]
        filtered_data = filtered_data[filtered_data["type_of_incident"].isin(filter_incident_types)]

        radar_region_incident_rates = compute_agg_incident_rate_per_100k(filtered_data)
        radar_region_fatality_rates = compute_agg_fatality_rate_per_100k(filtered_data)
        radar_region_lost_workday_rate = compute_agg_lost_workday_rate(filtered_data)
        radar_region_severity_index = compute_agg_severity_index(filtered_data)
        radar_region_death_to_incident = compute_death_to_incident_ratio(filtered_data)
        radar_region_safety_score = compute_agg_safety_score(filtered_data)

    incident_rate = radar_region_incident_rates[radar_region_incident_rates["state_code"] == state_code]["incident_rate"].values[0]
    fatality_rate = radar_region_fatality_rates[radar_region_fatality_rates["state_code"] == state_code]["fatality_rate"].values[0]
    lost_workday_rate = radar_region_lost_workday_rate[radar_region_lost_workday_rate["state_code"] == state_code][
        "lost_workday_rate"
    ].values[0]
    severity_index = radar_region_severity_index[radar_region_severity_index["state_code"] == state_code]["severity_index"].values[
        0
    ]
    death_to_incident = radar_region_death_to_incident[radar_region_death_to_incident["state_code"] == state_code][
        "death_to_incident"
    ].values[0]
    safety_score = radar_region_safety_score[radar_region_safety_score["state_code"] == state_code]["safety_score"].values[0]

    radar_data = {
        "kpi": [
            "incident_rate",
            "fatality_rate",
            "lost_workday_rate",
            "severity_index",
            "death_to_incident",
            "safety_score",
        ],
        "value": [
            incident_rate,
            fatality_rate,
            lost_workday_rate,
            severity_index,
            death_to_incident,
            safety_score,
        ],
        "scaled_value": [
            (incident_rate - min_metric_values["incident_rate"])
            / (max_metric_values["incident_rate"] - min_metric_values["incident_rate"]),
            (fatality_rate - min_metric_values["fatality_rate"])
            / (max_metric_values["fatality_rate"] - min_metric_values["fatality_rate"]),
            (lost_workday_rate - min_metric_values["lost_workday_rate"])
            / (max_metric_values["lost_workday_rate"] - min_metric_values["lost_workday_rate"]),
            (severity_index - min_metric_values["severity_index"])
            / (max_metric_values["severity_index"] - min_metric_values["severity_index"]),
            (death_to_incident - min_metric_values["death_to_incident"])
            / (max_metric_values["death_to_incident"] - min_metric_values["death_to_incident"]),
            (safety_score - min_metric_values["safety_score"])
            / (max_metric_values["safety_score"] - min_metric_values["safety_score"]),
        ],
    }
    return pd.DataFrame(radar_data)


def prepare_state_data(
    start_date,
    end_date,
    filter_incident_types,
    agg_column="incident_month",
    kpi="incident_rate",
):
    filtered_data = data[(data["date_of_incident"] >= start_date) & (data["date_of_incident"] <= end_date)]
    if filter_incident_types:
        filtered_data = filtered_data[filtered_data["type_of_incident"].isin(filter_incident_types)]

    if kpi == "incident_rate":
        timeline_data = compute_agg_incident_rate_per_100k(filtered_data, agg_column)
        map_data = compute_agg_incident_rate_per_100k(filtered_data, None)
    elif kpi == "fatality_rate":
        timeline_data = compute_agg_fatality_rate_per_100k(filtered_data, agg_column)
        map_data = compute_agg_fatality_rate_per_100k(filtered_data, None)
    elif kpi == "lost_workday_rate":
        timeline_data = compute_agg_lost_workday_rate(filtered_data, agg_column)
        map_data = compute_agg_lost_workday_rate(filtered_data, None)
    elif kpi == "severity_index":
        timeline_data = compute_agg_severity_index(filtered_data, agg_column)
        map_data = compute_agg_severity_index(filtered_data, None)
    elif kpi == "death_to_incident":
        timeline_data = compute_death_to_incident_ratio(filtered_data, agg_column)
        map_data = compute_death_to_incident_ratio(filtered_data, None)
    else:
        timeline_data = compute_agg_safety_score(filtered_data, agg_column)
        map_data = compute_agg_safety_score(filtered_data, None)

    return map_data, timeline_data


def prepare_bar_chart_data(state_code, feature, kpi, start_date, end_date, filter_incident_types):
    temp = data[data["state_code"] == state_code]
    temp = temp[(temp["date_of_incident"] >= start_date) & (temp["date_of_incident"] <= end_date)]
    if filter_incident_types:
        temp = temp[temp["type_of_incident"].isin(filter_incident_types)]

    if kpi == "incident_rate":
        temp = compute_agg_incident_rate_per_100k(temp, feature)
    elif kpi == "fatality_rate":
        temp = compute_agg_fatality_rate_per_100k(temp, feature)
    elif kpi == "lost_workday_rate":
        temp = compute_agg_lost_workday_rate(temp, feature)
    elif kpi == "severity_index":
        temp = compute_agg_severity_index(temp, feature)
    elif kpi == "death_to_incident":
        temp = compute_death_to_incident_ratio(temp, feature)
    else:
        temp = compute_agg_safety_score(temp, feature)

    return temp


# def prepare_treemap_data(state_code, kpi):
#     temp = data[data["state_code"] == state_code]
#     return(
#         temp.groupby(
#             [
#                 "soc_description_1",
#                 "soc_description_2",
#                 "soc_description_3",
#                 "soc_description_4",
#             ],
#             observed=True,
#         )
#         .agg(count=("soc_description_1", "size"))
#         .reset_index()
#     )
