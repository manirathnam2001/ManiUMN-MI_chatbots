<?php
/**
 * Logger.php - Logging utility for MI chatbot feedback and PDF events
 * 
 * LAMP-stack compatible logging system for Motivational Interviewing chatbots
 * Provides structured logging for feedback generation, PDF creation, and system events
 * Integrates with MySQL database for persistent logging and debugging
 * 
 * @package MIUtils
 * @version 1.0
 * @author MI Assessment System
 */

require_once __DIR__ . '/SessionStorage.php';

class Logger {
    
    // Log levels (compatible with Python logging levels)
    const DEBUG = 'DEBUG';
    const INFO = 'INFO';
    const WARNING = 'WARNING';
    const ERROR = 'ERROR';
    const CRITICAL = 'CRITICAL';
    
    // Event types for structured logging
    const EVENT_SESSION_START = 'session_start';
    const EVENT_SESSION_END = 'session_end';
    const EVENT_MESSAGE_SENT = 'message_sent';
    const EVENT_MESSAGE_RECEIVED = 'message_received';
    const EVENT_FEEDBACK_GENERATED = 'feedback_generated';
    const EVENT_FEEDBACK_DISPLAYED = 'feedback_displayed';
    const EVENT_PDF_REQUESTED = 'pdf_requested';
    const EVENT_PDF_GENERATED = 'pdf_generated';
    const EVENT_PDF_DOWNLOADED = 'pdf_downloaded';
    const EVENT_ERROR_OCCURRED = 'error_occurred';
    const EVENT_VALIDATION_FAILED = 'validation_failed';
    const EVENT_SCORE_CALCULATED = 'score_calculated';
    
    private $storage;
    private $logToFile;
    private $logFile;
    private $minLogLevel;
    
    // Log level priorities for filtering
    private static $logLevels = [
        self::DEBUG => 0,
        self::INFO => 1,
        self::WARNING => 2,
        self::ERROR => 3,
        self::CRITICAL => 4
    ];
    
    /**
     * Initialize logger
     * 
     * @param SessionStorage|null $storage Database storage instance
     * @param bool $logToFile Whether to also log to file
     * @param string|null $logFile Path to log file (default: logs/mi_system.log)
     * @param string $minLogLevel Minimum log level to record
     */
    public function __construct($storage = null, $logToFile = true, $logFile = null, $minLogLevel = self::INFO) {
        $this->storage = $storage;
        $this->logToFile = $logToFile;
        $this->minLogLevel = $minLogLevel;
        
        if ($logToFile) {
            if ($logFile === null) {
                // Create logs directory if it doesn't exist
                $logDir = dirname(__FILE__) . '/../../logs';
                if (!is_dir($logDir)) {
                    mkdir($logDir, 0755, true);
                }
                $this->logFile = $logDir . '/mi_system.log';
            } else {
                $this->logFile = $logFile;
            }
        }
    }
    
    /**
     * Log a message with specified level
     * 
     * @param string $level Log level
     * @param string $eventType Event type identifier
     * @param string $message Log message
     * @param array $context Additional context data
     * @param string|null $sessionId Session ID if applicable
     */
    public function log($level, $eventType, $message, $context = [], $sessionId = null) {
        // Check if this log level should be recorded
        if (!$this->shouldLog($level)) {
            return;
        }
        
        $timestamp = date('Y-m-d H:i:s');
        $contextJson = !empty($context) ? json_encode($context, JSON_UNESCAPED_UNICODE) : null;
        
        // Get client information
        $ipAddress = $this->getClientIP();
        $userAgent = $_SERVER['HTTP_USER_AGENT'] ?? null;
        
        // Log to database if storage is available
        if ($this->storage) {
            try {
                $this->storage->logActivity(
                    $sessionId,
                    $level,
                    $eventType,
                    $message,
                    $contextJson,
                    $ipAddress,
                    $userAgent
                );
            } catch (Exception $e) {
                // Fallback to file logging if database fails
                $this->logToFileSystem($timestamp, $level, $eventType, $message, $context, $sessionId, 
                    "DB Error: " . $e->getMessage());
            }
        }
        
        // Log to file system if enabled
        if ($this->logToFile) {
            $this->logToFileSystem($timestamp, $level, $eventType, $message, $context, $sessionId);
        }
    }
    
    /**
     * Log debug message
     */
    public function debug($eventType, $message, $context = [], $sessionId = null) {
        $this->log(self::DEBUG, $eventType, $message, $context, $sessionId);
    }
    
    /**
     * Log info message
     */
    public function info($eventType, $message, $context = [], $sessionId = null) {
        $this->log(self::INFO, $eventType, $message, $context, $sessionId);
    }
    
