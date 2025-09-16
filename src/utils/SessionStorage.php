<?php
/**
 * SessionStorage.php - MySQL database operations for MI chatbot sessions
 * 
 * LAMP-stack compatible database storage for Motivational Interviewing chatbots
 * Handles storage and retrieval of conversations, feedback, and PDF reports
 * Uses prepared statements for security and supports the mi_sessions schema
 * 
 * @package MIUtils
 * @version 1.0
 * @author MI Assessment System
 */

class SessionStorage {
    
    private $pdo;
    private $config;
    
    /**
     * Initialize database connection
     * 
     * @param array $config Database configuration
     *   - host: Database host (default: localhost)
     *   - dbname: Database name (default: mi_sessions)
     *   - username: Database username
     *   - password: Database password
     *   - charset: Character set (default: utf8mb4)
     *   - options: PDO options array
     */
    public function __construct($config = []) {
        $defaultConfig = [
            'host' => 'localhost',
            'dbname' => 'mi_sessions',
            'username' => 'root',
            'password' => '',
            'charset' => 'utf8mb4',
            'options' => [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ]
        ];
        
        $this->config = array_merge($defaultConfig, $config);
        $this->connect();
    }
    
    /**
     * Establish database connection
     */
    private function connect() {
        $dsn = "mysql:host={$this->config['host']};dbname={$this->config['dbname']};charset={$this->config['charset']}";
        
        try {
            $this->pdo = new PDO($dsn, $this->config['username'], $this->config['password'], $this->config['options']);
        } catch (PDOException $e) {
            throw new Exception("Database connection failed: " . $e->getMessage());
        }
    }
    
