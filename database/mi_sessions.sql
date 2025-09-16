-- ============================================================================
-- MI Sessions Database Schema
-- ============================================================================
-- Database schema for storing motivational interviewing chatbot sessions,
-- feedback, and PDF exports with full traceability
-- 
-- Compatible with: MySQL 5.7+, MariaDB 10.2+
-- Author: MI Chatbots System
-- Created: 2024
-- ============================================================================

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS mi_chatbots 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE mi_chatbots;

-- ============================================================================
-- TABLE: sessions
-- Core session information for MI chatbot interactions
-- ============================================================================
CREATE TABLE sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL UNIQUE COMMENT 'Unique session identifier',
    student_name VARCHAR(255) NOT NULL COMMENT 'Name of the student participant',
    session_type ENUM('HPV', 'OHI', 'OTHER') NOT NULL COMMENT 'Type of MI session',
    persona VARCHAR(100) DEFAULT NULL COMMENT 'Selected patient persona/scenario',
    status ENUM('ACTIVE', 'COMPLETED', 'ABANDONED') DEFAULT 'ACTIVE' COMMENT 'Session status',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Session creation timestamp',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update timestamp',
    completed_at TIMESTAMP NULL COMMENT 'Session completion timestamp',
    
    -- Session metadata
    ip_address VARCHAR(45) DEFAULT NULL COMMENT 'Client IP address',
    user_agent TEXT DEFAULT NULL COMMENT 'Browser user agent string',
    session_duration INT DEFAULT NULL COMMENT 'Session duration in seconds',
    
    INDEX idx_session_id (session_id),
    INDEX idx_student_name (student_name),
    INDEX idx_session_type (session_type),
    INDEX idx_created_at (created_at),
    INDEX idx_status (status)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci 
  COMMENT='Main sessions table storing MI chatbot interaction metadata';

-- ============================================================================
-- TABLE: conversations
-- Individual messages within each session
-- ============================================================================
CREATE TABLE conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL COMMENT 'Reference to parent session',
    message_order INT NOT NULL COMMENT 'Order of message in conversation',
    role ENUM('user', 'assistant', 'system') NOT NULL COMMENT 'Message sender role',
    content TEXT NOT NULL COMMENT 'Message content',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Message timestamp',
    
    -- Message metadata
    token_count INT DEFAULT NULL COMMENT 'Number of tokens in message',
    processing_time_ms INT DEFAULT NULL COMMENT 'Message processing time in milliseconds',
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_message_order (message_order),
    INDEX idx_role (role),
    INDEX idx_created_at (created_at),
    
    UNIQUE KEY unique_session_message (session_id, message_order)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci 
  COMMENT='Individual conversation messages for each session';

