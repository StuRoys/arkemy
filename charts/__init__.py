# charts/__init__.py
"""
Charts package for Time Record Analyzer.
This package contains modules for different visualization tabs.
"""

from .customer_charts import render_customer_tab
from .project_type_charts import render_project_type_tab
from .project_charts import render_project_tab
from .phase_charts import render_phase_tab
from .activity_charts import render_activity_tab
from .people_charts import render_people_tab
from .price_model_charts import render_price_model_tab  # Add this line

# Export all tab rendering functions
__all__ = [
    'render_customer_tab',
    'render_project_type_tab',
    'render_project_tab',
    'render_phase_tab',
    'render_activity_tab',
    'render_people_tab',
    'render_price_model_tab'  # Add this line
]