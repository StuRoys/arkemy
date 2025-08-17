# utils/currency_formatter.py
import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List

# Currency configuration dictionaries
CURRENCY_SYMBOLS = {
    'usd': '$',       # United States Dollar
    'eur': '€',       # Euro
    'jpy': '¥',       # Japanese Yen
    'gbp': '£',       # British Pound Sterling
    'aud': 'A$',      # Australian Dollar
    'cad': 'C$',      # Canadian Dollar
    'chf': 'CHF',     # Swiss Franc
    'cny': '¥',       # Chinese Yuan/Renminbi
    'hkd': 'HK$',     # Hong Kong Dollar
    'sgd': 'S$',      # Singapore Dollar
    'nzd': 'NZ$',     # New Zealand Dollar
    'sek': 'kr',      # Swedish Krona
    'nok': 'kr',      # Norwegian Krone
    'krw': '₩',       # South Korean Won
    'mxn': 'Mex$',    # Mexican Peso
    'inr': '₹',       # Indian Rupee
    'rub': '₽',       # Russian Ruble
    'brl': 'R$',      # Brazilian Real
    'zar': 'R',       # South African Rand
    'try': '₺',       # Turkish Lira
    'dkk': 'kr',      # Danish Krone
    'pln': 'zł',      # Polish Złoty
    'thb': '฿',       # Thai Baht
    'idr': 'Rp',      # Indonesian Rupiah
    'czk': 'Kč',      # Czech Koruna
    'huf': 'Ft',      # Hungarian Forint
    'ils': '₪',       # Israeli New Shekel
    'clp': 'CLP$',    # Chilean Peso
    'php': '₱',       # Philippine Peso
    'aed': 'د.إ',     # UAE Dirham
    'cop': 'COL$',    # Colombian Peso
    'sar': '﷼',       # Saudi Riyal
    'myr': 'RM',      # Malaysian Ringgit
    'ron': 'lei',     # Romanian Leu
    'twd': 'NT$',     # Taiwanese Dollar
    'ars': 'AR$',     # Argentine Peso
    'ngn': '₦',       # Nigerian Naira
    'pkr': '₨',       # Pakistani Rupee
    'egp': 'E£',      # Egyptian Pound
    'bdt': '৳',       # Bangladeshi Taka
    'vnd': '₫',       # Vietnamese Dong
    'uah': '₴',       # Ukrainian Hryvnia
    'qar': 'QR',      # Qatari Riyal
    'kwd': 'KD',      # Kuwaiti Dinar
    'mad': 'MAD',     # Moroccan Dirham
    'pen': 'S/',      # Peruvian Sol
    'isk': 'kr',      # Icelandic Króna
    'bgn': 'лв',      # Bulgarian Lev
    'hrk': 'kn',      # Croatian Kuna
    'kzt': '₸',       # Kazakhstani Tenge
}

# Symbol positions (before or after the number)
SYMBOL_POSITIONS = {
    'usd': 'before',  # $100
    'eur': 'before',  # €100
    'jpy': 'before',  # ¥100
    'gbp': 'before',  # £100
    'aud': 'before',  # A$100
    'cad': 'before',  # C$100
    'chf': 'before',  # CHF100
    'cny': 'before',  # ¥100
    'hkd': 'before',  # HK$100
    'sgd': 'before',  # S$100
    'nzd': 'before',  # NZ$100
    'sek': 'after',   # 100 kr
    'nok': 'after',   # 100 kr
    'krw': 'before',  # ₩100
    'mxn': 'before',  # Mex$100
    'inr': 'before',  # ₹100
    'rub': 'after',   # 100 ₽
    'brl': 'before',  # R$100
    'zar': 'before',  # R100
    'try': 'before',  # ₺100
    'dkk': 'after',   # 100 kr
    'pln': 'after',   # 100 zł
    'thb': 'before',  # ฿100
    'idr': 'before',  # Rp100
    'czk': 'after',   # 100 Kč
    'huf': 'after',   # 100 Ft
    'ils': 'before',  # ₪100
    'clp': 'before',  # CLP$100
    'php': 'before',  # ₱100
    'aed': 'before',  # د.إ100
    'cop': 'before',  # COL$100
    'sar': 'before',  # ﷼100
    'myr': 'before',  # RM100
    'ron': 'after',   # 100 lei
    'twd': 'before',  # NT$100
    'ars': 'before',  # AR$100
    'ngn': 'before',  # ₦100
    'pkr': 'before',  # ₨100
    'egp': 'before',  # E£100
    'bdt': 'before',  # ৳100
    'vnd': 'after',   # 100 ₫
    'uah': 'before',  # ₴100
    'qar': 'after',   # 100 QR
    'kwd': 'after',   # 100 KD
    'mad': 'before',  # MAD100
    'pen': 'before',  # S/100
    'isk': 'after',   # 100 kr
    'bgn': 'after',   # 100 лв
    'hrk': 'after',   # 100 kn
    'kzt': 'after',   # 100 ₸
}

