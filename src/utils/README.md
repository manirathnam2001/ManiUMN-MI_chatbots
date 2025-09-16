# MI Chatbots LAMP-Stack Utilities

This directory contains PHP utilities for implementing LAMP-stack compatible motivational interviewing (MI) chatbot functionality with MySQL integration. These utilities provide unified feedback processing, comprehensive logging, database storage, and professional PDF report generation.

## 📁 File Overview

- **`FeedbackUtils.php`** - Unified feedback processing and MI scoring system
- **`Logger.php`** - Comprehensive logging with file and database support  
- **`SessionStorage.php`** - Complete MySQL database operations for sessions, feedback, and PDFs
- **`PdfGenerator.php`** - Professional PDF report generation using Dompdf
- **`README.md`** - This documentation file
- **`example_integration.php`** - Complete working integration example

## 🎯 Features

### MI Assessment Compatibility
- **Same 30-point scoring system** as existing Python implementation
- **Four MI components**: COLLABORATION, EVOCATION, ACCEPTANCE, COMPASSION (7.5 points each)
- **Status levels**: Met (100%), Partially Met (50%), Not Met (0%)
- **Performance levels**: Excellent, Proficient, Developing, Beginning, Needs Improvement

### Security & Performance
- **SQL Injection Protection**: All database operations use prepared statements
- **Input Validation**: Comprehensive sanitization and validation
- **File Security**: PDF generator uses security restrictions
- **Database Optimization**: Proper indexing and foreign key relationships

### Production Ready
- **Error Handling**: Comprehensive exception handling throughout
- **Logging**: Structured JSON logging with multiple levels
- **Documentation**: Complete API reference and examples
- **Testing**: Self-test capabilities for all utilities

## 🚀 Quick Start

### 1. Database Setup

First, import the database schema:

```bash
mysql -u username -p database_name < ../database/mi_sessions.sql
```

### 2. Install Dependencies

Install Dompdf for PDF generation:

```bash
composer require dompdf/dompdf
```

### 3. Basic Usage Example

```php
<?php
// Include the utilities
require_once 'FeedbackUtils.php';
require_once 'Logger.php';
require_once 'SessionStorage.php';
require_once 'PdfGenerator.php';

// Database configuration
$dbConfig = [
    'host' => 'localhost',
    'dbname' => 'mi_chatbots',
    'username' => 'your_username',
    'password' => 'your_password',
    'charset' => 'utf8mb4'
];

// Initialize components
$storage = new SessionStorage($dbConfig);
$logger = new Logger($storage, true, true, '/path/to/logs');
$pdfGenerator = new PdfGenerator();

// Example MI assessment workflow
$sessionId = 'session_' . uniqid();
$studentName = 'John Doe';
$sessionType = 'HPV';
$persona = 'College Student - Sarah';

// Start session
$storage->createSession($sessionId, $studentName, $sessionType, $persona);
$logger->logSessionStart($sessionId, $studentName, $sessionType, $persona);

// Store conversation messages
$chatHistory = [
    ['role' => 'assistant', 'content' => 'Hi, I have questions about vaccines.'],
    ['role' => 'user', 'content' => 'I\'d be happy to help. What would you like to know?']
];

foreach ($chatHistory as $index => $message) {
    $messageId = $storage->storeMessage(
        $sessionId, 
        $message['role'], 
        $message['content'], 
        $index + 1
    );
    $logger->logMessageSent($sessionId, $message['role'], strlen($message['content']), $index + 1);
}

// AI-generated feedback (this would come from your AI system)
$feedbackText = "
1. COLLABORATION (7.5 pts): Met - Excellent rapport building and partnership approach.
2. EVOCATION (7.5 pts): Partially Met - Good exploration of motivations but could go deeper.
3. ACCEPTANCE (7.5 pts): Met - Strong respect for autonomy and reflective listening.
4. COMPASSION (7.5 pts): Met - Demonstrated warmth and non-judgmental approach.

Overall Performance: Strong MI techniques with room for improvement in evocation.
";

// Parse feedback and calculate scores
$scoreBreakdown = FeedbackUtils::getScoreBreakdown($feedbackText);

// Store feedback in database
$feedbackId = $storage->storeFeedback(
    $sessionId,
    $studentName,
    $sessionType,
    $scoreBreakdown['components'],
    $scoreBreakdown['total_score'],
    $scoreBreakdown['percentage'],
    $feedbackText,
    'AI Evaluator'
);

$logger->logFeedbackGenerated(
    $sessionId,
    $studentName,
    $scoreBreakdown['total_score'],
    $scoreBreakdown['percentage'],
    $scoreBreakdown['performance_level'],
    $scoreBreakdown['component_count']
);

// Generate PDF report
$pdfInfo = $pdfGenerator->generatePdfInfo($studentName, $feedbackText, $chatHistory, $sessionType, $persona);

// Store PDF metadata
$reportId = $storage->storePdfReport(
    $sessionId,
    $feedbackId,
    $pdfInfo['filename'],
    null, // file_path - you might want to save the actual file
    $pdfInfo['size'],
    $pdfInfo['hash']
);

$logger->logPdfGenerated($sessionId, $pdfInfo['filename'], $pdfInfo['size']);

// Complete session
$storage->updateSessionStatus($sessionId, 'completed');
$logger->logSessionEnd($sessionId, count($chatHistory));

echo "MI Assessment completed successfully!\n";
echo "Total Score: {$scoreBreakdown['total_score']}/30.0 ({$scoreBreakdown['percentage']}%)\n";
echo "Performance Level: {$scoreBreakdown['performance_level']}\n";
?>
```

