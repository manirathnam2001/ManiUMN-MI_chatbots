-- MySQL Database Schema for MI Chatbots
-- Supports sessions, feedback, PDF reports, and comprehensive logging
-- Created for LAMP-stack compatible MI assessment utilities

-- Create database (optional - may be created separately)
-- CREATE DATABASE IF NOT EXISTS mi_chatbots CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE mi_chatbots;

-- Sessions table - stores main conversation sessions
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    student_name VARCHAR(255) NOT NULL,
    session_type ENUM('HPV', 'OHI', 'GENERAL') NOT NULL,
    persona VARCHAR(255),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    status ENUM('active', 'completed', 'abandoned') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_student_name (student_name),
    INDEX idx_session_type (session_type),
    INDEX idx_started_at (started_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Messages table - stores individual chat messages
CREATE TABLE IF NOT EXISTS messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_order INT NOT NULL DEFAULT 0,
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_role (role),
    INDEX idx_timestamp (timestamp),
    INDEX idx_message_order (message_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Feedback table - stores MI assessment results
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    student_name VARCHAR(255) NOT NULL,
    session_type ENUM('HPV', 'OHI', 'GENERAL') NOT NULL,
    
    -- MI Component Scores (7.5 points each, 30 total)
    collaboration_score DECIMAL(3,1) NOT NULL DEFAULT 0.0,
    collaboration_status ENUM('Met', 'Partially Met', 'Not Met') NOT NULL,
    collaboration_feedback TEXT,
    
    evocation_score DECIMAL(3,1) NOT NULL DEFAULT 0.0,
    evocation_status ENUM('Met', 'Partially Met', 'Not Met') NOT NULL,
    evocation_feedback TEXT,
    
    acceptance_score DECIMAL(3,1) NOT NULL DEFAULT 0.0,
    acceptance_status ENUM('Met', 'Partially Met', 'Not Met') NOT NULL,
    acceptance_feedback TEXT,
    
    compassion_score DECIMAL(3,1) NOT NULL DEFAULT 0.0,
    compassion_status ENUM('Met', 'Partially Met', 'Not Met') NOT NULL,
    compassion_feedback TEXT,
    
    -- Overall scores
    total_score DECIMAL(4,1) NOT NULL DEFAULT 0.0,
    percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    performance_level ENUM('Excellent', 'Proficient', 'Developing', 'Beginning', 'Needs Improvement') NOT NULL,
    
    -- Raw feedback content
    raw_feedback TEXT NOT NULL,
    evaluator VARCHAR(255),
    feedback_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_student_name (student_name),
    INDEX idx_session_type (session_type),
    INDEX idx_total_score (total_score),
    INDEX idx_performance_level (performance_level),
    INDEX idx_feedback_timestamp (feedback_timestamp),
    
    -- Ensure score constraints
    CONSTRAINT chk_collaboration_score CHECK (collaboration_score >= 0.0 AND collaboration_score <= 7.5),
    CONSTRAINT chk_evocation_score CHECK (evocation_score >= 0.0 AND evocation_score <= 7.5),
    CONSTRAINT chk_acceptance_score CHECK (acceptance_score >= 0.0 AND acceptance_score <= 7.5),
    CONSTRAINT chk_compassion_score CHECK (compassion_score >= 0.0 AND compassion_score <= 7.5),
    CONSTRAINT chk_total_score CHECK (total_score >= 0.0 AND total_score <= 30.0),
    CONSTRAINT chk_percentage CHECK (percentage >= 0.00 AND percentage <= 100.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- PDF Reports table - tracks generated PDF reports
CREATE TABLE IF NOT EXISTS pdf_reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    feedback_id INT NOT NULL,
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000),
    file_size INT,
    content_hash VARCHAR(64), -- SHA-256 hash for integrity checking
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    downloaded_at TIMESTAMP NULL,
    download_count INT DEFAULT 0,
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (feedback_id) REFERENCES feedback(feedback_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_feedback_id (feedback_id),
    INDEX idx_generated_at (generated_at),
    INDEX idx_filename (filename)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Activity Log table - comprehensive system logging
CREATE TABLE IF NOT EXISTS activity_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255),
    log_level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL DEFAULT 'INFO',
    event_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    context JSON, -- Store additional context data
    user_agent TEXT,
    ip_address VARCHAR(45), -- IPv6 compatible
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_session_id (session_id),
    INDEX idx_log_level (log_level),
    INDEX idx_event_type (event_type),
    INDEX idx_timestamp (timestamp),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Performance tracking for analytics
CREATE TABLE IF NOT EXISTS performance_metrics (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4),
    metric_data JSON,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_session_id (session_id),
    INDEX idx_metric_name (metric_name),
    INDEX idx_recorded_at (recorded_at),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Views for common queries
CREATE OR REPLACE VIEW session_summary AS
SELECT 
    s.session_id,
    s.student_name,
    s.session_type,
    s.persona,
    s.started_at,
    s.completed_at,
    s.status,
    COUNT(m.message_id) as message_count,
    f.total_score,
    f.percentage,
    f.performance_level,
    f.feedback_timestamp,
    COUNT(p.report_id) as pdf_count
FROM sessions s
LEFT JOIN messages m ON s.session_id = m.session_id
LEFT JOIN feedback f ON s.session_id = f.session_id
LEFT JOIN pdf_reports p ON s.session_id = p.session_id
GROUP BY s.session_id, f.feedback_id;

-- Student performance summary view
CREATE OR REPLACE VIEW student_performance AS
SELECT 
    student_name,
    session_type,
    COUNT(*) as total_sessions,
    AVG(total_score) as avg_score,
    AVG(percentage) as avg_percentage,
    MAX(total_score) as best_score,
    MIN(total_score) as lowest_score,
    AVG(collaboration_score) as avg_collaboration,
    AVG(evocation_score) as avg_evocation,
    AVG(acceptance_score) as avg_acceptance,
    AVG(compassion_score) as avg_compassion,
    MAX(feedback_timestamp) as latest_assessment
FROM feedback
GROUP BY student_name, session_type;

-- Insert sample data for testing (optional)
-- Uncomment for development/testing purposes
/*
INSERT INTO sessions (session_id, student_name, session_type, persona, status) VALUES
('demo_session_001', 'John Doe', 'HPV', 'College Student - Sarah', 'completed'),
('demo_session_002', 'Jane Smith', 'OHI', 'Working Parent - Maria', 'completed');

INSERT INTO messages (session_id, role, content, message_order) VALUES
('demo_session_001', 'assistant', 'Hi there! I\'m Sarah, a college student. I have some questions about vaccines.', 1),
('demo_session_001', 'user', 'Hello Sarah! I\'m here to help. What would you like to know about vaccines?', 2),
('demo_session_001', 'assistant', 'I\'ve heard about the HPV vaccine but I\'m not sure if I need it.', 3);

INSERT INTO feedback (session_id, student_name, session_type, 
    collaboration_score, collaboration_status, collaboration_feedback,
    evocation_score, evocation_status, evocation_feedback,
    acceptance_score, acceptance_status, acceptance_feedback,
    compassion_score, compassion_status, compassion_feedback,
    total_score, percentage, performance_level, raw_feedback) VALUES
('demo_session_001', 'John Doe', 'HPV',
    6.0, 'Met', 'Good rapport building and partnership approach.',
    5.5, 'Partially Met', 'Some evocation techniques used, could explore motivations more deeply.',
    7.0, 'Met', 'Excellent respect for autonomy and reflective listening.',
    6.5, 'Met', 'Showed warmth and non-judgmental approach throughout.',
    25.0, 83.33, 'Proficient', 'Overall good MI performance with room for improvement in evocation.');
*/

-- Indexes for optimization
CREATE INDEX idx_feedback_composite ON feedback (student_name, session_type, feedback_timestamp);
CREATE INDEX idx_messages_composite ON messages (session_id, timestamp, message_order);
CREATE INDEX idx_activity_log_composite ON activity_log (event_type, log_level, timestamp);

-- Final schema notes
-- This schema supports:
-- 1. Complete session tracking with start/end times
-- 2. Full conversation history storage
-- 3. Detailed MI component scoring (30-point system)
-- 4. PDF generation tracking with file integrity
-- 5. Comprehensive logging for debugging and analytics
-- 6. Performance metrics for system optimization
-- 7. Views for common reporting queries
-- 8. Proper foreign key relationships and constraints
-- 9. Optimized indexes for query performance
-- 10. UTF-8 support for international characters