import pandas as pd

data = pd.read_parquet("datasets/processed_data.parquet")

categorical_features = [
    "state",
    "naics_year",
    "establishment_type",
    "size",
    "incident_outcome",
    "type_of_incident",
    "time_unknown",
    "soc_reviewed",
    "soc_description_1",
    "soc_description_2",
    "soc_description_3",
    "soc_description_4",
]


def prepare_map_data(start_date, end_date):
    filtered_data = data[(data["date_of_incident"] >= start_date) & (data["date_of_incident"] <= end_date)]
    return filtered_data.groupby("state_code", observed=False).size().reset_index(name="count")
