from dash import dcc, html
from src.data import data, incident_types, state_codes
from src.mappings import dropdown_options, state_map

main_layout = html.Div(
    style={
        "display": "flex",
        "flexDirection": "column",
        "height": "100vh",
        "margin": "0",
        "padding": "0",
        "boxSizing": "border-box",
    },
    children=[
        # Menu bar at the top
        html.Link(
            rel="stylesheet",
            href="data:text/css,body { margin: 0; }"
        ),
        dcc.Store(id="selected_state", storage_type="memory"),
        html.Div(
            style={
                "width": "100%",
                "backgroundColor": "#2c3e50",
                "padding": "1%",
                "color": "white",
                "textAlign": "center",
                "boxSizing": "border-box",
            },
            children=[
                html.H2(
                    "Work-related injuries dashboard",
                    style={"margin": "0", "fontSize": "1.5em"},
                ),
            ],
        ),
        # Dropdown and content area
        html.Div(
            style={
                "display": "flex",
                "flexGrow": "1",
                "height": "100%",
                "overflow": "hidden",
            },
            children=[
                # Dropdown menu on the left (Sidebar)
                html.Div(
                    id="left-menu",
                    style={
                        "width": "20%",
                        "backgroundColor": "#f4f4f4",
                        "padding": "2%",
                        "borderRight": "1px solid #dfe4ea",
                        "boxSizing": "border-box",
                        "minHeight": "100vh",  # Ensures it always fills the viewport height
                        "flexShrink": "0",  # Prevents sidebar from shrinking
                        "overflowY": "auto",  # Adds scrolling if content exceeds the height
                    },
                    children=[
                        html.Div(
                            id="state-dropdown-container",
                            children=[
                                html.H4("Select State", style={"marginBottom": "5%"}),
                                dcc.Dropdown(
                                    id="state-dropdown",
                                    options=state_map,
                                    value=state_codes[0],
                                    placeholder="Select State",
                                    style={"width": "100%"},
                                    clearable=False,
                                ),
                            ],
                        ),
                        html.Div(
                            id="kpi-select-container",
                            children=[
                                html.H4("Select KPI", style={"marginBottom": "5%"}),
                                dcc.Dropdown(
                                    id="kpi-select-dropdown",
                                    options=dropdown_options,
                                    value="incident_rate",
                                    placeholder="Select KPI",
                                    optionHeight=50,
                                    style={"width": "100%"},
                                    clearable=False,
                                ),
                            ],
                        ),
                        html.Div(
                            id="date-picker-container",
                            children=[
                                html.H4(
                                    "Select Date Range", style={"marginBottom": "5%"}
                                ),
                                dcc.DatePickerRange(
                                    id="date-picker-range",
                                    start_date=data["date_of_incident"].min(),
                                    end_date=data["date_of_incident"].max(),
                                    display_format="DD/MM/YYYY",
                                    style={"width": "100%"},
                                ),
                            ],
                        ),
                        html.Div(
                            id="incident-filter-container",
                            children=[
                                html.H4(
                                    "Filter by Incident Type",
                                    style={"marginBottom": "5%"},
                                ),
                                dcc.Dropdown(
                                    id="incident-filter-dropdown",
                                    options=[
                                        {"label": cat_value, "value": cat_value}
                                        for cat_value in incident_types
                                    ],
                                    placeholder="Select one or more categories",
                                    multi=True,
                                    clearable=True,
                                    style={"width": "100%"},
                                ),
                            ],
                        ),
                    ],
                ),
                # Tabs and visualizations on the right (Main Content)
                html.Div(
                    style={
                        "width": "80%",
                        "padding": "0%",
                        "boxSizing": "border-box",
                        "overflow": "auto",
                    },
                    children=[
                        dcc.Tabs(
                            id="tabs",
                            value="state_analysis_tab",
                            children=[
                                dcc.Tab(
                                    label="State Analysis",
                                    value="state_analysis_tab",
                                    children=[
                                        html.Div(
                                            id="content",
                                            style={"width": "100%", "height": "100%"},
                                        ),
                                    ],
                                ),
                                dcc.Tab(
                                    label="Metric Analysis",
                                    value="metric_analysis_tab",
                                    children=[
                                        html.Div(
                                            id="content-metric-analysis",
                                            style={"width": "100%", "height": "100%"},
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)
