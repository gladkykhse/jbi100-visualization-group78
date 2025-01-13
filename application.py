# application.py

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from flask import Flask
from flask_caching import Cache

from src.data import (data, filter_data, prepare_radar_data,
                      prepare_scatter_plot, prepare_stacked_bar_chart,
                      prepare_state_data, prepare_treemap_data)
from src.layouts import main_layout
from src.mappings import dropdown_options_rev
from src.visualizations import (create_map, create_radar_chart,
                                create_scatter_plot, create_splom,
                                create_stacked_bar_chart, create_treemap)

application = Flask(__name__)
cache = Cache(application, config={"CACHE_TYPE": "SimpleCache"})  # Use "RedisCache" for production

app = dash.Dash(__name__, server=application)
app.layout = main_layout


@app.callback(
    [Output("kpi-select-container", "style")],
    [Input("tabs", "value")],
)
def update_left_menu_visibility(tab_name):
    if tab_name == "state_analysis_tab":
        return [{"display": "block"}]

    elif tab_name == "metric_analysis_tab":
        return [{"display": "none"}]

    return [{"display": "none"}]


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def filter_data_cached(df, start_date, end_date, incident_types):
    return filter_data(df, start_date, end_date, incident_types)


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_scatter_plot_cached(df, state_code):
    scatter_plot_data = prepare_scatter_plot(df, state_code)
    return scatter_plot_data


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_treemap_data_cached(df, state_code, selected_kpi):
    return prepare_treemap_data(df, state_code, selected_kpi)


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_stacked_bar_chart_cached(df, state_code):
    return prepare_stacked_bar_chart(df, state_code)


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_radar_data_cached(df, dropdown_state):
    return prepare_radar_data(df, dropdown_state)


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_state_data_cached(df, kpi):
    return prepare_state_data(df, kpi)


@app.callback(
    Output("state-dropdown", "value"),
    [Input("map-container", "clickData")],
    [State("state-dropdown", "value")],
)
def update_selected_state(click_data, current_state):
    print(">>> update_selected_state triggered")
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
    print(">>> update_on_radar_click triggered")
    if click_data and "points" in click_data:
        # Retrieve the metric name from the clicked radar segment
        selected_metric = dropdown_options_rev.get(click_data["points"][0]["theta"], "incident_rate")
    else:
        selected_metric = "incident_rate"
    return selected_metric