-- ============================================================================
-- TABLE: feedback
-- MI assessment feedback and scoring
-- ============================================================================
CREATE TABLE feedback (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL COMMENT 'Reference to parent session',
    feedback_content TEXT NOT NULL COMMENT 'Complete feedback text',
    
    -- MI Component Scores (each out of 7.5 points)
    collaboration_score DECIMAL(3,2) DEFAULT NULL COMMENT 'Collaboration component score (0-7.5)',
    collaboration_status ENUM('Met', 'Partially Met', 'Not Met') DEFAULT NULL COMMENT 'Collaboration status',
    
    evocation_score DECIMAL(3,2) DEFAULT NULL COMMENT 'Evocation component score (0-7.5)',
    evocation_status ENUM('Met', 'Partially Met', 'Not Met') DEFAULT NULL COMMENT 'Evocation status',
    
    acceptance_score DECIMAL(3,2) DEFAULT NULL COMMENT 'Acceptance component score (0-7.5)',
    acceptance_status ENUM('Met', 'Partially Met', 'Not Met') DEFAULT NULL COMMENT 'Acceptance status',
    
    compassion_score DECIMAL(3,2) DEFAULT NULL COMMENT 'Compassion component score (0-7.5)',
    compassion_status ENUM('Met', 'Partially Met', 'Not Met') DEFAULT NULL COMMENT 'Compassion status',
    
    -- Total scoring
    total_score DECIMAL(4,2) DEFAULT NULL COMMENT 'Total score (0-30)',
    percentage_score DECIMAL(5,2) DEFAULT NULL COMMENT 'Percentage score (0-100)',
    
    -- Feedback metadata
    evaluator VARCHAR(255) DEFAULT NULL COMMENT 'Name or ID of evaluator',
    evaluation_method ENUM('AI_AUTOMATED', 'HUMAN_REVIEW', 'HYBRID') DEFAULT 'AI_AUTOMATED' COMMENT 'Method of evaluation',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Feedback creation timestamp',
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_total_score (total_score),
    INDEX idx_percentage_score (percentage_score),
    INDEX idx_evaluator (evaluator),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci 
  COMMENT='MI assessment feedback and component scoring';

-- ============================================================================
-- TABLE: pdf_exports
-- Generated PDF reports for traceability
-- ============================================================================
CREATE TABLE pdf_exports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL COMMENT 'Reference to parent session',
    filename VARCHAR(255) NOT NULL COMMENT 'Generated PDF filename',
    file_path VARCHAR(500) DEFAULT NULL COMMENT 'Storage path of PDF file',
    file_size INT DEFAULT NULL COMMENT 'PDF file size in bytes',
    
    -- PDF metadata
    pdf_type ENUM('PERFORMANCE_REPORT', 'CONVERSATION_TRANSCRIPT', 'FEEDBACK_ONLY') 
             DEFAULT 'PERFORMANCE_REPORT' COMMENT 'Type of PDF generated',
    generation_method VARCHAR(100) DEFAULT 'DomPDF' COMMENT 'PDF generation library used',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'PDF generation timestamp',
    downloaded_at TIMESTAMP NULL COMMENT 'First download timestamp',
    download_count INT DEFAULT 0 COMMENT 'Number of times downloaded',
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_filename (filename),
    INDEX idx_pdf_type (pdf_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci 
  COMMENT='Generated PDF reports and download tracking';

-- ============================================================================
-- TABLE: system_logs
-- System activity logging for debugging and monitoring
-- ============================================================================
CREATE TABLE system_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) DEFAULT NULL COMMENT 'Related session (if applicable)',
    log_level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL COMMENT 'Log severity level',
    log_category VARCHAR(100) NOT NULL COMMENT 'Log category (e.g., PDF_GENERATION, FEEDBACK, DATABASE)',
    message TEXT NOT NULL COMMENT 'Log message',
    
    -- Context data
    context_data JSON DEFAULT NULL COMMENT 'Additional context as JSON',
    user_id VARCHAR(255) DEFAULT NULL COMMENT 'User identifier (if available)',
    ip_address VARCHAR(45) DEFAULT NULL COMMENT 'Client IP address',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Log entry timestamp',
    
    INDEX idx_session_id (session_id),
    INDEX idx_log_level (log_level),
    INDEX idx_log_category (log_category),
    INDEX idx_created_at (created_at),
    INDEX idx_user_id (user_id),
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE SET NULL
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci 
  COMMENT='System activity logs for debugging and monitoring';

-- ============================================================================
-- VIEWS for Common Queries
-- ============================================================================

-- Complete session overview with latest feedback
CREATE VIEW v_session_overview AS
SELECT 
    s.id,
    s.session_id,
    s.student_name,
    s.session_type,
    s.persona,
    s.status,
    s.created_at,
    s.completed_at,
    s.session_duration,
    f.total_score,
    f.percentage_score,
    f.evaluator,
    f.created_at as feedback_date,
    COUNT(c.id) as message_count,
    COUNT(p.id) as pdf_count
FROM sessions s
LEFT JOIN feedback f ON s.session_id = f.session_id
LEFT JOIN conversations c ON s.session_id = c.session_id
LEFT JOIN pdf_exports p ON s.session_id = p.session_id
GROUP BY s.id, f.id
ORDER BY s.created_at DESC;

-- Detailed MI component scoring
CREATE VIEW v_mi_scoring_detail AS
SELECT 
    s.session_id,
    s.student_name,
    s.session_type,
    f.collaboration_score,
    f.collaboration_status,
    f.evocation_score,
    f.evocation_status,
    f.acceptance_score,
    f.acceptance_status,
    f.compassion_score,
    f.compassion_status,
    f.total_score,
    f.percentage_score,
    f.created_at as feedback_date
FROM sessions s
INNER JOIN feedback f ON s.session_id = f.session_id
ORDER BY f.created_at DESC;

-- ============================================================================
-- TRIGGERS for Data Integrity and Automation
-- ============================================================================

-- Auto-calculate total score when component scores are updated
DELIMITER //
CREATE TRIGGER tr_feedback_calculate_totals
    BEFORE INSERT ON feedback
    FOR EACH ROW
BEGIN
    -- Calculate total score from components
    SET NEW.total_score = COALESCE(NEW.collaboration_score, 0) + 
                         COALESCE(NEW.evocation_score, 0) + 
                         COALESCE(NEW.acceptance_score, 0) + 
                         COALESCE(NEW.compassion_score, 0);
    
    -- Calculate percentage (out of 30 total points)
    SET NEW.percentage_score = (NEW.total_score / 30.0) * 100.0;
END//

CREATE TRIGGER tr_feedback_update_totals
    BEFORE UPDATE ON feedback
    FOR EACH ROW
BEGIN
    -- Calculate total score from components
    SET NEW.total_score = COALESCE(NEW.collaboration_score, 0) + 
                         COALESCE(NEW.evocation_score, 0) + 
                         COALESCE(NEW.acceptance_score, 0) + 
                         COALESCE(NEW.compassion_score, 0);
    
    -- Calculate percentage (out of 30 total points)
    SET NEW.percentage_score = (NEW.total_score / 30.0) * 100.0;
END//

-- Auto-update session status when feedback is added
CREATE TRIGGER tr_session_complete_on_feedback
    AFTER INSERT ON feedback
    FOR EACH ROW
BEGIN
    UPDATE sessions 
    SET status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP
    WHERE session_id = NEW.session_id AND status = 'ACTIVE';
END//

DELIMITER ;

-- ============================================================================
-- SAMPLE DATA (for testing and development)
-- ============================================================================

-- Insert sample session
INSERT INTO sessions (session_id, student_name, session_type, persona, status) VALUES
('demo_session_001', 'John Doe', 'HPV', 'Alex - Hesitant Patient', 'COMPLETED');

-- Insert sample conversation
INSERT INTO conversations (session_id, message_order, role, content) VALUES
('demo_session_001', 1, 'assistant', 'Hello! I heard you wanted to discuss the HPV vaccine?'),
('demo_session_001', 2, 'user', 'Yes, I have some concerns about it.'),
('demo_session_001', 3, 'assistant', 'I understand. What specific concerns do you have? I am here to listen and help address them.');

-- Insert sample feedback
INSERT INTO feedback (session_id, feedback_content, collaboration_score, collaboration_status, 
                     evocation_score, evocation_status, acceptance_score, acceptance_status,
                     compassion_score, compassion_status, evaluator) VALUES
('demo_session_001', 'Good use of open-ended questions and reflective listening...', 
 6.0, 'Met', 5.5, 'Partially Met', 7.0, 'Met', 6.5, 'Met', 'AI Evaluator');

-- Insert sample PDF export
INSERT INTO pdf_exports (session_id, filename, pdf_type) VALUES
('demo_session_001', 'HPV_MI_Report_John_Doe_20240101.pdf', 'PERFORMANCE_REPORT');

-- ============================================================================
-- INDEXES for Performance Optimization
-- ============================================================================

-- Composite indexes for common query patterns
CREATE INDEX idx_sessions_student_type_date ON sessions(student_name, session_type, created_at);
CREATE INDEX idx_feedback_scores_date ON feedback(total_score, percentage_score, created_at);
CREATE INDEX idx_conversations_session_order ON conversations(session_id, message_order);
CREATE INDEX idx_logs_category_level_date ON system_logs(log_category, log_level, created_at);

-- ============================================================================
-- STORED PROCEDURES for Common Operations
-- ============================================================================

DELIMITER //

-- Get complete session data with conversation and feedback
CREATE PROCEDURE sp_get_session_complete(IN p_session_id VARCHAR(100))
BEGIN
    -- Session details
    SELECT * FROM sessions WHERE session_id = p_session_id;
    
    -- Conversation messages
    SELECT * FROM conversations 
    WHERE session_id = p_session_id 
    ORDER BY message_order;
    
    -- Feedback details
    SELECT * FROM feedback WHERE session_id = p_session_id;
    
    -- PDF exports
    SELECT * FROM pdf_exports WHERE session_id = p_session_id;
END//

-- Clean up old sessions (for maintenance)
CREATE PROCEDURE sp_cleanup_old_sessions(IN days_old INT)
BEGIN
    DECLARE session_count INT DEFAULT 0;
    
    -- Count sessions to be deleted
    SELECT COUNT(*) INTO session_count
    FROM sessions 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL days_old DAY)
    AND status IN ('COMPLETED', 'ABANDONED');
    
    -- Delete old sessions (cascade will handle related records)
    DELETE FROM sessions 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL days_old DAY)
    AND status IN ('COMPLETED', 'ABANDONED');
    
    -- Log the cleanup
    INSERT INTO system_logs (log_level, log_category, message) 
    VALUES ('INFO', 'MAINTENANCE', CONCAT('Cleaned up ', session_count, ' old sessions'));
    
    SELECT CONCAT('Deleted ', session_count, ' sessions older than ', days_old, ' days') AS result;
END//

DELIMITER ;

-- ============================================================================
-- GRANT PERMISSIONS (adjust as needed for your setup)
-- ============================================================================

-- Create dedicated user for the application
-- CREATE USER 'mi_app'@'localhost' IDENTIFIED BY 'secure_password_here';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON mi_chatbots.* TO 'mi_app'@'localhost';
-- GRANT EXECUTE ON PROCEDURE mi_chatbots.sp_get_session_complete TO 'mi_app'@'localhost';
-- GRANT EXECUTE ON PROCEDURE mi_chatbots.sp_cleanup_old_sessions TO 'mi_app'@'localhost';
-- FLUSH PRIVILEGES;

-- ============================================================================
-- End of Schema
-- ============================================================================