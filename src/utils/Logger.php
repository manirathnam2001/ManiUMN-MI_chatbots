<?php
/**
 * Logger.php
 * 
 * LAMP-compatible logging utility for MI chatbot system operations including
 * feedback logging, PDF export tracking, error handling, and system monitoring.
 * 
 * This class provides comprehensive logging functionality for debugging,
 * monitoring, and audit trail purposes.
 * 
 * PHP Version: 7.4+
 * Dependencies: PDO (for database logging), optional file system access
 * 
 * @package MIChatbots
 * @author MI Chatbots System
 * @version 1.0.0
 * @since 2024
 */

namespace MIChatbots\Utils;

/**
 * Class Logger
 * Comprehensive logging utility for MI chatbot operations
 */
class Logger {
    
    // Log levels
    const DEBUG = 'DEBUG';
    const INFO = 'INFO';
    const WARNING = 'WARNING';
    const ERROR = 'ERROR';
    const CRITICAL = 'CRITICAL';
    
    // Log categories
    const CATEGORY_FEEDBACK = 'FEEDBACK';
    const CATEGORY_PDF_GENERATION = 'PDF_GENERATION';
    const CATEGORY_DATABASE = 'DATABASE';
    const CATEGORY_SESSION = 'SESSION';
    const CATEGORY_AUTHENTICATION = 'AUTHENTICATION';
    const CATEGORY_VALIDATION = 'VALIDATION';
    const CATEGORY_SYSTEM = 'SYSTEM';
    const CATEGORY_PERFORMANCE = 'PERFORMANCE';
    
    private $pdo;
    private $logFilePath;
    private $logToDatabase;
    private $logToFile;
    private $logLevel;
    private $contextData;
    
    /**
     * Constructor
     * 
     * @param PDO|null $pdo Database connection for database logging
     * @param string|null $logFilePath File path for file logging
     * @param bool $logToDatabase Enable database logging
     * @param bool $logToFile Enable file logging
     * @param string $logLevel Minimum log level to record
     */
    public function __construct(
        $pdo = null, 
        $logFilePath = null, 
        $logToDatabase = true, 
        $logToFile = true,
        $logLevel = self::INFO
    ) {
        $this->pdo = $pdo;
        $this->logFilePath = $logFilePath ?: $this->getDefaultLogPath();
        $this->logToDatabase = $logToDatabase && ($pdo !== null);
        $this->logToFile = $logToFile;
        $this->logLevel = $logLevel;
        $this->contextData = $this->gatherContextData();
        
        // Ensure log directory exists
        if ($this->logToFile) {
            $this->ensureLogDirectoryExists();
        }
    }
    
    /**
     * Log a feedback processing event
     * 
     * @param string $sessionId Session identifier
     * @param string $studentName Student name
     * @param array $scoreBreakdown Feedback score breakdown
     * @param string $evaluator Evaluator name
     * @param string $level Log level
     */
    public function logFeedbackProcessing($sessionId, $studentName, $scoreBreakdown, $evaluator, $level = self::INFO) {
        $message = "Feedback processed for student: {$studentName}";
        $context = [
            'session_id' => $sessionId,
            'student_name' => $studentName,
            'total_score' => $scoreBreakdown['total_score'] ?? null,
            'percentage' => $scoreBreakdown['percentage'] ?? null,
            'evaluator' => $evaluator,
            'components' => $scoreBreakdown['components'] ?? []
        ];
        
        $this->log($level, self::CATEGORY_FEEDBACK, $message, $context, $sessionId);
    }
    
    /**
     * Log a PDF generation event
     * 
     * @param string $sessionId Session identifier
     * @param string $filename Generated PDF filename
     * @param string $filePath File path (optional)
     * @param int $fileSize File size in bytes (optional)
     * @param float $generationTime Generation time in seconds (optional)
     * @param string $level Log level
     */
    public function logPdfGeneration($sessionId, $filename, $filePath = null, $fileSize = null, $generationTime = null, $level = self::INFO) {
        $message = "PDF generated: {$filename}";
        $context = [
            'session_id' => $sessionId,
            'filename' => $filename,
            'file_path' => $filePath,
            'file_size_bytes' => $fileSize,
            'generation_time_seconds' => $generationTime,
            'memory_usage_mb' => memory_get_peak_usage(true) / 1024 / 1024
        ];
        
        $this->log($level, self::CATEGORY_PDF_GENERATION, $message, $context, $sessionId);
    }
    
