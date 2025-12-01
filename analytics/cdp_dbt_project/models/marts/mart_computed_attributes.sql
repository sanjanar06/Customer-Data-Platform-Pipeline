{{ config(
    materialized='table',
    schema='marts'
) }}

WITH base_events AS (
    -- 1. Unnest the event history JSON array into individual rows
    SELECT 
        master_profile_id,
        value AS event
    FROM {{ ref('stg_profiles') }},
    LATERAL jsonb_array_elements(event_history_json)
),

parsed_events AS (
    -- 2. Extract relevant fields from the JSON
    SELECT
        master_profile_id,
        event->>'event_type' as event_type,
        (event->>'timestamp')::bigint as event_ts,
        (event->'data'->'properties'->>'total')::numeric as total_amount,
        event->'data'->'properties'->>'product_name' as product_name
    FROM base_events
),

metrics AS (
    -- 3. Compute Aggregates (Replaces compute_event_metrics, time_metrics, ltv)
    SELECT
        master_profile_id,
        
        -- LTV
        COALESCE(SUM(CASE WHEN event_type = 'purchase' THEN total_amount ELSE 0 END), 0) as lifetime_value,
        
        -- Event Metrics
        COUNT(*) as total_events,
        COUNT(DISTINCT event_type) as unique_event_types,
        
        -- Time Metrics
        MIN(event_ts) as first_seen_ts,
        MAX(event_ts) as last_seen_ts,
        EXTRACT(EPOCH FROM NOW())::bigint as now_ts
        
    FROM parsed_events
    GROUP BY 1
),

product_stats AS (
    -- 4. Compute Product Lists (Replaces compute_product_metrics)
    SELECT 
        master_profile_id,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN product_name END) as products_purchased_count
        -- Note: Constructing full lists in SQL can be heavy, we'll stick to counts for the score
    FROM parsed_events
    GROUP BY 1
),

scores AS (
    -- 5. Calculate Engagement Score (Replaces compute_engagement_score)
    SELECT
        m.master_profile_id,
        m.lifetime_value,
        m.total_events,
        m.unique_event_types,
        p.products_purchased_count,
        
        -- Time Calculations (Days)
        (m.now_ts - m.last_seen_ts) / 86400.0 as days_since_last_event,
        (m.last_seen_ts - m.first_seen_ts) / 86400.0 as customer_lifetime_days,
        
        -- ENGAGEMENT SCORE LOGIC 🧠
        (
            -- Event Activity (Max 40)
            LEAST(m.total_events * 5, 40) +
            
            -- Purchase Behavior (Max 30)
            (CASE WHEN m.lifetime_value > 1000 THEN 30 
                  WHEN m.lifetime_value > 0 THEN 15 
                  ELSE 0 END) +
            
            -- Recent Activity (Max 20)
            (CASE WHEN (m.now_ts - m.last_seen_ts) / 86400.0 < 1 THEN 20
                  WHEN (m.now_ts - m.last_seen_ts) / 86400.0 < 7 THEN 10
                  WHEN (m.now_ts - m.last_seen_ts) / 86400.0 < 30 THEN 5
                  ELSE 0 END) +
            
            -- Diversity (Max 10)
            LEAST(m.unique_event_types * 2, 10)
        )::int as engagement_score

    FROM metrics m
    LEFT JOIN product_stats p ON m.master_profile_id = p.master_profile_id
)

-- 6. Final Select
SELECT * FROM scores