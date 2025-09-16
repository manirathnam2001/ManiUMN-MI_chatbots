<?php
/**
 * SessionStorage.php
 * 
 * Complete MySQL database operations for MI chatbot sessions, conversations, 
 * feedback storage, PDF tracking, and comprehensive logging.
 * 
 * Features:
 * - Session management with full lifecycle tracking  
 * - Message storage with conversation history
 * - Feedback storage with MI component breakdown
 * - PDF report tracking with metadata
 * - Activity logging with structured JSON data
 * - Performance metrics collection
 * - Security with prepared statements
 * - Transaction support for atomic operations
 * 
 * @package MIChatbots
 * @author LAMP-Stack MI Assessment System
 * @version 1.0.0
 */

class SessionStorage
{
    private $pdo;
    private $dbConfig;
    
    /**
     * Initialize SessionStorage with database connection
     * 
     * @param array $dbConfig Database configuration
     *   - host: Database host
     *   - dbname: Database name
     *   - username: Database username  
     *   - password: Database password
     *   - charset: Character set (default: utf8mb4)
     *   - options: PDO options array
     */
    public function __construct($dbConfig)
    {
        $this->dbConfig = $dbConfig;
        $this->connect();
    }
    
    /**
     * Establish database connection
     */
    private function connect()
    {
        $host = $this->dbConfig['host'] ?? 'localhost';
        $dbname = $this->dbConfig['dbname'] ?? 'mi_chatbots';
        $username = $this->dbConfig['username'] ?? 'root';
        $password = $this->dbConfig['password'] ?? '';
        $charset = $this->dbConfig['charset'] ?? 'utf8mb4';
        
        $dsn = "mysql:host=$host;dbname=$dbname;charset=$charset";
        
        $defaultOptions = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ];
        
        $options = array_merge($defaultOptions, $this->dbConfig['options'] ?? []);
        