# Decimal separators by currency
DECIMAL_SEPARATORS = {
    'usd': '.',
    'eur': ',',
    'jpy': '.',
    'gbp': '.',
    'aud': '.',
    'cad': '.',
    'chf': '.',
    'cny': '.',
    'hkd': '.',
    'sgd': '.',
    'nzd': '.',
    'sek': ',',
    'nok': ',',
    'krw': '.',
    'mxn': '.',
    'inr': '.',
    'rub': ',',
    'brl': ',',
    'zar': '.',
    'try': ',',
    'dkk': ',',
    'pln': ',',
    'thb': '.',
    'idr': ',',
    'czk': ',',
    'huf': ',',
    'ils': '.',
    'clp': ',',
    'php': '.',
    'aed': '.',
    'cop': ',',
    'sar': '.',
    'myr': '.',
    'ron': ',',
    'twd': '.',
    'ars': ',',
    'ngn': '.',
    'pkr': '.',
    'egp': '.',
    'bdt': '.',
    'vnd': ',',
    'uah': ',',
    'qar': '.',
    'kwd': '.',
    'mad': '.',
    'pen': '.',
    'isk': ',',
    'bgn': ',',
    'hrk': ',',
    'kzt': ',',
}

# Thousand separators by currency
THOUSAND_SEPARATORS = {
    'usd': ',',
    'eur': '.',
    'jpy': ',',
    'gbp': ',',
    'aud': ',',
    'cad': ',',
    'chf': "'",
    'cny': ',',
    'hkd': ',',
    'sgd': ',',
    'nzd': ',',
    'sek': ' ',
    'nok': ' ',
    'krw': ',',
    'mxn': ',',
    'inr': ',',
    'rub': ' ',
    'brl': '.',
    'zar': ',',
    'try': '.',
    'dkk': '.',
    'pln': ' ',
    'thb': ',',
    'idr': '.',
    'czk': ' ',
    'huf': ' ',
    'ils': ',',
    'clp': '.',
    'php': ',',
    'aed': ',',
    'cop': '.',
    'sar': ',',
    'myr': ',',
    'ron': '.',
    'twd': ',',
    'ars': '.',
    'ngn': ',',
    'pkr': ',',
    'egp': ',',
    'bdt': ',',
    'vnd': '.',
    'uah': ' ',
    'qar': ',',
    'kwd': ',',
    'mad': ',',
    'pen': ',',
    'isk': '.',
    'bgn': ' ',
    'hrk': '.',
    'kzt': ' ',
}

