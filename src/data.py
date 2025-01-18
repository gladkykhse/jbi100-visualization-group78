from datetime import datetime

import numpy as np
import pandas as pd

### IN CASE OF NOT LOADING DATAFRAME


# def reduce_mem_usage(df):
#     """iterate through all the columns of a dataframe and modify the data type
#     to reduce memory usage.
#     """
#     start_mem = df.memory_usage().sum() / 1024**2
#     print("Memory usage of dataframe is {:.2f} MB".format(start_mem))

#     for col in df.columns:
#         with contextlib.suppress(Exception):
#             col_type = df[col].dtype

#             if col_type is not object:
#                 c_min = df[col].min()
#                 c_max = df[col].max()
#                 if str(col_type).startswith("int"):
#                     if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
#                         df[col] = df[col].astype(np.int8)
#                     elif (
#                         c_min > np.iinfo(np.int16).min
#                         and c_max < np.iinfo(np.int16).max
#                     ):
#                         df[col] = df[col].astype(np.int16)
#                     elif (
#                         c_min > np.iinfo(np.int32).min
#                         and c_max < np.iinfo(np.int32).max
#                     ):
#                         df[col] = df[col].astype(np.int32)
#                     elif (
#                         c_min > np.iinfo(np.int64).min
#                         and c_max < np.iinfo(np.int64).max
#                     ):
#                         df[col] = df[col].astype(np.int64)
#                 elif (
#                         c_min > np.finfo(np.float16).min
#                         and c_max < np.finfo(np.float16).max
#                     ):
#                     df[col] = df[col].astype(np.float16)
#                 elif (
#                     c_min > np.finfo(np.float32).min
#                     and c_max < np.finfo(np.float32).max
#                 ):
#                     df[col] = df[col].astype(np.float32)
#                 else:
#                     df[col] = df[col].astype(np.float64)
#     end_mem = df.memory_usage().sum() / 1024**2
#     print("Memory usage after optimization is: {:.2f} MB".format(end_mem))
#     print("Decreased by {:.1f}%".format(100 * (start_mem - end_mem) / start_mem))
#     print(df.info())
#     return df


data = pd.read_parquet("datasets/processed_data copy.parquet")


incident_types = sorted(data["type_of_incident"].unique())
state_codes = sorted(data["state_code"].unique())


def compute_agg_incident_rate(df, column=None):
    # Deduplicate for company-level fields
    deduplicated = df.drop_duplicates(subset=["state_code", "company_name"])
    agg_cols = ["state_code", column] if column is not None else ["state_code"]

    # Sum case numbers directly from injury-level data
    injury_data = (
        df.groupby(agg_cols, observed=False)
        .agg(case_number=("case_number", "count"))
        .reset_index()
    )

    # Aggregate deduplicated company-level data
    company_data = (
        deduplicated.groupby(agg_cols, observed=False)
        .agg(total_hours_worked=("total_hours_worked", "sum"))
        .reset_index()
    )

    # Merge and calculate incident rate
    temp = injury_data.merge(company_data, on=agg_cols, how="left")
    temp["incident_rate"] = np.where(
        temp["total_hours_worked"] > 0,
        temp["case_number"] / temp["total_hours_worked"] * 1e5,
        0,
    )
    return temp[agg_cols + ["incident_rate"]]


def compute_agg_fatality_rate(df, column=None):
    # Deduplicate for company-level fields
    # deduplicated = df.drop_duplicates(subset=["state_code", "company_name"])
    agg_cols = ["state_code", column] if column is not None else ["state_code"]

    # Sum fatalities directly from injury-level data
    temp = (
        df.groupby(agg_cols, observed=False)
        .agg(death=("death", "sum"), case_number=("case_number", "count"))
        .reset_index()
    )

    # Aggregate deduplicated company-level data
    # company_data = (
    #     deduplicated.groupby(agg_cols, observed=False)
    #     .agg(total_hours_worked=("total_hours_worked", "sum"))
    #     .reset_index()
    # )

    # Merge and calculate fatality rate
    # temp = injury_data.merge(company_data, on=agg_cols, how="left")
    temp["fatality_rate"] = np.where(
        temp["case_number"] > 0,
        temp["death"] / temp["case_number"] * 1e4,
        0,
    )
    return temp[agg_cols + ["fatality_rate"]]


