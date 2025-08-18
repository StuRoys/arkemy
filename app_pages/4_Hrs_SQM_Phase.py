import streamlit as st

# ==========================================
# AUTHENTICATION CHECK - MUST COME FIRST
# ==========================================

# Check if user is authenticated
authentication_status = st.session_state.get('authentication_status')
if authentication_status != True:
    # User is not authenticated - redirect to main page
    st.error("🔒 Access denied. Please log in through the main page.")
    st.markdown("[👉 Go to Login Page](/?page=main)")
    st.stop()

import pandas as pd
import plotly.express as px
import os
import glob

st.set_page_config(
    page_title="Hrs SQM Phase Analysis",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Hrs SQM Phase Analysis")
st.markdown("Calculate hours per square meter across different project phases")

def get_data_directory():
    """Get the appropriate data directory - Railway volume or local"""
    # Check for Railway volume first
    if os.path.exists("/data"):
        return "/data"
    # Check for local temp directory
    elif os.path.exists(os.path.expanduser("~/temp_data")):
        return os.path.expanduser("~/temp_data")
    # Fallback to local data directory
    else:
        return "data"

# Auto-load CSV file from data folder
data_dir = get_data_directory()
csv_pattern = os.path.join(data_dir, "*sqm*.csv")
csv_files = glob.glob(csv_pattern)

if csv_files:
    file_path = csv_files[0]
    file_name = os.path.basename(file_path)
    
    try:
        df = pd.read_csv(file_path)
        st.success(f"Loaded data from: {file_name}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Projects", len(df))
        with col2:
            st.metric("Total SQM", f"{df['project_sqm'].sum():,.0f}")
        with col3:
            st.metric("Total Hours", f"{df['hours_total'].sum():,.0f}")
        
        # Detect phase columns
        phase_columns = [col for col in df.columns if col.endswith('_hrs_per_sqm')]
        phase_names = [col.replace('_hrs_per_sqm', '').replace('/', ' / ') for col in phase_columns]
        
        # Filter controls
        st.subheader("🔍 Analysis Filters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_projects = st.selectbox(
                "Select Project",
                ["All Projects"] + list(df['project_name'].unique()),
                key="project_filter"
            )
        
        with col2:
            selected_phase = st.selectbox(
                "Select Phase",
                ["All Phases"] + phase_names,
                key="phase_filter"
            )
        
        with col3:
            selected_type = st.selectbox(
                "Select Project Type",
                ["All Types"] + sorted(df['project_tags'].unique()),
                key="type_filter"
            )
        
        # Additional filters
        st.write("**Range Filters:**")
        col1, col2 = st.columns(2)
        
        with col1:
            sqm_range = st.slider(
                "Total SQM Range",
                min_value=int(df['project_sqm'].min()),
                max_value=int(df['project_sqm'].max()),
                value=(int(df['project_sqm'].min()), int(df['project_sqm'].max())),
                key="sqm_filter"
            )
        
        with col2:
            hours_range = st.slider(
                "Total Hours Range", 
                min_value=int(df['hours_total'].min()),
                max_value=int(df['hours_total'].max()),
                value=(int(df['hours_total'].min()), int(df['hours_total'].max())),
                key="hours_filter"
            )
        
        # Filter data based on selections
        filtered_df = df.copy()
        
        if selected_projects != "All Projects":
            filtered_df = filtered_df[filtered_df['project_name'] == selected_projects]
        
        if selected_type != "All Types":
            filtered_df = filtered_df[filtered_df['project_tags'] == selected_type]
        
        # Apply range filters
        filtered_df = filtered_df[
            (filtered_df['project_sqm'] >= sqm_range[0]) & 
            (filtered_df['project_sqm'] <= sqm_range[1]) &
            (filtered_df['hours_total'] >= hours_range[0]) & 
            (filtered_df['hours_total'] <= hours_range[1])
        ]
        
        st.subheader("📋 Project Data")
        
        # Display filtered dataframe with all phase columns
        display_columns = ['project_number', 'project_name', 'project_tags', 'project_status', 'project_sqm', 'hours_total']
        
        # Add all phase columns to display
        display_columns.extend(phase_columns)
        
        column_config = {
            "project_sqm": st.column_config.NumberColumn("SQM", format="%.0f"),
            "hours_total": st.column_config.NumberColumn("Total Hours", format="%.1f"),
            "project_tags": st.column_config.TextColumn("Project Type"),
            "project_status": st.column_config.TextColumn("Status")
        }
        
        # Configure all phase columns
        for i, phase_col in enumerate(phase_columns):
            clean_name = phase_names[i][:20] + "..." if len(phase_names[i]) > 20 else phase_names[i]
            column_config[phase_col] = st.column_config.NumberColumn(clean_name, format="%.3f")
        
        # Display with horizontal scroll for many columns in expander
        with st.expander("📋 Detailed Project Data (All Phases)", expanded=False):
            if len(filtered_df) > 0:
                st.dataframe(
                    filtered_df[display_columns],
                    use_container_width=True,
                    column_config=column_config,
                    height=400
                )
            else:
                st.info("No projects match the current filters.")

        # === 1. PROJECT TYPE ANALYSIS ===
        st.subheader("🏢 Project Type Analysis")
        
        # Create type summary
        if len(filtered_df) > 0:
            type_summary = filtered_df.groupby('project_tags').agg({
                'project_sqm': 'sum',
                'hours_total': 'sum', 
                'project_name': 'count'
            }).reset_index()
            
            type_summary.columns = ['Project_Type', 'Total_SQM', 'Total_Hours', 'Project_Count']
            type_summary['Avg_Hrs_per_SQM'] = type_summary['Total_Hours'] / type_summary['Total_SQM']
            type_summary['Avg_Hrs_per_SQM'] = type_summary['Avg_Hrs_per_SQM'].fillna(0)
            type_summary = type_summary.sort_values('Avg_Hrs_per_SQM', ascending=False)
            
            # Bar chart for project types
            fig_type = px.bar(
                type_summary,
                x='Project_Type',
                y='Avg_Hrs_per_SQM',
                title='Average Hours per SQM by Project Type',
                color='Avg_Hrs_per_SQM',
                color_continuous_scale='RdYlGn_r',
                labels={'Avg_Hrs_per_SQM': 'Avg Hrs/SQM', 'Project_Type': 'Project Type'}
            )
            
            # Custom hover template
            fig_type.update_traces(
                hovertemplate=(
                    "<b style='font-size:16px'>%{x}</b><br><br>"
                    "<span style='font-size:14px'>"
                    "Average Efficiency: <b>%{y:.4f} hrs/sqm</b><br>"
                    "Total Projects: <b>%{customdata[0]}</b><br>"
                    "Total Area: <b>%{customdata[1]:,.0f} sqm</b><br>"
                    "Total Hours: <b>%{customdata[2]:,.0f}</b>"
                    "</span>"
                    "<extra></extra>"
                ),
                customdata=type_summary[['Project_Count', 'Total_SQM', 'Total_Hours']].values
            )
            
            fig_type.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_type, use_container_width=True)
            
            # Project type details in expander
            with st.expander("📊 Project Type Details"):
                # Create detailed breakdown with phase averages per type
                type_phase_breakdown = []
                
                for project_type in type_summary['Project_Type']:
                    type_projects = filtered_df[filtered_df['project_tags'] == project_type]
                    if len(type_projects) > 0:
                        breakdown_row = {
                            'Project_Type': project_type,
                            'Projects': len(type_projects),
                            'Total_SQM': type_projects['project_sqm'].sum(),
                            'Total_Hours': type_projects['hours_total'].sum(),
                            'Avg_Hrs_per_SQM': type_projects['hours_total'].sum() / type_projects['project_sqm'].sum() if type_projects['project_sqm'].sum() > 0 else 0
                        }
                        
                        # Add average phase values for this type
                        for i, phase_col in enumerate(phase_columns):
                            phase_avg = type_projects[phase_col].mean()
                            breakdown_row[f'{phase_names[i][:15]}...'] = phase_avg if phase_avg > 0 else 0
                            
                        type_phase_breakdown.append(breakdown_row)
                
                if type_phase_breakdown:
                    type_phase_df = pd.DataFrame(type_phase_breakdown)
                    
                    # Create column config
                    type_col_config = {
                        "Project_Type": st.column_config.TextColumn("Type"),
                        "Projects": st.column_config.NumberColumn("Count", format="%.0f"),
                        "Total_SQM": st.column_config.NumberColumn("Total SQM", format="%.0f"),
                        "Total_Hours": st.column_config.NumberColumn("Total Hrs", format="%.0f"),
                        "Avg_Hrs_per_SQM": st.column_config.NumberColumn("Avg Hrs/SQM", format="%.3f")
                    }
                    
                    # Add phase column configs
                    for i, phase_col in enumerate(phase_columns):
                        phase_key = f'{phase_names[i][:15]}...'
                        if phase_key in type_phase_df.columns:
                            type_col_config[phase_key] = st.column_config.NumberColumn(phase_names[i][:15], format="%.3f")
                    
                    st.dataframe(
                        type_phase_df,
                        use_container_width=True,
                        column_config=type_col_config,
                        height=300
                    )
        else:
            st.info("No data available for type analysis with current filters.")
        
        # === 2. PROJECT ANALYSIS ===
        st.subheader("🏗️ Project Analysis")
        
        if len(filtered_df) > 0:
            # Calculate overall hrs/sqm for each project
            project_summary = filtered_df.copy()
            project_summary['Overall_Hrs_per_SQM'] = project_summary['hours_total'] / project_summary['project_sqm']
            project_summary['Overall_Hrs_per_SQM'] = project_summary['Overall_Hrs_per_SQM'].fillna(0)
            project_summary = project_summary.sort_values('Overall_Hrs_per_SQM', ascending=False)
            
            # Show top projects by efficiency
            top_projects = project_summary.head(20)
            
            fig_project = px.bar(
                top_projects,
                x='project_name',
                y='Overall_Hrs_per_SQM',
                title='Top 20 Projects by Overall Hours per SQM',
                color='Overall_Hrs_per_SQM',
                color_continuous_scale='Viridis',
                labels={'Overall_Hrs_per_SQM': 'Overall Hrs/SQM', 'project_name': 'Project'}
            )
            
            # Custom hover template
            fig_project.update_traces(
                hovertemplate=(
                    "<b style='font-size:16px'>%{x}</b><br><br>"
                    "<span style='font-size:14px'>"
                    "Overall Efficiency: <b>%{y:.4f} hrs/sqm</b><br>"
                    "Project Type: <b>%{customdata[0]}</b><br>"
                    "Total Area: <b>%{customdata[1]:,.0f} sqm</b><br>"
                    "Total Hours: <b>%{customdata[2]:,.0f}</b><br>"
                    "Status: <b>%{customdata[3]}</b>"
                    "</span>"
                    "<extra></extra>"
                ),
                customdata=top_projects[['project_tags', 'project_sqm', 'hours_total', 'project_status']].values
            )
            
            fig_project.update_layout(height=500, xaxis_tickangle=-45)
            st.plotly_chart(fig_project, use_container_width=True)
            
            # Project details in expander
            with st.expander("📊 Project Details"):
                # Include base columns plus all phase columns
                display_cols = ['project_name', 'project_tags', 'project_status', 'project_sqm', 'hours_total', 'Overall_Hrs_per_SQM']
                display_cols.extend(phase_columns)
                
                # Create column config for all columns
                project_col_config = {
                    "project_name": st.column_config.TextColumn("Project"),
                    "project_tags": st.column_config.TextColumn("Type"),
                    "project_status": st.column_config.TextColumn("Status"),
                    "project_sqm": st.column_config.NumberColumn("SQM", format="%.0f"),
                    "hours_total": st.column_config.NumberColumn("Total Hrs", format="%.1f"),
                    "Overall_Hrs_per_SQM": st.column_config.NumberColumn("Overall Hrs/SQM", format="%.3f")
                }
                
                # Add phase column configs
                for i, phase_col in enumerate(phase_columns):
                    clean_name = phase_names[i][:15] + "..." if len(phase_names[i]) > 15 else phase_names[i]
                    project_col_config[phase_col] = st.column_config.NumberColumn(clean_name, format="%.3f")
                
                st.dataframe(
                    project_summary[display_cols],
                    use_container_width=True,
                    column_config=project_col_config,
                    height=400
                )
        else:
            st.info("No data available for project analysis with current filters.")
        
        # === 3. PHASE ANALYSIS ===
        st.subheader("📊 Phase Analysis")
        
        if len(filtered_df) > 0:
            # Create phase summary
            phase_data = []
            for i, phase_col in enumerate(phase_columns):
                phase_name = phase_names[i]
                avg_hrs_sqm = filtered_df[phase_col].mean()
                total_projects = (filtered_df[phase_col] > 0).sum()
                if avg_hrs_sqm > 0:
                    phase_data.append({
                        'Phase': phase_name,
                        'Avg_Hrs_per_SQM': avg_hrs_sqm,
                        'Active_Projects': total_projects
                    })
            
            if phase_data:
                phase_summary_df = pd.DataFrame(phase_data)
                phase_summary_df = phase_summary_df.sort_values('Avg_Hrs_per_SQM', ascending=False)
                
                # Bar chart for phases
                top_phases = phase_summary_df.head(15)
                fig_phase = px.bar(
                    top_phases,
                    x='Phase',
                    y='Avg_Hrs_per_SQM',
                    title='Average Hours per SQM by Phase (Top 15)',
                    color='Avg_Hrs_per_SQM',
                    color_continuous_scale='RdYlGn_r',
                    labels={'Avg_Hrs_per_SQM': 'Avg Hrs/SQM'}
                )
                
                # Custom hover template
                fig_phase.update_traces(
                    hovertemplate=(
                        "<b style='font-size:16px'>%{x}</b><br><br>"
                        "<span style='font-size:14px'>"
                        "Average Efficiency: <b>%{y:.4f} hrs/sqm</b><br>"
                        "Active Projects: <b>%{customdata[0]} projects</b><br>"
                        "Usage Rate: <b>%{customdata[1]:.1f}%</b>"
                        "</span>"
                        "<extra></extra>"
                    ),
                    customdata=list(zip(
                        top_phases['Active_Projects'].values,
                        (top_phases['Active_Projects'] / len(filtered_df) * 100).values
                    ))
                )
                
                fig_phase.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig_phase, use_container_width=True)
                
                # Phase details in expander
                with st.expander("📊 Phase Details"):
                    # Create enhanced phase breakdown with project examples
                    phase_breakdown = []
                    
                    for _, phase_row in phase_summary_df.iterrows():
                        phase_name = phase_row['Phase']
                        # Find the corresponding column name
                        phase_col = None
                        for i, pname in enumerate(phase_names):
                            if pname == phase_name:
                                phase_col = phase_columns[i]
                                break
                        
                        if phase_col:
                            # Get projects that use this phase
                            phase_projects = filtered_df[filtered_df[phase_col] > 0]
                            
                            breakdown_row = {
                                'Phase': phase_name,
                                'Avg_Hrs_per_SQM': phase_row['Avg_Hrs_per_SQM'],
                                'Active_Projects': int(phase_row['Active_Projects']),
                                'Usage_Rate_%': (phase_row['Active_Projects'] / len(filtered_df) * 100) if len(filtered_df) > 0 else 0,
                                'Min_Hrs_SQM': phase_projects[phase_col].min() if len(phase_projects) > 0 else 0,
                                'Max_Hrs_SQM': phase_projects[phase_col].max() if len(phase_projects) > 0 else 0,
                                'Total_Hours_All_Projects': (phase_projects[phase_col] * phase_projects['project_sqm']).sum() if len(phase_projects) > 0 else 0
                            }
                            
                            # Add most and least efficient project examples
                            if len(phase_projects) > 0:
                                most_efficient = phase_projects.loc[phase_projects[phase_col].idxmin()]
                                least_efficient = phase_projects.loc[phase_projects[phase_col].idxmax()]
                                breakdown_row['Best_Project'] = f"{most_efficient['project_name'][:20]}... ({most_efficient[phase_col]:.3f})"
                                breakdown_row['Worst_Project'] = f"{least_efficient['project_name'][:20]}... ({least_efficient[phase_col]:.3f})"
                            else:
                                breakdown_row['Best_Project'] = "N/A"
                                breakdown_row['Worst_Project'] = "N/A"
                            
                            phase_breakdown.append(breakdown_row)
                    
                    if phase_breakdown:
                        phase_detail_df = pd.DataFrame(phase_breakdown)
                        
                        st.dataframe(
                            phase_detail_df,
                            use_container_width=True,
                            column_config={
                                "Phase": st.column_config.TextColumn("Phase"),
                                "Avg_Hrs_per_SQM": st.column_config.NumberColumn("Avg Hrs/SQM", format="%.3f"),
                                "Active_Projects": st.column_config.NumberColumn("Active Projects", format="%.0f"),
                                "Usage_Rate_%": st.column_config.NumberColumn("Usage %", format="%.1f"),
                                "Min_Hrs_SQM": st.column_config.NumberColumn("Min Hrs/SQM", format="%.3f"),
                                "Max_Hrs_SQM": st.column_config.NumberColumn("Max Hrs/SQM", format="%.3f"),
                                "Total_Hours_All_Projects": st.column_config.NumberColumn("Total Phase Hours", format="%.0f"),
                                "Best_Project": st.column_config.TextColumn("Most Efficient"),
                                "Worst_Project": st.column_config.TextColumn("Least Efficient")
                            },
                            height=400
                        )
            else:
                st.info("No phase data available with current filters.")
        else:
            st.info("No data available for phase analysis with current filters.")
        
        # Pie charts for distribution analysis
        st.subheader("📈 Distribution Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Project status distribution
            if selected_projects == "All Projects":
                status_counts = filtered_df['project_status'].value_counts()
                fig_pie1 = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title='Projects by Status'
                )
                st.plotly_chart(fig_pie1, use_container_width=True)
            else:
                # Hours distribution by phase for selected project
                if selected_projects != "All Projects":
                    project_data = filtered_df[filtered_df['project_name'] == selected_projects].iloc[0]
                    phase_hours = []
                    phase_labels = []
                    
                    for i, phase_col in enumerate(phase_columns):
                        if project_data[phase_col] > 0:
                            # Calculate actual hours for this phase
                            actual_hours = project_data[phase_col] * project_data['project_sqm']
                            phase_hours.append(actual_hours)
                            phase_labels.append(phase_names[i])
                    
                    if phase_hours:
                        fig_pie1 = px.pie(
                            values=phase_hours,
                            names=phase_labels,
                            title=f'Hours Distribution: {selected_projects}'
                        )
                        st.plotly_chart(fig_pie1, use_container_width=True)
        
        with col2:
            # Project tags distribution
            if selected_projects == "All Projects":
                tag_counts = filtered_df['project_tags'].value_counts()
                fig_pie2 = px.pie(
                    values=tag_counts.values,
                    names=tag_counts.index,
                    title='Projects by Category'
                )
                st.plotly_chart(fig_pie2, use_container_width=True)
            else:
                # SQM vs Hours scatter for context
                if len(filtered_df) > 1:
                    fig_scatter = px.scatter(
                        filtered_df,
                        x='project_sqm',
                        y='hours_total',
                        hover_data=['project_name'],
                        title='Project Size vs Total Hours',
                        labels={'project_sqm': 'Project SQM', 'hours_total': 'Total Hours'}
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Export functionality  
        st.subheader("💾 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Data",
                data=csv_data,
                file_name=f'hrs_sqm_data_{selected_projects.replace(" ", "_") if selected_projects != "All Projects" else "all_projects"}.csv',
                mime='text/csv',
            )
        
        with col2:
            if selected_phase == "All Phases":
                phase_data = []
                for i, phase_col in enumerate(phase_columns):
                    avg_hrs_sqm = filtered_df[phase_col].mean()
                    if avg_hrs_sqm > 0:
                        phase_data.append({
                            'Phase': phase_names[i],
                            'Avg_Hrs_per_SQM': avg_hrs_sqm,
                            'Active_Projects': (filtered_df[phase_col] > 0).sum()
                        })
                
                if phase_data:
                    phase_summary_csv = pd.DataFrame(phase_data).to_csv(index=False)
                    st.download_button(
                        label="📥 Download Phase Summary",
                        data=phase_summary_csv,
                        file_name='phase_summary.csv',
                        mime='text/csv',
                    )
        
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.info("Please check that the CSV file is properly formatted")
else:
    st.warning("No CSV files found matching pattern '*sqm*.csv' in data folder")
    st.info("Please add a CSV file with 'sqm' in the filename to the data folder")