## 📚 Detailed Usage

### FeedbackUtils.php

The `FeedbackUtils` class provides comprehensive feedback processing:

```php
// Parse AI-generated feedback text
$scoreBreakdown = FeedbackUtils::getScoreBreakdown($feedbackText);

// Individual component operations
$score = FeedbackUtils::calculateComponentScore('COLLABORATION', 'Met'); // Returns 7.5
$percentage = FeedbackUtils::calculatePercentage(22.5); // Returns 75.0
$level = FeedbackUtils::getPerformanceLevel(75.0); // Returns 'Developing'

// Input validation and sanitization
$validName = FeedbackUtils::validateStudentName('John Doe');
$safeName = FeedbackUtils::sanitizeForFilename('John Doe'); // Returns 'John_Doe'
$cleanText = FeedbackUtils::sanitizeSpecialCharacters($feedbackText);

// Generate standardized filenames
$filename = FeedbackUtils::generateFilename('HPV', 'John Doe', 'Sarah'); 
// Returns: 'HPV_MI_Feedback_Report_John_Doe_Sarah.pdf'

// Extract improvement suggestions
$suggestions = FeedbackUtils::extractSuggestions($feedbackText);

// Format feedback for display
$displayFormat = FeedbackUtils::formatFeedbackForDisplay($feedbackText, date('c'), 'AI Evaluator');
```

### Logger.php

The `Logger` class provides comprehensive activity logging:

```php
// Initialize logger
$logger = new Logger($storage, true, true, '/var/log/mi_chatbots');

// Log at different levels
$logger->debug('user_action', 'User clicked button', ['button' => 'start'], $sessionId);
$logger->info('session_event', 'Session started', ['type' => 'HPV'], $sessionId);
$logger->warning('validation', 'Invalid input detected', ['field' => 'name'], $sessionId);
$logger->error('system', 'Database connection failed', ['host' => 'localhost'], $sessionId);
$logger->critical('security', 'Authentication failure', ['attempts' => 5], $sessionId);

// Specialized logging methods
$logger->logSessionStart($sessionId, $studentName, $sessionType, $persona);
$logger->logSessionEnd($sessionId, $messageCount, $duration);
$logger->logMessageSent($sessionId, $role, $messageLength, $messageOrder);
$logger->logFeedbackGenerated($sessionId, $studentName, $totalScore, $percentage, $performanceLevel, $componentCount);
$logger->logPdfGenerated($sessionId, $filename, $fileSize, $generationTime);
$logger->logPdfDownloaded($sessionId, $filename, $downloadCount);
$logger->logException($sessionId, $exception, 'Additional context');
$logger->logPerformanceMetric($sessionId, 'response_time', 1.25, ['endpoint' => '/api/feedback']);
$logger->logUserAction($sessionId, 'download_pdf', ['filename' => $filename]);

// Set context for all subsequent logs
$logger->setContext(['user_id' => 123, 'ip_address' => '192.168.1.1']);

// Get statistics
$stats = $logger->getLogStatistics($sessionId);

// Rotate old log files
$logger->rotateLogFiles(30); // Keep 30 days
```

### SessionStorage.php

The `SessionStorage` class handles all database operations:

