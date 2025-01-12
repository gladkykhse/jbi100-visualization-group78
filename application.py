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
    create_map,
    create_radar_chart,
    create_scatter_plot,
    create_splom,
    create_stacked_bar_chart,
    create_treemap,
)

application = Flask(__name__)
cache = Cache(
    application, config={"CACHE_TYPE": "SimpleCache"}
)  # Use "RedisCache" for production


app = dash.Dash(__name__, server=application)
app.layout = main_layout


@app.callback(
    [
        Output("kpi-select-container", "style"),
    ],
    [Input("tabs", "value")],
)
def update_left_menu_visibility(tab_name):
    if tab_name == "state_analysis_tab":
        return [{"display": "block"}]

    elif tab_name == "metric_analysis_tab":
        return [{"display": "none"}]

    return [{"display": "none"}]


# @app.callback(
#     [
#         Output("bar-chart-sector", "figure"),
#         Output("treemap-chart", "figure"),
#         Output("bar-chart-soc", "figure"),
#     ],
#     [
#         Input("radar-chart", "clickData"),
#         Input("state-dropdown", "value"),
#         Input("date-picker-range", "start_date"),
#         Input("date-picker-range", "end_date"),
#         Input("incident-filter-dropdown", "value"),
#         Input("splom-container", "dimensions"),
#     ],
# )
@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_scatter_plot_cached(state_code, start_date, end_date, incident_types):
    scatter_plot_data, incident_outcomes = prepare_scatter_plot(
        state_code,
        start_date,
        end_date,
        incident_types,
    )
    return scatter_plot_data, incident_outcomes


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_treemap_data_cached(
    state_code, selected_kpi, start_date, end_date, incident_types
):
    return prepare_treemap_data(
        state_code, selected_kpi, start_date, end_date, incident_types
    )


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_stacked_bar_chart_cached(state_code, start_date, end_date, incident_types):
    return prepare_stacked_bar_chart(state_code, start_date, end_date, incident_types)


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_radar_data_cached(dropdown_state, start_date, end_date, incident_types):
    return prepare_radar_data(dropdown_state, start_date, end_date, incident_types)


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_state_data_cached(start_date, end_date, incident_types, kpi):
    return prepare_state_data(start_date, end_date, incident_types, kpi)


def update_bar_charts(
    click_data, state_code, start_date, end_date, incident_types, restyleData
):
    selected_kpi = "incident_rate"
    if click_data and "points" in click_data:
        selected_kpi = dropdown_options_rev[click_data["points"][0]["theta"]]

    scatter_plot_data, incident_outcomes = prepare_scatter_plot_cached(
        state_code, start_date, end_date, incident_types
    )

    treemap_data = prepare_treemap_data_cached(
        state_code, selected_kpi, start_date, end_date, incident_types
    )

    stacked_bar_chart = prepare_stacked_bar_chart_cached(
        state_code, start_date, end_date, incident_types
    )

    return (
        create_scatter_plot(scatter_plot_data, incident_outcomes, state_code),
        create_treemap(treemap_data, selected_kpi, state_code),
        create_stacked_bar_chart(stacked_bar_chart, state_code),
    )


@app.callback(
    Output("state-dropdown", "value"),
    [Input("map-container", "clickData")],
    [State("state-dropdown", "value")],
)
def update_selected_state(click_data, current_state):
    if click_data:
        clicked_state = click_data["points"][0]["location"]  # Get clicked state
        if clicked_state == current_state:
            return current_state
        return clicked_state  # Update to the newly clicked state
    return current_state  # Retain the current state if no new click


@app.callback(
    Output("kpi-select-dropdown", "value"),
    Input("radar-chart", "clickData"),
)
def update_on_radar_click(click_data):
    if click_data and "points" in click_data:
        # Retrieve the metric name from the clicked radar segment
        selected_metric = dropdown_options_rev[click_data["points"][0]["theta"]]
    else:
        selected_metric = "incident_rate"
    return selected_metric


@app.callback(
    Output("content", "children"),
    Output("content-metric-analysis", "children"),
    [
        Input("tabs", "value"),
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date"),
        Input("incident-filter-dropdown", "value"),
        Input("kpi-select-dropdown", "value"),
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
    selected_state,
    dropdown_state,
):
    state_analysis_content = html.Div()
    metric_analysis_content = html.Div()

    if tab_name == "state_analysis_tab" and start_date and end_date and kpi:
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
                    "height": "calc(100vh - 8rem - 40px)",

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
                                children=[
                                    dcc.Loading(
                                        children=[
                                            dcc.Graph(
                                                figure=create_radar_chart(
                                                    radar_chart_data, dropdown_state
                                                ),
                                                id="radar-chart",
                                            ),
                                        ]
                                    )
                                ],
                            ),
                            html.Div(
                                style={"width": "50%", "padding": "5px"},
                                children=[
                                    dcc.Loading(
                                        children=[
                                            dcc.Graph(
                                                figure=create_map(
                                                    map_data, kpi, dropdown_state
                                                ),
                                                id="map-container",
                                            ),
                                        ]
                                    )
                                ],
                            ),
                        ],
                    ),
                    # Row 2: The splom below
                    html.Div(
                        style={
                            "width": "100%",
                            "height": "800px",
                            "marginTop": "20px",
                            "flex": "1",
                        },
                        children=[
                            dcc.Loading(
                                children=[
                                    dcc.Graph(
                                        figure=create_splom(
                                            map_data, kpi, dropdown_state
                                        ),
                                        id="splom-container",
                                    )
                                ],
                            )
                        ],
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
                    "height": "calc(100vh - 8rem - 40px)"
                },
                children=[
                    html.Div(
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "1fr 1fr",  # Two equal-width columns
                            "gridTemplateRows": "1fr 1fr",  # Equal-height rows
                            "gap": "1rem",  # Add spacing between graphs
                            "flexGrow": "1",  # Allow grid to grow to fill space
                        },
                        children=[
                            # First Graph: Spanning from [0,0] to [1,1]
                            html.Div(
                                dcc.Loading(
                                    children=[
                                        dcc.Graph(
                                            figure=create_scatter_plot(
                                                scatter_plot_data,
                                                incident_outcomes,
                                                dropdown_state,
                                            ),
                                            id="scatter-plot",
                                            style={"height": "100%", "width": "100%"}
                                        )
                                    ]
                                ),
                            ),
                            # Second Graph: Spanning [2,0] to [2,2]
                            html.Div(
                                dcc.Loading(
                                    children=[
                                        dcc.Graph(
                                            figure=create_treemap(
                                                treemap_data,
                                                "incident_rate",
                                                dropdown_state,
                                            ),
                                            id="treemap-chart",
                                        )
                                    ]
                                ),
                                style={
                                    "gridColumn": "1/3",  # Spans columns 1 to 3
                                    "gridRow": "2",
                                    "height": "100%", "width": "100%",  # Occupies the third row
                                },
                            ),
                            # Third Graph: Spanning [2,0] to [2,1]
                            html.Div(
                                dcc.Loading(
                                    children=[
                                        dcc.Graph(
                                            figure=create_stacked_bar_chart(
                                                stacked_bar_chart, dropdown_state
                                            ),
                                            id="stacked-bar-chart",
                                            style={"height": "100%", "width": "100%"}
                                        )
                                    ]
                                ),
                                style={
                                    "gridColumn": "2",  # Spans columns 1 to 2
                                    "gridRow": "1",
                                    "height": "100%", "width": "100%",  # Occupies the third row
                                },
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
