import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
from utils.localhost_selector import is_localhost, render_localhost_file_selector

st.set_page_config(
    page_title="Hours / m2 / phase (beta)",
    page_icon="🏗️",
    layout="wide"
)

st.subheader("🏗️ Hours / m2 / phase (beta)")
#st.markdown("Calculate hours per square meter across different project phases")

def get_data_directory():
    """Get the appropriate data directory - prioritize project data over temp"""
    # First priority: Railway volume (production environment)
    if os.path.exists("/data"):
        return "/data"

    # Second priority: Project data directory (preferred for development)
    project_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    if os.path.exists(project_data_dir):
        return project_data_dir

    # Third priority: Local temp directory (fallback)
    temp_data_dir = os.path.expanduser("~/temp_data")
    if os.path.exists(temp_data_dir):
        return temp_data_dir

    # Final fallback: Create project data directory
    return project_data_dir

def try_autoload_sqm_data():
    """Try to autoload SQM data from data directory."""
    # LOCALHOST MODE: Show file selector
    if is_localhost():
        selected_client, selected_file_path = render_localhost_file_selector(
            session_prefix="sqm_",
            file_extensions=('.csv',),
            title="📂 Hours/SQM Data (Localhost)"
        )

        if not selected_file_path:
            # No file selected - return None to trigger "no data" message
            return None

        # Load the selected CSV file
        try:
            df = pd.read_csv(selected_file_path)
            return df
        except Exception as e:
            st.error(f"Could not load {os.path.basename(selected_file_path)}: {str(e)}")
            return None

    # PRODUCTION MODE: Auto-load from /data
    data_dir = get_data_directory()

    # Look for CSV files that might contain SQM data
    patterns = ['*hrs_sqm_phase*.csv']

    for pattern in patterns:
        files = glob.glob(os.path.join(data_dir, pattern))
        if files:
            # Use the first matching file
            filepath = files[0]
            try:
                df = pd.read_csv(filepath)
                return df
            except Exception as e:
                st.warning(f"Could not load {os.path.basename(filepath)}: {str(e)}")
                continue

    # If no pattern matches, try to load any CSV and check if it has SQM-like columns
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
    for filepath in csv_files:
        try:
            df = pd.read_csv(filepath)
            # Check if it has typical SQM columns
            sqm_columns = ['project_sqm', 'hours_total', 'project_name', '_hrs_per_sqm']
            if any(col in df.columns for col in sqm_columns) or any('_hrs_per_sqm' in col for col in df.columns):
                return df
        except Exception as e:
            continue

    return None

def render_upload_interface():
    """Render CSV file upload interface for SQM data."""
    st.error("📂 No SQM data found")
    st.markdown("""
    **To view SQM analysis, either:**
    1. Place a CSV file in the `/data` or `./data` directory with this naming pattern:
       - `*hrs_sqm_phase*.csv`

    2. **Or upload a file below:**
    """)

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload a CSV file with SQM phase data"
    )

    if uploaded_file is not None:
        st.info(f"📁 **File selected**: `{uploaded_file.name}` ({round(len(uploaded_file.getvalue()) / (1024*1024), 2)} MB)")

        with st.spinner("Processing file..."):
            try:
                # Read CSV file
                df = pd.read_csv(uploaded_file)

                # Store in session state
                st.session_state.sqm_data = df

                st.success("🎉 **File processed successfully!**")
                st.info(f"Loaded {len(df):,} records")

            except Exception as e:
                st.error(f"❌ **File processing failed**: {str(e)}")

    st.markdown("""
    **Expected CSV structure:**
    - project_number
    - project_name
    - project_tags
    - project_status
    - project_sqm
    - hours_total
    - Various phase columns ending with '_hrs_per_sqm'
    """)

    return None

# Check if SQM data is available
if not st.session_state.get('sqm_available', False):
    st.error("📂 Hrs/m²/Phase data not available")
    st.info("Please select a dataset that includes an hrs/sqm/phase CSV file.")
    st.stop()

# Session state for SQM data
if 'sqm_data' not in st.session_state:
    st.session_state.sqm_data = None

# Load data from global CSV path if not already loaded
if st.session_state.sqm_data is None:
    csv_path = st.session_state.get('sqm_csv_path')
    if csv_path:
        try:
            df = pd.read_csv(csv_path)
            st.session_state.sqm_data = df
        except Exception as e:
            st.error(f"Failed to load SQM data: {str(e)}")
            st.stop()
    else:
        st.error("SQM CSV path not found in session state")
        st.stop()
else:
    df = st.session_state.sqm_data

