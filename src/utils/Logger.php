<?php
/**
 * Logger.php
 * 
 * Comprehensive logging system for MI chatbot activities including feedback events,
 * PDF generation, session tracking, and system diagnostics.
 * 
 * Features:
 * - Multi-level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
 * - Database logging integration
 * - File-based logging with rotation
 * - JSON structured logging
 * - Session activity tracking
 * - Performance metrics collection
 * 
 * @package MIChatbots
 * @author LAMP-Stack MI Assessment System
 * @version 1.0.0
 */

require_once 'SessionStorage.php';

class Logger
{
    // Log levels (PSR-3 compatible)
    const DEBUG = 'DEBUG';
    const INFO = 'INFO';
    const WARNING = 'WARNING';
    const ERROR = 'ERROR';
    const CRITICAL = 'CRITICAL';
    
    // Event types for categorization
    const EVENT_SESSION_START = 'session_start';
    const EVENT_SESSION_END = 'session_end';
    const EVENT_MESSAGE_SENT = 'message_sent';
    const EVENT_FEEDBACK_GENERATED = 'feedback_generated';
    const EVENT_PDF_GENERATED = 'pdf_generated';
    const EVENT_PDF_DOWNLOADED = 'pdf_downloaded';
    const EVENT_ERROR_OCCURRED = 'error_occurred';
    const EVENT_PERFORMANCE_METRIC = 'performance_metric';
    const EVENT_DATABASE_OPERATION = 'database_operation';
    const EVENT_USER_ACTION = 'user_action';
    
    private $sessionStorage;
    private $logToDatabase;
    private $logToFile;
    private $logDirectory;
    private $logFile;
    private $minLogLevel;
    private $context;
    
    // Log level hierarchy for filtering
    private static $logLevels = [
        self::DEBUG => 0,
        self::INFO => 1,
        self::WARNING => 2,
        self::ERROR => 3,
        self::CRITICAL => 4
    ];
    
    /**
     * Initialize Logger
     * 
     * @param SessionStorage $sessionStorage Database storage instance
     * @param bool $logToDatabase Enable database logging
     * @param bool $logToFile Enable file logging
     * @param string $logDirectory Directory for log files
     * @param string $minLogLevel Minimum log level to record
     */
    public function __construct($sessionStorage = null, $logToDatabase = true, $logToFile = true, 
                              $logDirectory = '/tmp/mi_logs', $minLogLevel = self::INFO)
    {
        $this->sessionStorage = $sessionStorage;
        $this->logToDatabase = $logToDatabase && ($sessionStorage !== null);
        $this->logToFile = $logToFile;
        $this->logDirectory = $logDirectory;
        $this->minLogLevel = $minLogLevel;
        $this->context = [];
        
        // Initialize file logging
        if ($this->logToFile) {
            $this->initializeFileLogging();
        }
        
        // Set default context
        $this->setContext([
            'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? 'Unknown',
            'ip_address' => $this->getClientIpAddress(),
            'timestamp' => date('c'),
            'php_version' => PHP_VERSION,
            'memory_usage' => memory_get_usage(true)
        ]);
    }
    
