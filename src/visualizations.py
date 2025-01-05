import plotly.express as px
import plotly.graph_objects as go
from src.mappings import dropdown_options, state_map

def create_radar_chart(df, dropdown_state):
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
        title_text=f'{state_map[dropdown_state]} Safety Profile',
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
        xaxis_title=feature,   # Set the x-axis label
    )

    return fig


def create_map(df, kpi="incident_rate", selected_state=None):
    kpi_name = dropdown_options[kpi]
    background_color = "white"
    border_color = "rgba(0, 0, 0, 0.2)"
    # Prepare data for the map
    df = df[["state_code", kpi]].groupby(["state_code"], observed=False).mean().reset_index()

    # Create the base map
    fig = go.Figure(
        data=go.Choropleth(
            locations=df["state_code"],
            z=df[kpi],
            zmin=0,  # Set the minimum value to 0 to avoid issues with the color scale
            locationmode="USA-states",
            colorscale="RdBu", # "Viridis, Cividis, Plasma, Oranges
            autocolorscale=False,
            marker_line_color=border_color,  # Default boundary lines
            colorbar=dict(title=dict(text=kpi_name)),
            # hovertemplate="<b>State:</b> %{customdata[0]}<br><b>Value:</b> %{z}<extra></extra>",
            text=df["state_code"].map(state_map),  # Add state names to the hover info
            hoverinfo="text+z",
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
                    colorscale=[[0, "rgba(255, 0, 0, 0.2)"], [1, "rgba(255, 0, 0, 0.6)"]],
                    autocolorscale=False,
                    marker_line_color="red",  # Red border for the selected state
                    marker_line_width=2,  # Thicker border
                    text=df["state_code"].map(state_map),  # Add state names to the hover info
                    hoverinfo="text+z",  # Include hover info
                    showscale=False,  # No color scale for the highlight layer
                )
            )
    fig.update_layout(
        title_text=f"{kpi_name} by State",
        margin={"r":0, "t": 30, "l":0,"b":0},
        clickmode="event+select",  # Enable click events
        geo=dict(
            scope="usa",
            projection=go.layout.geo.Projection(type="albers usa"),
            showlakes=True,
            lakecolor=background_color,
            bgcolor=background_color, 
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
    # Define mappings for months and weekdays
    month_labels = {
        1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
        7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
    }
    weekday_labels = {
        0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 
        4: "Friday", 5: "Saturday", 6: "Sunday"
    }

    # Map numeric columns to text labels if applicable
    if period_column == "incident_month":
        df[period_column] = df[period_column].map(month_labels)
    elif period_column == "incident_weekday":
        df[period_column] = df[period_column].map(weekday_labels)
    else:
        df[period_column] = df[period_column].astype("string")


    # Prepare average data
    avg_df = df.groupby(period_column, as_index=False)[kpi].mean()
    kpi_name = dropdown_options[kpi]

    # Create the figure
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
                    name=state_map[state],
                    marker=dict(color="blue", size=4),
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
                name=f"Selected State: {state_map[selected_state]}",  # Add the state name to the legend
                marker=dict(color="red", size=6),  # Red points with larger size
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
            name=f"Average {kpi_name}",
            marker=dict(color="orange", size=6),
            line=dict(color="orange", width=2),
        )
    )

    fig.update_layout(
        title=f"{kpi_name} by Period and State",
        xaxis_title=period_column.capitalize(),
        yaxis_title=kpi_name,
        legend_title="Legend",
    )

    return fig


# def create_treemap(df, metric):
#     pass