# Display data metrics and continue with analysis
if df is not None:
    #st.success(f"✅ Data loaded successfully!")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Projects", len(df))
    with col2:
        st.metric("Hours", f"{df['hours_total'].sum():,.0f}")
    with col3:
        st.metric("GFA (m2)", f"{df['project_sqm'].sum():,.0f}")

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

    # === 1. PHASE ANALYSIS ===
    st.subheader("📊 Hours per SQM by Phase")

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

            # Bar chart for ALL phases (removed top 15 limit)
            fig_phase = px.bar(
                phase_summary_df,
                x='Phase',
                y='Avg_Hrs_per_SQM',
                title='Average Hours per SQM by Phase',
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
                    phase_summary_df['Active_Projects'].values,
                    (phase_summary_df['Active_Projects'] / len(filtered_df) * 100).values
                ))
            )

            fig_phase.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_phase, use_container_width=True)

            # Phase details table
            with st.expander("📊 Complete Phase Breakdown"):
                st.dataframe(
                    phase_summary_df,
                    use_container_width=True,
                    column_config={
                        "Phase": st.column_config.TextColumn("Phase"),
                        "Avg_Hrs_per_SQM": st.column_config.NumberColumn("Avg Hrs/SQM", format="%.3f"),
                        "Active_Projects": st.column_config.NumberColumn("Active Projects", format="%.0f")
                    },
                    height=400
                )
        else:
            st.info("No phase data available with current filters.")
    else:
        st.info("No data available for phase analysis with current filters.")

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

    # === 2. PROJECT TYPE ANALYSIS ===
    st.subheader("🏢 Phase Factors by Project Type")

    # Create phase-by-project-type matrix
    if len(filtered_df) > 0:
        # Create a matrix of phases vs project types
        phase_type_data = []
        project_types = filtered_df['project_tags'].unique()

        for project_type in project_types:
            type_projects = filtered_df[filtered_df['project_tags'] == project_type]
            row_data = {'Project_Type': project_type, 'Project_Count': len(type_projects)}

            # Calculate average hrs/sqm for each phase for this project type
            for i, phase_col in enumerate(phase_columns):
                phase_name = phase_names[i]
                # Only include projects that use this phase
                phase_projects = type_projects[type_projects[phase_col] > 0]
                if len(phase_projects) > 0:
                    avg_hrs_sqm = phase_projects[phase_col].mean()
                    row_data[phase_name] = avg_hrs_sqm
                else:
                    row_data[phase_name] = 0

            phase_type_data.append(row_data)

        if phase_type_data:
            phase_type_df = pd.DataFrame(phase_type_data)

            # Create visualization for top phases only (for readability)
            # Get top 10 phases by overall usage
            top_phase_names = [p for p in phase_names[:10]]  # Take first 10 phases

            # Prepare data for grouped bar chart
            melted_data = []
            for _, row in phase_type_df.iterrows():
                for phase_name in top_phase_names:
                    if phase_name in row and row[phase_name] > 0:
                        melted_data.append({
                            'Project_Type': row['Project_Type'],
                            'Phase': phase_name,
                            'Hrs_per_SQM': row[phase_name]
                        })

            if melted_data:
                melted_df = pd.DataFrame(melted_data)

                # Grouped bar chart
                fig_type = px.bar(
                    melted_df,
                    x='Phase',
                    y='Hrs_per_SQM',
                    color='Project_Type',
                    title='Phase Factors by Project Type (Top 10 Phases)',
                    labels={'Hrs_per_SQM': 'Hrs/SQM', 'Phase': 'Phase'},
                    barmode='group'
                )

                fig_type.update_layout(height=500, xaxis_tickangle=-45)
                st.plotly_chart(fig_type, use_container_width=True)

                # Complete phase-by-project-type matrix table
                with st.expander("📊 Complete Phase Factor Matrix"):
                    # Display the complete matrix
                    display_cols = ['Project_Type', 'Project_Count'] + phase_names
                    available_cols = [col for col in display_cols if col in phase_type_df.columns]

                    # Create column config
                    col_config = {
                        "Project_Type": st.column_config.TextColumn("Project Type"),
                        "Project_Count": st.column_config.NumberColumn("Projects", format="%.0f")
                    }

                    # Add phase column configs
                    for phase_name in phase_names:
                        if phase_name in phase_type_df.columns:
                            col_config[phase_name] = st.column_config.NumberColumn(
                                phase_name[:15] + "..." if len(phase_name) > 15 else phase_name,
                                format="%.3f"
                            )

                    st.dataframe(
                        phase_type_df[available_cols],
                        use_container_width=True,
                        column_config=col_config,
                        height=300
                    )
            else:
                st.info("No phase data available for grouping by project type.")
        else:
            st.info("No phase-type matrix data available.")
    else:
        st.info("No data available for phase analysis by project type.")
    
    # === 3. INDIVIDUAL PROJECT ANALYSIS ===
    st.subheader("🏗️ Individual Project Analysis")
    
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