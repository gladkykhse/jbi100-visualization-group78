import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.colors import sequential
from plotly_resampler import FigureResampler

from src.mappings import dropdown_options, state_code_map, state_map


def transform_kpi_names(s):
    return " ".join(map(str.capitalize, s.split("_")))


def preprocess_radar_data(df):
    df["formatted_kpi"] = df["kpi"].apply(transform_kpi_names)
    df_closed = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    return df_closed


def create_radar_chart(df, dropdown_state):
    fig = go.Figure()

    df_closed = preprocess_radar_data(df)
    worst_kpi = df_closed.loc[df_closed["value"].idxmax(), "formatted_kpi"]
    best_kpi = df_closed.loc[df_closed["value"].idxmin(), "formatted_kpi"]

    # Add trace for scaled values
    fig.add_trace(
        go.Scatterpolar(
            r=df_closed["scaled_value"],
            theta=df_closed["formatted_kpi"],
            fill="toself",
            fillcolor=px.colors.qualitative.Plotly[0],
            name=f"{state_map[dropdown_state]} Metric Values",
            customdata=df_closed["value"],
            opacity=0.8,
            hovertemplate="<b>Metric Name</b>: %{theta}<br><b>Metric Score</b>: %{customdata:.2f}<br>",
        )
    )

    # Add trace for mean scaled values
    fig.add_trace(
        go.Scatterpolar(
            r=df_closed["scaled_mean_value"],
            theta=df_closed["formatted_kpi"],
            fill="toself",  # No fill for the mean values
            name="Average Metric Values Across All States",
            customdata=df_closed["mean_value"],
            fillcolor=px.colors.qualitative.Plotly[4],
            opacity=0.8,
            hovertemplate="<b>Metric Name</b>: %{theta}<br><b>Metric Score</b>: %{customdata:.2f}<br>",
        )
    )

    # Add annotations for best and worst KPIs
    fig.add_annotation(
        text=f"<b>Best KPI:</b> {best_kpi}<br><b>Worst KPI:</b> {worst_kpi}",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.2,
        showarrow=False,
        font=dict(size=12),
        align="center",
    )

    # Update chart layout
    fig.update_layout(
        title={
            "text": f"{state_map[dropdown_state]} Safety Profile",
            "x": 0.5,  # Horizontally center the title
            "y": 0.98,  # Push it a bit down from the top
            "xanchor": "center",
            "yanchor": "middle",
        },
        polar=dict(
            radialaxis=dict(
                visible=False,
            ),
        ),
        clickmode="event+select",
        showlegend=True,
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="bottom",  # Align the legend's bottom with the top of the plot
            y=1.05,  # Position above the chart
            xanchor="center",  # Center-align the legend
            x=0.5,  # Center position horizontally
        ),
    )

    return fig


def create_grouped_bar_chart(df, feature, kpi):
    kpi_name = dropdown_options[kpi]  # Get the KPI name for the y-axis label
    df[kpi] = df[kpi].round(2)
    # Create the bar chart
    fig = px.bar(
        df,
        x=feature,
        y=kpi,
        title=f"{kpi_name} by {feature}",
        # text_auto=True,  # Add y-values as data labels on the bars
    )
    fig.update_traces(
        texttemplate="%{y:.2f}",  # Display y-values rounded to 2 decimal places
        # textposition="inside",  # Position the labels outside the bars
    )
    # Update layout
    fig.update_layout(
        yaxis_title=kpi_name,  # Set the y-axis label to the KPI name
        xaxis_title=feature,  # Set the x-axis label
    )

    return fig