```php
// Initialize with database config
$storage = new SessionStorage($dbConfig);

// Session management
$storage->createSession($sessionId, $studentName, $sessionType, $persona);
$storage->updateSessionStatus($sessionId, 'completed');
$session = $storage->getSession($sessionId);

// Message storage
$messageId = $storage->storeMessage($sessionId, 'user', 'Hello there', 1);
$messages = $storage->getConversationHistory($sessionId, 100);

// Feedback storage
$feedbackId = $storage->storeFeedback(
    $sessionId, $studentName, $sessionType, 
    $components, $totalScore, $percentage, 
    $rawFeedback, $evaluator
);
$feedback = $storage->getFeedback($sessionId);

// PDF tracking
$reportId = $storage->storePdfReport($sessionId, $feedbackId, $filename, $filePath, $fileSize, $hash);
$storage->trackPdfDownload($reportId);
$reports = $storage->getPdfReports($sessionId);

// Activity logging
$logId = $storage->logActivity($sessionId, 'INFO', 'user_action', 'Button clicked', $context);

// Performance metrics
$metricId = $storage->storePerformanceMetric($sessionId, 'response_time', 1.25, $metricData);

// Analytics and reporting
$summary = $storage->getSessionSummary($sessionId);
$performance = $storage->getStudentPerformance($studentName, $sessionType, 50);
$logStats = $storage->getLogStatistics($sessionId);
$health = $storage->getDatabaseHealth();

// Maintenance
$cleanupStats = $storage->cleanupOldData(90); // Keep 90 days
```

### PdfGenerator.php

The `PdfGenerator` class creates professional PDF reports:

```php
// Initialize PDF generator
$generator = new PdfGenerator();

// Generate complete PDF report
$pdfContent = $generator->generatePdfReport($studentName, $feedbackText, $chatHistory, $sessionType, $persona);

// Generate filename
$filename = $generator->generateFilename($sessionType, $studentName, $persona);

// Get complete PDF information
$pdfInfo = $generator->generatePdfInfo($studentName, $feedbackText, $chatHistory, $sessionType, $persona);
// Returns: ['content' => ..., 'filename' => ..., 'size' => ..., 'hash' => ..., 'mime_type' => ...]

// Save PDF to file
$generator->savePdfToFile($pdfContent, '/path/to/reports/' . $filename);

// Output PDF for download
$generator->outputPdfForDownload($pdfContent, $filename, false); // false = attachment, true = inline
```

## 🔧 Configuration

### Database Configuration

```php
$dbConfig = [
    'host' => 'localhost',           // Database server host
    'dbname' => 'mi_chatbots',      // Database name
    'username' => 'your_username',   // Database username
    'password' => 'your_password',   // Database password
    'charset' => 'utf8mb4',         // Character set
    'options' => [                   // Additional PDO options
        PDO::ATTR_PERSISTENT => false,
        PDO::ATTR_TIMEOUT => 30
    ]
];
```

### Logger Configuration

```php
$loggerOptions = [
    'logToDatabase' => true,              // Enable database logging
    'logToFile' => true,                  // Enable file logging
    'logDirectory' => '/var/log/mi_logs', // Log file directory
    'minLogLevel' => Logger::INFO         // Minimum log level to record
];

$logger = new Logger($storage, $loggerOptions['logToDatabase'], $loggerOptions['logToFile'], 
                    $loggerOptions['logDirectory'], $loggerOptions['minLogLevel']);
```

### PDF Generator Configuration

```php
$pdfOptions = [
    'enable_remote' => false,           // Security: disable remote content
    'temp_dir' => '/tmp/pdf_temp',     // Temporary directory
    'default_paper_size' => 'letter',  // Paper size
    'default_font' => 'DejaVu Sans',   // Default font
    'dpi' => 96                        // Resolution
];

$generator = new PdfGenerator($pdfOptions);
```

## 🧪 Testing

Each utility includes self-test functionality:

```php
// Test FeedbackUtils
$results = FeedbackUtils::runSelfTest();
print_r($results);

// Test Logger
$results = Logger::runSelfTest();
print_r($results);

// Test SessionStorage (requires database)
$storage = new SessionStorage($dbConfig);
$results = $storage->runSelfTest();
print_r($results);

// Test PdfGenerator
$results = PdfGenerator::runSelfTest();
print_r($results);
```

## 🚨 Error Handling

All utilities use comprehensive error handling:

```php
try {
    $storage = new SessionStorage($dbConfig);
    $feedbackId = $storage->storeFeedback(/* parameters */);
} catch (Exception $e) {
    $logger->logException($sessionId, $e, 'Failed to store feedback');
    
    // Handle error appropriately
    if ($e->getMessage() === 'Database connection failed') {
        // Try fallback storage or queue for retry
    }
    
    // Return user-friendly error message
    return ['error' => 'Unable to save assessment. Please try again.'];
}
```

## 📊 Database Schema

The utilities work with the following main tables:

- **`sessions`** - Main conversation sessions
- **`messages`** - Individual chat messages
- **`feedback`** - MI assessment results with component breakdowns
- **`pdf_reports`** - Generated PDF report metadata
- **`activity_log`** - System events and debugging information
- **`performance_metrics`** - System performance tracking

Refer to `../database/mi_sessions.sql` for the complete schema definition.

## 🔒 Security Considerations

### Input Validation
- All user inputs are validated and sanitized
- Student names are validated for appropriate characters and length
- Feedback text is sanitized for PDF compatibility

### Database Security
- All database operations use prepared statements
- SQL injection protection throughout
- Appropriate error handling without information disclosure

### File Security
- PDF generator restricts file system access
- Remote content loading is disabled by default
- Temporary files are properly cleaned up

### Logging Security
- Sensitive information is not logged
- User inputs are sanitized before logging
- Log files have appropriate permissions

## 🔧 Troubleshooting

### Common Issues

**Database Connection Failed**
```php
// Check database configuration
$storage = new SessionStorage($dbConfig);
$health = $storage->getDatabaseHealth();
if ($health['status'] === 'error') {
    echo "Database issue: " . $health['error'];
}
```

**PDF Generation Fails**
```php
// Ensure Dompdf is installed
if (!class_exists('Dompdf\Dompdf')) {
    echo "Install Dompdf: composer require dompdf/dompdf\n";
}

// Check temporary directory permissions
$tempDir = sys_get_temp_dir();
if (!is_writable($tempDir)) {
    echo "Temp directory not writable: $tempDir\n";
}
```

**Logging Issues**
```php
// Check log directory permissions
$logDir = '/var/log/mi_logs';
if (!is_dir($logDir) || !is_writable($logDir)) {
    echo "Log directory issue: $logDir\n";
}
```

### Debug Mode

Enable debug logging for troubleshooting:

```php
$logger = new Logger($storage, true, true, '/tmp/debug_logs', Logger::DEBUG);
$logger->debug('system', 'Debug mode enabled', ['timestamp' => time()]);
```

## 📈 Performance Optimization

### Database Optimization
- Use connection pooling in production
- Implement query caching where appropriate
- Regular database maintenance and optimization

### Logging Optimization
- Use appropriate log levels to reduce I/O
- Implement log rotation to manage disk space
- Consider asynchronous logging for high-traffic applications

### PDF Generation Optimization
- Cache generated PDFs when possible
- Use background processing for large PDF generation
- Optimize images and content for faster rendering

## 🤝 Integration with Existing Python Code

These PHP utilities are designed to be compatible with the existing Python Streamlit applications:

### Shared Standards
- Same 30-point MI scoring system
- Identical component names and scoring logic
- Compatible feedback parsing patterns
- Consistent performance level calculations

### Data Compatibility
- Database schema supports both PHP and Python applications
- JSON-based logging format for cross-language compatibility
- Standardized filename conventions

### Migration Path
- PHP utilities can process feedback generated by Python applications
- Database can store sessions from both platforms
- PDFs maintain consistent formatting across implementations

## 📝 Example Integration

See `example_integration.php` for a complete working example that demonstrates:

- Full MI assessment workflow
- Database operations
- PDF generation
- Comprehensive logging
- Error handling
- Performance monitoring

## 📞 Support

For issues or questions:

1. Check the troubleshooting section above
2. Run self-tests to identify specific problems
3. Review log files for detailed error information
4. Ensure all dependencies are properly installed

## 🔄 Updates and Maintenance

### Regular Maintenance Tasks
- Run database cleanup periodically: `$storage->cleanupOldData(90)`
- Rotate log files: `$logger->rotateLogFiles(30)`
- Monitor database health: `$storage->getDatabaseHealth()`
- Update dependencies regularly

### Version Compatibility
- Maintain backward compatibility with existing Python applications
- Test thoroughly after any updates
- Document any breaking changes

---

This documentation provides comprehensive guidance for implementing and using the MI chatbot LAMP-stack utilities. The utilities are production-ready and designed to integrate seamlessly with existing Python applications while providing enterprise-grade functionality for web-based implementations.