        try {
            $this->pdo = new PDO($dsn, $username, $password, $options);
        } catch (PDOException $e) {
            throw new Exception("Database connection failed: " . $e->getMessage());
        }
    }
    
    /**
     * Get PDO instance for advanced operations
     * 
     * @return PDO PDO instance
     */
    public function getPdo()
    {
        return $this->pdo;
    }
    
    /**
     * Create a new session
     * 
     * @param string $sessionId Unique session identifier
     * @param string $studentName Student name
     * @param string $sessionType Session type (HPV, OHI, GENERAL)
     * @param string $persona Selected persona
     * @return bool Success status
     */
    public function createSession($sessionId, $studentName, $sessionType, $persona = null)
    {
        $sql = "INSERT INTO sessions (session_id, student_name, session_type, persona, status) 
                VALUES (?, ?, ?, ?, 'active')";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            return $stmt->execute([$sessionId, $studentName, $sessionType, $persona]);
        } catch (PDOException $e) {
            throw new Exception("Failed to create session: " . $e->getMessage());
        }
    }
    
    /**
     * Update session status
     * 
     * @param string $sessionId Session ID
     * @param string $status New status (active, completed, abandoned)
     * @return bool Success status
     */
    public function updateSessionStatus($sessionId, $status)
    {
        $sql = "UPDATE sessions SET status = ?, updated_at = CURRENT_TIMESTAMP";
        
        if ($status === 'completed') {
            $sql .= ", completed_at = CURRENT_TIMESTAMP";
        }
        
        $sql .= " WHERE session_id = ?";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            return $stmt->execute([$status, $sessionId]);
        } catch (PDOException $e) {
            throw new Exception("Failed to update session status: " . $e->getMessage());
        }
    }
    
    /**
     * Get session information
     * 
     * @param string $sessionId Session ID
     * @return array|null Session data or null if not found
     */
    public function getSession($sessionId)
    {
        $sql = "SELECT * FROM sessions WHERE session_id = ?";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([$sessionId]);
            return $stmt->fetch();
        } catch (PDOException $e) {
            throw new Exception("Failed to get session: " . $e->getMessage());
        }
    }
    
    /**
     * Store a chat message
     * 
     * @param string $sessionId Session ID
     * @param string $role Message role (user, assistant, system)
     * @param string $content Message content
     * @param int $messageOrder Message order in conversation
     * @return int Message ID
     */
    public function storeMessage($sessionId, $role, $content, $messageOrder)
    {
        $sql = "INSERT INTO messages (session_id, role, content, message_order) 
                VALUES (?, ?, ?, ?)";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([$sessionId, $role, $content, $messageOrder]);
            return $this->pdo->lastInsertId();
        } catch (PDOException $e) {
            throw new Exception("Failed to store message: " . $e->getMessage());
        }
    }
    
    /**
     * Get conversation history for a session
     * 
     * @param string $sessionId Session ID
     * @param int $limit Maximum number of messages to retrieve
     * @return array Array of messages
     */
    public function getConversationHistory($sessionId, $limit = 1000)
    {
        $sql = "SELECT role, content, timestamp, message_order 
                FROM messages 
                WHERE session_id = ? 
                ORDER BY message_order ASC 
                LIMIT ?";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([$sessionId, $limit]);
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            throw new Exception("Failed to get conversation history: " . $e->getMessage());
        }
    }
    
    /**
     * Store MI feedback with component breakdown
     * 
     * @param string $sessionId Session ID
     * @param string $studentName Student name
     * @param string $sessionType Session type
     * @param array $components MI component scores
     * @param float $totalScore Total score
     * @param float $percentage Score percentage
     * @param string $rawFeedback Raw feedback text
     * @param string $evaluator Evaluator name
     * @return int Feedback ID
     */
    public function storeFeedback($sessionId, $studentName, $sessionType, $components, 
                                $totalScore, $percentage, $rawFeedback, $evaluator = null)
    {
        // Begin transaction for atomic operation
        $this->pdo->beginTransaction();
        
        try {
            // Determine performance level
            $performanceLevel = $this->calculatePerformanceLevel($percentage);
            
            // Prepare component data
            $componentData = $this->prepareComponentData($components);
            
            $sql = "INSERT INTO feedback (
                        session_id, student_name, session_type,
                        collaboration_score, collaboration_status, collaboration_feedback,
                        evocation_score, evocation_status, evocation_feedback,
                        acceptance_score, acceptance_status, acceptance_feedback,
                        compassion_score, compassion_status, compassion_feedback,
                        total_score, percentage, performance_level, raw_feedback, evaluator
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
            
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([
                $sessionId, $studentName, $sessionType,
                $componentData['COLLABORATION']['score'], $componentData['COLLABORATION']['status'], $componentData['COLLABORATION']['feedback'],
                $componentData['EVOCATION']['score'], $componentData['EVOCATION']['status'], $componentData['EVOCATION']['feedback'],
                $componentData['ACCEPTANCE']['score'], $componentData['ACCEPTANCE']['status'], $componentData['ACCEPTANCE']['feedback'],
                $componentData['COMPASSION']['score'], $componentData['COMPASSION']['status'], $componentData['COMPASSION']['feedback'],
                $totalScore, $percentage, $performanceLevel, $rawFeedback, $evaluator
            ]);
            
            $feedbackId = $this->pdo->lastInsertId();
            
            $this->pdo->commit();
            return $feedbackId;
            
        } catch (Exception $e) {
            $this->pdo->rollback();
            throw new Exception("Failed to store feedback: " . $e->getMessage());
        }
    }
    
    /**
     * Prepare component data for database storage
     * 
     * @param array $components Component scores array
     * @return array Prepared component data
     */
    private function prepareComponentData($components)
    {
        $defaultComponent = ['score' => 0.0, 'status' => 'Not Met', 'feedback' => 'No assessment provided'];
        
        $prepared = [
            'COLLABORATION' => $defaultComponent,
            'EVOCATION' => $defaultComponent,
            'ACCEPTANCE' => $defaultComponent,
            'COMPASSION' => $defaultComponent
        ];
        
        // Fill in actual component data
        foreach ($components as $component) {
            $componentName = strtoupper($component['component']);
            if (array_key_exists($componentName, $prepared)) {
                $prepared[$componentName] = [
                    'score' => $component['score'],
                    'status' => $component['status'],
                    'feedback' => $component['feedback']
                ];
            }
        }
        
        return $prepared;
    }
    
    /**
     * Calculate performance level from percentage
     * 
     * @param float $percentage Score percentage
     * @return string Performance level
     */
    private function calculatePerformanceLevel($percentage)
    {
        if ($percentage >= 90.0) return 'Excellent';
        if ($percentage >= 80.0) return 'Proficient';
        if ($percentage >= 70.0) return 'Developing';
        if ($percentage >= 60.0) return 'Beginning';
        return 'Needs Improvement';
    }
    
    /**
     * Get feedback for a session
     * 
     * @param string $sessionId Session ID
     * @return array|null Feedback data or null if not found
     */
    public function getFeedback($sessionId)
    {
        $sql = "SELECT * FROM feedback WHERE session_id = ? ORDER BY feedback_timestamp DESC LIMIT 1";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([$sessionId]);
            return $stmt->fetch();
        } catch (PDOException $e) {
            throw new Exception("Failed to get feedback: " . $e->getMessage());
        }
    }
    
    /**
     * Store PDF report metadata
     * 
     * @param string $sessionId Session ID
     * @param int $feedbackId Feedback ID
     * @param string $filename Generated filename
     * @param string $filePath File path (optional)
     * @param int $fileSize File size in bytes (optional)
     * @param string $contentHash File content hash (optional)
     * @return int Report ID
     */
    public function storePdfReport($sessionId, $feedbackId, $filename, $filePath = null, 
                                 $fileSize = null, $contentHash = null)
    {
        $sql = "INSERT INTO pdf_reports (session_id, feedback_id, filename, file_path, file_size, content_hash) 
                VALUES (?, ?, ?, ?, ?, ?)";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([$sessionId, $feedbackId, $filename, $filePath, $fileSize, $contentHash]);
            return $this->pdo->lastInsertId();
        } catch (PDOException $e) {
            throw new Exception("Failed to store PDF report: " . $e->getMessage());
        }
    }
    
    /**
     * Update PDF download tracking
     * 
     * @param int $reportId Report ID
     * @return bool Success status
     */
    public function trackPdfDownload($reportId)
    {
        $sql = "UPDATE pdf_reports 
                SET downloaded_at = CURRENT_TIMESTAMP, download_count = download_count + 1 
                WHERE report_id = ?";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            return $stmt->execute([$reportId]);
        } catch (PDOException $e) {
            throw new Exception("Failed to track PDF download: " . $e->getMessage());
        }
    }
    
    /**
     * Get PDF reports for a session
     * 
     * @param string $sessionId Session ID
     * @return array Array of PDF report data
     */
    public function getPdfReports($sessionId)
    {
        $sql = "SELECT * FROM pdf_reports WHERE session_id = ? ORDER BY generated_at DESC";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([$sessionId]);
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            throw new Exception("Failed to get PDF reports: " . $e->getMessage());
        }
    }
    
    /**
     * Log activity with structured data
     * 
     * @param string $sessionId Session ID (optional)
     * @param string $logLevel Log level
     * @param string $eventType Event type
     * @param string $message Log message
     * @param array $context Context data (will be JSON encoded)
     * @return int Log ID
     */
    public function logActivity($sessionId, $logLevel, $eventType, $message, $context = [])
    {
        $sql = "INSERT INTO activity_log (session_id, log_level, event_type, message, context, user_agent, ip_address) 
                VALUES (?, ?, ?, ?, ?, ?, ?)";
        
        $userAgent = $_SERVER['HTTP_USER_AGENT'] ?? null;
        $ipAddress = $this->getClientIpAddress();
        $contextJson = !empty($context) ? json_encode($context) : null;
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([$sessionId, $logLevel, $eventType, $message, $contextJson, $userAgent, $ipAddress]);
            return $this->pdo->lastInsertId();
        } catch (PDOException $e) {
            throw new Exception("Failed to log activity: " . $e->getMessage());
        }
    }
    
    /**
     * Get client IP address with proxy support
     * 
     * @return string Client IP address
     */
    private function getClientIpAddress()
    {
        $ipKeys = ['HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP', 'HTTP_CLIENT_IP', 'REMOTE_ADDR'];
        
        foreach ($ipKeys as $key) {
            if (!empty($_SERVER[$key])) {
                $ip = trim(explode(',', $_SERVER[$key])[0]);
                if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE)) {
                    return $ip;
                }
            }
        }
        
        return $_SERVER['REMOTE_ADDR'] ?? 'Unknown';
    }
    
    /**
     * Store performance metric
     * 
     * @param string $sessionId Session ID
     * @param string $metricName Metric name
     * @param float $metricValue Metric value
     * @param array $metricData Additional metric data
     * @return int Metric ID
     */
    public function storePerformanceMetric($sessionId, $metricName, $metricValue, $metricData = [])
    {
        $sql = "INSERT INTO performance_metrics (session_id, metric_name, metric_value, metric_data) 
                VALUES (?, ?, ?, ?)";
        
        $metricDataJson = !empty($metricData) ? json_encode($metricData) : null;
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([$sessionId, $metricName, $metricValue, $metricDataJson]);
            return $this->pdo->lastInsertId();
        } catch (PDOException $e) {
            throw new Exception("Failed to store performance metric: " . $e->getMessage());
        }
    }
    
    /**
     * Get session summary with statistics
     * 
     * @param string $sessionId Session ID
     * @return array Session summary data
     */
    public function getSessionSummary($sessionId)
    {
        $sql = "SELECT * FROM session_summary WHERE session_id = ?";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([$sessionId]);
            return $stmt->fetch();
        } catch (PDOException $e) {
            throw new Exception("Failed to get session summary: " . $e->getMessage());
        }
    }
    
    /**
     * Get student performance history
     * 
     * @param string $studentName Student name
     * @param string $sessionType Session type (optional)
     * @param int $limit Maximum number of records
     * @return array Student performance data
     */
    public function getStudentPerformance($studentName, $sessionType = null, $limit = 50)
    {
        $sql = "SELECT * FROM student_performance WHERE student_name = ?";
        $params = [$studentName];
        
        if ($sessionType) {
            $sql .= " AND session_type = ?";
            $params[] = $sessionType;
        }
        
        $sql .= " ORDER BY latest_assessment DESC LIMIT ?";
        $params[] = $limit;
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute($params);
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            throw new Exception("Failed to get student performance: " . $e->getMessage());
        }
    }
    
    /**
     * Get log statistics
     * 
     * @param string $sessionId Optional session ID filter
     * @return array Log statistics
     */
    public function getLogStatistics($sessionId = null)
    {
        $sql = "SELECT 
                    log_level,
                    event_type,
                    COUNT(*) as count,
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest
                FROM activity_log";
        $params = [];
        
        if ($sessionId) {
            $sql .= " WHERE session_id = ?";
            $params[] = $sessionId;
        }
        
        $sql .= " GROUP BY log_level, event_type ORDER BY count DESC";
        
        try {
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute($params);
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            throw new Exception("Failed to get log statistics: " . $e->getMessage());
        }
    }
    
    /**
     * Clean up old data based on retention policies
     * 
     * @param int $daysToKeep Number of days to keep data
     * @return array Cleanup statistics
     */
    public function cleanupOldData($daysToKeep = 90)
    {
        $cutoffDate = date('Y-m-d H:i:s', strtotime("-$daysToKeep days"));
        $stats = [];
        
        try {
            $this->pdo->beginTransaction();
            
            // Clean up old activity logs
            $stmt = $this->pdo->prepare("DELETE FROM activity_log WHERE timestamp < ?");
            $stmt->execute([$cutoffDate]);
            $stats['activity_logs_deleted'] = $stmt->rowCount();
            
            // Clean up old performance metrics
            $stmt = $this->pdo->prepare("DELETE FROM performance_metrics WHERE recorded_at < ?");
            $stmt->execute([$cutoffDate]);
            $stats['performance_metrics_deleted'] = $stmt->rowCount();
            
            // Clean up old PDF reports (metadata only, not files)
            $stmt = $this->pdo->prepare("DELETE FROM pdf_reports WHERE generated_at < ?");
            $stmt->execute([$cutoffDate]);
            $stats['pdf_reports_deleted'] = $stmt->rowCount();
            
            // Clean up completed sessions older than retention period
            $stmt = $this->pdo->prepare("DELETE FROM sessions WHERE status = 'completed' AND completed_at < ?");
            $stmt->execute([$cutoffDate]);
            $stats['old_sessions_deleted'] = $stmt->rowCount();
            
            $this->pdo->commit();
            $stats['cleanup_completed'] = true;
            
        } catch (Exception $e) {
            $this->pdo->rollback();
            $stats['cleanup_completed'] = false;
            $stats['error'] = $e->getMessage();
        }
        
        return $stats;
    }
    
    /**
     * Get database health statistics
     * 
     * @return array Database health metrics
     */
    public function getDatabaseHealth()
    {
        $health = [];
        
        try {
            // Table row counts
            $tables = ['sessions', 'messages', 'feedback', 'pdf_reports', 'activity_log', 'performance_metrics'];
            foreach ($tables as $table) {
                $stmt = $this->pdo->query("SELECT COUNT(*) as count FROM $table");
                $health["${table}_count"] = $stmt->fetch()['count'];
            }
            
            // Disk usage (if available)
            $stmt = $this->pdo->query("SELECT 
                SUM(data_length + index_length) as total_size,
                SUM(data_length) as data_size,
                SUM(index_length) as index_size
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()");
            $sizeInfo = $stmt->fetch();
            
            $health['total_size_bytes'] = $sizeInfo['total_size'];
            $health['data_size_bytes'] = $sizeInfo['data_size'];
            $health['index_size_bytes'] = $sizeInfo['index_size'];
            
            // Recent activity
            $stmt = $this->pdo->query("SELECT COUNT(*) as recent_activity FROM activity_log WHERE timestamp > DATE_SUB(NOW(), INTERVAL 24 HOUR)");
            $health['recent_activity_24h'] = $stmt->fetch()['recent_activity'];
            
            $health['status'] = 'healthy';
            
        } catch (Exception $e) {
            $health['status'] = 'error';
            $health['error'] = $e->getMessage();
        }
        
        return $health;
    }
    
    /**
     * Run self-test to verify database functionality
     * 
     * @return array Test results
     */
    public function runSelfTest()
    {
        $results = [];
        $testSessionId = 'test_session_' . uniqid();
        
        try {
            // Test session creation
            $this->createSession($testSessionId, 'Test Student', 'HPV', 'Test Persona');
            $results['session_creation'] = 'PASS';
            
            // Test message storage
            $messageId = $this->storeMessage($testSessionId, 'user', 'Test message', 1);
            $results['message_storage'] = ($messageId > 0) ? 'PASS' : 'FAIL';
            
            // Test conversation retrieval
            $messages = $this->getConversationHistory($testSessionId);
            $results['conversation_retrieval'] = (count($messages) === 1) ? 'PASS' : 'FAIL';
            
            // Test feedback storage
            $testComponents = [
                ['component' => 'COLLABORATION', 'score' => 7.5, 'status' => 'Met', 'feedback' => 'Test feedback']
            ];
            $feedbackId = $this->storeFeedback($testSessionId, 'Test Student', 'HPV', $testComponents, 7.5, 25.0, 'Test raw feedback');
            $results['feedback_storage'] = ($feedbackId > 0) ? 'PASS' : 'FAIL';
            
            // Test PDF report storage
            $reportId = $this->storePdfReport($testSessionId, $feedbackId, 'test_report.pdf');
            $results['pdf_storage'] = ($reportId > 0) ? 'PASS' : 'FAIL';
            
            // Test activity logging
            $logId = $this->logActivity($testSessionId, 'INFO', 'test', 'Test log message', ['test' => true]);
            $results['activity_logging'] = ($logId > 0) ? 'PASS' : 'FAIL';
            
            // Test session update
            $this->updateSessionStatus($testSessionId, 'completed');
            $session = $this->getSession($testSessionId);
            $results['session_update'] = ($session['status'] === 'completed') ? 'PASS' : 'FAIL';
            
            // Clean up test data
            $this->pdo->prepare("DELETE FROM sessions WHERE session_id = ?")->execute([$testSessionId]);
            
            $results['overall'] = 'PASS';
            
        } catch (Exception $e) {
            $results['overall'] = 'FAIL';
            $results['error'] = $e->getMessage();
            
            // Clean up any partial test data
            try {
                $this->pdo->prepare("DELETE FROM sessions WHERE session_id = ?")->execute([$testSessionId]);
            } catch (Exception $cleanupError) {
                // Ignore cleanup errors
            }
        }
        
        return $results;
    }
}

// Example usage and testing
if (basename(__FILE__) === basename($_SERVER['PHP_SELF'])) {
    echo "SessionStorage requires database configuration.\n";
    echo "Example configuration:\n\n";
    
    $exampleConfig = [
        'host' => 'localhost',
        'dbname' => 'mi_chatbots',
        'username' => 'your_username',
        'password' => 'your_password',
        'charset' => 'utf8mb4'
    ];
    
    echo "<?php\n";
    echo '$dbConfig = ' . var_export($exampleConfig, true) . ";\n";
    echo '$storage = new SessionStorage($dbConfig);' . "\n\n";
    echo "// Run self-test\n";
    echo '$results = $storage->runSelfTest();' . "\n";
    echo "print_r(\$results);\n";
    echo "?>\n\n";
    
    echo "Make sure to:\n";
    echo "1. Import the database schema: mysql -u username -p dbname < database/mi_sessions.sql\n";
    echo "2. Configure database credentials\n";
    echo "3. Ensure proper database permissions\n";
}
?>