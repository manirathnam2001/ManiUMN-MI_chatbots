<?php
/**
 * SessionStorage.php
 * 
 * LAMP-compatible storage utility for managing MI chatbot sessions, conversations,
 * feedback, and PDF exports in MySQL database. Provides comprehensive CRUD operations
 * with transaction support and data integrity.
 * 
 * This class serves as the primary data access layer for all MI chatbot operations,
 * ensuring consistent data storage and retrieval.
 * 
 * PHP Version: 7.4+
 * Dependencies: PDO (MySQL), Logger (optional)
 * 
 * @package MIChatbots
 * @author MI Chatbots System
 * @version 1.0.0
 * @since 2024
 */

namespace MIChatbots\Utils;

require_once 'Logger.php';
require_once 'FeedbackUtils.php';

/**
 * Class SessionStorage
 * Comprehensive storage management for MI chatbot data
 */
class SessionStorage {
    
    private $pdo;
    private $logger;
    
    /**
     * Constructor
     * 
     * @param PDO $pdo Database connection
     * @param Logger|null $logger Optional logger instance
     */
    public function __construct(\PDO $pdo, Logger $logger = null) {
        $this->pdo = $pdo;
        $this->logger = $logger;
        
        // Set PDO attributes for better error handling
        $this->pdo->setAttribute(\PDO::ATTR_ERRMODE, \PDO::ERRMODE_EXCEPTION);
        $this->pdo->setAttribute(\PDO::ATTR_DEFAULT_FETCH_MODE, \PDO::FETCH_ASSOC);
    }
    
    // ========================================================================
    // SESSION MANAGEMENT
    // ========================================================================
    
