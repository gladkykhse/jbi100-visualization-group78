import plotly.express as px
import plotly.graph_objects as go


def create_radar_chart(df):
    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=df["scaled_value"],
            theta=df["kpi"],
            fill="toself",
            name="kpi",
            customdata=df["value"],
            hovertemplate="<b>%{theta}</b><br>Value: %{customdata}<br>",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                showticklabels=False,
                showline=False,
            ),
        ),
        clickmode="event+select",
        showlegend=False,
    )

    return fig


def create_grouped_bar_chart(df, feature, kpi):
    df[feature] = df[feature].apply(lambda x: x[:13] + "..." if len(x) > 16 else x)

    # Create the bar chart
    fig = px.bar(
        df,
        x=feature,
        y=kpi,
        labels={feature: feature, kpi: kpi},
        title=f"{kpi} by {feature}",
    )

    fig.update_traces(texttemplate=None)

    fig.update_layout(
        yaxis_title=kpi,
        xaxis_title=feature,
    )

    return fig


def create_map(df, kpi="incident_rate", selected_state=None):
    # Prepare data for the map
    df = df[["state_code", kpi]].groupby("state_code", observed=False).mean().reset_index()

    # Create the base map
    fig = go.Figure(
        data=go.Choropleth(
            locations=df["state_code"],
            z=df[kpi],
            locationmode="USA-states",
            colorscale="Blues",
            autocolorscale=False,
            marker_line_color="white",  # Default boundary lines
            colorbar=dict(title=dict(text="Number of cases")),
            hoverinfo="location+z",
        )
    )

    # Add a highlight for the selected state
    if selected_state:
        selected_row = df[df["state_code"] == selected_state]
        if not selected_row.empty:
            # Add the selected state with a red fill and border
            fig.add_trace(
                go.Choropleth(
                    locations=selected_row["state_code"],
                    z=selected_row[kpi],  # Use the same KPI for consistency
                    locationmode="USA-states",
                    colorscale=[[0, "rgba(255, 0, 0, 0.2)"], [1, "rgba(255, 0, 0, 0.6)"]],
                    autocolorscale=False,
                    marker_line_color="red",  # Red border for the selected state
                    marker_line_width=2,  # Thicker border
                    hoverinfo="location+z",  # Include hover info
                    showscale=False,  # No color scale for the highlight layer
                )
            )

    fig.update_layout(
        title_text="Work-related injuries by State",
        clickmode="event+select",  # Enable click events
        geo=dict(
            scope="usa",
            projection=go.layout.geo.Projection(type="albers usa"),
            showlakes=True,
            lakecolor="rgb(255, 255, 255)",
        ),
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


def create_timeline(df, period_column="incident_month", kpi="incident_rate", selected_state=None):
    avg_df = df.groupby(period_column, as_index=False)[kpi].mean()

    fig = go.Figure()

    # Add traces for all states (blue points)
    for state in df["state_code"].unique():
        if state != selected_state:  # Add all states except the selected one
            state_data = df[df["state_code"] == state]
            fig.add_trace(
                go.Scatter(
                    x=state_data[period_column],
                    y=state_data[kpi],
                    mode="markers",
                    name=f"State {state}",
                    marker=dict(color="blue"),
                    showlegend=False,
                )
            )

    # Add trace for the selected state (red points + line)
    if selected_state:
        selected_data = df[df["state_code"] == selected_state]
        fig.add_trace(
            go.Scatter(
                x=selected_data[period_column],
                y=selected_data[kpi],
                mode="lines+markers",  # Connect the points with a line
                name=f"Selected State {selected_state}",
                marker=dict(color="red", size=7),  # Red points with larger size
                line=dict(color="red", width=2),  # Red line
                showlegend=True,  # Show legend for the selected state
            )
        )

    # Add trace for the average incident rate (orange line)
    fig.add_trace(
        go.Scatter(
            x=avg_df[period_column],
            y=avg_df[kpi],
            mode="lines+markers",
            name="Average Incident Rate",
            marker=dict(color="orange", size=7),
            line=dict(color="orange", width=2),
        )
    )

    fig.update_layout(
        title="Incident Rate by Period and State",
        xaxis_title=period_column.capitalize(),
        yaxis_title="Incident Rate",
        legend_title="Legend",
    )

    return fig
