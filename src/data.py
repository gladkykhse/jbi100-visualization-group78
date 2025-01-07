from datetime import datetime

import numpy as np
import pandas as pd

data = pd.read_parquet("datasets/processed_data.parquet")
data["incident_year"] = data["date_of_incident"].dt.year
data["incident_month"] = data["date_of_incident"].dt.month
data["incident_weekday"] = data["date_of_incident"].dt.weekday
data["death"] = data["date_of_death"].notna().astype(np.int32)


incident_types = sorted(data["type_of_incident"].unique())
state_codes = sorted(data["state_code"].unique())


def compute_agg_incident_rate(df, column=None):
    agg_cols = ["state_code", column] if column is not None else ["state_code"]
    temp = (
        df.groupby(agg_cols, observed=False)
        .agg(
            case_number=("case_number", "count"),
            total_hours_worked=("total_hours_worked", "sum"),
        )
        .reset_index()
    )

    temp["incident_rate"] = np.where(
        temp["total_hours_worked"] > 0,
        temp["case_number"] / temp["total_hours_worked"] * 1e7,
        0,
    )
    return temp[agg_cols + ["incident_rate"]]


def compute_agg_fatality_rate(df, column=None):
    agg_cols = ["state_code", column] if column is not None else ["state_code"]
    temp = (
        df.groupby(agg_cols, observed=False)
        .agg(
            death=("death", "sum"),
            total_hours_worked=("total_hours_worked", "sum"),
        )
        .reset_index()
    )

    temp["fatality_rate"] = np.where(
        temp["total_hours_worked"] > 0,
        temp["death"] / temp["total_hours_worked"] * 1e10,
        0,
    )
    return temp[agg_cols + ["fatality_rate"]]


def compute_agg_lost_workday_rate(df, column=None):
    agg_cols = ["state_code", column] if column is not None else ["state_code"]
    temp = (
        df.groupby(agg_cols, observed=False)
        .agg(
            dafw_num_away=("dafw_num_away", "sum"),
            djtr_num_tr=("djtr_num_tr", "sum"),
            case_number=("case_number", "count"),
        )
        .reset_index()
    )

    temp["total_lost_days"] = temp["dafw_num_away"] + temp["djtr_num_tr"]
    temp["lost_workday_rate"] = np.where(
        temp["case_number"] > 0, temp["total_lost_days"] / temp["case_number"], 0
    )
    return temp[agg_cols + ["lost_workday_rate"]]


def compute_death_to_incident_ratio(df, column=None):
    agg_cols = ["state_code", column] if column is not None else ["state_code"]
    temp = (
        df.groupby(agg_cols, observed=False)
        .agg(
            death=("death", "sum"),
            case_number=("case_number", "count"),
        )
        .reset_index()
    )

    temp["death_to_incident"] = np.where(
        temp["case_number"] > 0, temp["death"] / temp["case_number"] * 1e4, 0
    )
    return temp[agg_cols + ["death_to_incident"]]


def compute_agg_severity_index(df, column=None):
    agg_cols = ["state_code", column] if column is not None else ["state_code"]
    temp = (
        df.groupby(agg_cols, observed=False)
        .agg(
            dafw_num_away=("dafw_num_away", "sum"),
            case_number=("case_number", "count"),
        )
        .reset_index()
    )

    temp["severity_index"] = np.where(
        temp["case_number"] > 0, temp["dafw_num_away"] / temp["case_number"], 0
    )
    return temp[agg_cols + ["severity_index"]]


def compute_agg_safety_score(df, column=None):
    stats = compute_agg_incident_rate(df, column)
    stats = stats.merge(
        compute_agg_fatality_rate(df, column),
        on=["state_code"] + ([column] if column else []),
        how="left",
    )
    stats = stats.merge(
        compute_agg_lost_workday_rate(df, column),
        on=["state_code"] + ([column] if column else []),
        how="left",
    )
    stats = stats.merge(
        compute_agg_severity_index(df, column),
        on=["state_code"] + ([column] if column else []),
        how="left",
    )
    stats = stats.merge(
        compute_death_to_incident_ratio(df, column),
        on=["state_code"] + ([column] if column else []),
        how="left",
    )

    stats["safety_score"] = (
        0.5 * stats["incident_rate"]
        + 1 * stats["fatality_rate"]
        + 0.25 * stats["lost_workday_rate"]
        + 0.45 * stats["severity_index"]
        + 1 * stats["death_to_incident"]
    )
    return stats