def create_map(df, kpi="incident_rate", selected_state=None):
    kpi_name = dropdown_options[kpi]
    background_color = "white"
    border_color = "rgba(0, 0, 0, 0.2)"

    # Find the states with the highest and lowest KPI values
    max_kpi_state = df.loc[df[kpi].idxmax()]
    min_kpi_state = df.loc[df[kpi].idxmin()]
    kpi_naming = transform_kpi_names(kpi)
    max_state_text = f"<b>Highest {kpi_naming}</b>: {state_map[max_kpi_state['state_code']]} ({max_kpi_state[kpi]:.2f})"
    min_state_text = f"<b>Lowest {kpi_naming}</b>: {state_map[min_kpi_state['state_code']]} ({min_kpi_state[kpi]:.2f})"

    # Create the base map

    fig = FigureResampler(
        go.Figure(
            data=go.Choropleth(
                locations=df["state_code"],
                z=df[kpi],
                zmin=0,
                locationmode="USA-states",
                colorscale="Oranges",
                autocolorscale=False,
                marker_line_color=border_color,  # Default boundary lines
                colorbar=dict(title=dict(text=kpi_name)),
                hovertemplate="<b>State:</b> %{text}<br><b>Value:</b> %{z:.2f}<extra></extra>",
                text=df["state_code"].map(
                    state_map
                ),  # Add state names to the hover info
                hoverinfo="text+z",
            )
        )
    )

    # Add a highlight for the selected state
    if selected_state:
        selected_row = df.query("state_code == @selected_state")
        if not selected_row.empty:
            # Add the selected state with a red fill and border
            fig.add_trace(
                go.Choropleth(
                    locations=selected_row["state_code"],
                    z=selected_row[kpi],  # Use the same KPI for consistency
                    zmin=0,  # Set the minimum value to 0 to avoid issues with the color scale
                    locationmode="USA-states",
                    colorscale=[
                        [0, "rgba(99, 110, 250, 0.2)"],
                        [1, "rgba(99, 110, 250, 0.4)"],
                    ],
                    autocolorscale=False,
                    marker_line_color="rgb(99, 110, 250)",  # Red border for the selected state
                    marker_line_width=2,  # Thicker border
                    text=df["state_code"].map(
                        state_map
                    ),  # Add state names to the hover info
                    hovertemplate="<b>State:</b> %{text}<br><b>Value:</b> %{z:.2f}<extra></extra>",
                    showscale=False,  # No color scale for the highlight layer
                )
            )

    fig.add_annotation(
        text=f"{max_state_text}<br>{min_state_text}",
        showarrow=False,
        xref="paper",
        yref="paper",
        x=0.5,  # Centered horizontally
        y=-0.1,  # Below the map
        xanchor="center",
        yanchor="top",
        font=dict(size=12),
        align="center",
    )

    fig.update_layout(
        title_text=f"{kpi_name} by State",
        margin={"r": 0, "t": 30, "l": 0, "b": 80},
        clickmode="event+select",  # Enable click events
        geo=dict(
            scope="usa",
            projection=go.layout.geo.Projection(type="albers usa"),
            showlakes=False,
            lakecolor=background_color,
            bgcolor=background_color,
        ),
        mapbox=dict(zoom=False),
        dragmode=False,
        uirevision=True,
    )
    return fig


def create_histogram(filtered_df, feature):
    fig = px.histogram(
        filtered_df,
        x=feature,
        title=f"Distribution of {feature.capitalize()}",
        labels={feature: feature.capitalize()},
    )
    fig.update_layout(
        xaxis_title=feature.capitalize(),
        yaxis_title="Count",
        bargap=0.1,
    )
    return fig


def create_treemap(df, kpi, selected_state):
    filtered_df = df.query("count > 10")
    kpi_name = dropdown_options[kpi]
    # Create the treemap with hover information
    fig = px.treemap(
        filtered_df,
        path=[px.Constant("US Market"), "soc_description_1", "soc_description_2"],
        title=f"{kpi_name} across different {state_map[selected_state]} jobs",
        values="count",
        color="metric",
        color_continuous_scale=sequential.Oranges,
        maxdepth=2,
    )

    # Update hovertemplate for clarity
    fig.update_traces(
        marker=dict(cornerradius=1),
        hovertemplate=(
            "<b>Job description:</b> %{label}<br>"
            "<b>Number of workers:</b> %{value}<br>"
            f"<b>{kpi_name}:</b> " + "%{color}<extra></extra>"
        ),
    )

    return fig


