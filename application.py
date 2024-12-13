import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from flask import Flask

from src.data import data, prepare_map_data
from src.layouts import main_layout
from src.visualizations import (create_choropleth, create_histogram)

server = Flask(__name__)

app = dash.Dash(__name__, server=server)
app.layout = main_layout


@app.callback(
    [Output("date-picker-container", "style"), Output("feature-dropdown-container", "style")], [Input("tabs", "value")]
)
def update_left_menu_visibility(tab_name):
    if tab_name == "choropleth":
        return {"display": "block"}, {"display": "none"}
    elif tab_name == "histogram":
        return {"display": "none"}, {"display": "block"}
    return {"display": "none"}, {"display": "none"}


@app.callback(
    Output("content", "children"),
    [
        Input("tabs", "value"),
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date"),
        Input("feature-dropdown", "value"),
    ],
)
def update_content(tab_name, start_date, end_date, selected_feature):
    if tab_name == "choropleth" and start_date and end_date:
        filtered_df = prepare_map_data(start_date, end_date)
        if not filtered_df.empty:
            return dcc.Graph(figure=create_choropleth(filtered_df))
        else:
            return html.Div("No data available for the selected date range.")

    elif tab_name == "histogram" and selected_feature:
        if not data.empty:
            return dcc.Graph(figure=create_histogram(data, selected_feature))
        else:
            return html.Div("No data available for the selected feature.")

    return html.Div("No content available for this tab.")


if __name__ == "__main__":
    server.run(debug=True)