    /**
     * Log a PDF download event
     * 
     * @param string $sessionId Session identifier
     * @param string $filename Downloaded filename
     * @param string $userAgent User agent string
     * @param string $ipAddress Client IP address
     */
    public function logPdfDownload($sessionId, $filename, $userAgent = null, $ipAddress = null) {
        $message = "PDF downloaded: {$filename}";
        $context = [
            'session_id' => $sessionId,
            'filename' => $filename,
            'user_agent' => $userAgent ?: $_SERVER['HTTP_USER_AGENT'] ?? null,
            'ip_address' => $ipAddress ?: $this->getClientIpAddress(),
            'download_timestamp' => date('Y-m-d H:i:s')
        ];
        
        $this->log(self::INFO, self::CATEGORY_PDF_GENERATION, $message, $context, $sessionId);
    }
    
    /**
     * Log a session event
     * 
     * @param string $sessionId Session identifier
     * @param string $event Event type (START, COMPLETE, ABANDON, etc.)
     * @param string $studentName Student name
     * @param string $sessionType Session type (HPV, OHI)
     * @param array $additionalData Additional context data
     */
    public function logSessionEvent($sessionId, $event, $studentName, $sessionType, $additionalData = []) {
        $message = "Session {$event}: {$sessionId}";
        $context = array_merge([
            'session_id' => $sessionId,
            'event' => $event,
            'student_name' => $studentName,
            'session_type' => $sessionType,
            'timestamp' => date('Y-m-d H:i:s')
        ], $additionalData);
        
        $this->log(self::INFO, self::CATEGORY_SESSION, $message, $context, $sessionId);
    }
    
    /**
     * Log a database operation
     * 
     * @param string $operation Operation type (INSERT, UPDATE, DELETE, SELECT)
     * @param string $table Database table
     * @param string $sessionId Related session ID (optional)
     * @param array $data Operation data
     * @param string $level Log level
     */
    public function logDatabaseOperation($operation, $table, $sessionId = null, $data = [], $level = self::DEBUG) {
        $message = "Database {$operation} on {$table}";
        $context = [
            'operation' => $operation,
            'table' => $table,
            'session_id' => $sessionId,
            'data_keys' => array_keys($data),
            'record_count' => is_array($data) ? count($data) : 1
        ];
        
        $this->log($level, self::CATEGORY_DATABASE, $message, $context, $sessionId);
    }
    
    /**
     * Log an error event
     * 
     * @param string $message Error message
     * @param \Exception|\Throwable $exception Exception object (optional)
     * @param string $sessionId Related session ID (optional)
     * @param array $additionalContext Additional context data
     */
    public function logError($message, $exception = null, $sessionId = null, $additionalContext = []) {
        $context = $additionalContext;
        
        if ($exception) {
            $context['exception'] = [
                'message' => $exception->getMessage(),
                'code' => $exception->getCode(),
                'file' => $exception->getFile(),
                'line' => $exception->getLine(),
                'trace' => $exception->getTraceAsString()
            ];
        }
        
        $this->log(self::ERROR, self::CATEGORY_SYSTEM, $message, $context, $sessionId);
    }
    
    /**
     * Log a validation event
     * 
     * @param string $validationType Type of validation (student_name, feedback, etc.)
     * @param bool $isValid Whether validation passed
     * @param string $input Input that was validated
     * @param string $errorMessage Error message if validation failed
     * @param string $sessionId Related session ID (optional)
     */
    public function logValidation($validationType, $isValid, $input, $errorMessage = null, $sessionId = null) {
        $message = "Validation {$validationType}: " . ($isValid ? 'PASSED' : 'FAILED');
        $context = [
            'validation_type' => $validationType,
            'is_valid' => $isValid,
            'input_length' => strlen($input),
            'input_hash' => md5($input), // Don't log actual input for privacy
            'error_message' => $errorMessage
        ];
        
        $level = $isValid ? self::DEBUG : self::WARNING;
        $this->log($level, self::CATEGORY_VALIDATION, $message, $context, $sessionId);
    }
    
