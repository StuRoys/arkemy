import streamlit as st
import plotly.express as px
import pandas as pd
from period_translations.translations import t

def render_person_chart(df, selected_person):
    """
    Render a bar chart showing hours data filtered by person.
    
    Parameters:
    df (DataFrame): The DataFrame containing the data
    selected_person (str): The person to filter by
    
    Returns:
    DataFrame: The filtered dataframe
    """
    # Check required columns
    required_columns = ["Period", "Person", "Capacity/Period", "Planned hours", 
                        "Hours/Registered", "Project hours", "Hours/Period"]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return df[df["Person"] == selected_person] if "Person" in df.columns else df
    
    # Drop duplicate columns
    df = df.loc[:, ~df.columns.duplicated()]
    
    # Create a copy of the dataframe
    df_copy = df.copy()
    
    # Ensure Period is datetime for proper sorting
    if not pd.api.types.is_datetime64_any_dtype(df_copy["Period"]):
        df_copy["Period"] = pd.to_datetime(df_copy["Period"], errors='coerce')
    
    # Filter data by selected person
    filtered_df = df_copy[df_copy["Person"] == selected_person].sort_values("Period")
    
    # Create formatted period string for display
    filtered_df["Period_display"] = filtered_df["Period"].dt.strftime("%b %Y")
    
    # Translation mapping for categories and hover display
    translations_map = {
        "Capacity/Period": "Capacity",
        "Planned hours": "Planned",
        "Hours/Registered": "Registered",
        "Project hours": "Billable",
        "Unpaid work": "Non-billable",
        "Hours/Period": "Schedule"
    }
    
    # Melt the DataFrame for plotting using the display column
    melted_df = pd.melt(
        filtered_df,
        id_vars=["Period_display", "Person"],
        value_vars=["Hours/Period", "Capacity/Period", "Planned hours", "Hours/Registered", "Project hours", "Unpaid work"],
        var_name="Hour Type",
        value_name="Hours"
    )
    
    # Add translated hour type for hover and for legend
    melted_df["Hour Type Translated"] = melted_df["Hour Type"].map(translations_map)
    
    # Define specific colors for each hour type
    color_map = {
    "Hours/Period": "#5b7fa7",      # Slate blue
    "Capacity/Period": "#88b1df",   # Sky blue
    "Planned hours": "#f4b942",     # Amber
    "Hours/Registered": "#9d7dbc",  # Lavender
    "Project hours": "#4caf50",     # Green
    "Unpaid work": "#e64a45"        # Red
    }
    
    # Create translated color map (for the legend)
    translated_color_map = {}
    for key, value in color_map.items():
        if key in translations_map:
            translated_color_map[translations_map[key]] = value
        else:
            translated_color_map[key] = value
    
    # Create the bar chart with ordered periods, custom colors, and translated title and legends
    fig = px.bar(
        melted_df,
        x="Period_display",
        y="Hours",
        color="Hour Type Translated",  # Use translated column for color/legend
        barmode="group",
        labels={"Period_display": t("period"), "Hours": t("hours_period"), "Hour Type Translated": ""},
        category_orders={"Period_display": filtered_df["Period_display"].tolist()},
        color_discrete_map=translated_color_map,
        height=600,
        custom_data=["Hour Type Translated"]  # Add custom data for hover
    )
    
    # Create custom hovertemplate using translations
    hovertemplate = (
        f"<span style='font-size:16px'><b>%{{customdata[0]}}</b><br>"
        f"%{{x}}<br>"
        f"%{{y:.0f}} {t('hrs')}</span><br>"
        "<extra></extra>"  # Removes trace name from hover
    )
    
    # Apply the custom hovertemplate to all traces
    for trace in fig.data:
        trace.hovertemplate = hovertemplate
    
    # Ensure all labels are shown
    fig.update_xaxes(tickangle=45)

    fig.update_layout(
        xaxis=dict(tickfont=dict(size=16)),
        yaxis=dict(tickfont=dict(size=16)),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=14)
        )
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    return filtered_df