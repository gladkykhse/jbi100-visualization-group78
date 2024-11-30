from dash import dcc, html

from src.data import categorical_features, data

main_layout = html.Div(
    style={"display": "flex", "flexDirection": "column", "height": "100vh"},
    children=[
        # Menu bar at the top
        html.Div(
            style={
                "width": "100%",
                "backgroundColor": "#2c3e50",
                "padding": "10px",
                "color": "white",
                "textAlign": "center",
            },
            children=[
                html.H2("OSHA Injury Tracking Application (ITA) Case Detail", style={"margin": "0"}),
            ],
        ),
        # Dropdown and content area
        html.Div(
            style={"display": "flex", "flexGrow": "1"},
            children=[
                # Dropdown menu on the left
                html.Div(
                    id="left-menu",
                    style={
                        "width": "20%",
                        "backgroundColor": "#f4f4f4",
                        "padding": "10px",
                        "borderRight": "1px solid #dfe4ea",
                    },
                    children=[
                        # Date picker for choropleth tab
                        html.Div(
                            id="date-picker-container",
                            children=[
                                html.H4("Select Date Range", style={"marginBottom": "10px"}),
                                dcc.DatePickerRange(
                                    id="date-picker-range",
                                    start_date=data["date_of_incident"].min(),
                                    end_date=data["date_of_incident"].max(),
                                    display_format="DD/MM/YYYY",
                                    style={"width": "100%"},
                                ),
                            ],
                        ),
                        # Dropdown for histogram tab
                        html.Div(
                            id="feature-dropdown-container",
                            children=[
                                html.H4("Select Feature", style={"marginBottom": "10px"}),
                                dcc.Dropdown(
                                    id="feature-dropdown",
                                    options=[
                                        {"label": feature.capitalize(), "value": feature}
                                        for feature in categorical_features
                                    ],
                                    value=categorical_features[0],
                                    placeholder="Select a feature",
                                ),
                            ],
                        ),
                    ],
                ),
                # Tabs and visualizations on the right
                html.Div(
                    style={"width": "80%", "padding": "10px"},
                    children=[
                        dcc.Tabs(
                            id="tabs",
                            value="choropleth",
                            children=[
                                dcc.Tab(label="Map", value="choropleth"),
                                dcc.Tab(label="Other plots", value="histogram"),
                            ],
                        ),
                        html.Div(id="content", style={"flexGrow": "1", "padding": "10px"}),
                    ],
                ),
            ],
        ),
    ],
)