    /**
     * Create or update session record
     * 
     * @param string $sessionId Unique session identifier
     * @param string $studentName Student name
     * @param string $sessionType Session type (HPV, OHI, General)
     * @param string|null $personaSelected Selected persona
     * @return bool Success status
     */
    public function createSession($sessionId, $studentName, $sessionType = 'General', $personaSelected = null) {
        $sql = "INSERT INTO sessions (session_id, student_name, session_type, persona_selected, started_at) 
                VALUES (:session_id, :student_name, :session_type, :persona_selected, NOW())
                ON DUPLICATE KEY UPDATE 
                student_name = VALUES(student_name),
                session_type = VALUES(session_type),
                persona_selected = VALUES(persona_selected)";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            return $stmt->execute([
                ':session_id' => $sessionId,
                ':student_name' => $studentName,
                ':session_type' => $sessionType,
                ':persona_selected' => $personaSelected
            ]);
        } catch (PDOException $e) {
            throw new Exception("Failed to create session: " . $e->getMessage());
        }
    }
    
    /**
     * Add message to session
     * 
     * @param string $sessionId Session identifier
     * @param string $role Message role (user, assistant, system)
     * @param string $content Message content
     * @return bool Success status
     */
    public function addMessage($sessionId, $role, $content) {
        $sql = "INSERT INTO messages (session_id, role, content, timestamp) 
                VALUES (:session_id, :role, :content, NOW())";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $result = $stmt->execute([
                ':session_id' => $sessionId,
                ':role' => $role,
                ':content' => $content
            ]);
            
            // Update message count in sessions table
            $this->updateMessageCount($sessionId);
            
            return $result;
        } catch (PDOException $e) {
            throw new Exception("Failed to add message: " . $e->getMessage());
        }
    }
    
    /**
     * Get all messages for a session
     * 
     * @param string $sessionId Session identifier
     * @return array Messages array
     */
    public function getMessages($sessionId) {
        $sql = "SELECT role, content, timestamp FROM messages 
                WHERE session_id = :session_id 
                ORDER BY timestamp ASC";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([':session_id' => $sessionId]);
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            throw new Exception("Failed to get messages: " . $e->getMessage());
        }
    }
    
    /**
     * Store feedback data
     * 
     * @param string $sessionId Session identifier
     * @param string $studentName Student name
     * @param string $sessionType Session type
     * @param array $componentScores Array of component score details
     * @param float $totalScore Total calculated score
     * @param float $percentage Score percentage
     * @param string $rawFeedback Raw feedback text
     * @param string $evaluator Evaluator name (default: AI_System)
     * @return int Feedback record ID
     */
    public function storeFeedback($sessionId, $studentName, $sessionType, $componentScores, 
                                 $totalScore, $percentage, $rawFeedback, $evaluator = 'AI_System') {
        
        // Extract component details
        $components = [
            'COLLABORATION' => ['status' => null, 'score' => 0.00, 'feedback' => null],
            'EVOCATION' => ['status' => null, 'score' => 0.00, 'feedback' => null],
            'ACCEPTANCE' => ['status' => null, 'score' => 0.00, 'feedback' => null],
            'COMPASSION' => ['status' => null, 'score' => 0.00, 'feedback' => null]
        ];
        
        foreach ($componentScores as $comp) {
            if (isset($components[$comp['component']])) {
                $components[$comp['component']] = [
                    'status' => $comp['status'],
                    'score' => $comp['score'],
                    'feedback' => $comp['feedback']
                ];
            }
        }
        
        // Get performance level
        $performanceLevel = $this->getPerformanceLevel($percentage);
        
        // Extract suggestions
        $suggestions = $this->extractSuggestions($rawFeedback);
        
        $sql = "INSERT INTO feedback (
            session_id, student_name, session_type, evaluator,
            collaboration_status, collaboration_score, collaboration_feedback,
            evocation_status, evocation_score, evocation_feedback,
            acceptance_status, acceptance_score, acceptance_feedback,
            compassion_status, compassion_score, compassion_feedback,
            total_score, max_possible_score, percentage, performance_level,
            raw_feedback, suggestions, created_at
        ) VALUES (
            :session_id, :student_name, :session_type, :evaluator,
            :collab_status, :collab_score, :collab_feedback,
            :evoc_status, :evoc_score, :evoc_feedback,
            :accept_status, :accept_score, :accept_feedback,
            :compass_status, :compass_score, :compass_feedback,
            :total_score, :max_possible_score, :percentage, :performance_level,
            :raw_feedback, :suggestions, NOW()
        )";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([
                ':session_id' => $sessionId,
                ':student_name' => $studentName,
                ':session_type' => $sessionType,
                ':evaluator' => $evaluator,
                ':collab_status' => $components['COLLABORATION']['status'],
                ':collab_score' => $components['COLLABORATION']['score'],
                ':collab_feedback' => $components['COLLABORATION']['feedback'],
                ':evoc_status' => $components['EVOCATION']['status'],
                ':evoc_score' => $components['EVOCATION']['score'],
                ':evoc_feedback' => $components['EVOCATION']['feedback'],
                ':accept_status' => $components['ACCEPTANCE']['status'],
                ':accept_score' => $components['ACCEPTANCE']['score'],
                ':accept_feedback' => $components['ACCEPTANCE']['feedback'],
                ':compass_status' => $components['COMPASSION']['status'],
                ':compass_score' => $components['COMPASSION']['score'],
                ':compass_feedback' => $components['COMPASSION']['feedback'],
                ':total_score' => $totalScore,
                ':max_possible_score' => 30.00,
                ':percentage' => $percentage,
                ':performance_level' => $performanceLevel,
                ':raw_feedback' => $rawFeedback,
                ':suggestions' => $suggestions
            ]);
            
            return $this->pdo->lastInsertId();
        } catch (PDOException $e) {
            throw new Exception("Failed to store feedback: " . $e->getMessage());
        }
    }
    
    /**
     * Get feedback for a session
     * 
     * @param string $sessionId Session identifier
     * @return array|null Feedback data or null if not found
     */
    public function getFeedback($sessionId) {
        $sql = "SELECT * FROM feedback WHERE session_id = :session_id ORDER BY created_at DESC LIMIT 1";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([':session_id' => $sessionId]);
            return $stmt->fetch();
        } catch (PDOException $e) {
            throw new Exception("Failed to get feedback: " . $e->getMessage());
        }
    }
    
    /**
     * Store PDF report information
     * 
     * @param string $sessionId Session identifier
     * @param string $studentName Student name
     * @param string $sessionType Session type
     * @param string $filename Generated filename
     * @param string|null $filePath Path to PDF file
     * @param int|null $fileSize File size in bytes
     * @param float|null $totalScore Total score for quick access
     * @param float|null $percentage Score percentage for quick access
     * @return int PDF report record ID
     */
    public function storePdfReport($sessionId, $studentName, $sessionType, $filename, 
                                 $filePath = null, $fileSize = null, $totalScore = null, $percentage = null) {
        $sql = "INSERT INTO pdf_reports (
            session_id, student_name, session_type, filename, file_path, file_size,
            total_score, percentage, generated_at
        ) VALUES (
            :session_id, :student_name, :session_type, :filename, :file_path, :file_size,
            :total_score, :percentage, NOW()
        )";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([
                ':session_id' => $sessionId,
                ':student_name' => $studentName,
                ':session_type' => $sessionType,
                ':filename' => $filename,
                ':file_path' => $filePath,
                ':file_size' => $fileSize,
                ':total_score' => $totalScore,
                ':percentage' => $percentage
            ]);
            
            return $this->pdo->lastInsertId();
        } catch (PDOException $e) {
            throw new Exception("Failed to store PDF report: " . $e->getMessage());
        }
    }
    
    /**
     * Record PDF download
     * 
     * @param int $pdfId PDF report ID
     * @return bool Success status
     */
    public function recordPdfDownload($pdfId) {
        $sql = "UPDATE pdf_reports SET 
                downloaded = TRUE, 
                download_count = download_count + 1,
                last_downloaded_at = NOW()
                WHERE id = :pdf_id";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            return $stmt->execute([':pdf_id' => $pdfId]);
        } catch (PDOException $e) {
            throw new Exception("Failed to record PDF download: " . $e->getMessage());
        }
    }
    
    /**
     * Complete session (mark as completed)
     * 
     * @param string $sessionId Session identifier
     * @return bool Success status
     */
    public function completeSession($sessionId) {
        $sql = "UPDATE sessions SET 
                status = 'completed', 
                completed_at = NOW() 
                WHERE session_id = :session_id";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            return $stmt->execute([':session_id' => $sessionId]);
        } catch (PDOException $e) {
            throw new Exception("Failed to complete session: " . $e->getMessage());
        }
    }
    
    /**
     * Get session information
     * 
     * @param string $sessionId Session identifier
     * @return array|null Session data or null if not found
     */
    public function getSession($sessionId) {
        $sql = "SELECT * FROM sessions WHERE session_id = :session_id";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([':session_id' => $sessionId]);
            return $stmt->fetch();
        } catch (PDOException $e) {
            throw new Exception("Failed to get session: " . $e->getMessage());
        }
    }
    
    /**
     * Log activity
     * 
     * @param string|null $sessionId Session ID
     * @param string $logLevel Log level
     * @param string $eventType Event type
     * @param string $message Log message
     * @param string|null $context JSON context data
     * @param string|null $ipAddress Client IP address
     * @param string|null $userAgent User agent string
     * @return bool Success status
     */
    public function logActivity($sessionId, $logLevel, $eventType, $message, 
                              $context = null, $ipAddress = null, $userAgent = null) {
        $sql = "INSERT INTO activity_log (
            session_id, log_level, event_type, message, context, 
            ip_address, user_agent, created_at
        ) VALUES (
            :session_id, :log_level, :event_type, :message, :context,
            :ip_address, :user_agent, NOW()
        )";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            return $stmt->execute([
                ':session_id' => $sessionId,
                ':log_level' => $logLevel,
                ':event_type' => $eventType,
                ':message' => $message,
                ':context' => $context,
                ':ip_address' => $ipAddress,
                ':user_agent' => $userAgent
            ]);
        } catch (PDOException $e) {
            throw new Exception("Failed to log activity: " . $e->getMessage());
        }
    }
    
    /**
     * Get activity logs
     * 
     * @param string|null $sessionId Filter by session ID
     * @param string|null $logLevel Filter by log level
     * @param string|null $eventType Filter by event type
     * @param int $limit Number of records to return
     * @param int $offset Offset for pagination
     * @return array Activity log entries
     */
    public function getActivityLogs($sessionId = null, $logLevel = null, $eventType = null, 
                                  $limit = 100, $offset = 0) {
        $where = [];
        $params = [];
        
        if ($sessionId) {
            $where[] = "session_id = :session_id";
            $params[':session_id'] = $sessionId;
        }
        
        if ($logLevel) {
            $where[] = "log_level = :log_level";
            $params[':log_level'] = $logLevel;
        }
        
        if ($eventType) {
            $where[] = "event_type = :event_type";
            $params[':event_type'] = $eventType;
        }
        
        $whereClause = !empty($where) ? 'WHERE ' . implode(' AND ', $where) : '';
        
        $sql = "SELECT * FROM activity_log 
                $whereClause 
                ORDER BY created_at DESC 
                LIMIT :limit OFFSET :offset";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            
            // Bind parameters
            foreach ($params as $key => $value) {
                $stmt->bindValue($key, $value);
            }
            $stmt->bindValue(':limit', (int)$limit, PDO::PARAM_INT);
            $stmt->bindValue(':offset', (int)$offset, PDO::PARAM_INT);
            
            $stmt->execute();
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            throw new Exception("Failed to get activity logs: " . $e->getMessage());
        }
    }
    
    /**
     * Clear old activity logs
     * 
     * @param string $cutoffDate Cutoff date (YYYY-MM-DD HH:MM:SS)
     * @return int Number of records deleted
     */
    public function clearOldActivityLogs($cutoffDate) {
        $sql = "DELETE FROM activity_log WHERE created_at < :cutoff_date";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([':cutoff_date' => $cutoffDate]);
            return $stmt->rowCount();
        } catch (PDOException $e) {
            throw new Exception("Failed to clear old activity logs: " . $e->getMessage());
        }
    }
    
    /**
     * Get dashboard statistics
     * 
     * @return array Statistics summary
     */
    public function getDashboardStats() {
        $stats = [];
        
        try {
            // Total sessions
            $stmt = $this->pdo->query("SELECT COUNT(*) as count FROM sessions");
            $stats['total_sessions'] = $stmt->fetch()['count'];
            
            // Completed sessions
            $stmt = $this->pdo->query("SELECT COUNT(*) as count FROM sessions WHERE status = 'completed'");
            $stats['completed_sessions'] = $stmt->fetch()['count'];
            
            // Total feedback records
            $stmt = $this->pdo->query("SELECT COUNT(*) as count FROM feedback");
            $stats['total_feedback'] = $stmt->fetch()['count'];
            
            // Total PDF reports
            $stmt = $this->pdo->query("SELECT COUNT(*) as count FROM pdf_reports");
            $stats['total_pdfs'] = $stmt->fetch()['count'];
            
            // Average score
            $stmt = $this->pdo->query("SELECT AVG(total_score) as avg_score FROM feedback");
            $result = $stmt->fetch();
            $stats['average_score'] = $result['avg_score'] ? round($result['avg_score'], 2) : 0;
            
            // Session types breakdown
            $stmt = $this->pdo->query("SELECT session_type, COUNT(*) as count FROM sessions GROUP BY session_type");
            $stats['session_types'] = [];
            while ($row = $stmt->fetch()) {
                $stats['session_types'][$row['session_type']] = $row['count'];
            }
            
            return $stats;
        } catch (PDOException $e) {
            throw new Exception("Failed to get dashboard stats: " . $e->getMessage());
        }
    }
    
    /**
     * Update message count for session
     */
    private function updateMessageCount($sessionId) {
        $sql = "UPDATE sessions SET total_messages = (
            SELECT COUNT(*) FROM messages WHERE session_id = :session_id
        ) WHERE session_id = :session_id";
        
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([':session_id' => $sessionId]);
    }
    
    /**
     * Get performance level based on percentage
     */
    private function getPerformanceLevel($percentage) {
        if ($percentage >= 90) return "Excellent";
        if ($percentage >= 80) return "Proficient";
        if ($percentage >= 70) return "Developing";
        if ($percentage >= 60) return "Beginning";
        return "Needs Improvement";
    }
    
    /**
     * Extract suggestions from feedback text
     */
    private function extractSuggestions($feedback) {
        $suggestions = [];
        $lines = explode("\n", $feedback);
        $inSuggestions = false;
        
        $suggestionIndicators = [
            'suggestions for improvement',
            'next steps',
            'recommendations',
            'areas to focus',
            'improvement suggestions'
        ];
        
        foreach ($lines as $line) {
            $line = trim($line);
            if (empty($line)) continue;
            
            foreach ($suggestionIndicators as $indicator) {
                if (stripos($line, $indicator) !== false) {
                    $inSuggestions = true;
                    $suggestions[] = $line;
                    continue 2;
                }
            }
            
            if ($inSuggestions && (preg_match('/^[-•*]\s*/', $line) || 
                (!empty($line) && !ctype_upper($line) && !preg_match('/^\d+\./', $line)))) {
                $suggestions[] = $line;
            }
        }
        
        return implode("\n", $suggestions);
    }
    
    /**
     * Close database connection
     */
    public function close() {
        $this->pdo = null;
    }
}

// Example usage and testing functions (can be removed in production)
if (basename(__FILE__) == basename($_SERVER["SCRIPT_FILENAME"])) {
    // Simple test when file is run directly
    echo "=== SessionStorage PHP Test ===\n";
    
    try {
        // Test with SQLite for local testing (change to MySQL config for production)
        $testConfig = [
            'host' => 'localhost',
            'dbname' => 'sqlite:' . sys_get_temp_dir() . '/mi_test.db',
            'username' => '',
            'password' => ''
        ];
        
        echo "Note: This test requires proper MySQL database configuration.\n";
        echo "✓ Class loaded successfully\n";
        echo "✓ Methods available: " . count(get_class_methods('SessionStorage')) . "\n";
        
    } catch (Exception $e) {
        echo "Note: " . $e->getMessage() . "\n";
        echo "This is expected without proper database configuration.\n";
    }
}
?>