    /**
     * Log performance metrics
     * 
     * @param string $operation Operation name
     * @param float $executionTime Execution time in seconds
     * @param int $memoryUsage Memory usage in bytes
     * @param string $sessionId Related session ID (optional)
     * @param array $additionalMetrics Additional performance metrics
     */
    public function logPerformance($operation, $executionTime, $memoryUsage, $sessionId = null, $additionalMetrics = []) {
        $message = "Performance: {$operation}";
        $context = array_merge([
            'operation' => $operation,
            'execution_time_seconds' => $executionTime,
            'memory_usage_mb' => $memoryUsage / 1024 / 1024,
            'peak_memory_mb' => memory_get_peak_usage(true) / 1024 / 1024,
            'timestamp' => microtime(true)
        ], $additionalMetrics);
        
        $this->log(self::DEBUG, self::CATEGORY_PERFORMANCE, $message, $context, $sessionId);
    }
    
    /**
     * Core logging method
     * 
     * @param string $level Log level
     * @param string $category Log category
     * @param string $message Log message
     * @param array $context Context data
     * @param string|null $sessionId Session ID
     */
    public function log($level, $category, $message, $context = [], $sessionId = null) {
        // Check if we should log this level
        if (!$this->shouldLog($level)) {
            return;
        }
        
        $logEntry = $this->formatLogEntry($level, $category, $message, $context, $sessionId);
        
        // Log to database
        if ($this->logToDatabase) {
            $this->logToDatabase($level, $category, $message, $context, $sessionId);
        }
        
        // Log to file
        if ($this->logToFile) {
            $this->logToFile($logEntry);
        }
    }
    
