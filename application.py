import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from flask import Flask
from flask_caching import Cache

from src.data import (
    prepare_radar_data,
    prepare_scatter_plot,
    prepare_stacked_bar_chart,
    prepare_state_data,
    prepare_treemap_data,
)
from src.layouts import main_layout
from src.mappings import dropdown_options_rev
from src.visualizations import (
    create_grouped_bar_chart,
    create_map,
    create_radar_chart,
    create_scatter_plot,
    create_splom,
    create_treemap,
    create_stacked_bar_chart
)

application = Flask(__name__)
cache = Cache(application, config={"CACHE_TYPE": "SimpleCache"})  # Use "RedisCache" for production


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
        Output("bar-chart-sector", "figure"),
        Output("treemap-chart", "figure"),
        Output("bar-chart-soc", "figure"),
    ],
    [
        Input("radar-chart", "clickData"),
        Input("state-dropdown", "value"),
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date"),
        Input("incident-filter-dropdown", "value"),
        Input("splom-container", "dimensions"),
    ],
)

@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_scatter_plot_cached(state_code, start_date, end_date,incident_types):
    scatter_plot_data, incident_outcomes = prepare_scatter_plot(
            state_code,
            start_date,
            end_date,
            incident_types,
        )
    return scatter_plot_data, incident_outcomes

@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_treemap_data_cached(state_code, selected_kpi, start_date, end_date, incident_types):
    return prepare_treemap_data(
        state_code, selected_kpi, start_date, end_date, incident_types
    )

@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_stacked_bar_chart_cached(state_code, start_date, end_date, incident_types):
    return prepare_stacked_bar_chart(
        state_code, start_date, end_date, incident_types
    )

@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_radar_data_cached(dropdown_state, start_date, end_date, incident_types):
        return prepare_radar_data(
            dropdown_state, start_date, end_date, incident_types
        )

@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_state_data_cached(start_date, end_date, incident_types, kpi):
    return prepare_state_data(start_date, end_date, incident_types, kpi)


def update_bar_charts(
    click_data, state_code, start_date, end_date, incident_types, restyleData
):
    selected_kpi = "incident_rate"
    if click_data and "points" in click_data:
        selected_kpi = dropdown_options_rev[click_data["points"][0]["theta"]]

    scatter_plot_data, incident_outcomes = prepare_scatter_plot_cached(state_code, start_date, end_date,incident_types)
    
    treemap_data = prepare_treemap_data_cached(
        state_code, selected_kpi, start_date, end_date, incident_types
    )

    stacked_bar_chart = prepare_stacked_bar_chart_cached(
        state_code, start_date, end_date, incident_types
    )

    return (
        create_scatter_plot(scatter_plot_data, incident_outcomes, state_code),
        create_treemap(treemap_data, selected_kpi),
        create_stacked_bar_chart(stacked_bar_chart, state_code),
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

@cache.memoize(timeout=600)  # Cache result for 10 minutes
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
        map_data = prepare_state_data_cached(start_date, end_date, incident_types, kpi)

        if selected_state is not None:
            dropdown_state = selected_state

        radar_chart_data = prepare_radar_data_cached(
            dropdown_state, start_date, end_date, incident_types
        )

        if not map_data.empty:
            state_analysis_content = html.Div(
                style={
                    "display": "flex",
                    "flexDirection": "column",  # Stack rows vertically
                    "padding": "10px",
                },
                children=[
                    # Row 1: Radar (left) and Map (right)
                    html.Div(
                        style={
                            "display": "flex",
                            "flexDirection": "row",  # Place children side by side
                            "width": "100%",
                        },
                        children=[
                            html.Div(
                                style={
                                    "width": "50%",
                                    "padding": "5px",
                                },
                                children=[dcc.Loading(children=[
                                    dcc.Graph(
                                        figure=create_radar_chart(
                                            radar_chart_data, dropdown_state
                                        ),
                                        id="radar-chart",
                                    ),
                                ])],
                            ),
                            html.Div(
                                style={"width": "50%", "padding": "5px"},
                                children=[dcc.Loading(children=[
                                    dcc.Graph(
                                        figure=create_map(
                                            map_data, kpi, selected_state
                                        ),
                                        id="map-container",
                                    ),
                                ])],
                            ),
                        ],
                    ),
                    # Row 2: The splom below
                    html.Div(
                        style={
                            "width": "100%",
                            "height": "800px",
                            "marginTop": "20px",
                        },
                        children=[dcc.Loading(
                        children=[
                            dcc.Graph(
                                figure=create_splom(map_data, kpi, selected_state),
                                id="splom-container",
                                    )
                                ],
                                            )
                                ]
                            ),
                ],
            )
        else:
            state_analysis_content = html.Div(
                html.H2("No data for selected date range.", style="margin: 1em 2em")
            )

    if tab_name == "metric_analysis_tab" and dropdown_state and start_date and end_date:
        radar_chart_data = prepare_radar_data_cached(
            dropdown_state, start_date, end_date, incident_types
        )

        if not radar_chart_data.empty:
            scatter_plot_data, incident_outcomes = prepare_scatter_plot_cached(
                dropdown_state,
                start_date,
                end_date,
                incident_types,
            )
            treemap_data = prepare_treemap_data_cached(
                dropdown_state, "incident_rate", start_date, end_date, incident_types
            )
            stacked_bar_chart = prepare_stacked_bar_chart_cached(
                dropdown_state, start_date, end_date, incident_types
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
                    html.Div(
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "1fr 1fr",
                            "gridTemplateRows": "1fr 1fr",  # Equal rows for bar charts
                            "gap": "1em",  # Add spacing between graphs
                            "minHeight": "1000px",  # Set minimum height for the grid
                        },
                        children=[
                            dcc.Loading(children=[
                            dcc.Graph(
                                figure=create_scatter_plot(
                                    scatter_plot_data,
                                    incident_outcomes,
                                    dropdown_state,
                                ),
                                id="bar-chart-sector",
                            )]),
                            dcc.Loading(children=[
                            dcc.Graph(
                                figure=create_treemap(treemap_data, "incident_rate"),
                                id="treemap-chart",
                            )]),
                            dcc.Loading(children=[
                            dcc.Graph(
                                figure=create_stacked_bar_chart(
                                    stacked_bar_chart, dropdown_state
                                ),
                                id="bar-chart-soc",
                            )]),
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
