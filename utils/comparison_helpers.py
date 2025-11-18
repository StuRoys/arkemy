# utils/comparison_helpers.py
"""
Helper functions for period comparison feature.
Handles date calculations, data aggregation, and comparison metrics.
"""

import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, Tuple, Optional


def calculate_period_dates(
    end_date: datetime,
    months: int,
    mode: str
) -> Tuple[datetime, datetime, datetime, datetime]:
    """
    Calculate Period A and Period B date ranges based on comparison mode.

    Args:
        end_date: Last day of Period A
        months: Number of months in each period (1-12)
        mode: 'period' (consecutive) or 'year' (year-over-year)

    Returns:
        Tuple of (period_a_start, period_a_end, period_b_start, period_b_end)

    Examples:
        >>> # Period vs Period, 6 months, ending 2025-09-30
        >>> calculate_period_dates(date(2025, 9, 30), 6, 'period')
        (date(2025, 4, 1), date(2025, 9, 30), date(2024, 10, 1), date(2025, 3, 31))

        >>> # Year vs Year, 3 months, ending 2025-09-30
        >>> calculate_period_dates(date(2025, 9, 30), 3, 'year')
        (date(2025, 7, 1), date(2025, 9, 30), date(2024, 7, 1), date(2024, 9, 30))
    """
    # Convert to datetime if needed
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date).date()
    elif isinstance(end_date, pd.Timestamp):
        end_date = end_date.date()

    # Period A: end_date minus months to end_date
    period_a_end = end_date
    period_a_start = (end_date - relativedelta(months=months) + timedelta(days=1))

    if mode == 'period':
        # Period vs Period: consecutive/adjacent periods
        # Period B ends the day before Period A starts
        period_b_end = period_a_start - timedelta(days=1)
        period_b_start = period_b_end - relativedelta(months=months) + timedelta(days=1)
    else:  # mode == 'year'
        # Year vs Year: same period, previous year(s)
        period_b_end = period_a_end - relativedelta(years=1)
        period_b_start = period_a_start - relativedelta(years=1)

    return (period_a_start, period_a_end, period_b_start, period_b_end)


def format_period_label(start_date: datetime, end_date: datetime) -> str:
    """
    Format period date range for display.

    Args:
        start_date: Period start
        end_date: Period end

    Returns:
        Formatted string like "Apr 1, 2025 - Sep 30, 2025"
    """
    return f"{start_date.strftime('%b %-d, %Y')} - {end_date.strftime('%b %-d, %Y')}"


def format_period_label_short(start_date: datetime, end_date: datetime) -> str:
    """
    Format period date range in short format for card headers.

    Args:
        start_date: Period start
        end_date: Period end

    Returns:
        Formatted string like "JUL-SEP 2025" or "APR-JUN 2025"
    """
    start_month = start_date.strftime('%b').upper()
    end_month = end_date.strftime('%b').upper()
    year = end_date.strftime('%Y')

    return f"{start_month}-{end_month} {year}"