    /**
     * Log warning message
     */
    public function warning($eventType, $message, $context = [], $sessionId = null) {
        $this->log(self::WARNING, $eventType, $message, $context, $sessionId);
    }
    
    /**
     * Log error message
     */
    public function error($eventType, $message, $context = [], $sessionId = null) {
        $this->log(self::ERROR, $eventType, $message, $context, $sessionId);
    }
    
    /**
     * Log critical message
     */
    public function critical($eventType, $message, $context = [], $sessionId = null) {
        $this->log(self::CRITICAL, $eventType, $message, $context, $sessionId);
    }
    
    /**
     * Log session start event
     */
    public function logSessionStart($sessionId, $studentName, $sessionType, $context = []) {
        $message = "Session started for student: $studentName, type: $sessionType";
        $context['student_name'] = $studentName;
        $context['session_type'] = $sessionType;
        $this->info(self::EVENT_SESSION_START, $message, $context, $sessionId);
    }
    
    /**
     * Log session end event
     */
    public function logSessionEnd($sessionId, $messageCount = 0, $context = []) {
        $message = "Session ended with $messageCount messages";
        $context['message_count'] = $messageCount;
        $this->info(self::EVENT_SESSION_END, $message, $context, $sessionId);
    }
    
    /**
     * Log message sent/received
     */
    public function logMessage($sessionId, $role, $contentLength, $context = []) {
        $eventType = ($role === 'user') ? self::EVENT_MESSAGE_SENT : self::EVENT_MESSAGE_RECEIVED;
        $message = "Message $role: {$contentLength} characters";
        $context['role'] = $role;
        $context['content_length'] = $contentLength;
        $this->debug($eventType, $message, $context, $sessionId);
    }
    
    /**
     * Log feedback generation event
     */
    public function logFeedbackGenerated($sessionId, $studentName, $sessionType, $totalScore, $percentage, $context = []) {
        $message = "Feedback generated for $studentName: $totalScore/30 ($percentage%)";
        $context['student_name'] = $studentName;
        $context['session_type'] = $sessionType;
        $context['total_score'] = $totalScore;
        $context['percentage'] = $percentage;
        $this->info(self::EVENT_FEEDBACK_GENERATED, $message, $context, $sessionId);
    }
    
    /**
     * Log PDF generation event
     */
    public function logPdfGenerated($sessionId, $studentName, $filename, $fileSize = null, $context = []) {
        $message = "PDF generated for $studentName: $filename";
        if ($fileSize) {
            $message .= " (" . $this->formatBytes($fileSize) . ")";
        }
        $context['student_name'] = $studentName;
        $context['filename'] = $filename;
        $context['file_size'] = $fileSize;
        $this->info(self::EVENT_PDF_GENERATED, $message, $context, $sessionId);
    }
    
    /**
     * Log PDF download event
     */
    public function logPdfDownloaded($sessionId, $studentName, $filename, $context = []) {
        $message = "PDF downloaded by $studentName: $filename";
        $context['student_name'] = $studentName;
        $context['filename'] = $filename;
        $this->info(self::EVENT_PDF_DOWNLOADED, $message, $context, $sessionId);
    }
    
    /**
     * Log error with exception details
     */
    public function logException($sessionId, Exception $exception, $context = []) {
        $message = "Exception occurred: " . $exception->getMessage();
        $context['exception_class'] = get_class($exception);
        $context['exception_code'] = $exception->getCode();
        $context['exception_file'] = $exception->getFile();
        $context['exception_line'] = $exception->getLine();
        $context['exception_trace'] = $exception->getTraceAsString();
        $this->error(self::EVENT_ERROR_OCCURRED, $message, $context, $sessionId);
    }
    
    /**
     * Log validation failure
     */
    public function logValidationFailure($sessionId, $validationType, $errors, $context = []) {
        $message = "Validation failed for $validationType: " . implode(', ', $errors);
        $context['validation_type'] = $validationType;
        $context['validation_errors'] = $errors;
        $this->warning(self::EVENT_VALIDATION_FAILED, $message, $context, $sessionId);
    }
    
    /**
     * Log score calculation event
     */
    public function logScoreCalculated($sessionId, $componentScores, $totalScore, $context = []) {
        $message = "Scores calculated: Total $totalScore/30";
        $context['component_scores'] = $componentScores;
        $context['total_score'] = $totalScore;
        $this->debug(self::EVENT_SCORE_CALCULATED, $message, $context, $sessionId);
    }
    
    /**
     * Check if a log level should be recorded
     */
    private function shouldLog($level) {
        return self::$logLevels[$level] >= self::$logLevels[$this->minLogLevel];
    }
    