def compute_agg_lost_workday_rate(df, column=None):
    agg_cols = ["state_code", column] if column is not None else ["state_code"]

    # Sum injury-level data
    injury_data = (
        df.groupby(agg_cols, observed=False)
        .agg(
            dafw_num_away=("dafw_num_away", "sum"),
            djtr_num_tr=("djtr_num_tr", "sum"),
            case_number=("case_number", "count"),
        )
        .reset_index()
    )

    # Calculate lost workdays and rate
    injury_data["total_lost_days"] = (
        injury_data["dafw_num_away"] + injury_data["djtr_num_tr"]
    )
    injury_data["lost_workday_rate"] = np.where(
        injury_data["case_number"] > 0,
        injury_data["total_lost_days"] / injury_data["case_number"],
        0,
    )
    return injury_data[agg_cols + ["lost_workday_rate"]]


# def compute_death_to_incident_ratio(df, column=None):
#     # No adjustment needed as all fields are injury-level data
#     agg_cols = ["state_code", column] if column is not None else ["state_code"]
#     temp = (
#         df.groupby(agg_cols, observed=False)
#         .agg(
#             death=("death", "sum"),
#             case_number=("case_number", "count"),
#         )
#         .reset_index()
#     )

#     temp["death_to_incident"] = np.where(
#         temp["case_number"] > 0,
#         temp["death"] / temp["case_number"] * 1e4,
#         0,
#     )
#     return temp[agg_cols + ["death_to_incident"]]


def compute_workforce_exposure(df, column=None):
    # Deduplicate for company-level fields
    deduplicated = df.drop_duplicates(subset=["state_code", "company_name"])
    agg_cols = ["state_code", column] if column is not None else ["state_code"]

    # Sum injury-level data
    injury_data = (
        df.groupby(agg_cols, observed=False)
        .agg(case_number=("case_number", "count"))
        .reset_index()
    )

    # Aggregate deduplicated company-level data
    company_data = (
        deduplicated.groupby(agg_cols, observed=False)
        .agg(annual_average_employees=("annual_average_employees", "sum"))
        .reset_index()
    )

    # Merge and calculate workforce exposure
    temp = injury_data.merge(company_data, on=agg_cols, how="left")
    temp["workforce_exposure"] = np.where(
        temp["case_number"] > 0,
        temp["case_number"] / temp["annual_average_employees"] * 1e2,
        0,
    )
    return temp[agg_cols + ["workforce_exposure"]]


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
        compute_workforce_exposure(df, column),
        on=["state_code"] + ([column] if column else []),
        how="left",
    )
    # stats = stats.merge(
    #     compute_death_to_incident_ratio(df, column),
    #     on=["state_code"] + ([column] if column else []),
    #     how="left",
    # )
    stats["danger_score"] = (
        2.38 * stats["incident_rate"]
        + 3.33 * stats["fatality_rate"]
        + 0.37 * stats["lost_workday_rate"]
        + 1.4 * stats["workforce_exposure"]
    )
    return stats


kpi_name_function_mapping = {
    "incident_rate": compute_agg_incident_rate,
    "fatality_rate": compute_agg_fatality_rate,
    "lost_workday_rate": compute_agg_lost_workday_rate,
    "workforce_exposure": compute_workforce_exposure,
    # "death_to_incident": compute_death_to_incident_ratio,
    "danger_score": compute_agg_safety_score,
}

region_safety_score = compute_agg_safety_score(data)

# Initialize dictionaries to store min, max, and mean
min_metric_values = {}
max_metric_values = {}
mean_metric_values = {}

# Single loop to calculate all statistics
for metric in kpi_name_function_mapping:
    column_data = region_safety_score[metric]
    min_metric_values[metric] = column_data.min()
    max_metric_values[metric] = column_data.max()
    mean_metric_values[metric] = column_data.mean()


def filter_data(df, start_date, end_date, filter_incident_types):
    start_date = datetime.fromisoformat(start_date)
    end_date = datetime.fromisoformat(end_date)

    # Determine if filtering is necessary
    use_precomputed = (
        start_date == df["date_of_incident"].min()
        and end_date == df["date_of_incident"].max()
    )

    if use_precomputed and not filter_incident_types:
        return df  # Return unfiltered dataset if precomputed can be used

    # Apply filtering
    filtered_data = df[
        (df["date_of_incident"] >= start_date) & (df["date_of_incident"] <= end_date)
    ]
    if filter_incident_types:
        filtered_data = filtered_data[
            filtered_data["type_of_incident"].isin(filter_incident_types)
        ]

    return filtered_data


def prepare_mean_radar_data(radar_region_safety_score):
    mean_values = radar_region_safety_score.iloc[:, 1:].mean()

    # Add the mean values as new columns to the dataframe
    for col in mean_values.index:
        radar_region_safety_score[f"mean_{col}"] = mean_values[col]

    return radar_region_safety_score