def aggregate_period_metrics(
    df: pd.DataFrame,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, float]:
    """
    Aggregate company-wide metrics for a specific date range.

    Args:
        df: Time records DataFrame
        start_date: Period start date (inclusive)
        end_date: Period end date (inclusive)

    Returns:
        Dictionary containing:
            - effective_rate: Total fee / total hours worked
            - billability: Billable hours % (0-100)
            - fee: Total fee/revenue
            - profit: Total profit
            - profit_margin: Profit % of fee (0-100)
            - hours_used: Total hours worked (for reference)
    """
    # Filter to date range (inclusive)
    period_df = df[
        (df['record_date'] >= pd.to_datetime(start_date)) &
        (df['record_date'] <= pd.to_datetime(end_date))
    ]

    # Check if period has data
    if period_df.empty:
        return {
            'effective_rate': 0.0,
            'billability': 0.0,
            'fee': 0.0,
            'profit': 0.0,
            'profit_margin': 0.0,
            'hours_used': 0.0,
            'has_data': False
        }

    # Aggregate base metrics
    total_hours = period_df['hours_used'].sum()
    total_billable = period_df['hours_billable'].sum()
    total_fee = period_df['fee_record'].sum()
    total_profit = period_df['profit_record'].sum() if 'profit_record' in period_df.columns else 0.0

    # Calculate derived metrics with safe division
    effective_rate = total_fee / total_hours if total_hours > 0 else 0.0
    billability = (total_billable / total_hours * 100) if total_hours > 0 else 0.0
    profit_margin = (total_profit / total_fee * 100) if total_fee > 0 else 0.0

    return {
        'effective_rate': round(effective_rate, 2),
        'billability': round(billability, 2),
        'fee': round(total_fee, 2),
        'profit': round(total_profit, 2),
        'profit_margin': round(profit_margin, 2),
        'hours_used': round(total_hours, 2),
        'has_data': True
    }


def calculate_comparison(
    period_a_metrics: Dict[str, float],
    period_b_metrics: Dict[str, float]
) -> Dict[str, Dict[str, float]]:
    """
    Calculate absolute and percentage differences between two periods.

    Args:
        period_a_metrics: Metrics dict from aggregate_period_metrics() for Period A
        period_b_metrics: Metrics dict from aggregate_period_metrics() for Period B

    Returns:
        Dictionary with structure:
        {
            'metric_name': {
                'a': Period A value,
                'b': Period B value,
                'diff': Absolute difference (A - B),
                'pct_change': Percentage change ((A - B) / B * 100),
                'direction': 'up', 'down', or 'neutral'
            }
        }
    """
    metrics_to_compare = ['hours_used', 'effective_rate', 'billability', 'fee', 'profit', 'profit_margin']
    comparison = {}

    for metric in metrics_to_compare:
        a_value = period_a_metrics.get(metric, 0.0)
        b_value = period_b_metrics.get(metric, 0.0)

        # Calculate difference
        diff = a_value - b_value

        # Calculate percentage change (handle division by zero)
        if b_value != 0:
            pct_change = (diff / b_value) * 100
        else:
            # If B is zero and A is positive, show as +100% or more
            # If both are zero, show as 0%
            pct_change = 100.0 if a_value > 0 else 0.0

        # Determine direction
        if abs(diff) < 0.01:  # Essentially zero
            direction = 'neutral'
        elif diff > 0:
            direction = 'up'
        else:
            direction = 'down'

        comparison[metric] = {
            'a': round(a_value, 2),
            'b': round(b_value, 2),
            'diff': round(diff, 2),
            'pct_change': round(pct_change, 2),
            'direction': direction
        }

    return comparison


def validate_period_data(
    df: pd.DataFrame,
    period_b_start: datetime,
    period_b_end: datetime
) -> Tuple[bool, Optional[str]]:
    """
    Validate if Period B has data available in the dataset.

    Args:
        df: Time records DataFrame
        period_b_start: Period B start date
        period_b_end: Period B end date

    Returns:
        Tuple of (is_valid, warning_message)
        - is_valid: True if Period B has data, False otherwise
        - warning_message: None if valid, error message string if invalid
    """
    # Get earliest date in dataset
    earliest_date = df['record_date'].min()

    # Convert to date for comparison
    if isinstance(earliest_date, pd.Timestamp):
        earliest_date = earliest_date.date()
    if isinstance(period_b_start, pd.Timestamp):
        period_b_start = period_b_start.date()
    if isinstance(period_b_end, pd.Timestamp):
        period_b_end = period_b_end.date()

    # Check if Period B starts before earliest data
    if period_b_start < earliest_date:
        return (
            False,
            f"⚠️ Period B extends before available data. "
            f"Data starts on {earliest_date.strftime('%b %-d, %Y')}, "
            f"but Period B needs data from {period_b_start.strftime('%b %-d, %Y')}."
        )

    # Check if Period B has any records
    period_b_df = df[
        (df['record_date'] >= pd.to_datetime(period_b_start)) &
        (df['record_date'] <= pd.to_datetime(period_b_end))
    ]

    if period_b_df.empty:
        return (
            False,
            f"⚠️ No data exists in Period B "
            f"({period_b_start.strftime('%b %-d, %Y')} - {period_b_end.strftime('%b %-d, %Y')})."
        )

    return (True, None)


