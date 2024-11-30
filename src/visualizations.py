import plotly.express as px
import plotly.graph_objects as go


def create_choropleth(filtered_df):
    fig = go.Figure(
        data=go.Choropleth(
            locations=filtered_df["state_code"],
            z=filtered_df["count"],
            locationmode="USA-states",
            colorscale="Blues",
            autocolorscale=False,
            marker_line_color="white",
            colorbar=dict(title=dict(text="Number of cases")),
        )
    )

    fig.update_layout(
        title_text="Work-related injuries by State",
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
