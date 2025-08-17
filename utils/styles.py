#file_name.py
# styles.py

def get_tab_css():
    """
    Returns CSS styling for tabs with hidden radio button bullseyes.
    Only targets navigation tabs, not sidebar radio buttons.
    """
    return """
    <style>
    /* Hide the radio button bullseye/indicator - only for navigation tabs */
    div[aria-label="Navigation"] .st-c2.st-dl.st-dm.st-dn.st-do.st-dp.st-ay.st-b3.st-dq.st-dr.st-ds.st-b5.st-dt.st-b6.st-ck.st-du.st-dv.st-d1.st-b1.st-br {
        display: none !important;
    }
    
    /* Also hide inner circle - only for navigation tabs */
    div[aria-label="Navigation"] .st-dw.st-dm.st-dn.st-do.st-dp.st-dx.st-b1.st-br.st-dy {
        display: none !important;
    }
    
    /* Hide any radio button visual indicators - only for navigation tabs */
    div[aria-label="Navigation"] label[data-baseweb="radio"] > div:first-child {
        display: none !important;
    }

    /* Remove spacing so text expands into bullseye space - only for navigation tabs */
    div[aria-label="Navigation"] label[data-baseweb="radio"] .st-du.st-e1 {
        margin-left: 0 !important;
        padding-left: 0 !important;
    }

    /* Style the radio button labels to look like tabs - only for navigation tabs */
    div[aria-label="Navigation"] label[data-baseweb="radio"] {
        background-color: #f0f2f6 !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        margin: 0 5px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
    }

    /* Hover effect - only for navigation tabs */
    div[aria-label="Navigation"] label[data-baseweb="radio"]:hover {
        background-color: #e6e9ef !important;
        border-color: #c0c0c0 !important;
    }

    /* Active/checked state styling - only for navigation tabs */
    div[aria-label="Navigation"] input[type="radio"]:checked + label,
    div[aria-label="Navigation"] label[data-baseweb="radio"]:has(input[type="radio"]:checked) {
        background-color: #4e89ae !important;
        color: white !important;
        border-color: #4e89ae !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }

    /* Text styling - only for navigation tabs */
    div[aria-label="Navigation"] label[data-baseweb="radio"] p {
        font-size: 16px !important;
        font-weight: 600 !important;
        margin: 0 !important;
        color: #333 !important;
    }

    /* White text when selected - only for navigation tabs */
    div[aria-label="Navigation"] input[type="radio"]:checked + label p,
    div[aria-label="Navigation"] label[data-baseweb="radio"]:has(input[type="radio"]:checked) p {
        color: white !important;
    }

    /* Hide Navigation and Company View labels */
    label[data-testid="stWidgetLabel"] .st-emotion-cache-br351g p:contains("Navigation"),
    label[data-testid="stWidgetLabel"] .st-emotion-cache-br351g p:contains("Company View") {
        display: none !important;
    }
    
    /* Alternative approach - hide the entire widget label if it contains these texts */
    label[data-testid="stWidgetLabel"]:has(p:conta
    ins("Navigation")),
    label[data-testid="stWidgetLabel"]:has(p:contains("Company View")) {
        display: none !important;
    }

    /* Reduce padding to 0 */
    .st-emotion-cache-zy6yx3 {
        padding: 0rem 2rem 2rem 2rem !important;
    }
    </style>
    """