# Million abbreviations by currency
MILLION_UNITS = {
    'usd': 'M$',
    'eur': 'M€',
    'jpy': 'M¥',
    'gbp': 'M£',
    'aud': 'MA$',
    'cad': 'MC$',
    'chf': 'MCHF',
    'cny': 'M¥',
    'hkd': 'MHK$',
    'sgd': 'MS$',
    'nzd': 'MNZ$',
    'sek': 'Mkr',
    'nok': 'MNOK',
    'krw': 'M₩',
    'mxn': 'MMex$',
    'inr': 'M₹',
    'rub': 'M₽',
    'brl': 'MR$',
    'zar': 'MR',
    'try': 'M₺',
    'dkk': 'Mkr',
    'pln': 'Mzł',
    'thb': 'M฿',
    'idr': 'MRp',
    'czk': 'MKč',
    'huf': 'MFt',
    'ils': 'M₪',
    'clp': 'MCLP$',
    'php': 'M₱',
    'aed': 'Mد.إ',
    'cop': 'MCOL$',
    'sar': 'M﷼',
    'myr': 'MRM',
    'ron': 'Mlei',
    'twd': 'MNT$',
    'ars': 'MAR$',
    'ngn': 'M₦',
    'pkr': 'M₨',
    'egp': 'ME£',
    'bdt': 'M৳',
    'vnd': 'M₫',
    'uah': 'M₴',
    'qar': 'MQR',
    'kwd': 'MKD',
    'mad': 'MMAD',
    'pen': 'MS/',
    'isk': 'Mkr',
    'bgn': 'Mлв',
    'hrk': 'Mkn',
    'kzt': 'M₸',
}

# Currency names to display in UI
CURRENCY_NAMES = {
    'usd': 'US Dollar',
    'eur': 'Euro',
    'jpy': 'Japanese Yen',
    'gbp': 'British Pound',
    'aud': 'Australian Dollar',
    'cad': 'Canadian Dollar',
    'chf': 'Swiss Franc',
    'cny': 'Chinese Yuan',
    'hkd': 'Hong Kong Dollar',
    'sgd': 'Singapore Dollar',
    'nzd': 'New Zealand Dollar',
    'sek': 'Swedish Krona',
    'nok': 'Norwegian Krone',
    'krw': 'South Korean Won',
    'mxn': 'Mexican Peso',
    'inr': 'Indian Rupee',
    'rub': 'Russian Ruble',
    'brl': 'Brazilian Real',
    'zar': 'South African Rand',
    'try': 'Turkish Lira',
    'dkk': 'Danish Krone',
    'pln': 'Polish Złoty',
    'thb': 'Thai Baht',
    'idr': 'Indonesian Rupiah',
    'czk': 'Czech Koruna',
    'huf': 'Hungarian Forint',
    'ils': 'Israeli New Shekel',
    'clp': 'Chilean Peso',
    'php': 'Philippine Peso',
    'aed': 'UAE Dirham',
    'cop': 'Colombian Peso',
    'sar': 'Saudi Riyal',
    'myr': 'Malaysian Ringgit',
    'ron': 'Romanian Leu',
    'twd': 'Taiwanese Dollar',
    'ars': 'Argentine Peso',
    'ngn': 'Nigerian Naira',
    'pkr': 'Pakistani Rupee',
    'egp': 'Egyptian Pound',
    'bdt': 'Bangladeshi Taka',
    'vnd': 'Vietnamese Dong',
    'uah': 'Ukrainian Hryvnia',
    'qar': 'Qatari Riyal',
    'kwd': 'Kuwaiti Dinar',
    'mad': 'Moroccan Dirham',
    'pen': 'Peruvian Sol',
    'isk': 'Icelandic Króna',
    'bgn': 'Bulgarian Lev',
    'hrk': 'Croatian Kuna',
    'kzt': 'Kazakhstani Tenge',
}

def get_currency_code() -> str:
    """
    Get the current currency code from session state.
    Returns None if not set.
    """
    if 'currency' in st.session_state:
        return st.session_state.currency
    return None

def format_currency(value: float, decimals: int = 0) -> str:
    """
    Format a value as currency based on the current currency settings.
    If no currency is selected, returns a simple formatted number.
    
    Args:
        value: The numeric value to format
        decimals: Number of decimal places to show
    
    Returns:
        Formatted currency string
    """
    currency = get_currency_code()
    
    # If no currency is selected, just format as a number
    if currency is None:
        return f"{value:,.{decimals}f}"
    
    # Get formatting parameters for this currency
    symbol = CURRENCY_SYMBOLS.get(currency, '')
    decimal_sep = DECIMAL_SEPARATORS.get(currency, '.')
    thousand_sep = THOUSAND_SEPARATORS.get(currency, ',')
    position = SYMBOL_POSITIONS.get(currency, 'after')
    
    # Format the numeric part
    if decimals == 0:
        formatted_value = f"{int(value):,}".replace(',', thousand_sep)
    else:
        formatted_value = f"{value:,.{decimals}f}".replace(',', '#').replace('.', decimal_sep).replace('#', thousand_sep)
    
    # Add the currency symbol in the correct position
    if position == 'before':
        return f"{symbol}{formatted_value}"
    else:
        return f"{formatted_value} {symbol}"

