# utils/person_reference.py
import pandas as pd
import streamlit as st

def load_person_reference(file_path=None):
    """
    Load person reference data from a file or provide UI to upload one.
    
    Args:
        file_path: Optional path to reference file
        
    Returns:
        DataFrame with person reference data
    """
    if 'person_reference_df' not in st.session_state:
        if file_path:
            # Load from predefined path
            try:
                df = pd.read_csv(file_path)
                st.session_state.person_reference_df = df
                return df
            except Exception as e:
                st.warning(f"Error loading person reference file: {e}")
                st.session_state.person_reference_df = None
        else:
            # Let user upload reference file
            st.session_state.person_reference_df = None
    
    return st.session_state.person_reference_df

def enrich_person_data(df, reference_df):
    """
    Add person attributes from reference data to dataframe.
    
    Args:
        df: DataFrame with Person column
        reference_df: Reference DataFrame with person attributes
        
    Returns:
        Enriched DataFrame
    """
    if df is None or reference_df is None:
        st.warning("Cannot enrich person data: DataFrame or reference data is missing")
        return df
    
    # Create a copy to avoid modifying original
    enriched_df = df.copy()
    
    # Normalize column names (case-insensitive matching)
    ref_columns = {col.lower(): col for col in reference_df.columns}
    
    # Try to find Person and Person type columns (case-insensitive)
    person_col = ref_columns.get('person')
    person_type_col = ref_columns.get('person type')
    
    # Log the columns we found
    st.info(f"Reference data columns: {list(reference_df.columns)}")
    st.info(f"Using '{person_col}' as Person column and '{person_type_col}' as Person type column")
    
    # Check if we found the required columns
    if not person_col or not person_type_col:
        st.error("Reference data missing required columns that match 'Person' and/or 'Person type'")
        st.info("Please ensure your CSV has columns named 'Person' and 'Person type' (case sensitive)")
        return df
    
    # Check if Person column exists in main dataframe
    if 'Person' not in enriched_df.columns:
        st.error("Main dataframe is missing the 'Person' column, cannot enrich")
        return df
    
    # If Person type already exists, don't overwrite
    if 'Person type' not in enriched_df.columns:
        try:
            # Create a temporary dataframe with normalized column names
            temp_ref_df = reference_df[[person_col, person_type_col]].copy()
            temp_ref_df.columns = ['Person', 'Person type']
            
            # Display some debug information
            if st.session_state.get('debug_mode', False):
                st.success(f"🐛 Debug - Reference data: {len(temp_ref_df)} entries, {temp_ref_df['Person'].nunique()} unique persons")
            
            # Normalize person names (trim whitespace)
            enriched_df['Person'] = enriched_df['Person'].str.strip()
            temp_ref_df['Person'] = temp_ref_df['Person'].str.strip()
            
            # Convert Person type to lowercase for consistency
            temp_ref_df['Person type'] = temp_ref_df['Person type'].str.lower()
            
            # Count before merge
            before_count = enriched_df.shape[0]
            
            # Show sample of data before merge
            with st.expander("Sample reference data"):
                st.write(temp_ref_df.head())
            
            # Perform the merge
            enriched_df = pd.merge(
                enriched_df,
                temp_ref_df,
                on='Person',
                how='left'
            )
            
            # Count after merge
            after_count = enriched_df.shape[0]
            
            # Check if merge changed row count (would indicate join issues)
            if before_count != after_count:
                st.warning(f"⚠️ Row count changed from {before_count} to {after_count} during person data merge")
            
            # Check how many rows got a person type
            null_count = enriched_df['Person type'].isna().sum()
            match_percentage = 100 - (null_count / len(enriched_df) * 100)
            st.info(f"Person type match rate: {match_percentage:.1f}% ({len(enriched_df) - null_count} of {len(enriched_df)} rows)")
            
            # If all Person types are null, something went wrong
            if null_count == len(enriched_df):
                st.error("❌ No matches found between Person names in main data and reference data")
                
                # Show some examples to help debugging
                if st.session_state.get('debug_mode', False):
                    main_persons = set(enriched_df['Person'].head(10))
                    ref_persons = set(temp_ref_df['Person'].head(10))
                    st.info(f"🐛 Debug - Main data examples: {', '.join(list(main_persons))}")
                    st.info(f"🐛 Debug - Reference data examples: {', '.join(list(ref_persons))}")
            else:
                st.success(f"✅ Successfully added Person type to {len(enriched_df) - null_count} rows")
        
        except Exception as e:
            st.error(f"Error during person data enrichment: {str(e)}")
    else:
        st.info("Person type column already exists in main dataframe, skipping enrichment")
    
    return enriched_df