    /**
     * Get recent log entries for a session
     * 
     * @param string $sessionId Session identifier
     * @param int $limit Number of entries to return
     * @param string|null $category Filter by category
     * @return array Log entries
     */
    public function getSessionLogs($sessionId, $limit = 50, $category = null) {
        if (!$this->pdo) {
            return [];
        }
        
        try {
            $sql = "SELECT * FROM system_logs WHERE session_id = :session_id";
            $params = ['session_id' => $sessionId];
            
            if ($category) {
                $sql .= " AND log_category = :category";
                $params['category'] = $category;
            }
            
            $sql .= " ORDER BY created_at DESC LIMIT :limit";
            
            $stmt = $this->pdo->prepare($sql);
            $stmt->bindValue(':limit', $limit, \PDO::PARAM_INT);
            
            foreach ($params as $key => $value) {
                $stmt->bindValue(":{$key}", $value);
            }
            
            $stmt->execute();
            return $stmt->fetchAll(\PDO::FETCH_ASSOC);
            
        } catch (\Exception $e) {
            error_log("Failed to retrieve session logs: " . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Get system statistics from logs
     * 
     * @param int $hours Number of hours to analyze (default: 24)
     * @return array System statistics
     */
    public function getSystemStats($hours = 24) {
        if (!$this->pdo) {
            return [];
        }
        
        try {
            $sql = "SELECT 
                        log_level,
                        log_category,
                        COUNT(*) as count,
                        AVG(CASE WHEN JSON_EXTRACT(context_data, '$.execution_time_seconds') IS NOT NULL 
                                 THEN JSON_EXTRACT(context_data, '$.execution_time_seconds') END) as avg_exec_time
                    FROM system_logs 
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL :hours HOUR)
                    GROUP BY log_level, log_category
                    ORDER BY count DESC";
            
            $stmt = $this->pdo->prepare($sql);
            $stmt->bindValue(':hours', $hours, \PDO::PARAM_INT);
            $stmt->execute();
            
            return $stmt->fetchAll(\PDO::FETCH_ASSOC);
            
        } catch (\Exception $e) {
            error_log("Failed to retrieve system stats: " . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Clean up old log entries
     * 
     * @param int $daysToKeep Number of days to keep logs
     * @return int Number of deleted entries
     */
    public function cleanupOldLogs($daysToKeep = 30) {
        if (!$this->pdo) {
            return 0;
        }
        
        try {
            $sql = "DELETE FROM system_logs 
                    WHERE created_at < DATE_SUB(NOW(), INTERVAL :days DAY)
                    AND log_level NOT IN ('ERROR', 'CRITICAL')";
            
            $stmt = $this->pdo->prepare($sql);
            $stmt->bindValue(':days', $daysToKeep, \PDO::PARAM_INT);
            $stmt->execute();
            
            $deletedCount = $stmt->rowCount();
            
            $this->log(self::INFO, self::CATEGORY_SYSTEM, 
                      "Cleaned up {$deletedCount} old log entries older than {$daysToKeep} days");
            
            return $deletedCount;
            
        } catch (\Exception $e) {
            $this->logError("Failed to cleanup old logs", $e);
            return 0;
        }
    }
    
    /**
     * Check if a log level should be recorded
     * 
     * @param string $level Log level to check
     * @return bool Whether to log this level
     */
    private function shouldLog($level) {
        $levels = [
            self::DEBUG => 0,
            self::INFO => 1,
            self::WARNING => 2,
            self::ERROR => 3,
            self::CRITICAL => 4
        ];
        
        return ($levels[$level] ?? 0) >= ($levels[$this->logLevel] ?? 1);
    }
    
    /**
     * Format log entry for file output
     * 
     * @param string $level Log level
     * @param string $category Log category
     * @param string $message Log message
     * @param array $context Context data
     * @param string|null $sessionId Session ID
     * @return string Formatted log entry
     */
    private function formatLogEntry($level, $category, $message, $context, $sessionId) {
        $timestamp = date('Y-m-d H:i:s');
        $contextJson = empty($context) ? '' : ' | Context: ' . json_encode($context);
        $sessionInfo = $sessionId ? " | Session: {$sessionId}" : '';
        
        return "[{$timestamp}] [{$level}] [{$category}]{$sessionInfo} {$message}{$contextJson}\n";
    }
    
    /**
     * Log entry to database
     * 
     * @param string $level Log level
     * @param string $category Log category
     * @param string $message Log message
     * @param array $context Context data
     * @param string|null $sessionId Session ID
     */
    private function logToDatabase($level, $category, $message, $context, $sessionId) {
        if (!$this->pdo) {
            return;
        }
        
        try {
            $sql = "INSERT INTO system_logs (session_id, log_level, log_category, message, context_data, user_id, ip_address) 
                    VALUES (:session_id, :log_level, :log_category, :message, :context_data, :user_id, :ip_address)";
            
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([
                'session_id' => $sessionId,
                'log_level' => $level,
                'log_category' => $category,
                'message' => $message,
                'context_data' => empty($context) ? null : json_encode($context),
                'user_id' => $this->contextData['user_id'] ?? null,
                'ip_address' => $this->contextData['ip_address']
            ]);
            
        } catch (\Exception $e) {
            // Fallback to file logging if database fails
            error_log("Database logging failed: " . $e->getMessage());
            $this->logToFile($this->formatLogEntry($level, $category, $message, $context, $sessionId));
        }
    }
    
    /**
     * Log entry to file
     * 
     * @param string $logEntry Formatted log entry
     */
    private function logToFile($logEntry) {
        if (!$this->logFilePath) {
            return;
        }
        
        try {
            file_put_contents($this->logFilePath, $logEntry, FILE_APPEND | LOCK_EX);
        } catch (\Exception $e) {
            error_log("File logging failed: " . $e->getMessage());
        }
    }
    
    /**
     * Get default log file path
     * 
     * @return string Default log file path
     */
    private function getDefaultLogPath() {
        $logDir = sys_get_temp_dir() . '/mi_chatbots_logs';
        return $logDir . '/mi_chatbots_' . date('Y-m-d') . '.log';
    }
    
    /**
     * Ensure log directory exists
     */
    private function ensureLogDirectoryExists() {
        $logDir = dirname($this->logFilePath);
        if (!is_dir($logDir)) {
            mkdir($logDir, 0755, true);
        }
    }
    
    /**
     * Gather contextual data for logging
     * 
     * @return array Context data
     */
    private function gatherContextData() {
        return [
            'user_id' => $_SESSION['user_id'] ?? null,
            'ip_address' => $this->getClientIpAddress(),
            'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? null,
            'request_uri' => $_SERVER['REQUEST_URI'] ?? null,
            'request_method' => $_SERVER['REQUEST_METHOD'] ?? null,
            'php_version' => PHP_VERSION,
            'memory_limit' => ini_get('memory_limit'),
            'max_execution_time' => ini_get('max_execution_time')
        ];
    }
    
    /**
     * Get client IP address with proxy support
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
 * Performance Logger
 * Utility class for measuring and logging performance metrics
 */
class PerformanceLogger {
    private $logger;
    private $startTimes = [];
    private $operations = [];
    
    public function __construct(Logger $logger) {
        $this->logger = $logger;
    }
    
    /**
     * Start timing an operation
     * 
     * @param string $operationName Name of the operation
     * @param string $sessionId Related session ID
     */
    public function startTiming($operationName, $sessionId = null) {
        $this->startTimes[$operationName] = microtime(true);
        $this->operations[$operationName] = [
            'session_id' => $sessionId,
            'start_memory' => memory_get_usage(true)
        ];
    }
    
    /**
     * End timing an operation and log the results
     * 
     * @param string $operationName Name of the operation
     * @param array $additionalMetrics Additional metrics to log
     */
    public function endTiming($operationName, $additionalMetrics = []) {
        if (!isset($this->startTimes[$operationName])) {
            return;
        }
        
        $endTime = microtime(true);
        $executionTime = $endTime - $this->startTimes[$operationName];
        $endMemory = memory_get_usage(true);
        $memoryUsed = $endMemory - $this->operations[$operationName]['start_memory'];
        $sessionId = $this->operations[$operationName]['session_id'];
        
        $this->logger->logPerformance(
            $operationName, 
            $executionTime, 
            $memoryUsed, 
            $sessionId, 
            $additionalMetrics
        );
        
        // Clean up
        unset($this->startTimes[$operationName]);
        unset($this->operations[$operationName]);
    }
    
    /**
     * Time a callable function/method
     * 
     * @param string $operationName Name of the operation
     * @param callable $callable Function to execute
     * @param string $sessionId Related session ID
     * @param array $additionalMetrics Additional metrics to log
     * @return mixed Result of the callable
     */
    public function timeOperation($operationName, callable $callable, $sessionId = null, $additionalMetrics = []) {
        $this->startTiming($operationName, $sessionId);
        
        try {
            $result = $callable();
            $this->endTiming($operationName, $additionalMetrics);
            return $result;
        } catch (\Exception $e) {
            $this->endTiming($operationName, array_merge($additionalMetrics, ['error' => $e->getMessage()]));
            throw $e;
        }
    }
}

/**
 * Example usage and testing functions
 */
class LoggerExample {
    
    /**
     * Demonstrate basic logging functionality
     */
    public static function demonstrateUsage() {
        echo "<h2>Logger Example Usage</h2>\n";
        
        // Create logger instance (file logging only for demo)
        $logger = new Logger(null, '/tmp/mi_demo.log', false, true, Logger::DEBUG);
        
        // Example session data
        $sessionId = 'demo_session_' . time();
        $studentName = 'Jane Doe';
        
        // Log session start
        $logger->logSessionEvent($sessionId, 'START', $studentName, 'HPV', [
            'persona' => 'Alex - Hesitant Patient',
            'user_agent' => 'Demo Browser'
        ]);
        
        // Log feedback processing
        $scoreBreakdown = [
            'total_score' => 22.5,
            'percentage' => 75.0,
            'components' => [
                'COLLABORATION' => ['score' => 7.5, 'status' => 'Met'],
                'EVOCATION' => ['score' => 5.0, 'status' => 'Partially Met']
            ]
        ];
        
        $logger->logFeedbackProcessing($sessionId, $studentName, $scoreBreakdown, 'AI Evaluator');
        
        // Log PDF generation
        $logger->logPdfGeneration($sessionId, 'demo_report.pdf', '/tmp/demo_report.pdf', 1024000, 2.5);
        
        // Log an error
        $logger->logError('Demonstration error', new \Exception('This is just a demo error'));
        
        // Log performance
        $performanceLogger = new PerformanceLogger($logger);
        $result = $performanceLogger->timeOperation('demo_operation', function() {
            usleep(100000); // Simulate 0.1 second operation
            return 'Operation completed';
        }, $sessionId);
        
        echo "<p>Logging demonstration completed. Check /tmp/mi_demo.log for output.</p>\n";
        echo "<p>Performance operation result: {$result}</p>\n";
        
        // Show log file contents if accessible
        if (file_exists('/tmp/mi_demo.log')) {
            echo "<h3>Log File Contents:</h3>\n";
            echo "<pre>" . htmlspecialchars(file_get_contents('/tmp/mi_demo.log')) . "</pre>\n";
        }
    }
}

// Uncomment the following line to run the example when this file is accessed directly
// if (basename(__FILE__) == basename($_SERVER['PHP_SELF'])) {
//     LoggerExample::demonstrateUsage();
// }

?>