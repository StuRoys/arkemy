#summary_kpis.py
import streamlit as st
from datetime import datetime
from typing import Dict, Any

# Import currency formatter functions
from utils.currency_formatter import format_currency, format_millions

def display_summary_metrics(metrics: Dict[str, Any]) -> None:
    """
    Display the summary metrics in a structured card layout.
    
    Args:
        metrics: Dictionary containing calculated metrics
    """
    # Define card styles
    st.markdown("""
        <style>
        .metric-card {
            background-color: #f8f9fa;
            border-radius: 11px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            height: 100%;
        }
        .card-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #484848;
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 5px;
        }
        .metric-row {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
        }
        .metric-column {
            flex: 1;
            min-width: 120px;
            padding: 0 10px;
            margin-bottom: 10px;
            text-align: center;
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .metric-label {
            font-size: 0.9em;
            color: #666;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Format dates and basic metrics
    first_date = metrics['first_time_record'].strftime("%d.%m.%Y") if metrics.get('first_time_record') else "N/A"
    last_date = metrics['last_time_record'].strftime("%d.%m.%Y") if metrics.get('last_time_record') else "N/A"
    years_between = f"{metrics.get('years_between', 0):.1f}"
    total_entries = f"{metrics.get('total_entries', 0):,}".replace(',', ' ')
    
    # Row 1: Context (2 columns)
    col1, col2 = st.columns(2)
    
    # Overview card
    with col1:
        html_content = f"""
        <div class="metric-card">
            <div class="card-title">📊 Overview</div>
            <div class="metric-row">
                <div class="metric-column">
                    <div class="metric-value">{first_date}</div>
                    <div class="metric-label">First record</div>
                </div>
                <div class="metric-column">
                    <div class="metric-value">{last_date}</div>
                    <div class="metric-label">Last record</div>
                </div>
                <div class="metric-column">
                    <div class="metric-value">{years_between}</div>
                    <div class="metric-label">Years</div>
                </div>
            </div>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)
    
    # Scope card
    with col2:
        html_content = f"""
        <div class="metric-card">
            <div class="card-title">👥 Scope</div>
            <div class="metric-row">
                <div class="metric-column">
                    <div class="metric-value">{metrics.get('unique_people', 0)}</div>
                    <div class="metric-label">Coworkers</div>
                </div>
                <div class="metric-column">
                    <div class="metric-value">{metrics.get('unique_projects', 0)}</div>
                    <div class="metric-label">Projects</div>
                </div>
                <div class="metric-column">
                    <div class="metric-value">{total_entries}</div>
                    <div class="metric-label">Time records</div>
                </div>
            </div>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)
    
    # Row 2: Core Business (2 columns)
    col3, col4 = st.columns(2)
    
    # Hours card
    with col3:
        total_hours = f"{int(metrics.get('total_hours', 0)):,}".replace(',', ' ')
        billable_hours = f"{int(metrics.get('total_billable_hours', 0)):,}".replace(',', ' ')
        billability_percentage = f"{metrics.get('billability_percentage', 0):.1f}%"
        
        html_content = f"""
        <div class="metric-card">
            <div class="card-title">⏱️ Hours</div>
            <div class="metric-row">
                <div class="metric-column">
                    <div class="metric-value">{total_hours}</div>
                    <div class="metric-label">Hours worked</div>
                </div>
                <div class="metric-column">
                    <div class="metric-value">{billable_hours}</div>
                    <div class="metric-label">Hours billable</div>
                </div>
                <div class="metric-column">
                    <div class="metric-value">{billability_percentage}</div>
                    <div class="metric-label">Billability</div>
                </div>
            </div>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)
    
    # Financial Results card
    with col4:
        total_fee = format_millions(metrics.get('total_fee', 0))
        total_cost = format_millions(metrics.get('total_cost', 0))
        total_profit = format_millions(metrics.get('total_profit', 0))
        
        html_content = f"""
        <div class="metric-card">
            <div class="card-title">💰 Income</div>
            <div class="metric-row">
                <div class="metric-column">
                    <div class="metric-value">{total_fee}</div>
                    <div class="metric-label">Fees</div>
                </div>
                <div class="metric-column">
                    <div class="metric-value">{total_cost}</div>
                    <div class="metric-label">Cost</div>
                </div>
                <div class="metric-column">
                    <div class="metric-value">{total_profit}</div>
                    <div class="metric-label">Profit</div>
                </div>
            </div>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)
    
    # Row 3: Performance (full width)
    billable_hourly_rate = format_currency(metrics.get('Billable rate', 0)) + "/hr"
    effective_hourly_rate = format_currency(metrics.get('Effective rate', 0)) + "/hr"
    avg_fee_per_project = format_millions(metrics.get('avg_fee_per_project', 0))
    
    # Handle profit margin with N/A when fee = 0
    if metrics.get('total_fee', 0) > 0:
        profit_margin = f"{metrics.get('profit_margin_percentage', 0):.1f}%"
    else:
        profit_margin = "N/A"
    
    html_content = f"""
    <div class="metric-card">
        <div class="card-title">📈 Performance</div>
        <div class="metric-row">
            <div class="metric-column">
                <div class="metric-value">{billable_hourly_rate}</div>
                <div class="metric-label">Billable rate</div>
            </div>
            <div class="metric-column">
                <div class="metric-value">{effective_hourly_rate}</div>
                <div class="metric-label">Effective rate</div>
            </div>
            <div class="metric-column">
                <div class="metric-value">{avg_fee_per_project}</div>
                <div class="metric-label">Avg fee per project</div>
            </div>
            <div class="metric-column">
                <div class="metric-value">{profit_margin}</div>
                <div class="metric-label">Profit margin</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)