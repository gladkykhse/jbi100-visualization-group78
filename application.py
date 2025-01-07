import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from flask import Flask

from src.data import (
    prepare_bar_chart_data,
    prepare_radar_data,
    prepare_state_data,
    prepare_treemap_data,
)
# from src.mappings import reverse_dropdown_options
from src.layouts import main_layout
from src.visualizations import (
    create_grouped_bar_chart,
    create_map,
    create_radar_chart,
    create_timeline,
    create_treemap,
)

application = Flask(__name__)

app = dash.Dash(__name__, server=application)
app.layout = main_layout


@app.callback(
    [
        Output("date-picker-container", "style"),
        Output("incident-filter-container", "style"),
        Output("time-period-container", "style"),
        Output("kpi-select-container", "style"),
        Output("state-dropdown-container", "style"),
    ],
    [Input("tabs", "value")],
)
def update_left_menu_visibility(tab_name):
    if tab_name == "state_analysis_tab":
        return (
            {"display": "block"},
            {"display": "block"},
            {"display": "block"},
            {"display": "block"},
            {"display": "none"},
        )
    elif tab_name == "metric_analysis_tab":
        return (
            {"display": "block"},
            {"display": "block"},
            {"display": "none"},
            {"display": "none"},
            {"display": "block"},
        )
    return {"display": "none"}, {"display": "none"}


@app.callback(
    [
        Output("bar-chart-size", "figure"),
        Output("bar-chart-sector", "figure"),
        Output("bar-chart-industry", "figure"),
        Output("bar-chart-soc", "figure"),
    ],
    [
        Input("radar-chart", "clickData"),
        Input("state-dropdown", "value"),
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date"),
        Input("incident-filter-dropdown", "value"),
    ],
)
def update_bar_charts(click_data, state_code, start_date, end_date, incident_types):
    selected_kpi = "incident_rate"
    if click_data and "points" in click_data:
        # selected_kpi = reverse_dropdown_options[click_data["points"][0]["theta"]]
        selected_kpi = click_data["points"][0]["theta"].lower().replace(" ", "_")

    size_data = prepare_bar_chart_data(
        state_code, "size", selected_kpi, start_date, end_date, incident_types
    )
    establishment_type_data = prepare_bar_chart_data(
        state_code,
        "establishment_type",
        selected_kpi,
        start_date,
        end_date,
        incident_types,
    )
    soc_description_1_data = prepare_bar_chart_data(
        state_code,
        "soc_description_1",
        selected_kpi,
        start_date,
        end_date,
        incident_types,
    )
    type_of_incident_data = prepare_bar_chart_data(
        state_code,
        "type_of_incident",
        selected_kpi,
        start_date,
        end_date,
        incident_types,
    )

    return (
        create_grouped_bar_chart(size_data, "size", selected_kpi),
        create_grouped_bar_chart(
            establishment_type_data, "establishment_type", selected_kpi
        ),
        create_grouped_bar_chart(
            soc_description_1_data, "soc_description_1", selected_kpi
        ),
        create_grouped_bar_chart(
            type_of_incident_data, "type_of_incident", selected_kpi
        ),
    )


@app.callback(
    Output("selected_state", "data"),
    [Input("map-container", "clickData")],
    [State("selected_state", "data")],
)
def update_selected_state(click_data, current_state):
    if click_data:
        clicked_state = click_data["points"][0]["location"]  # Get clicked state
        if clicked_state == current_state:
            return None  # Deselect if the same state is clicked again
        return clicked_state  # Update to the newly clicked state
    return current_state  # Retain the current state if no new click