    /**
     * Log to file system
     */
    private function logToFileSystem($timestamp, $level, $eventType, $message, $context, $sessionId, $error = null) {
        if (!$this->logFile) return;
        
        $logEntry = [
            'timestamp' => $timestamp,
            'level' => $level,
            'session_id' => $sessionId,
            'event_type' => $eventType,
            'message' => $message
        ];
        
        if (!empty($context)) {
            $logEntry['context'] = $context;
        }
        
        if ($error) {
            $logEntry['error'] = $error;
        }
        
        $logLine = json_encode($logEntry, JSON_UNESCAPED_UNICODE) . "\n";
        
        // Ensure log directory exists
        $logDir = dirname($this->logFile);
        if (!is_dir($logDir)) {
            mkdir($logDir, 0755, true);
        }
        
        // Write to log file with lock
        file_put_contents($this->logFile, $logLine, FILE_APPEND | LOCK_EX);
    }
    
    /**
     * Get client IP address
     */
    private function getClientIP() {
        $ipKeys = ['HTTP_CLIENT_IP', 'HTTP_X_FORWARDED_FOR', 'HTTP_X_FORWARDED', 
                  'HTTP_FORWARDED_FOR', 'HTTP_FORWARDED', 'REMOTE_ADDR'];
        
        foreach ($ipKeys as $key) {
            if (array_key_exists($key, $_SERVER) === true) {
                foreach (explode(',', $_SERVER[$key]) as $ip) {
                    $ip = trim($ip);
                    if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE)) {
                        return $ip;
                    }
                }
            }
        }
        
        return $_SERVER['REMOTE_ADDR'] ?? null;
    }
    
    /**
     * Format bytes for human readable display
     */
    private function formatBytes($bytes, $precision = 2) {
        $units = ['B', 'KB', 'MB', 'GB', 'TB'];
        
        for ($i = 0; $bytes > 1024; $i++) {
            $bytes /= 1024;
        }
        
        return round($bytes, $precision) . ' ' . $units[$i];
    }
    
    /**
     * Get recent logs for debugging
     * 
     * @param string|null $sessionId Filter by session ID
     * @param string|null $level Filter by log level
     * @param int $limit Number of logs to retrieve
     * @return array Recent log entries
     */
    public function getRecentLogs($sessionId = null, $level = null, $limit = 100) {
        if (!$this->storage) {
            return [];
        }
        
        try {
            return $this->storage->getActivityLogs($sessionId, $level, null, $limit);
        } catch (Exception $e) {
            $this->error(self::EVENT_ERROR_OCCURRED, "Failed to retrieve logs: " . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Clear old logs (cleanup utility)
     * 
     * @param int $daysOld Remove logs older than this many days
     * @return int Number of logs removed
     */
    public function clearOldLogs($daysOld = 30) {
        if (!$this->storage) {
            return 0;
        }
        
        try {
            $cutoffDate = date('Y-m-d H:i:s', strtotime("-$daysOld days"));
            $removed = $this->storage->clearOldActivityLogs($cutoffDate);
            $this->info('log_cleanup', "Cleared $removed old log entries (older than $daysOld days)");
            return $removed;
        } catch (Exception $e) {
            $this->error(self::EVENT_ERROR_OCCURRED, "Failed to clear old logs: " . $e->getMessage());
            return 0;
        }
    }
}

// Example usage and testing functions (can be removed in production)
if (basename(__FILE__) == basename($_SERVER["SCRIPT_FILENAME"])) {
    // Simple test when file is run directly
    echo "=== Logger PHP Test ===\n";
    
    try {
        // Test basic logging (file only, no database)
        $logger = new Logger(null, true, '/tmp/mi_test.log', Logger::DEBUG);
        
        // Test different log levels
        $logger->debug('test_event', 'This is a debug message', ['test' => true]);
        $logger->info('test_event', 'This is an info message', ['test' => true]);
        $logger->warning('test_event', 'This is a warning message', ['test' => true]);
        $logger->error('test_event', 'This is an error message', ['test' => true]);
        
        // Test specific event logging
        $logger->logSessionStart('test_session_001', 'John Doe', 'HPV');
        $logger->logMessage('test_session_001', 'user', 45);
        $logger->logFeedbackGenerated('test_session_001', 'John Doe', 'HPV', 22.5, 75.0);
        $logger->logPdfGenerated('test_session_001', 'John Doe', 'HPV_Report_John_Doe.pdf', 150000);
        $logger->logSessionEnd('test_session_001', 8);
        
        echo "✓ All logging tests completed\n";
        echo "✓ Log file created at: /tmp/mi_test.log\n";
        
        // Show log file contents
        if (file_exists('/tmp/mi_test.log')) {
            echo "\n--- Log File Contents ---\n";
            echo file_get_contents('/tmp/mi_test.log');
        }
        
    } catch (Exception $e) {
        echo "✗ Test error: " . $e->getMessage() . "\n";
    }
}
?>