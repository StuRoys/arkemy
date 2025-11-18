# Arkemy Schema System Documentation

## 🎯 **What Is This?**

The Arkemy Schema System is a **YAML-driven data validation and loading system** that automatically handles:
- **Data validation** - Ensures your data has the right fields and types
- **Record type separation** - Splits time records from planned records automatically
- **Easy maintenance** - Change data requirements by editing YAML, not code

## 📊 **Core Concepts**

### **Two Data Types**
- **`time_record`**: Actual hours worked on projects (historical data)
- **`planned_record`**: Future hours/fees planned for projects (forecasting data)

### **One File, Two Datasets**
Your parquet file contains both types, distinguished by the `record_type` column:
```
record_type    | person_name | project_number | hours_used
time_record    | John Doe    | P001          | 8.0
time_record    | Jane Smith  | P002          | 6.5
planned_record | John Doe    | P001          | 12.0
planned_record | Jane Smith  | P003          | 16.0
```

## 🛠 **How It Works**

### **1. Schema Definition** (`utils/arkemy_schema.yaml`)
```yaml
record_types:
  time_record:
    required_fields: [record_date, person_name, project_number, hours_used]
    optional_fields: [hours_billable, cost_hour, fee_record]

  planned_record:
    required_fields: [record_date, person_name, project_number]
    optional_fields: [planned_hours, planned_rate]

fields:
  hours_used:
    type: float
    description: "Total time logged in hours"
    min_value: 0
```

### **2. Automatic Processing**
1. **Load** parquet file
2. **Filter** by `record_type` column
3. **Validate** against schema requirements
4. **Transform** data types automatically
5. **Store** in separate session variables

### **3. Result**
- `st.session_state.transformed_df` = time records only
- `st.session_state.transformed_planned_df` = planned records only

## 📋 **Quick Start Guide**

### **For Data Users**
Your parquet files need:
- A `record_type` column with values: `time_record` or `planned_record`
- Required fields for each record type (see schema)
- Currency code in filename (e.g., `data_NOK.parquet`)

### **For Developers**
The system loads automatically when you:
```python
from utils.unified_data_loader import load_data_hybrid

# Auto-loads from /data volume or shows upload interface
results = load_data_hybrid()
```

## ⚙️ **Configuration**

### **Adding New Fields**
Edit `utils/arkemy_schema.yaml`:
```yaml
fields:
  new_field_name:
    type: float
    description: "What this field contains"
    min_value: 0  # Optional constraint
```

### **Changing Requirements**
```yaml
time_record:
  required_fields:
    - record_date
    - person_name
    - project_number
    - hours_used
    - new_required_field  # Add here
```

### **Adding New Record Types**
```yaml
record_types:
  invoice_record:
    description: "Invoice data entries"
    required_fields: [record_date, invoice_number, amount]
    session_state_target: "invoice_df"
```

## 🔧 **Key Components**

### **Files You Care About**
- `utils/arkemy_schema.yaml` - **The schema definition** (edit this to change requirements)
- `utils/schema_manager.py` - Loads and validates schema
- `utils/unified_data_loader.py` - Loads and processes data files
- `pages/1_Analytics_Dashboard.py` - User interface for data loading

### **Session State Variables**
- `transformed_df` - Time tracking data (actual hours worked)
- `transformed_planned_df` - Planning data (future hours/fees)
- `csv_loaded` - Flag: time data is loaded
- `planned_csv_loaded` - Flag: planned data is loaded

## 🚨 **Troubleshooting**

### **"Missing required fields" Error**
Check your data has all required fields for that record type:
```bash
# In your parquet file, time_record rows need:
record_date, person_name, project_number, hours_used
```

### **"No record_type column" Error**
Your file needs a `record_type` column with values `time_record` or `planned_record`.

### **"Schema validation failed" Error**
Check the debug output - it shows exactly which fields are missing or have wrong types.

## 💡 **Best Practices**

### **Data File Structure**
```
record_type    | record_date | person_name | project_number | hours_used
time_record    | 2023-01-15  | John Doe    | P001          | 8.0
time_record    | 2023-01-15  | Jane Smith  | P002          | 6.5
planned_record | 2023-02-01  | John Doe    | P001          | 12.0
```

### **Schema Updates**
1. **Edit** `utils/arkemy_schema.yaml`
2. **Test** with your data file
3. **No code changes needed** - system adapts automatically

### **Validation**
- Use **required_fields** for must-have data
- Use **optional_fields** for nice-to-have data
- Add **constraints** (min_value, max_value) for data quality

## 🎯 **Benefits**

- ✅ **No hardcoded schemas** - everything driven by YAML
- ✅ **Easy maintenance** - edit YAML, not Python code
- ✅ **Automatic validation** - catches data issues early
- ✅ **Flexible** - add new record types or fields easily
- ✅ **Self-documenting** - schema includes field descriptions
- ✅ **Type safety** - automatic data type conversion

---

**Need help?** Check the schema file (`utils/arkemy_schema.yaml`) for current field definitions and requirements.