@app.callback(
    [
        Output("store-treemap2", "data"),
        Output("store-bar2", "data"),
    ],
    [
        Input("scatter-plot", "relayoutData"),
        State("date-picker-range", "start_date"),
        State("date-picker-range", "end_date"),
        State("incident-filter-dropdown", "value"),
        State("kpi-select-dropdown", "value"),
        State("state-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
@cache.memoize(timeout=600)  # Cache result for 10 minutes
def update_dependent_charts(
    scatter_relayoutData,
    start_date,
    end_date,
    incident_types,
    kpi,
    dropdown_state,
):
    print(">>> update_dependent_charts triggered")

    if not scatter_relayoutData or "autosize" in scatter_relayoutData:
        print(">>> Preventing update_dependent_charts due to insufficient relayoutData")
        raise dash.exceptions.PreventUpdate

    # Re-filter data based on date and incident filters
    filtered_data = filter_data_cached(data, start_date, end_date, incident_types)

    # If zoom info is available, further filter the data
    if scatter_relayoutData:
        x_min = scatter_relayoutData.get("xaxis.range[0]", None)
        x_max = scatter_relayoutData.get("xaxis.range[1]", None)
        y_min = scatter_relayoutData.get("yaxis.range[0]", None)
        y_max = scatter_relayoutData.get("yaxis.range[1]", None)
        if x_min is not None and x_max is not None:
            filtered_data = filtered_data[
                (
                    filtered_data["time_started_work"].dt.hour + filtered_data["time_started_work"].dt.minute / 60
                    >= float(x_min)
                )
                & (
                    filtered_data["time_started_work"].dt.hour + filtered_data["time_started_work"].dt.minute / 60
                    <= float(x_max)
                )
            ]
        if y_min is not None and y_max is not None:
            filtered_data = filtered_data[
                (
                    filtered_data["time_of_incident"].dt.hour + filtered_data["time_of_incident"].dt.minute / 60
                    >= float(y_min)
                )
                & (
                    filtered_data["time_of_incident"].dt.hour + filtered_data["time_of_incident"].dt.minute / 60
                    <= float(y_max)
                )
            ]

    # Prepare data and figures for treemap and stacked bar chart
    treemap_data = prepare_treemap_data_cached(filtered_data, dropdown_state, kpi)
    stacked_bar_data = prepare_stacked_bar_chart_cached(filtered_data, dropdown_state)

    treemap_fig = create_treemap(treemap_data, "incident_rate", dropdown_state)
    stacked_bar_fig = create_stacked_bar_chart(stacked_bar_data, dropdown_state)

    return treemap_fig, stacked_bar_fig


@app.callback(
    [
        Output("store-treemap1", "data"),
        Output("store-scatter1", "data"),
    ],
    [
        Input("stacked-bar-chart", "clickData"),
        State("date-picker-range", "start_date"),
        State("date-picker-range", "end_date"),
        State("incident-filter-dropdown", "value"),
        State("kpi-select-dropdown", "value"),
        State("state-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
@cache.memoize(timeout=600)  # Cache result for 10 minutes
def update_graphs_on_barchart_click(
    barchart_clickData,
    start_date,
    end_date,
    incident_types,
    kpi,
    selected_state,
):
    print(">>> update_graphs_on_barchart_click triggered")
    if not barchart_clickData:
        print(">>> Preventing update_graphs_on_barchart_click due to no clickData")
        raise dash.exceptions.PreventUpdate

    # Filter data based on the date range and incident types
    filtered_data = filter_data_cached(data, start_date, end_date, incident_types)

    # Handle filtering based on the clicked bar
    if "points" in barchart_clickData:
        clicked_outcome = barchart_clickData["points"][0]["y"]  # Incident outcome
        filtered_data = filtered_data[filtered_data["incident_outcome"] == clicked_outcome]

    # Prepare data and figures for treemap and scatter plot
    treemap_data = prepare_treemap_data_cached(filtered_data, selected_state, kpi)
    scatter_plot_data = prepare_scatter_plot_cached(filtered_data, selected_state)

    treemap_fig = create_treemap(treemap_data, kpi, selected_state)
    scatter_plot_fig = create_scatter_plot(scatter_plot_data, selected_state)

    return treemap_fig, scatter_plot_fig


@app.callback(
    [
        Output("store-bar1", "data"),
        Output("store-scatter2", "data"),
    ],
    [
        Input("treemap-chart", "clickData"),
    ],
    [
        State("date-picker-range", "start_date"),
        State("date-picker-range", "end_date"),
        State("incident-filter-dropdown", "value"),
        State("kpi-select-dropdown", "value"),
        State("state-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
@cache.memoize(timeout=600)  # Cache result for 10 minutes
def update_graphs_with_treemap_click(
    treemap_clickData,
    start_date,
    end_date,
    incident_types,
    kpi,
    selected_state,
):
    print(">>> update_graphs_with_treemap_click triggered")
    if not treemap_clickData:
        print(">>> Preventing update_graphs_with_treemap_click due to no clickData")
        raise dash.exceptions.PreventUpdate

    # Filter data based on the date range and incident types
    filtered_data = filter_data_cached(data, start_date, end_date, incident_types)

    # If a region on the treemap was clicked, further filter by the clicked region
    if "points" in treemap_clickData:
        print(treemap_clickData)
        clicked_label = treemap_clickData["points"][0]["label"]  # Get clicked label
        clicked_parent = treemap_clickData["points"][0].get("parent", None)  # Get parent label if present
        # Filter data based on the clicked region
        if clicked_parent and clicked_parent != "US Market":
            filtered_data = filtered_data[
                (filtered_data["soc_description_1"] == clicked_parent)
                & (filtered_data["soc_description_2"] == clicked_label)
            ]
        elif clicked_label != "US Market":
            filtered_data = filtered_data[(filtered_data["soc_description_1"] == clicked_label)]

    # Prepare data and figures for stacked bar chart and scatter plot
    stacked_bar_data = prepare_stacked_bar_chart_cached(filtered_data, selected_state)
    scatter_plot_data = prepare_scatter_plot_cached(filtered_data, selected_state)

    stacked_bar_fig = create_stacked_bar_chart(stacked_bar_data, selected_state)
    scatter_plot_fig = create_scatter_plot(scatter_plot_data, selected_state)

    return stacked_bar_fig, scatter_plot_fig


@app.callback(
    Output("stacked-bar-chart", "figure"),
    Input("store-bar1", "data"),
    Input("store-bar2", "data"),
    prevent_initial_call=True,
)
def update_stacked_bar_figure(bar_figure_dict1, bar_figure_dict2):
    print(">>> update_stacked_bar_figure triggered")
    if bar_figure_dict1 is None and bar_figure_dict2 is None:
        print(">>> Preventing update_stacked_bar_figure due to None data")
        raise dash.exceptions.PreventUpdate
    return bar_figure_dict1 if bar_figure_dict1 is not None else bar_figure_dict2


@app.callback(
    Output("scatter-plot", "figure"),
    Input("store-scatter1", "data"),
    Input("store-scatter2", "data"),
    prevent_initial_call=True,
)
def update_scatter_figure(scatter_figure_dict1, scatter_figure_dict2):
    print(">>> update_scatter_figure triggered")
    if scatter_figure_dict1 is None and scatter_figure_dict2 is None:
        print(">>> Preventing update_scatter_figure due to None data")
        raise dash.exceptions.PreventUpdate
    return scatter_figure_dict1 if scatter_figure_dict1 is not None else scatter_figure_dict2


@app.callback(
    Output("treemap-chart", "figure"),
    Input("store-treemap1", "data"),
    Input("store-treemap2", "data"),
    prevent_initial_call=True,
)
def update_treemap_figure(treemap_figure_dict1, treemap_figure_dict2):
    print(">>> update_treemap_figure triggered")
    if treemap_figure_dict1 is None and treemap_figure_dict2 is None:
        print(">>> Preventing update_treemap_figure due to None data")
        raise dash.exceptions.PreventUpdate
    return treemap_figure_dict1 if treemap_figure_dict1 is not None else treemap_figure_dict2


@app.callback(
    [Output("content", "children"), Output("content-metric-analysis", "children")],
    [
        Input("tabs", "value"),
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date"),
        Input("incident-filter-dropdown", "value"),
        Input("kpi-select-dropdown", "value"),
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
    dropdown_state,
):
    print(">>> update_tab_contents triggered")
    filtered_data = filter_data_cached(data, start_date, end_date, incident_types)
    metric_analysis_content = html.Div()
    state_analysis_content = html.Div()
    if filtered_data.empty:
        return html.Div(
            html.H2(
                "No data for filters. Try to change the filters or refresh the page to reset them",
                style={"margin": "1em 2em"},
            )
        ), html.Div(
            html.H2(
                "No data for filters. Try to change the filters or refresh the page to reset them",
                style={"margin": "1em 2em"},
            )
        )
    if tab_name == "state_analysis_tab" and start_date and end_date:
        map_data = prepare_state_data_cached(filtered_data, kpi)

        radar_chart_data = prepare_radar_data_cached(filtered_data, dropdown_state)

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
                                            figure=create_radar_chart(radar_chart_data, dropdown_state),
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
                                            figure=create_map(map_data, kpi, dropdown_state),
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
                                    figure=create_splom(map_data, kpi, dropdown_state),
                                    id="splom-container",
                                )
                            ],
                        )
                    ],
                ),
            ],
        )

    if tab_name == "metric_analysis_tab":
        scatter_plot_data = prepare_scatter_plot_cached(
            filtered_data,
            dropdown_state,
        )
        treemap_data = prepare_treemap_data_cached(
            filtered_data,
            dropdown_state,
            "incident_rate",
        )
        stacked_bar_chart = prepare_stacked_bar_chart_cached(filtered_data, dropdown_state)
        metric_analysis_content = html.Div(
            style={
                "display": "flex",
                "alignContent": "center",
                "justifyContent": "center",
                "flexDirection": "column",
                "padding": "1rem",
                "height": "calc(100vh - 8rem - 40px)",
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
                                            dropdown_state,
                                        ),
                                        id="scatter-plot",
                                        style={"height": "100%", "width": "100%"},
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
                                "height": "100%",
                                "width": "100%",  # Occupies the third row
                            },
                        ),
                        # Third Graph: Spanning [2,0] to [2,1]
                        html.Div(
                            dcc.Loading(
                                children=[
                                    dcc.Graph(
                                        figure=create_stacked_bar_chart(stacked_bar_chart, dropdown_state),
                                        id="stacked-bar-chart",
                                        style={"height": "100%", "width": "100%"},
                                    )
                                ]
                            ),
                            style={
                                "gridColumn": "2",  # Spans columns 1 to 2
                                "gridRow": "1",
                                "height": "100%",
                                "width": "100%",  # Occupies the third row
                            },
                        ),
                    ],
                ),
            ],
        )

    return state_analysis_content, metric_analysis_content


if __name__ == "__main__":
    application.run(debug=True)