def create_splom(df, kpi, selected_state=None):
    fig = FigureResampler(go.Figure())

    # Check if a state is selected
    if selected_state:
        # Filter the dataframe for the selected state
        # selected_state_data = df[df["state_code"] == selected_state].iloc[0]

        # Prepare constraintrange for each dimension
        constrained_state = state_code_map[selected_state]

    else:
        constrained_state = None  # No filtering if no state is selected

    # Add the Parallel Coordinates trace
    fig.add_trace(
        go.Parcoords(
            line=dict(
                color=df["injury_density"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(
                    title="Injury per worker",
                    titlefont=dict(size=14),
                ),
            ),
            dimensions=[
                dict(
                    label="State Code",
                    values=df["state_code"].map(state_code_map),
                    tickvals=df["state_code"].map(state_code_map),
                    ticktext=df["state_code"].map(state_map).tolist(),
                    constraintrange=[constrained_state - 0.5, constrained_state + 0.5]
                    if constrained_state
                    else None,
                ),
                dict(
                    label=dropdown_options[kpi],
                    values=df[kpi],
                ),
                dict(
                    label="Total Deaths",
                    values=df["death"],
                ),
                dict(
                    label="Total Hours Worked",
                    values=df["total_hours_worked"],
                ),
                dict(
                    label="Annual Employees",
                    values=df["annual_average_employees_median"],
                ),
                dict(
                    label="Days Away from Work",
                    values=df["dafw_num_away"],
                ),
                dict(
                    label="Days Job Transfer/Restriction",
                    values=df["djtr_num_tr"],
                ),
            ],
            unselected=dict(line=dict(color="gray", opacity=0.15)),
        )
    )

    # Update layout
    fig.update_layout(
        height=700,
        title="Parallel Coordinates Plot of US States",
    )

    return fig


def create_scatter_plot(df, incident_outcomes, selected_state):
    fig = FigureResampler(go.Figure())

    # Add a single trace for all data points
    fig.add_trace(
        go.Scatter(
            x=df["time_started_work"].dt.hour + df["time_started_work"].dt.minute / 60,
            y=df["time_of_incident"].dt.hour + df["time_of_incident"].dt.minute / 60,
            mode="markers",
            marker=dict(
                size=10,  # Set a fixed size for all points
                opacity=0.8,  # Set opacity
                color=df["case_number"],  # Use `case_number` for coloring
                colorscale="Viridis",  # Choose a continuous colorscale
                showscale=True,  # Display colorbar
                colorbar=dict(
                    title="Number of injuries",  # Colorbar title
                    titleside="top",
                ),
            ),
            text=df["naics_description_5"],  # Use SOC description for hover
            hovertemplate=(
                "<b>Industry:</b> %{text}<br>"
                "<b>Time Started Work:</b> %{customdata[0]}<br>"
                "<b>Time of Incident:</b> %{customdata[1]}<br>"
                "<b>Number of Injuries:</b> %{marker.color}<br>"
                "<extra></extra>"
            ),
            customdata=df[["time_started_work_str", "time_of_incident_str"]].values,
        )
    )

    # Update layout
    fig.update_layout(
        title=f"Work Start vs Incident Time in {state_map[selected_state]}",
        xaxis=dict(title="Time Started Work (Hours)"),
        yaxis=dict(title="Time of Incident (Hours)"),
    )
    return fig


def create_stacked_bar_chart(df, selected_state):
    fig = FigureResampler(go.Figure())

    # Define a safe qualitative color mapping
    colors = px.colors.qualitative.Dark2

    # Add a bar trace for each establishment type
    for i, establishment in enumerate(
        df.columns[1:]
    ):  # Skip the 'type_of_incident' column
        fig.add_trace(
            go.Bar(
                y=df["incident_outcome"],
                x=df[establishment],
                name=establishment,
                orientation="h",
                text=(df[establishment] * 100).round(1).astype(str)
                + "%",  # Display percentages
                textposition="inside",
                marker=dict(
                    color=colors[i % len(colors)],  # Cycle through Safe colors
                    line=dict(width=0.5, color="rgb(248, 248, 249)"),
                ),
            )
        )

    # Update layout
    fig.update_layout(
        barmode="stack",
        title=f"Distribution of Incident Outcomes by Establishment type in {state_map[selected_state]}",
        xaxis=dict(title="Proportion of Incidents", tickformat=".0%"),
        yaxis=dict(title="Incident Outcome"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=120, r=10, t=140, b=80),
        showlegend=True,
        legend=dict(title="Establishment Type", orientation="h", x=0.5, xanchor="center", y=-0.4),
    )
    return fig