def format_millions(value: float, decimals: int = 2) -> str:
    """
    Format a value in millions with the appropriate currency unit.
    If no currency is selected, just formats as X.XX M
    
    Args:
        value: The numeric value to format (in the original currency)
        decimals: Number of decimal places to show
    
    Returns:
        Formatted string with million unit
    """
    currency = get_currency_code()
    
    # Convert to millions
    value_in_millions = value / 1000000
    
    # If no currency is selected, just format with M
    if currency is None:
        return f"{value_in_millions:.{decimals}f} M"
    
    million_unit = MILLION_UNITS.get(currency, 'M')
    decimal_sep = DECIMAL_SEPARATORS.get(currency, '.')
    thousand_sep = THOUSAND_SEPARATORS.get(currency, ',')
    position = SYMBOL_POSITIONS.get(currency, 'after')
    
    # Format with appropriate decimal separator
    if decimals == 0:
        formatted_value = f"{int(value_in_millions):,}".replace(',', thousand_sep)
    else:
        formatted_value = f"{value_in_millions:.{decimals}f}".replace('.', decimal_sep)
    
    # Respect the currency symbol position for millions format
    if position == 'before':
        # For currencies where the symbol goes before
        # We want symbol + value + M (e.g., €15,31M)
        # Extract the currency symbol from the million unit
        if million_unit.startswith('M'):
            currency_symbol = million_unit[1:]  # Remove the 'M' prefix to get the symbol
            return f"{currency_symbol}{formatted_value}M"
        else:
            # In case the million unit doesn't start with 'M'
            return f"{million_unit}{formatted_value}"
    else:
        # For currencies where the symbol goes after
        # We want value + M + symbol (e.g., 15,31M kr)
        return f"{formatted_value} {million_unit}"

def is_currency_selected() -> bool:
    """
    Check if a currency has been selected in the session state.
    
    Returns:
        True if a currency has been selected, False otherwise
    """
    return 'currency' in st.session_state and st.session_state.currency is not None

def get_currency_selector(key: str = "currency_selector", required: bool = True) -> Tuple[bool, str]:
    """
    Creates a currency selector dropdown in the Streamlit UI.
    
    Args:
        key: Unique key for the Streamlit widget
        required: Whether to display this as a required field
    
    Returns:
        Tuple of (is_valid, message) where is_valid is True if a currency is selected
        and message contains any validation message
    """
    # Define priority currencies to appear at the top of the list
    priority_currencies = ['nok', 'sek', 'dkk', 'eur', 'usd', 'gbp']
    
    # Create options list with priority currencies first, then the rest alphabetically
    remaining_currencies = [code for code in sorted(CURRENCY_SYMBOLS.keys()) 
                           if code not in priority_currencies]
    
    # Final options list with None as first option, then priority currencies, then others
    options = [None] + priority_currencies + remaining_currencies
    
    # Create display labels
    def format_option(code):
        if code is None:
            return "-- Select currency --"
        return f"{CURRENCY_NAMES.get(code, code.upper())} ({CURRENCY_SYMBOLS.get(code, code)})"
    
    # Create the selectbox with None as default (no selection)
    selected = st.selectbox(
        "",
        options=options,
        format_func=format_option,
        key=key
    )
    
    # Update session state
    if 'currency' not in st.session_state or st.session_state.currency != selected:
        st.session_state.currency = selected
        st.session_state.currency_selected = (selected is not None)
    
    # Validate selection
    is_valid = selected is not None
    message = "" if is_valid else "Please select a currency to continue."
    
    # Show warning if required and not valid
    if required and not is_valid:
        st.warning(message)
    
    return is_valid, message

