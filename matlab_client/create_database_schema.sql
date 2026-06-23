--==============================================================================
-- PostgreSQL Database Schema for Predictive Maintenance System
-- Created: February 12, 2026
-- Database: maintenance_db
--==============================================================================

--==============================================================================
-- TABLE 1: sensor_readings
-- Purpose: Store raw sensor data from virtual system and real equipment
--==============================================================================

CREATE TABLE IF NOT EXISTS sensor_readings (
    id SERIAL PRIMARY KEY,
    client_id UUID NOT NULL,
    machine_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    sensor_data FLOAT8[] NOT NULL,           -- Array: [vib_x, vib_y, vib_z, ...]
    sensor_names TEXT[] NOT NULL,            -- Metadata: ['Vib_X', 'Vib_Y', ...]
    sample_rate_hz INT DEFAULT 50,           -- Sampling rate in Hz
    num_samples INT GENERATED ALWAYS AS (array_length(sensor_data, 1)) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_machine_id FOREIGN KEY(machine_id) REFERENCES machines(machine_id) ON DELETE CASCADE
);

CREATE INDEX idx_sensor_readings_machine_time 
    ON sensor_readings(machine_id, timestamp DESC);
CREATE INDEX idx_sensor_readings_timestamp 
    ON sensor_readings(timestamp DESC);


--==============================================================================
-- TABLE 2: predictions_log
-- Purpose: Log all model predictions for auditing and analysis
--==============================================================================

CREATE TABLE IF NOT EXISTS predictions_log (
    id SERIAL PRIMARY KEY,
    client_id UUID NOT NULL,
    machine_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    prediction FLOAT NOT NULL,               -- Failure probability 0-1
    alert_level VARCHAR(20) NOT NULL,       -- NORMAL | WARNING | CRITICAL
    model_used VARCHAR(100) NOT NULL,       -- e.g., DL-05_Induction_Motor
    model_version INT DEFAULT 1,
    confidence FLOAT NOT NULL,               -- Model confidence 0-1
    inference_time_ms FLOAT NOT NULL,       -- Computation time
    sensor_count INT,                        -- Number of sensors processed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT alert_level_check CHECK(alert_level IN ('NORMAL', 'WARNING', 'CRITICAL')),
    CONSTRAINT prediction_range_check CHECK(prediction >= 0 AND prediction <= 1),
    CONSTRAINT confidence_range_check CHECK(confidence >= 0 AND confidence <= 1)
);

CREATE INDEX idx_predictions_log_machine_time 
    ON predictions_log(machine_id, timestamp DESC);
CREATE INDEX idx_predictions_log_alert 
    ON predictions_log(machine_id, alert_level, timestamp DESC);
CREATE INDEX idx_predictions_log_model 
    ON predictions_log(model_used, timestamp DESC);


--==============================================================================
-- TABLE 3: ground_truth
-- Purpose: Store actual failure outcomes (collected via Simulink)
--==============================================================================

CREATE TABLE IF NOT EXISTS ground_truth (
    id SERIAL PRIMARY KEY,
    client_id UUID NOT NULL,
    machine_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_failure INT NOT NULL,            -- 0 (no failure) or 1 (failure)
    days_to_failure INT,                    -- Days until/after failure
    failure_type VARCHAR(100),               -- e.g., 'bearing_wear', 'electrical_fault'
    notes TEXT,                              -- Additional context
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT actual_failure_check CHECK(actual_failure IN (0, 1))
);

CREATE INDEX idx_ground_truth_machine_time 
    ON ground_truth(machine_id, timestamp DESC);
CREATE INDEX idx_ground_truth_failure_type 
    ON ground_truth(failure_type, timestamp DESC);


--==============================================================================
-- TABLE 4: model_versions
-- Purpose: Track trained models, versions, and deployment status
--==============================================================================