    /**
     * Create a new session
     * 
     * @param string $sessionId Unique session identifier
     * @param string $studentName Student name
     * @param string $sessionType Session type (HPV, OHI, OTHER)
     * @param string|null $persona Selected persona/scenario
     * @param array $metadata Additional session metadata
     * @return bool Success status
     */
    public function createSession($sessionId, $studentName, $sessionType, $persona = null, $metadata = []) {
        try {
            $sql = "INSERT INTO sessions (session_id, student_name, session_type, persona, ip_address, user_agent, status) 
                    VALUES (:session_id, :student_name, :session_type, :persona, :ip_address, :user_agent, 'ACTIVE')";
            
            $stmt = $this->pdo->prepare($sql);
            $result = $stmt->execute([
                'session_id' => $sessionId,
                'student_name' => $studentName,
                'session_type' => $sessionType,
                'persona' => $persona,
                'ip_address' => $this->getClientIpAddress(),
                'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? null
            ]);
            
            if ($this->logger) {
                $this->logger->logSessionEvent($sessionId, 'CREATE', $studentName, $sessionType, $metadata);
                $this->logger->logDatabaseOperation('INSERT', 'sessions', $sessionId, [
                    'student_name' => $studentName,
                    'session_type' => $sessionType
                ]);
            }
            
            return $result;
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to create session: {$sessionId}", $e, $sessionId);
            }
            throw new \Exception("Failed to create session: " . $e->getMessage());
        }
    }
    
    /**
     * Get session information
     * 
     * @param string $sessionId Session identifier
     * @return array|null Session data or null if not found
     */
    public function getSession($sessionId) {
        try {
            $sql = "SELECT * FROM sessions WHERE session_id = :session_id";
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute(['session_id' => $sessionId]);
            
            $session = $stmt->fetch();
            
            if ($this->logger && $session) {
                $this->logger->logDatabaseOperation('SELECT', 'sessions', $sessionId);
            }
            
            return $session ?: null;
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to get session: {$sessionId}", $e, $sessionId);
            }
            return null;
        }
    }
    
    /**
     * Update session status
     * 
     * @param string $sessionId Session identifier
     * @param string $status New status (ACTIVE, COMPLETED, ABANDONED)
     * @param int|null $duration Session duration in seconds
     * @return bool Success status
     */
    public function updateSessionStatus($sessionId, $status, $duration = null) {
        try {
            $sql = "UPDATE sessions SET status = :status, updated_at = CURRENT_TIMESTAMP";
            $params = ['session_id' => $sessionId, 'status' => $status];
            
            if ($status === 'COMPLETED') {
                $sql .= ", completed_at = CURRENT_TIMESTAMP";
            }
            
            if ($duration !== null) {
                $sql .= ", session_duration = :duration";
                $params['duration'] = $duration;
            }
            
            $sql .= " WHERE session_id = :session_id";
            
            $stmt = $this->pdo->prepare($sql);
            $result = $stmt->execute($params);
            
            if ($this->logger) {
                $this->logger->logSessionEvent($sessionId, $status, '', '', ['duration' => $duration]);
                $this->logger->logDatabaseOperation('UPDATE', 'sessions', $sessionId, ['status' => $status]);
            }
            
            return $result;
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to update session status: {$sessionId}", $e, $sessionId);
            }
            throw new \Exception("Failed to update session status: " . $e->getMessage());
        }
    }
    
    /**
     * Get sessions by student name
     * 
     * @param string $studentName Student name
     * @param int $limit Maximum number of sessions to return
     * @param int $offset Offset for pagination
     * @return array List of sessions
     */
    public function getSessionsByStudent($studentName, $limit = 50, $offset = 0) {
        try {
            $sql = "SELECT * FROM sessions 
                    WHERE student_name = :student_name 
                    ORDER BY created_at DESC 
                    LIMIT :limit OFFSET :offset";
            
            $stmt = $this->pdo->prepare($sql);
            $stmt->bindValue(':student_name', $studentName);
            $stmt->bindValue(':limit', $limit, \PDO::PARAM_INT);
            $stmt->bindValue(':offset', $offset, \PDO::PARAM_INT);
            $stmt->execute();
            
            return $stmt->fetchAll();
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to get sessions for student: {$studentName}", $e);
            }
            return [];
        }
    }
    
    // ========================================================================
    // CONVERSATION MANAGEMENT
    // ========================================================================
    
    /**
     * Add a message to conversation
     * 
     * @param string $sessionId Session identifier
     * @param int $messageOrder Order of message in conversation
     * @param string $role Message role (user, assistant, system)
     * @param string $content Message content
     * @param array $metadata Additional message metadata
     * @return bool Success status
     */
    public function addConversationMessage($sessionId, $messageOrder, $role, $content, $metadata = []) {
        try {
            $sql = "INSERT INTO conversations (session_id, message_order, role, content, token_count, processing_time_ms) 
                    VALUES (:session_id, :message_order, :role, :content, :token_count, :processing_time)";
            
            $stmt = $this->pdo->prepare($sql);
            $result = $stmt->execute([
                'session_id' => $sessionId,
                'message_order' => $messageOrder,
                'role' => $role,
                'content' => $content,
                'token_count' => $metadata['token_count'] ?? null,
                'processing_time' => $metadata['processing_time_ms'] ?? null
            ]);
            
            if ($this->logger) {
                $this->logger->logDatabaseOperation('INSERT', 'conversations', $sessionId, [
                    'role' => $role,
                    'content_length' => strlen($content)
                ]);
            }
            
            return $result;
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to add conversation message", $e, $sessionId);
            }
            throw new \Exception("Failed to add conversation message: " . $e->getMessage());
        }
    }
    
    /**
     * Get complete conversation for a session
     * 
     * @param string $sessionId Session identifier
     * @return array List of conversation messages
     */
    public function getConversation($sessionId) {
        try {
            $sql = "SELECT * FROM conversations 
                    WHERE session_id = :session_id 
                    ORDER BY message_order ASC";
            
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute(['session_id' => $sessionId]);
            
            return $stmt->fetchAll();
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to get conversation", $e, $sessionId);
            }
            return [];
        }
    }
    
    /**
     * Store multiple conversation messages in a transaction
     * 
     * @param string $sessionId Session identifier
     * @param array $messages Array of message data
     * @return bool Success status
     */
    public function storeConversationMessages($sessionId, $messages) {
        try {
            $this->pdo->beginTransaction();
            
            // Clear existing messages for this session
            $clearSql = "DELETE FROM conversations WHERE session_id = :session_id";
            $clearStmt = $this->pdo->prepare($clearSql);
            $clearStmt->execute(['session_id' => $sessionId]);
            
            // Insert new messages
            $insertSql = "INSERT INTO conversations (session_id, message_order, role, content, token_count, processing_time_ms) 
                          VALUES (:session_id, :message_order, :role, :content, :token_count, :processing_time)";
            $insertStmt = $this->pdo->prepare($insertSql);
            
            foreach ($messages as $index => $message) {
                $insertStmt->execute([
                    'session_id' => $sessionId,
                    'message_order' => $index + 1,
                    'role' => $message['role'],
                    'content' => $message['content'],
                    'token_count' => $message['token_count'] ?? null,
                    'processing_time' => $message['processing_time_ms'] ?? null
                ]);
            }
            
            $this->pdo->commit();
            
            if ($this->logger) {
                $this->logger->logDatabaseOperation('INSERT_BATCH', 'conversations', $sessionId, [
                    'message_count' => count($messages)
                ]);
            }
            
            return true;
            
        } catch (\Exception $e) {
            $this->pdo->rollBack();
            if ($this->logger) {
                $this->logger->logError("Failed to store conversation messages", $e, $sessionId);
            }
            throw new \Exception("Failed to store conversation messages: " . $e->getMessage());
        }
    }
    
    // ========================================================================
    // FEEDBACK MANAGEMENT
    // ========================================================================
    
    /**
     * Store feedback and scores
     * 
     * @param string $sessionId Session identifier
     * @param string $feedbackContent Complete feedback text
     * @param array $componentScores Array of component scores
     * @param string $evaluator Evaluator name
     * @param string $evaluationMethod Evaluation method (AI_AUTOMATED, HUMAN_REVIEW, HYBRID)
     * @return bool Success status
     */
    public function storeFeedback($sessionId, $feedbackContent, $componentScores = [], $evaluator = null, $evaluationMethod = 'AI_AUTOMATED') {
        try {
            // Parse component scores if not provided
            if (empty($componentScores) && !empty($feedbackContent)) {
                try {
                    $componentScores = FeedbackUtils::parseFeedbackScores($feedbackContent);
                } catch (\Exception $e) {
                    // Continue without parsed scores if parsing fails
                }
            }
            
            // Prepare component data
            $collaborationScore = null;
            $collaborationStatus = null;
            $evocationScore = null;
            $evocationStatus = null;
            $acceptanceScore = null;
            $acceptanceStatus = null;
            $compassionScore = null;
            $compassionStatus = null;
            
            foreach ($componentScores as $score) {
                switch ($score->component) {
                    case 'COLLABORATION':
                        $collaborationScore = $score->score;
                        $collaborationStatus = $score->status;
                        break;
                    case 'EVOCATION':
                        $evocationScore = $score->score;
                        $evocationStatus = $score->status;
                        break;
                    case 'ACCEPTANCE':
                        $acceptanceScore = $score->score;
                        $acceptanceStatus = $score->status;
                        break;
                    case 'COMPASSION':
                        $compassionScore = $score->score;
                        $compassionStatus = $score->status;
                        break;
                }
            }
            
            $sql = "INSERT INTO feedback (
                        session_id, feedback_content, 
                        collaboration_score, collaboration_status,
                        evocation_score, evocation_status,
                        acceptance_score, acceptance_status,
                        compassion_score, compassion_status,
                        evaluator, evaluation_method
                    ) VALUES (
                        :session_id, :feedback_content,
                        :collaboration_score, :collaboration_status,
                        :evocation_score, :evocation_status,
                        :acceptance_score, :acceptance_status,
                        :compassion_score, :compassion_status,
                        :evaluator, :evaluation_method
                    )";
            
            $stmt = $this->pdo->prepare($sql);
            $result = $stmt->execute([
                'session_id' => $sessionId,
                'feedback_content' => $feedbackContent,
                'collaboration_score' => $collaborationScore,
                'collaboration_status' => $collaborationStatus,
                'evocation_score' => $evocationScore,
                'evocation_status' => $evocationStatus,
                'acceptance_score' => $acceptanceScore,
                'acceptance_status' => $acceptanceStatus,
                'compassion_score' => $compassionScore,
                'compassion_status' => $compassionStatus,
                'evaluator' => $evaluator,
                'evaluation_method' => $evaluationMethod
            ]);
            
            if ($this->logger) {
                $totalScore = ($collaborationScore ?? 0) + ($evocationScore ?? 0) + 
                             ($acceptanceScore ?? 0) + ($compassionScore ?? 0);
                
                $this->logger->logFeedbackProcessing($sessionId, '', [
                    'total_score' => $totalScore,
                    'percentage' => ($totalScore / 30) * 100,
                    'components' => $componentScores
                ], $evaluator);
                
                $this->logger->logDatabaseOperation('INSERT', 'feedback', $sessionId, [
                    'evaluator' => $evaluator,
                    'total_score' => $totalScore
                ]);
            }
            
            return $result;
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to store feedback", $e, $sessionId);
            }
            throw new \Exception("Failed to store feedback: " . $e->getMessage());
        }
    }
    
    /**
     * Get feedback for a session
     * 
     * @param string $sessionId Session identifier
     * @return array|null Feedback data or null if not found
     */
    public function getFeedback($sessionId) {
        try {
            $sql = "SELECT * FROM feedback WHERE session_id = :session_id ORDER BY created_at DESC LIMIT 1";
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute(['session_id' => $sessionId]);
            
            return $stmt->fetch() ?: null;
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to get feedback", $e, $sessionId);
            }
            return null;
        }
    }
    
    /**
     * Get feedback statistics
     * 
     * @param string|null $sessionType Filter by session type
     * @param int $days Number of days to analyze
     * @return array Feedback statistics
     */
    public function getFeedbackStatistics($sessionType = null, $days = 30) {
        try {
            $sql = "SELECT 
                        COUNT(*) as total_feedbacks,
                        AVG(total_score) as avg_total_score,
                        AVG(percentage_score) as avg_percentage,
                        AVG(collaboration_score) as avg_collaboration,
                        AVG(evocation_score) as avg_evocation,
                        AVG(acceptance_score) as avg_acceptance,
                        AVG(compassion_score) as avg_compassion,
                        COUNT(CASE WHEN percentage_score >= 80 THEN 1 END) as high_performers,
                        COUNT(CASE WHEN percentage_score < 60 THEN 1 END) as needs_improvement
                    FROM feedback f
                    JOIN sessions s ON f.session_id = s.session_id
                    WHERE f.created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)";
            
            $params = ['days' => $days];
            
            if ($sessionType) {
                $sql .= " AND s.session_type = :session_type";
                $params['session_type'] = $sessionType;
            }
            
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute($params);
            
            return $stmt->fetch();
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to get feedback statistics", $e);
            }
            return [];
        }
    }
    
    // ========================================================================
    // PDF EXPORT MANAGEMENT
    // ========================================================================
    
    /**
     * Record PDF export
     * 
     * @param string $sessionId Session identifier
     * @param string $filename PDF filename
     * @param string|null $filePath Storage path
     * @param int|null $fileSize File size in bytes
     * @param string $pdfType Type of PDF (PERFORMANCE_REPORT, CONVERSATION_TRANSCRIPT, FEEDBACK_ONLY)
     * @param string $generationMethod PDF generation method
     * @return bool Success status
     */
    public function recordPdfExport($sessionId, $filename, $filePath = null, $fileSize = null, $pdfType = 'PERFORMANCE_REPORT', $generationMethod = 'DomPDF') {
        try {
            $sql = "INSERT INTO pdf_exports (session_id, filename, file_path, file_size, pdf_type, generation_method) 
                    VALUES (:session_id, :filename, :file_path, :file_size, :pdf_type, :generation_method)";
            
            $stmt = $this->pdo->prepare($sql);
            $result = $stmt->execute([
                'session_id' => $sessionId,
                'filename' => $filename,
                'file_path' => $filePath,
                'file_size' => $fileSize,
                'pdf_type' => $pdfType,
                'generation_method' => $generationMethod
            ]);
            
            if ($this->logger) {
                $this->logger->logPdfGeneration($sessionId, $filename, $filePath, $fileSize);
                $this->logger->logDatabaseOperation('INSERT', 'pdf_exports', $sessionId, [
                    'filename' => $filename,
                    'pdf_type' => $pdfType
                ]);
            }
            
            return $result;
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to record PDF export", $e, $sessionId);
            }
            throw new \Exception("Failed to record PDF export: " . $e->getMessage());
        }
    }
    
    /**
     * Record PDF download
     * 
     * @param string $sessionId Session identifier
     * @param string $filename PDF filename
     * @return bool Success status
     */
    public function recordPdfDownload($sessionId, $filename) {
        try {
            $sql = "UPDATE pdf_exports 
                    SET downloaded_at = CASE WHEN downloaded_at IS NULL THEN CURRENT_TIMESTAMP ELSE downloaded_at END,
                        download_count = download_count + 1
                    WHERE session_id = :session_id AND filename = :filename";
            
            $stmt = $this->pdo->prepare($sql);
            $result = $stmt->execute([
                'session_id' => $sessionId,
                'filename' => $filename
            ]);
            
            if ($this->logger) {
                $this->logger->logPdfDownload($sessionId, $filename);
                $this->logger->logDatabaseOperation('UPDATE', 'pdf_exports', $sessionId, [
                    'filename' => $filename,
                    'action' => 'download'
                ]);
            }
            
            return $result;
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to record PDF download", $e, $sessionId);
            }
            return false;
        }
    }
    
    /**
     * Get PDF exports for a session
     * 
     * @param string $sessionId Session identifier
     * @return array List of PDF exports
     */
    public function getPdfExports($sessionId) {
        try {
            $sql = "SELECT * FROM pdf_exports WHERE session_id = :session_id ORDER BY created_at DESC";
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute(['session_id' => $sessionId]);
            
            return $stmt->fetchAll();
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to get PDF exports", $e, $sessionId);
            }
            return [];
        }
    }
    
    // ========================================================================
    // COMPREHENSIVE DATA RETRIEVAL
    // ========================================================================
    
    /**
     * Get complete session data including conversation, feedback, and PDFs
     * 
     * @param string $sessionId Session identifier
     * @return array Complete session data
     */
    public function getCompleteSessionData($sessionId) {
        try {
            $data = [
                'session' => $this->getSession($sessionId),
                'conversation' => $this->getConversation($sessionId),
                'feedback' => $this->getFeedback($sessionId),
                'pdf_exports' => $this->getPdfExports($sessionId)
            ];
            
            if ($this->logger) {
                $this->logger->logDatabaseOperation('SELECT_COMPLETE', 'multiple_tables', $sessionId);
            }
            
            return $data;
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to get complete session data", $e, $sessionId);
            }
            return [];
        }
    }
    
    /**
     * Search sessions with various filters
     * 
     * @param array $filters Search filters
     * @param int $limit Maximum results
     * @param int $offset Pagination offset
     * @return array Search results
     */
    public function searchSessions($filters = [], $limit = 50, $offset = 0) {
        try {
            $sql = "SELECT s.*, f.total_score, f.percentage_score, f.evaluator 
                    FROM sessions s 
                    LEFT JOIN feedback f ON s.session_id = f.session_id 
                    WHERE 1=1";
            
            $params = [];
            
            if (!empty($filters['student_name'])) {
                $sql .= " AND s.student_name LIKE :student_name";
                $params['student_name'] = '%' . $filters['student_name'] . '%';
            }
            
            if (!empty($filters['session_type'])) {
                $sql .= " AND s.session_type = :session_type";
                $params['session_type'] = $filters['session_type'];
            }
            
            if (!empty($filters['status'])) {
                $sql .= " AND s.status = :status";
                $params['status'] = $filters['status'];
            }
            
            if (!empty($filters['date_from'])) {
                $sql .= " AND s.created_at >= :date_from";
                $params['date_from'] = $filters['date_from'];
            }
            
            if (!empty($filters['date_to'])) {
                $sql .= " AND s.created_at <= :date_to";
                $params['date_to'] = $filters['date_to'];
            }
            
            if (!empty($filters['min_score'])) {
                $sql .= " AND f.percentage_score >= :min_score";
                $params['min_score'] = $filters['min_score'];
            }
            
            $sql .= " ORDER BY s.created_at DESC LIMIT :limit OFFSET :offset";
            
            $stmt = $this->pdo->prepare($sql);
            $stmt->bindValue(':limit', $limit, \PDO::PARAM_INT);
            $stmt->bindValue(':offset', $offset, \PDO::PARAM_INT);
            
            foreach ($params as $key => $value) {
                $stmt->bindValue(":{$key}", $value);
            }
            
            $stmt->execute();
            return $stmt->fetchAll();
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to search sessions", $e);
            }
            return [];
        }
    }
    
    // ========================================================================
    // UTILITY METHODS
    // ========================================================================
    
    /**
     * Test database connection and schema
     * 
     * @return array Connection test results
     */
    public function testConnection() {
        $results = [
            'connection' => false,
            'tables' => [],
            'version' => null,
            'errors' => []
        ];
        
        try {
            // Test basic connection
            $stmt = $this->pdo->query("SELECT VERSION() as version");
            $results['version'] = $stmt->fetch()['version'];
            $results['connection'] = true;
            
            // Test required tables
            $requiredTables = ['sessions', 'conversations', 'feedback', 'pdf_exports', 'system_logs'];
            
            foreach ($requiredTables as $table) {
                try {
                    $stmt = $this->pdo->query("SELECT 1 FROM {$table} LIMIT 1");
                    $results['tables'][$table] = true;
                } catch (\Exception $e) {
                    $results['tables'][$table] = false;
                    $results['errors'][] = "Table {$table}: " . $e->getMessage();
                }
            }
            
        } catch (\Exception $e) {
            $results['errors'][] = "Connection: " . $e->getMessage();
        }
        
        return $results;
    }
    
    /**
     * Generate unique session ID
     * 
     * @param string $prefix Optional prefix
     * @return string Unique session ID
     */
    public function generateSessionId($prefix = 'mi_session') {
        return $prefix . '_' . time() . '_' . bin2hex(random_bytes(8));
    }
    
    /**
     * Clean up old sessions and related data
     * 
     * @param int $daysOld Number of days old to consider for cleanup
     * @return array Cleanup results
     */
    public function cleanupOldSessions($daysOld = 90) {
        try {
            $this->pdo->beginTransaction();
            
            // Get sessions to be deleted
            $sql = "SELECT session_id FROM sessions 
                    WHERE created_at < DATE_SUB(NOW(), INTERVAL :days DAY)
                    AND status IN ('COMPLETED', 'ABANDONED')";
            
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute(['days' => $daysOld]);
            $sessionsToDelete = $stmt->fetchAll(\PDO::FETCH_COLUMN);
            
            $deletedCounts = [
                'sessions' => 0,
                'conversations' => 0,
                'feedback' => 0,
                'pdf_exports' => 0
            ];
            
            if (!empty($sessionsToDelete)) {
                // Delete in correct order due to foreign key constraints
                $placeholders = str_repeat('?,', count($sessionsToDelete) - 1) . '?';
                
                // Delete PDF exports
                $stmt = $this->pdo->prepare("DELETE FROM pdf_exports WHERE session_id IN ({$placeholders})");
                $stmt->execute($sessionsToDelete);
                $deletedCounts['pdf_exports'] = $stmt->rowCount();
                
                // Delete feedback
                $stmt = $this->pdo->prepare("DELETE FROM feedback WHERE session_id IN ({$placeholders})");
                $stmt->execute($sessionsToDelete);
                $deletedCounts['feedback'] = $stmt->rowCount();
                
                // Delete conversations
                $stmt = $this->pdo->prepare("DELETE FROM conversations WHERE session_id IN ({$placeholders})");
                $stmt->execute($sessionsToDelete);
                $deletedCounts['conversations'] = $stmt->rowCount();
                
                // Delete sessions
                $stmt = $this->pdo->prepare("DELETE FROM sessions WHERE session_id IN ({$placeholders})");
                $stmt->execute($sessionsToDelete);
                $deletedCounts['sessions'] = $stmt->rowCount();
            }
            
            $this->pdo->commit();
            
            if ($this->logger) {
                $this->logger->log(Logger::INFO, Logger::CATEGORY_SYSTEM, 
                    "Cleaned up old sessions", [
                        'days_old' => $daysOld,
                        'deleted_counts' => $deletedCounts
                    ]);
            }
            
            return [
                'success' => true,
                'deleted_counts' => $deletedCounts,
                'sessions_cleaned' => count($sessionsToDelete)
            ];
            
        } catch (\Exception $e) {
            $this->pdo->rollBack();
            if ($this->logger) {
                $this->logger->logError("Failed to cleanup old sessions", $e);
            }
            
            return [
                'success' => false,
                'error' => $e->getMessage(),
                'deleted_counts' => $deletedCounts ?? []
            ];
        }
    }
    
    /**
     * Get client IP address
     * 
     * @return string Client IP address
     */
    private function getClientIpAddress() {
        $ipKeys = ['HTTP_CF_CONNECTING_IP', 'HTTP_X_FORWARDED_FOR', 'HTTP_X_FORWARDED', 
                   'HTTP_X_CLUSTER_CLIENT_IP', 'HTTP_FORWARDED_FOR', 'HTTP_FORWARDED', 'REMOTE_ADDR'];
        
        foreach ($ipKeys as $key) {
            if (array_key_exists($key, $_SERVER) === true) {
                $ip = $_SERVER[$key];
                if (strpos($ip, ',') !== false) {
                    $ip = explode(',', $ip)[0];
                }
                $ip = trim($ip);
                if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE)) {
                    return $ip;
                }
            }
        }
        
        return $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    }
}