kpi_name_function_mapping = {
    "incident_rate": compute_agg_incident_rate,
    "fatality_rate": compute_agg_fatality_rate,
    "lost_workday_rate": compute_agg_lost_workday_rate,
    "severity_index": compute_agg_severity_index,
    "death_to_incident": compute_death_to_incident_ratio,
    "safety_score": compute_agg_safety_score,
}

region_safety_score = compute_agg_safety_score(data)

# Initialize dictionaries to store min, max, and mean
min_metric_values = {}
max_metric_values = {}
mean_metric_values = {}

# Single loop to calculate all statistics
for metric in kpi_name_function_mapping.keys():
    column_data = region_safety_score[metric]
    min_metric_values[metric] = column_data.min()
    max_metric_values[metric] = column_data.max()
    mean_metric_values[metric] = column_data.mean()


def prepare_radar_data(state_code, start_date, end_date, filter_incident_types):
    start_date = datetime.fromisoformat(start_date)
    end_date = datetime.fromisoformat(end_date)

    # Determine if we can use precomputed values
    use_precomputed = (
        start_date == data["date_of_incident"].min()
        and end_date == data["date_of_incident"].max()
    )

    # Filter data if necessary
    if not use_precomputed or filter_incident_types:
        filtered_data = data[
            (data["date_of_incident"] >= start_date)
            & (data["date_of_incident"] <= end_date)
        ]
        if filter_incident_types:
            filtered_data = filtered_data[
                filtered_data["type_of_incident"].isin(filter_incident_types)
            ]
        radar_region_safety_score = compute_agg_safety_score(filtered_data)
    else:
        radar_region_safety_score = region_safety_score

    # Extract metrics
    metrics = [
        "incident_rate",
        "fatality_rate",
        "lost_workday_rate",
        "severity_index",
        "death_to_incident",
        "safety_score",
    ]
    metric_values = radar_region_safety_score.loc[
        radar_region_safety_score["state_code"] == state_code, metrics
    ].squeeze()

    # Scale metrics
    scaled_values = [
        (metric_values[metric] - min_metric_values[metric])
        / (max_metric_values[metric] - min_metric_values[metric])
        for metric in metrics
    ]

    # Construct radar data
    radar_data = {
        "kpi": metrics,
        "value": metric_values.tolist(),
        "scaled_value": scaled_values,
    }
    return pd.DataFrame(radar_data)


def prepare_state_data(
    start_date,
    end_date,
    filter_incident_types,
    agg_column="incident_month",
    kpi="incident_rate",
):
    filtered_data = data[
        (data["date_of_incident"] >= start_date)
        & (data["date_of_incident"] <= end_date)
    ]
    if filter_incident_types:
        filtered_data = filtered_data[
            filtered_data["type_of_incident"].isin(filter_incident_types)
        ]
    func = kpi_name_function_mapping[kpi]

    return func(filtered_data, None), func(filtered_data, agg_column)


def prepare_bar_chart_data(
    state_code, feature, kpi, start_date, end_date, filter_incident_types
):
    temp = data[data["state_code"] == state_code]
    temp = temp[
        (temp["date_of_incident"] >= start_date)
        & (temp["date_of_incident"] <= end_date)
    ]
    if filter_incident_types:
        temp = temp[temp["type_of_incident"].isin(filter_incident_types)]
    return kpi_name_function_mapping[kpi](temp, feature)


def prepare_treemap_data(state_code, kpi, start_date, end_date, incident_types):
    temp = data[data["state_code"] == state_code]
    temp = temp[
        (temp["date_of_incident"] >= start_date)
        & (temp["date_of_incident"] <= end_date)
    ]
    if incident_types:
        temp = temp[temp["type_of_incident"].isin(incident_types)]
    metric_function = kpi_name_function_mapping[kpi]
    return (
        temp.query(
            "soc_description_1 != 'Insufficient info' & soc_description_1 != 'Not assigned'"
        )
        .groupby(["soc_description_1", "soc_description_2"], observed=True)
        .agg(
            count=(
                "soc_description_1",
                "size",
            ),  # Count the number of rows in each group
            metric=(
                "soc_description_1",
                lambda group: metric_function(temp.loc[group.index])
                .query(f"state_code == '{state_code}'")
                .iloc[0, -1],
            ),
        )
        .reset_index()
    )