def calculate_mean_values(min_metric_values, max_metric_values, metrics, mean_values):
    return [
        (
            (mean_value - min_metric_values[metric])
            / (max_metric_values[metric] - min_metric_values[metric])
            if max_metric_values[metric] > min_metric_values[metric]
            else 0
        )
        for metric, mean_value in zip(metrics, mean_values)
    ]


def prepare_radar_data(df, state_code):
    # Compute radar region safety score
    if df is data:  # No filtering applied, use precomputed values
        radar_region_safety_score = region_safety_score
    else:
        radar_region_safety_score = compute_agg_safety_score(df)

    radar_region_safety_score = prepare_mean_radar_data(radar_region_safety_score)

    # Extract metrics
    metrics = [
        "incident_rate",
        "fatality_rate",
        "lost_workday_rate",
        "workforce_exposure",
        "danger_score",
    ]
    metric_values = radar_region_safety_score.loc[
        radar_region_safety_score["state_code"] == state_code, metrics
    ].squeeze()

    # Scale metrics
    scaled_values = [
        (
            (metric_values[metric] - min_metric_values[metric])
            / (max_metric_values[metric] - min_metric_values[metric])
            if max_metric_values[metric] > min_metric_values[metric]
            else 0
        )
        for metric in metrics
    ]
    mean_values = [
        radar_region_safety_score[f"mean_{metric}"].iloc[0] for metric in metrics
    ]

    scaled_mean_values = calculate_mean_values(
        min_metric_values, max_metric_values, metrics, mean_values
    )

    # Construct radar data
    radar_data = {
        "kpi": metrics,
        "value": metric_values.tolist(),
        "scaled_value": scaled_values,
        "mean_value": mean_values,
        "scaled_mean_value": scaled_mean_values,
    }
    return pd.DataFrame(radar_data)


def prepare_state_data(df, kpi="incident_rate"):
    # Deduplicate company-level fields
    deduplicated = df.drop_duplicates(subset=["state_code", "company_name"])

    # Aggregate deduplicated company-level data
    company_data = (
        deduplicated.groupby("state_code", observed=False)
        .agg(
            annual_average_employees_median=("annual_average_employees", "mean"),
            annual_average_employees_sum=("annual_average_employees", "sum"),
            total_hours_worked=("total_hours_worked", "mean"),
        )
        .reset_index()
    )

    # Aggregate injury-level data
    injury_data = (
        df.groupby("state_code", observed=False)
        .agg(
            dafw_num_away=("dafw_num_away", "mean"),
            djtr_num_tr=("djtr_num_tr", "mean"),
            death=("death", "mean"),
            case_number=("case_number", "count"),
        )
        .reset_index()
    )

    # Merge company-level and injury-level data
    aggregated_data = pd.merge(company_data, injury_data, on="state_code", how="inner")

    # Calculate injury density using corrected annual_average_employees_sum
    aggregated_data["injury_density"] = np.where(
        aggregated_data["annual_average_employees_median"] > 0,
        aggregated_data["case_number"]
        / aggregated_data["annual_average_employees_sum"],
        0,
    )

    # Merge with the KPI-specific function output
    return pd.merge(
        aggregated_data,
        kpi_name_function_mapping[kpi](df),
        on="state_code",
        how="inner",
    )


def prepare_treemap_data(df, state_code, kpi):
    temp = df[df["state_code"] == state_code]

    # Select the metric function
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


def prepare_scatter_plot(df, state):
    # Filter data for the state of Ohio
    aggregated_data = (
        df[df["state_code"] == state]
        .groupby("naics_description_5", observed=True)
        .agg(
            {
                "case_number": "count",
                "time_started_work": "mean",
                "time_of_incident": "mean",
                "establishment_type": lambda x: x.mode().iloc[0],
            }
        )
        .reset_index()
    )

    # Format time for hover information
    aggregated_data["time_started_work_str"] = aggregated_data[
        "time_started_work"
    ].dt.strftime("%H:%M")
    aggregated_data["time_of_incident_str"] = aggregated_data[
        "time_of_incident"
    ].dt.strftime("%H:%M")

    # Unique incident outcomes
    return aggregated_data


def prepare_stacked_bar_chart(df, state):
    filtered_data = df.query(
        "state_code == @state & establishment_type != 'Not Stated' & establishment_type != 'Invalid Entry'"
    )

    # Aggregate the data: count incidents by type and establishment
    aggregated_data = (
        filtered_data.groupby(["incident_outcome", "establishment_type"], observed=True)
        .size()
        .reset_index(name="count")
    )

    # Pivot the data for a stacked bar chart structure
    pivot_data = aggregated_data.pivot(
        index="incident_outcome", columns="establishment_type", values="count"
    ).fillna(0)
    return pivot_data.div(pivot_data.sum(axis=1), axis=0).reset_index()
