{{ config(
    materialized='view'
) }}

-- This model simulates cleaning and selecting the core fields 
-- needed for metric calculation from the raw MongoDB export.
-- Since PostgreSQL handles JSONB, we can select the nested fields.

SELECT
    master_profile_id,
    
    -- Extract identities (e.g., email) from the nested JSON structure
    -- Coalesce is a placeholder in case the field is missing
    COALESCE(identities ->> 'email', identities ->> 'deviceID') AS primary_identity,
    
    -- Event history is a complex JSON array, keeping it for now
    event_history::jsonb AS event_history_json,
    
    -- Timestamps
    created_at,
    updated_at
    
FROM {{ source('raw', 'profiles_raw') }}