-- Motivational Interviewing Sessions Database Schema
-- Compatible with LAMP stack MySQL/MariaDB for MI chatbot applications
-- Version: 1.0

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS mi_sessions 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE mi_sessions;

-- Sessions table: Main conversation sessions
CREATE TABLE IF NOT EXISTS sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL UNIQUE,
    student_name VARCHAR(255) NOT NULL,
    session_type ENUM('HPV', 'OHI', 'General') NOT NULL DEFAULT 'General',
    persona_selected VARCHAR(100) DEFAULT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    status ENUM('active', 'completed', 'abandoned') DEFAULT 'active',
    total_messages INT DEFAULT 0,
    
    INDEX idx_session_id (session_id),
    INDEX idx_student_name (student_name),
    INDEX idx_session_type (session_type),
    INDEX idx_started_at (started_at)
) ENGINE=InnoDB;

-- Messages table: Individual chat messages in conversations
CREATE TABLE IF NOT EXISTS messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- Feedback table: MI assessment feedback and scores
CREATE TABLE IF NOT EXISTS feedback (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL,
    student_name VARCHAR(255) NOT NULL,
    session_type ENUM('HPV', 'OHI', 'General') NOT NULL,
    evaluator VARCHAR(100) DEFAULT 'AI_System',
    
    -- MI Component Scores (based on existing Python scoring system)
    collaboration_status ENUM('Met', 'Partially Met', 'Not Met') DEFAULT NULL,
    collaboration_score DECIMAL(4,2) DEFAULT 0.00,
    collaboration_feedback TEXT DEFAULT NULL,
    
    evocation_status ENUM('Met', 'Partially Met', 'Not Met') DEFAULT NULL,
    evocation_score DECIMAL(4,2) DEFAULT 0.00,
    evocation_feedback TEXT DEFAULT NULL,
    
    acceptance_status ENUM('Met', 'Partially Met', 'Not Met') DEFAULT NULL,
    acceptance_score DECIMAL(4,2) DEFAULT 0.00,
    acceptance_feedback TEXT DEFAULT NULL,
    
    compassion_status ENUM('Met', 'Partially Met', 'Not Met') DEFAULT NULL,
    compassion_score DECIMAL(4,2) DEFAULT 0.00,
    compassion_feedback TEXT DEFAULT NULL,
    
    total_score DECIMAL(5,2) DEFAULT 0.00,
    max_possible_score DECIMAL(5,2) DEFAULT 30.00,
    percentage DECIMAL(5,2) DEFAULT 0.00,
    performance_level VARCHAR(50) DEFAULT NULL,
    
    raw_feedback TEXT NOT NULL,
    suggestions TEXT DEFAULT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_student_name (student_name),
    INDEX idx_session_type (session_type),
    INDEX idx_total_score (total_score),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- PDF Reports table: Generated PDF report tracking
CREATE TABLE IF NOT EXISTS pdf_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL,
    student_name VARCHAR(255) NOT NULL,
    session_type ENUM('HPV', 'OHI', 'General') NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) DEFAULT NULL,
    file_size INT DEFAULT NULL,
    mime_type VARCHAR(100) DEFAULT 'application/pdf',
    
    total_score DECIMAL(5,2) DEFAULT NULL,
    percentage DECIMAL(5,2) DEFAULT NULL,
    
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    downloaded BOOLEAN DEFAULT FALSE,
    download_count INT DEFAULT 0,
    last_downloaded_at TIMESTAMP NULL,
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_student_name (student_name),
    INDEX idx_filename (filename),
    INDEX idx_generated_at (generated_at)
) ENGINE=InnoDB;

-- Activity Log table: System events and debugging
CREATE TABLE IF NOT EXISTS activity_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) DEFAULT NULL,
    log_level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') DEFAULT 'INFO',
    event_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    context JSON DEFAULT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    user_agent TEXT DEFAULT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_session_id (session_id),
    INDEX idx_log_level (log_level),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- Create user for application (optional - adjust privileges as needed)
-- CREATE USER IF NOT EXISTS 'mi_app'@'localhost' IDENTIFIED BY 'secure_password_here';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON mi_sessions.* TO 'mi_app'@'localhost';
-- FLUSH PRIVILEGES;

-- Sample data for testing (optional)
/*
INSERT INTO sessions (session_id, student_name, session_type, persona_selected) VALUES
('test_session_001', 'John Doe', 'HPV', 'Concerned Parent'),
('test_session_002', 'Jane Smith', 'OHI', 'Skeptical Adult');

INSERT INTO messages (session_id, role, content) VALUES
('test_session_001', 'user', 'I am concerned about the HPV vaccine safety.'),
('test_session_001', 'assistant', 'I understand your concerns. Can you tell me more about what specifically worries you?');
*/