CREATE TABLE IF NOT EXISTS model_versions (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(100) NOT NULL,         -- e.g., DL-05_Induction_Motor
    version INT NOT NULL,                   -- Version number
    training_date TIMESTAMP WITH TIME ZONE NOT NULL,
    validation_accuracy FLOAT,              -- Accuracy on validation set
    validation_precision FLOAT,             -- Precision (false alarm rate)
    validation_recall FLOAT,                -- Recall (missed detections)
    f1_score FLOAT,                         -- Harmonic mean of precision/recall
    roc_auc FLOAT,                          -- ROC-AUC metric
    training_samples INT,                   -- Number of samples used
    deployed BOOLEAN DEFAULT FALSE,         -- Is this model in production?
    deployment_date TIMESTAMP WITH TIME ZONE,
    deployment_traffic_percent INT DEFAULT 10,  -- A/B test: % traffic
    performance_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_model_version UNIQUE(model_id, version)
);

CREATE INDEX idx_model_versions_model_deployed 
    ON model_versions(model_id, deployed, version DESC);
CREATE INDEX idx_model_versions_training_date 
    ON model_versions(training_date DESC);


--==============================================================================
-- TABLE 5: machines
-- Purpose: Register equipment being monitored
--==============================================================================

CREATE TABLE IF NOT EXISTS machines (
    machine_id VARCHAR(100) PRIMARY KEY,
    machine_name VARCHAR(255) NOT NULL,
    machine_type VARCHAR(100),              -- e.g., 'Induction Motor', 'Bearing Assembly'
    model_assigned VARCHAR(100),            -- Which DL model to use for predictions
    location VARCHAR(255),
    status VARCHAR(20) DEFAULT 'ACTIVE',    -- ACTIVE | INACTIVE | MAINTENANCE
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO machines VALUES 
    ('MOTOR-001', 'Test Motor 1', 'Induction Motor', 'DL-05', 'Lab', 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('MOTOR-TEST-001', 'Simulink Virtual Motor', 'Virtual (Simulink)', 'DL-05', 'Simulation', 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;


--==============================================================================
-- TABLE 6: retraining_logs
-- Purpose: Track weekly retraining pipeline execution
--==============================================================================

CREATE TABLE IF NOT EXISTS retraining_logs (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(100) NOT NULL,
    run_date TIMESTAMP WITH TIME ZONE NOT NULL,
    samples_used INT,                       -- Number of training samples
    training_time_seconds FLOAT,            -- Duration of training
    new_model_version INT,                  -- Version number created
    validation_accuracy FLOAT,
    f1_before FLOAT,                        -- F1-score of previous model
    f1_after FLOAT,                         -- F1-score of new model
    improvement_percent FLOAT,              -- (f1_after - f1_before) / f1_before * 100
    promoted_to_production BOOLEAN,         -- Was this model deployed?
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_retraining_logs_model_date 
    ON retraining_logs(model_id, run_date DESC);


--==============================================================================
-- TABLE 7: api_health_metrics
-- Purpose: Monitor API performance and health
--==============================================================================

CREATE TABLE IF NOT EXISTS api_health_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    cpu_percent FLOAT,
    memory_percent FLOAT,
    active_connections INT,
    predictions_per_minute INT,
    avg_inference_time_ms FLOAT,
    errors_count INT DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_health_metrics_timestamp 
    ON api_health_metrics(timestamp DESC);


--==============================================================================
-- VIEW 1: recent_predictions
-- Purpose: Quick access to latest predictions
--==============================================================================

CREATE OR REPLACE VIEW recent_predictions AS
SELECT 
    pl.machine_id,
    pl.timestamp,
    pl.prediction,
    pl.alert_level,
    pl.model_used,
    pl.confidence,
    pl.inference_time_ms,
    ROW_NUMBER() OVER (PARTITION BY pl.machine_id ORDER BY pl.timestamp DESC) as rank
FROM predictions_log pl
WHERE pl.timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours';


--==============================================================================
-- VIEW 2: model_performance_summary
-- Purpose: Compare current vs previous models
--==============================================================================

CREATE OR REPLACE VIEW model_performance_summary AS
SELECT 
    model_id,
    version,
    validation_accuracy,
    f1_score,
    deployment_date,
    deployed,
    CASE 
        WHEN deployed THEN 'ACTIVE'
        ELSE 'INACTIVE'
    END as status
FROM model_versions
ORDER BY model_id, version DESC;


--==============================================================================
-- STORED PROCEDURE 1: cleanup_old_data
-- Purpose: Archive and delete old sensor readings (retention policy)
--==============================================================================

CREATE OR REPLACE FUNCTION cleanup_old_sensor_data(days_retention INT DEFAULT 90)
RETURNS TABLE(deleted_rows INT, archived_rows INT) AS $$
DECLARE
    v_deleted INT;
    v_archived INT;
BEGIN
    -- Archive to backup table (if exists)
    INSERT INTO sensor_readings_archive
    SELECT * FROM sensor_readings
    WHERE created_at < CURRENT_TIMESTAMP - (days_retention || ' days')::INTERVAL;
    GET DIAGNOSTICS v_archived = ROW_COUNT;
    
    -- Delete from main table
    DELETE FROM sensor_readings
    WHERE created_at < CURRENT_TIMESTAMP - (days_retention || ' days')::INTERVAL;
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    
    RETURN QUERY SELECT v_deleted, v_archived;
END;
$$ LANGUAGE plpgsql;


--==============================================================================
-- STORED PROCEDURE 2: get_weekly_retraining_data
-- Purpose: Aggregate ground truth + sensor data for retraining
--==============================================================================

CREATE OR REPLACE FUNCTION get_weekly_retraining_data(
    p_model_id VARCHAR(100) DEFAULT 'DL-05'
)
RETURNS TABLE(
    total_samples INT,
    fault_samples INT,
    normal_samples INT,
    avg_inference_time_ms FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INT as total_samples,
        SUM(CASE WHEN pl.alert_level = 'CRITICAL' THEN 1 ELSE 0 END)::INT as fault_samples,
        SUM(CASE WHEN pl.alert_level = 'NORMAL' THEN 1 ELSE 0 END)::INT as normal_samples,
        AVG(pl.inference_time_ms)::FLOAT as avg_inference_time_ms
    FROM predictions_log pl
    WHERE pl.model_used = p_model_id
        AND pl.timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;


--==============================================================================
-- DATA RETENTION POLICY (PostgreSQL Configuration)
--==============================================================================
-- Set up automated cleanup using pg_cron (if available):
--
-- SELECT cron.schedule('cleanup-old-sensor-data', '0 2 * * 0', 'SELECT cleanup_old_sensor_data(90)');
-- SELECT cron.schedule('cleanup-old-predictions', '0 3 * * 0', 'DELETE FROM predictions_log WHERE created_at < CURRENT_TIMESTAMP - INTERVAL ''180 days''');
-- SELECT cron.schedule('cleanup-old-api-metrics', '0 4 * * 0', 'DELETE FROM api_health_metrics WHERE created_at < CURRENT_TIMESTAMP - INTERVAL ''30 days''');


--==============================================================================
-- SAMPLE DATA QUERIES (for testing)
--==============================================================================

-- Query 1: Get latest prediction for all machines
-- SELECT machine_id, MAX(timestamp), prediction, alert_level FROM predictions_log GROUP BY machine_id;

-- Query 2: Get prediction statistics for today
-- SELECT alert_level, COUNT(*), AVG(prediction), AVG(confidence) FROM predictions_log WHERE DATE(timestamp) = CURRENT_DATE GROUP BY alert_level;

-- Query 3: Get all faults detected in last 7 days
-- SELECT * FROM ground_truth WHERE actual_failure = 1 AND timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days';

-- Query 4: Get average inference time by model
-- SELECT model_used, AVG(inference_time_ms), COUNT(*) FROM predictions_log GROUP BY model_used;

-- Query 5: Check A/B testing status
-- SELECT model_id, version, deployment_traffic_percent, deployed FROM model_versions WHERE deployed = true;

--==============================================================================
-- END OF SCHEMA
--==============================================================================