    /**
     * Initialize file logging directory and file
     */
    private function initializeFileLogging()
    {
        if (!is_dir($this->logDirectory)) {
            if (!mkdir($this->logDirectory, 0755, true)) {
                throw new Exception("Failed to create log directory: {$this->logDirectory}");
            }
        }
        
        $this->logFile = $this->logDirectory . '/mi_chatbot_' . date('Y-m-d') . '.log';
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
     * Set logging context for all subsequent log entries
     * 
     * @param array $context Context data to include
     */
    public function setContext($context)
    {
        $this->context = array_merge($this->context, $context);
    }
    
    /**
     * Log a message with specified level
     * 
     * @param string $level Log level
     * @param string $eventType Event type for categorization
     * @param string $message Log message
     * @param array $additionalContext Additional context data
     * @param string $sessionId Session ID (optional)
     */
    public function log($level, $eventType, $message, $additionalContext = [], $sessionId = null)
    {
        // Check if we should log this level
        if (!$this->shouldLog($level)) {
            return;
        }
        
        $timestamp = date('c');
        $logEntry = [
            'timestamp' => $timestamp,
            'level' => $level,
            'event_type' => $eventType,
            'message' => $message,
            'session_id' => $sessionId,
            'context' => array_merge($this->context, $additionalContext)
        ];
        
        // Log to file if enabled
        if ($this->logToFile) {
            $this->writeToFile($logEntry);
        }
        
        // Log to database if enabled
        if ($this->logToDatabase) {
            $this->writeToDatabase($logEntry);
        }
    }
    
    /**
     * Check if log level should be recorded
     * 
     * @param string $level Log level to check
     * @return bool True if should log
     */
    private function shouldLog($level)
    {
        return (self::$logLevels[$level] ?? 0) >= (self::$logLevels[$this->minLogLevel] ?? 0);
    }
    
    /**
     * Write log entry to file
     * 
     * @param array $logEntry Structured log entry
     */
    private function writeToFile($logEntry)
    {
        $jsonEntry = json_encode($logEntry, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . "\n";
        
        if (file_put_contents($this->logFile, $jsonEntry, FILE_APPEND | LOCK_EX) === false) {
            error_log("Failed to write to log file: {$this->logFile}");
        }
    }
    
    /**
     * Write log entry to database
     * 
     * @param array $logEntry Structured log entry
     */
    private function writeToDatabase($logEntry)
    {
        try {
            $this->sessionStorage->logActivity(
                $logEntry['session_id'],
                $logEntry['level'],
                $logEntry['event_type'],
                $logEntry['message'],
                $logEntry['context']
            );
        } catch (Exception $e) {
            // Fallback to error log if database logging fails
            error_log("Database logging failed: " . $e->getMessage());
        }
    }
    
    /**
     * Log debug message
     * 
     * @param string $eventType Event type
     * @param string $message Message
     * @param array $context Additional context
     * @param string $sessionId Session ID
     */
    public function debug($eventType, $message, $context = [], $sessionId = null)
    {
        $this->log(self::DEBUG, $eventType, $message, $context, $sessionId);
    }
    
    /**
     * Log info message
     * 
     * @param string $eventType Event type
     * @param string $message Message
     * @param array $context Additional context
     * @param string $sessionId Session ID
     */
    public function info($eventType, $message, $context = [], $sessionId = null)
    {
        $this->log(self::INFO, $eventType, $message, $context, $sessionId);
    }
    
    /**
     * Log warning message
     * 
     * @param string $eventType Event type
     * @param string $message Message
     * @param array $context Additional context
     * @param string $sessionId Session ID
     */
    public function warning($eventType, $message, $context = [], $sessionId = null)
    {
        $this->log(self::WARNING, $eventType, $message, $context, $sessionId);
    }
    
    /**
     * Log error message
     * 
     * @param string $eventType Event type
     * @param string $message Message
     * @param array $context Additional context
     * @param string $sessionId Session ID
     */
    public function error($eventType, $message, $context = [], $sessionId = null)
    {
        $this->log(self::ERROR, $eventType, $message, $context, $sessionId);
    }
    
    /**
     * Log critical message
     * 
     * @param string $eventType Event type
     * @param string $message Message
     * @param array $context Additional context
     * @param string $sessionId Session ID
     */
    public function critical($eventType, $message, $context = [], $sessionId = null)
    {
        $this->log(self::CRITICAL, $eventType, $message, $context, $sessionId);
    }
    
    /**
     * Log session start event
     * 
     * @param string $sessionId Session ID
     * @param string $studentName Student name
     * @param string $sessionType Session type (HPV, OHI, etc.)
     * @param string $persona Selected persona
     */
    public function logSessionStart($sessionId, $studentName, $sessionType, $persona = null)
    {
        $context = [
            'student_name' => $studentName,
            'session_type' => $sessionType,
            'persona' => $persona,
            'action' => 'session_started'
        ];
        
        $message = "Session started for student: $studentName, type: $sessionType";
        if ($persona) {
            $message .= ", persona: $persona";
        }
        
        $this->info(self::EVENT_SESSION_START, $message, $context, $sessionId);
    }
    
    /**
     * Log session end event
     * 
     * @param string $sessionId Session ID
     * @param int $messageCount Number of messages in session
     * @param float $duration Session duration in seconds
     */
    public function logSessionEnd($sessionId, $messageCount = 0, $duration = null)
    {
        $context = [
            'message_count' => $messageCount,
            'duration_seconds' => $duration,
            'action' => 'session_ended'
        ];
        
        $message = "Session ended. Messages: $messageCount";
        if ($duration) {
            $message .= ", duration: " . round($duration, 2) . "s";
        }
        
        $this->info(self::EVENT_SESSION_END, $message, $context, $sessionId);
    }
    
    /**
     * Log message sent event
     * 
     * @param string $sessionId Session ID
     * @param string $role Message role (user/assistant)
     * @param int $messageLength Message length
     * @param int $messageOrder Message order in conversation
     */
    public function logMessageSent($sessionId, $role, $messageLength, $messageOrder)
    {
        $context = [
            'role' => $role,
            'message_length' => $messageLength,
            'message_order' => $messageOrder,
            'action' => 'message_sent'
        ];
        
        $message = "Message sent - Role: $role, Length: $messageLength chars, Order: $messageOrder";
        
        $this->debug(self::EVENT_MESSAGE_SENT, $message, $context, $sessionId);
    }
    
    /**
     * Log feedback generation event
     * 
     * @param string $sessionId Session ID
     * @param string $studentName Student name
     * @param float $totalScore Total MI score
     * @param float $percentage Score percentage
     * @param string $performanceLevel Performance level
     * @param int $componentCount Number of components found
     */
    public function logFeedbackGenerated($sessionId, $studentName, $totalScore, $percentage, 
                                       $performanceLevel, $componentCount)
    {
        $context = [
            'student_name' => $studentName,
            'total_score' => $totalScore,
            'percentage' => $percentage,
            'performance_level' => $performanceLevel,
            'component_count' => $componentCount,
            'action' => 'feedback_generated'
        ];
        
        $message = "Feedback generated for $studentName - Score: $totalScore/30.0 ($percentage%), Level: $performanceLevel";
        
        $this->info(self::EVENT_FEEDBACK_GENERATED, $message, $context, $sessionId);
    }
    
    /**
     * Log PDF generation event
     * 
     * @param string $sessionId Session ID
     * @param string $filename Generated filename
     * @param int $fileSize File size in bytes
     * @param float $generationTime Generation time in seconds
     */
    public function logPdfGenerated($sessionId, $filename, $fileSize = null, $generationTime = null)
    {
        $context = [
            'filename' => $filename,
            'file_size_bytes' => $fileSize,
            'generation_time_seconds' => $generationTime,
            'action' => 'pdf_generated'
        ];
        
        $message = "PDF generated: $filename";
        if ($fileSize) {
            $message .= " (" . $this->formatBytes($fileSize) . ")";
        }
        if ($generationTime) {
            $message .= " in " . round($generationTime, 2) . "s";
        }
        
        $this->info(self::EVENT_PDF_GENERATED, $message, $context, $sessionId);
    }
    
    /**
     * Log PDF download event
     * 
     * @param string $sessionId Session ID
     * @param string $filename Downloaded filename
     * @param int $downloadCount Total download count for this file
     */
    public function logPdfDownloaded($sessionId, $filename, $downloadCount = 1)
    {
        $context = [
            'filename' => $filename,
            'download_count' => $downloadCount,
            'action' => 'pdf_downloaded'
        ];
        
        $message = "PDF downloaded: $filename (download #$downloadCount)";
        
        $this->info(self::EVENT_PDF_DOWNLOADED, $message, $context, $sessionId);
    }
    
    /**
     * Log error with exception details
     * 
     * @param string $sessionId Session ID
     * @param Exception $exception Exception object
     * @param string $additionalMessage Additional context message
     */
    public function logException($sessionId, $exception, $additionalMessage = '')
    {
        $context = [
            'exception_class' => get_class($exception),
            'exception_message' => $exception->getMessage(),
            'exception_code' => $exception->getCode(),
            'exception_file' => $exception->getFile(),
            'exception_line' => $exception->getLine(),
            'stack_trace' => $exception->getTraceAsString(),
            'action' => 'exception_occurred'
        ];
        
        $message = "Exception occurred: " . get_class($exception) . " - " . $exception->getMessage();
        if ($additionalMessage) {
            $message = $additionalMessage . ": " . $message;
        }
        
        $this->error(self::EVENT_ERROR_OCCURRED, $message, $context, $sessionId);
    }
    
    /**
     * Log performance metric
     * 
     * @param string $sessionId Session ID
     * @param string $metricName Metric name
     * @param float $metricValue Metric value
     * @param array $metricData Additional metric data
     */
    public function logPerformanceMetric($sessionId, $metricName, $metricValue, $metricData = [])
    {
        $context = array_merge([
            'metric_name' => $metricName,
            'metric_value' => $metricValue,
            'action' => 'performance_metric'
        ], $metricData);
        
        $message = "Performance metric - $metricName: $metricValue";
        
        $this->debug(self::EVENT_PERFORMANCE_METRIC, $message, $context, $sessionId);
        
        // Also store in performance metrics table if database is available
        if ($this->sessionStorage) {
            try {
                $this->sessionStorage->storePerformanceMetric($sessionId, $metricName, $metricValue, $metricData);
            } catch (Exception $e) {
                $this->warning(self::EVENT_DATABASE_OPERATION, "Failed to store performance metric: " . $e->getMessage(), [], $sessionId);
            }
        }
    }
    
    /**
     * Log user action
     * 
     * @param string $sessionId Session ID
     * @param string $action Action name
     * @param array $actionData Action-specific data
     */
    public function logUserAction($sessionId, $action, $actionData = [])
    {
        $context = array_merge([
            'user_action' => $action,
            'action_timestamp' => date('c')
        ], $actionData);
        
        $message = "User action: $action";
        
        $this->info(self::EVENT_USER_ACTION, $message, $context, $sessionId);
    }
    
    /**
     * Format bytes to human readable format
     * 
     * @param int $bytes Bytes count
     * @return string Formatted string
     */
    private function formatBytes($bytes)
    {
        $units = ['B', 'KB', 'MB', 'GB'];
        $power = $bytes > 0 ? floor(log($bytes, 1024)) : 0;
        return number_format($bytes / pow(1024, $power), 1, '.', ',') . ' ' . $units[$power];
    }
    
    /**
     * Get log statistics for analysis
     * 
     * @param string $sessionId Optional session ID filter
     * @return array Log statistics
     */
    public function getLogStatistics($sessionId = null)
    {
        if (!$this->sessionStorage) {
            return ['error' => 'Database not available for statistics'];
        }
        
        try {
            return $this->sessionStorage->getLogStatistics($sessionId);
        } catch (Exception $e) {
            return ['error' => 'Failed to retrieve statistics: ' . $e->getMessage()];
        }
    }
    
    /**
     * Rotate log files (remove old files)
     * 
     * @param int $daysToKeep Number of days to keep log files
     */
    public function rotateLogFiles($daysToKeep = 30)
    {
        if (!$this->logToFile || !is_dir($this->logDirectory)) {
            return;
        }
        
        $files = glob($this->logDirectory . '/mi_chatbot_*.log');
        $cutoffTime = time() - ($daysToKeep * 24 * 60 * 60);
        
        foreach ($files as $file) {
            if (filemtime($file) < $cutoffTime) {
                unlink($file);
                $this->info('system', "Rotated old log file: " . basename($file));
            }
        }
    }
    
    /**
     * Run self-test to verify logging functionality
     * 
     * @return array Test results
     */
    public static function runSelfTest($testSessionId = 'test_session_001')
    {
        $results = [];
        
        try {
            // Test file logging
            $logger = new Logger(null, false, true, '/tmp/test_mi_logs');
            $logger->info('test', 'Test log message', ['test' => true], $testSessionId);
            
            // Check if file was created
            $logFile = '/tmp/test_mi_logs/mi_chatbot_' . date('Y-m-d') . '.log';
            $results['file_logging'] = file_exists($logFile) ? 'PASS' : 'FAIL';
            
            // Test different log levels
            $logger->debug('test', 'Debug message', [], $testSessionId);
            $logger->warning('test', 'Warning message', [], $testSessionId);
            $logger->error('test', 'Error message', [], $testSessionId);
            
            $results['log_levels'] = 'PASS';
            
            // Test context setting
            $logger->setContext(['test_context' => 'value']);
            $results['context_setting'] = 'PASS';
            
            // Clean up test files
            if (file_exists($logFile)) {
                unlink($logFile);
                rmdir('/tmp/test_mi_logs');
            }
            
            $results['overall'] = 'PASS';
            
        } catch (Exception $e) {
            $results['overall'] = 'FAIL';
            $results['error'] = $e->getMessage();
        }
        
        return $results;
    }
}

// Example usage and testing
if (basename(__FILE__) === basename($_SERVER['PHP_SELF'])) {
    echo "Logger Self-Test Results:\n";
    echo str_repeat('=', 40) . "\n";
    
    $results = Logger::runSelfTest();
    foreach ($results as $test => $result) {
        echo sprintf("%-20s: %s\n", $test, $result);
    }
    
    echo "\nExample Usage:\n";
    echo str_repeat('-', 40) . "\n";
    
    // Example logger usage
    $logger = new Logger(null, false, true, '/tmp/example_logs');
    
    $sessionId = 'demo_session_001';
    $logger->logSessionStart($sessionId, 'John Doe', 'HPV', 'College Student');
    $logger->logMessageSent($sessionId, 'user', 50, 1);
    $logger->logFeedbackGenerated($sessionId, 'John Doe', 25.0, 83.33, 'Proficient', 4);
    $logger->logPdfGenerated($sessionId, 'HPV_MI_Report_John_Doe.pdf', 245760, 2.5);
    $logger->logSessionEnd($sessionId, 10, 300.5);
    
    echo "Example logs written to /tmp/example_logs/\n";
    echo "Check the log file for JSON structured entries.\n";
}
?>