def calculate_period_from_comparison_type(
    comparison_type: str,
    max_date: datetime,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None
) -> Tuple[datetime, datetime, datetime, datetime]:
    """
    Calculate period dates based on comparison type dropdown selection.

    Args:
        comparison_type: Selected comparison type from dropdown
        max_date: Maximum date from filtered dataset
        start_year: Start year from sidebar filters (for year comparison)
        end_year: End year from sidebar filters (for year comparison)

    Returns:
        Tuple of (period_a_start, period_a_end, period_b_start, period_b_end)
    """
    # Ensure max_date is a date object
    if isinstance(max_date, pd.Timestamp):
        max_date = max_date.date()

    if comparison_type == "Last month vs previous month":
        return calculate_period_dates(max_date, 1, 'period')

    elif comparison_type == "Last quarter vs previous quarter":
        return calculate_period_dates(max_date, 3, 'period')

    elif comparison_type == "Last 6 months vs previous 6 months":
        return calculate_period_dates(max_date, 6, 'period')

    elif comparison_type == "Last 12 months vs previous 12 months":
        return calculate_period_dates(max_date, 12, 'period')

    elif comparison_type == "Year to date vs previous year to date":
        # Period A: Jan 1 of current year to max_date
        period_a_start = datetime(max_date.year, 1, 1).date()
        period_a_end = max_date

        # Period B: Jan 1 of previous year to same day of previous year
        period_b_start = datetime(max_date.year - 1, 1, 1).date()
        period_b_end = datetime(max_date.year - 1, max_date.month, max_date.day).date()

        return (period_a_start, period_a_end, period_b_start, period_b_end)

    elif comparison_type == "Selected end year vs start year":
        # Period A: Full calendar year of end_year
        if end_year is None:
            end_year = max_date.year
        period_a_start = datetime(end_year, 1, 1).date()
        period_a_end = datetime(end_year, 12, 31).date()

        # Period B: Full calendar year of start_year
        if start_year is None:
            start_year = end_year - 1
        period_b_start = datetime(start_year, 1, 1).date()
        period_b_end = datetime(start_year, 12, 31).date()

        return (period_a_start, period_a_end, period_b_start, period_b_end)

    else:
        # Fallback to last 6 months
        return calculate_period_dates(max_date, 6, 'period')


def get_metric_config() -> Dict[str, Dict[str, any]]:
    """
    Get configuration for each comparison metric.

    Returns:
        Dictionary with metric display properties:
        - label: Display name
        - unit: Unit type ('currency', 'percentage', 'percentage_points', 'hours')
        - format: Format string
        - positive_is_good: Whether increases are positive (for color coding)
    """
    return {
        'hours_used': {
            'label': 'Hours Used',
            'unit': 'hours',
            'positive_is_good': True
        },
        'effective_rate': {
            'label': 'Effective Rate',
            'unit': 'currency_per_hour',
            'positive_is_good': True
        },
        'billability': {
            'label': 'Billability',
            'unit': 'percentage',
            'positive_is_good': True
        },
        'fee': {
            'label': 'Fee',
            'unit': 'currency',
            'positive_is_good': True
        },
        'profit': {
            'label': 'Profit',
            'unit': 'currency',
            'positive_is_good': True
        },
        'profit_margin': {
            'label': 'Profit Margin',
            'unit': 'percentage',
            'positive_is_good': True
        }
    }