/**
 * Example usage and testing functions
 */
class SessionStorageExample {
    
    /**
     * Demonstrate basic usage of SessionStorage
     */
    public static function demonstrateUsage() {
        echo "<h2>SessionStorage Example Usage</h2>\n";
        
        try {
            // Create database connection (adjust connection parameters as needed)
            $pdo = new \PDO('mysql:host=localhost;dbname=mi_chatbots;charset=utf8mb4', 'username', 'password', [
                \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
                \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
            ]);
            
            // Create logger and storage instances
            $logger = new Logger($pdo, null, true, false); // Database logging only
            $storage = new SessionStorage($pdo, $logger);
            
            // Test connection
            $connectionTest = $storage->testConnection();
            echo "<h3>Connection Test:</h3>\n";
            echo "<p>Connected: " . ($connectionTest['connection'] ? 'Yes' : 'No') . "</p>\n";
            echo "<p>MySQL Version: " . ($connectionTest['version'] ?? 'Unknown') . "</p>\n";
            
            if (!empty($connectionTest['errors'])) {
                echo "<p>Errors: " . implode(', ', $connectionTest['errors']) . "</p>\n";
                return;
            }
            
            // Generate session ID
            $sessionId = $storage->generateSessionId();
            echo "<h3>Generated Session ID:</h3>\n";
            echo "<p>{$sessionId}</p>\n";
            
            // Create session
            $sessionCreated = $storage->createSession($sessionId, 'Demo User', 'HPV', 'Alex - Hesitant Patient');
            echo "<h3>Session Created:</h3>\n";
            echo "<p>" . ($sessionCreated ? 'Yes' : 'No') . "</p>\n";
            
            // Store conversation
            $messages = [
                ['role' => 'assistant', 'content' => 'Hello! I heard you wanted to discuss the HPV vaccine?'],
                ['role' => 'user', 'content' => 'Yes, I have some concerns about it.'],
                ['role' => 'assistant', 'content' => 'I understand. What specific concerns do you have?']
            ];
            
            $conversationStored = $storage->storeConversationMessages($sessionId, $messages);
            echo "<h3>Conversation Stored:</h3>\n";
            echo "<p>" . ($conversationStored ? 'Yes' : 'No') . "</p>\n";
            
            // Store feedback
            $feedbackContent = "**1. COLLABORATION (7.5 pts): [Met] - Good partnership building**\n**2. EVOCATION (7.5 pts): [Partially Met] - Could use more open questions**";
            $feedbackStored = $storage->storeFeedback($sessionId, $feedbackContent, [], 'Demo Evaluator');
            echo "<h3>Feedback Stored:</h3>\n";
            echo "<p>" . ($feedbackStored ? 'Yes' : 'No') . "</p>\n";
            
            // Record PDF export
            $pdfRecorded = $storage->recordPdfExport($sessionId, 'demo_report.pdf', '/tmp/demo_report.pdf', 1024000);
            echo "<h3>PDF Export Recorded:</h3>\n";
            echo "<p>" . ($pdfRecorded ? 'Yes' : 'No') . "</p>\n";
            
            // Get complete session data
            $completeData = $storage->getCompleteSessionData($sessionId);
            echo "<h3>Complete Session Data Retrieved:</h3>\n";
            echo "<p>Session: " . (isset($completeData['session']) ? 'Yes' : 'No') . "</p>\n";
            echo "<p>Messages: " . count($completeData['conversation'] ?? []) . "</p>\n";
            echo "<p>Feedback: " . (isset($completeData['feedback']) ? 'Yes' : 'No') . "</p>\n";
            echo "<p>PDF Exports: " . count($completeData['pdf_exports'] ?? []) . "</p>\n";
            
        } catch (\Exception $e) {
            echo "<p>Error: " . $e->getMessage() . "</p>\n";
        }
    }
}

// Uncomment the following line to run the example when this file is accessed directly
// if (basename(__FILE__) == basename($_SERVER['PHP_SELF'])) {
//     SessionStorageExample::demonstrateUsage();
// }

?>