@app.callback(
    Output("content", "children"),
    Output("content-metric-analysis", "children"),
    [
        Input("tabs", "value"),
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date"),
        Input("incident-filter-dropdown", "value"),
        Input("kpi-select-dropdown", "value"),
        Input("time-period-dropdown", "value"),
        Input("selected_state", "data"),
        Input("state-dropdown", "value"),
    ],
)
def update_tab_contents(
    tab_name,
    start_date,
    end_date,
    incident_types,
    kpi,
    time_period,
    selected_state,
    dropdown_state,
):
    state_analysis_content = html.Div()
    metric_analysis_content = html.Div()

    if (
        tab_name == "state_analysis_tab"
        and start_date
        and end_date
        and kpi
        and time_period
    ):
        map_data, timeline_data = prepare_state_data(
            start_date, end_date, incident_types, time_period, kpi
        )
        if not map_data.empty and not timeline_data.empty:
            state_analysis_content = html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "flexDirection": "column",
                    "padding": "10px",
                },
                children=[
                    html.Div(
                        dcc.Graph(
                            figure=create_map(map_data, kpi, selected_state),
                            id="map-container",
                        ),
                        style={"flex": "1", "height": "500px"},
                    ),
                    html.Div(
                        dcc.Graph(
                            figure=create_timeline(
                                timeline_data, time_period, kpi, selected_state
                            )
                        ),
                        style={"flex": "1", "height": "500px"},
                    ),
                ],
            )
        else:
            state_analysis_content = html.Div(
                html.H2("No data for selected date range.", style="margin: 1em 2em")
            )

    if tab_name == "metric_analysis_tab" and dropdown_state and start_date and end_date:
        radar_chart_data = prepare_radar_data(
            dropdown_state, start_date, end_date, incident_types
        )

        if not radar_chart_data.empty:
            size_data = prepare_bar_chart_data(
                dropdown_state,
                "size",
                "incident_rate",
                start_date,
                end_date,
                incident_types,
            )
            establishment_type_data = prepare_bar_chart_data(
                dropdown_state,
                "establishment_type",
                "incident_rate",
                start_date,
                end_date,
                incident_types,
            )
            treemap_data = prepare_treemap_data(
                dropdown_state, "incident_rate", start_date, end_date, incident_types
            )
            type_of_incident_data = prepare_bar_chart_data(
                dropdown_state,
                "type_of_incident",
                "incident_rate",
                start_date,
                end_date,
                incident_types,
            )

            metric_analysis_content = html.Div(
                style={
                    "display": "flex",
                    "alignContent": "center",
                    "justifyContent": "center",
                    "flexDirection": "column",
                    "padding": "1rem",
                },
                children=[
                    # Radar chart
                    html.Div(
                        style={
                            "width": "100%",
                            "paddingRight": "10px",
                            "height": "500px",
                        },
                        children=[
                            dcc.Graph(
                                figure=create_radar_chart(
                                    radar_chart_data, dropdown_state
                                ),
                                id="radar-chart",
                            ),
                        ],
                    ),
                    # Bar charts
                    html.Div(
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "1fr 1fr",
                            "gridTemplateRows": "1fr 1fr",  # Equal rows for bar charts
                            "gap": "1em",  # Add spacing between graphs
                            "minHeight": "1000px",  # Set minimum height for the grid
                        },
                        children=[
                            dcc.Graph(
                                figure=create_grouped_bar_chart(
                                    size_data, "size", "incident_rate"
                                ),
                                id="bar-chart-size",
                            ),
                            dcc.Graph(
                                figure=create_grouped_bar_chart(
                                    establishment_type_data,
                                    "establishment_type",
                                    "incident_rate",
                                ),
                                id="bar-chart-sector",
                            ),
                            dcc.Graph(
                                figure=create_treemap(
                                    treemap_data, "incident_rate", dropdown_state
                                ),
                                id="treemap-chart",
                            ),
                            dcc.Graph(
                                figure=create_grouped_bar_chart(
                                    type_of_incident_data,
                                    "type_of_incident",
                                    "incident_rate",
                                ),
                                id="bar-chart-soc",
                            ),
                        ],
                    ),
                ],
            )
        else:
            metric_analysis_content = html.Div(
                "No data available for the selected feature."
            )

    return state_analysis_content, metric_analysis_content


if __name__ == "__main__":
    application.run(debug=True)
