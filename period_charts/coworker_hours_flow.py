import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from period_translations.translations import t

def render_hours_flow_chart(df, selected_person):
    """
    Render a Sankey diagram showing the flow of hours filtered by person.
    
    Parameters:
    df (DataFrame): The DataFrame containing the data
    selected_person (str): The person to filter by
    
    Returns:
    DataFrame: The filtered dataframe
    """
    # Check required columns
    required_columns = ["Period", "Person", "Capacity/Period", "Project hours"]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return df[df["Person"] == selected_person] if "Person" in df.columns else df
    
    # Create a copy of the dataframe
    df_copy = df.copy()
    
    # Ensure Period is datetime for proper sorting
    if not pd.api.types.is_datetime64_any_dtype(df_copy["Period"]):
        df_copy["Period"] = pd.to_datetime(df_copy["Period"], errors='coerce')
    
    # Filter data by selected person
    filtered_df = df_copy[df_copy["Person"] == selected_person].sort_values("Period")
    
    # Calculate sums
    sum_hours_period = filtered_df["Hours/Period"].sum() if "Hours/Period" in filtered_df.columns else 0
    sum_absence = filtered_df["Absence/Period"].sum() if "Absence/Period" in filtered_df.columns else 0
    sum_capacity = filtered_df["Capacity/Period"].sum()
    sum_registered = filtered_df["Hours/Registered"].sum() if "Hours/Registered" in filtered_df.columns else 0
    sum_project_hours = filtered_df["Project hours"].sum()
    sum_unpaid = filtered_df["Unpaid work"].sum() if "Unpaid work" in filtered_df.columns else 0
    
    # Create a Sankey diagram to visualize the flow of hours
    if sum_hours_period > 0:  # Only show diagram if there are hours to display
        # Define color map using your specified colors
        color_map = {
            "Schedule": "#5b7fa7",          # Deep blue
            "Absence": "#ff7f0e",           # Orange
            "Capacity": "#88b1df",          # Light blue
            "Registered": "#9d7dbc",        # Forest green
            "Billable": "#4caf50",          # Light green
            "Non-billable": "#e64a45"       # Red
        }
        
        # Define the nodes
        nodes = [
            {"label": "Schedule", "value": sum_hours_period},
            {"label": "Absence", "value": sum_absence},
            {"label": "Capacity", "value": sum_capacity},
            {"label": "Registered", "value": sum_registered},
            {"label": "Billable", "value": sum_project_hours},
            {"label": "Non-billable", "value": sum_unpaid}
        ]
        
        # Define the links (connections between nodes)
        links = []
        
        # Schedule splits into Absence and Capacity
        links.append({"source": 0, "target": 1, "value": sum_absence})
        links.append({"source": 0, "target": 2, "value": sum_capacity})
        
        # Handle Capacity to Registered flow
        # Always show flow from Capacity to Registered
        links.append({"source": 2, "target": 3, "value": min(sum_capacity, sum_registered)})
        
        # If registered hours exceed capacity, add an "overflow" node
        if sum_registered > sum_capacity:
            # Add overflow node (will be added at the end of the list)
            nodes.append({"label": "Overtime", "value": sum_registered - sum_capacity})
            overflow_node_index = len(nodes) - 1
            
            # Add link from overtime to registered
            links.append({"source": overflow_node_index, "target": 3, "value": sum_registered - sum_capacity})
            
            # Add color for overflow node
            color_map["Overtime"] = "#E377C2"  # Purple
        
        # Registered hours split into Billable and Non-billable
        links.append({"source": 3, "target": 4, "value": sum_project_hours})
        links.append({"source": 3, "target": 5, "value": sum_unpaid})
        
        # Create custom hover templates for each node
        node_labels = [node["label"] for node in nodes]
        node_values = [node["value"] for node in nodes]
        
        # Create node data for the Sankey diagram
        node_labels = [node["label"] for node in nodes]
        node_values = [node["value"] for node in nodes]
        node_colors = [color_map.get(node["label"], "#000000") for node in nodes]
        
        # Create the Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            arrangement="snap",  # Use snap arrangement to better separate nodes
            node=dict(
                pad=40,         # Increased padding between nodes
                thickness=30,
                line=dict(color="black", width=0.5),
                label=node_labels,
                color=node_colors,
                # Custom hover template that uses the node's specific value
                customdata=node_values,
                hovertemplate='%{label}: %{customdata:.0f} hrs<extra></extra>'
            ),
            link=dict(
                source=[link["source"] for link in links],
                target=[link["target"] for link in links],
                value=[link["value"] for link in links],
                hovertemplate='%{value:.0f} hrs<extra></extra>'
            )
        )])

        # Update the layout with font settings
        fig.update_layout(
            font=dict(
                family="Arial, sans-serif",
                size=16,
                color="black"
            ),
            height=600,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor='rgba(255,255,255,0.9)',
            plot_bgcolor='rgba(255,255,255,0.9)'
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hours data available to display the flow chart.")
    
    return filtered_df