def get_currency_display_name() -> str:
    """
    Returns a formatted display name for the current currency.
    
    Returns:
        Display name for the current currency (e.g. "US Dollar ($)")
        or "No currency selected" if none is selected
    """
    currency = get_currency_code()
    if currency is None:
        return "No currency selected"
    
    name = CURRENCY_NAMES.get(currency, currency.upper())
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    
    return f"{name} ({symbol})"

def get_hourly_rate_format() -> str:
    """
    Get the format string for hourly rates based on current currency.
    
    Returns:
        Format string for hourly rates (for column formatting)
    """
    currency = get_currency_code()
    
    # If no currency is selected, just format as a number
    if currency is None:
        return "%d/hr"
    
    symbol = CURRENCY_SYMBOLS.get(currency, '')
    position = SYMBOL_POSITIONS.get(currency, 'after')
    
    if position == 'before':
        return f"{symbol}%d/hr"
    else:
        return f"%d {symbol}/hr"

# Number formatter functions (added from utils/number_formatter.py)

def format_with_space_separators(df):
    """
    Format a DataFrame to display numbers with space thousand separators.
    
    Args:
        df: DataFrame to format
        
    Returns:
        DataFrame with numeric values formatted as strings with space separators
    """
    # Create a copy to avoid modifying the original
    formatted_df = df.copy()
    
    # Get currency info
    symbol = CURRENCY_SYMBOLS.get(get_currency_code(), '')
    position = SYMBOL_POSITIONS.get(get_currency_code(), 'after')
    
    # Process numeric columns
    for col in formatted_df.columns:
        # Skip non-numeric columns
        if not pd.api.types.is_numeric_dtype(formatted_df[col]):
            continue
            
        # Skip percentage columns
        if "Billability" in col or "percentage" in col.lower() or col.endswith("%"):
            continue
            
        # Skip Year column
        if col == "Year":
            continue
            
        # Check if column contains decimals
        has_decimals = False
        non_na_values = formatted_df[col].dropna()
        if len(non_na_values) > 0:
            sample = non_na_values.iloc[0]
            has_decimals = not np.isclose(sample, int(sample), rtol=1e-05)
        
        # Format each value in the column
        formatted_df[col] = formatted_df[col].apply(
            lambda x: _format_number(
                x, 
                decimals=1 if has_decimals else 0,
                is_currency="rate" in col.lower() or "Fee" in col or "fee" in col,
                is_rate="rate" in col.lower(),
                currency_symbol=symbol, 
                symbol_position=position
            )
        )
    
    return formatted_df

def create_formatter(decimals=0, currency_symbol=None, symbol_position='after', suffix=None):
    """
    Create a formatter function with fixed parameters.
    
    Args:
        decimals: Number of decimal places to show
        currency_symbol: Optional currency symbol to include
        symbol_position: Position of currency symbol ('before' or 'after') 
        suffix: Optional suffix to add (e.g., "/hr" for rates)
        
    Returns:
        A formatter function that can be used for display
    """
    def formatter(value):
        return _format_number(
            value, 
            decimals=decimals, 
            is_currency=currency_symbol is not None,
            is_rate=suffix == "/hr",
            currency_symbol=currency_symbol, 
            symbol_position=symbol_position
        )
    return formatter

def _format_number(value, decimals=0, is_currency=False, is_rate=False, 
                  currency_symbol=None, symbol_position='after'):
    """
    Format a single number with space thousand separators.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        is_currency: Whether this is a currency value
        is_rate: Whether this is a rate (add /hr suffix)
        currency_symbol: Symbol to use for currency
        symbol_position: Symbol position ('before' or 'after')
        
    Returns:
        Formatted string
    """
    if pd.isna(value):
        return value
        
    # Format with space separators
    if decimals == 0:
        formatted = f"{int(value):,}".replace(',', ' ')
    else:
        formatted = f"{value:,.{decimals}f}".replace(',', ' ')
        
    # Add currency symbol if needed
    if is_currency and currency_symbol:
        if symbol_position == 'before':
            formatted = f"{currency_symbol}{formatted}"
        else:
            formatted = f"{formatted} {currency_symbol}"
            
    # Add rate suffix if needed
    if is_rate:
        formatted = f"{formatted}/hr"
        
    return formatted