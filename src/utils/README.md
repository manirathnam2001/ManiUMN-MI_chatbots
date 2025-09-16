# MI Chatbots LAMP-Stack Utilities

This directory contains LAMP-stack compatible PHP utilities for Motivational Interviewing (MI) chatbot applications. These utilities provide unified feedback processing, logging, database storage, and PDF generation capabilities that complement the existing Python-based Streamlit applications.

## 📁 Directory Structure

```
src/utils/
├── FeedbackUtils.php     # Core feedback processing and scoring
├── Logger.php            # Structured logging system
├── SessionStorage.php    # MySQL database operations
├── PdfGenerator.php      # PDF report generation
└── README.md            # This documentation file
```

## 🎯 Overview

These utilities implement the same MI assessment framework used in the Python version:

- **4 MI Components**: COLLABORATION, EVOCATION, ACCEPTANCE, COMPASSION
- **30-point scoring system**: 7.5 points per component
- **Status levels**: Met (100%), Partially Met (50%), Not Met (0%)
- **Performance levels**: Excellent, Proficient, Developing, Beginning, Needs Improvement

## 📋 Requirements

### PHP Requirements
- PHP 7.4 or higher
- PDO extension with MySQL support
- JSON extension
- FileInfo extension (for PDF MIME types)

### External Dependencies
- **Dompdf**: For PDF generation
  ```bash
  composer require dompdf/dompdf
  ```
- **MySQL/MariaDB**: Database server
- **Web server**: Apache/Nginx with PHP support

### Database Setup
1. Import the schema from `../../database/mi_sessions.sql`
2. Configure database credentials in your application
3. Ensure proper user permissions

## 🔧 Installation

1. **Clone/copy the utilities** to your web server directory
2. **Install Dompdf** via Composer:
   ```bash
   cd /path/to/your/project
   composer require dompdf/dompdf
   ```
3. **Setup database** using the provided schema:
   ```bash
   mysql -u root -p < ../../database/mi_sessions.sql
   ```
4. **Configure database credentials** in your application

## 📖 Usage Examples

### 1. Basic Feedback Processing

```php
<?php
require_once 'src/utils/FeedbackUtils.php';

// Parse feedback text and get scores
$feedbackText = "
1. COLLABORATION (7.5 pts): [Met] - Student demonstrated excellent partnership building
2. EVOCATION (7.5 pts): [Partially Met] - Some effort to elicit patient motivations  
3. ACCEPTANCE (7.5 pts): [Met] - Respected patient autonomy throughout
4. COMPASSION (7.5 pts): [Partially Met] - Generally warm and non-judgmental
";

$scoreBreakdown = FeedbackUtils::getScoreBreakdown($feedbackText);
echo "Total Score: {$scoreBreakdown['total_score']}/30 ({$scoreBreakdown['percentage']}%)\n";
echo "Performance Level: {$scoreBreakdown['performance_level']}\n";

// Extract suggestions
$suggestions = FeedbackUtils::extractSuggestionsFromFeedback($feedbackText);
foreach ($suggestions as $suggestion) {
    echo "• $suggestion\n";
}

// Validate student name
$safeName = FeedbackUtils::validateStudentName("John Doe Test");
echo "Safe filename: $safeName\n";
?>
```

### 2. Database Operations

```php
<?php
require_once 'src/utils/SessionStorage.php';

// Initialize database connection
$dbConfig = [
    'host' => 'localhost',
    'dbname' => 'mi_sessions',
    'username' => 'mi_app',
    'password' => 'your_password'
];

$storage = new SessionStorage($dbConfig);

// Create a new session
$sessionId = 'session_' . uniqid();
$storage->createSession($sessionId, 'John Doe', 'HPV', 'Concerned Parent');

// Add messages to conversation
$storage->addMessage($sessionId, 'user', 'I am concerned about the HPV vaccine safety.');
$storage->addMessage($sessionId, 'assistant', 'I understand your concerns. Can you tell me more?');

// Store feedback
$componentScores = [
    ['component' => 'COLLABORATION', 'status' => 'Met', 'score' => 7.5, 'feedback' => 'Great partnership building'],
    ['component' => 'EVOCATION', 'status' => 'Partially Met', 'score' => 3.75, 'feedback' => 'Some motivation exploration'],
    // ... more components
];

$feedbackId = $storage->storeFeedback(
    $sessionId,
    'John Doe',
    'HPV',
    $componentScores,
    22.5,
    75.0,
    $rawFeedback
);

// Complete session
$storage->completeSession($sessionId);

// Get session data
$session = $storage->getSession($sessionId);
$messages = $storage->getMessages($sessionId);
$feedback = $storage->getFeedback($sessionId);
?>
```

### 3. Logging System

```php
<?php
require_once 'src/utils/Logger.php';
require_once 'src/utils/SessionStorage.php';

// Initialize logger with database storage
$storage = new SessionStorage($dbConfig);
$logger = new Logger($storage, true, '/var/log/mi_system.log');

// Log various events
$sessionId = 'session_001';

$logger->logSessionStart($sessionId, 'John Doe', 'HPV');
$logger->logMessage($sessionId, 'user', 45);
$logger->logFeedbackGenerated($sessionId, 'John Doe', 'HPV', 22.5, 75.0);
$logger->logPdfGenerated($sessionId, 'John Doe', 'HPV_Report_John_Doe.pdf', 150000);

// Log errors with exception details
try {
    // Some operation that might fail
    throw new Exception("Something went wrong");
} catch (Exception $e) {
    $logger->logException($sessionId, $e);
}

// Get recent logs for debugging
$recentLogs = $logger->getRecentLogs($sessionId, null, 50);
foreach ($recentLogs as $log) {
    echo "[{$log['created_at']}] {$log['log_level']}: {$log['message']}\n";
}
?>
```

### 4. PDF Generation

```php
<?php
require_once 'src/utils/PdfGenerator.php';
require_once 'src/utils/FeedbackUtils.php';

// Initialize PDF generator
$pdfGenerator = new PdfGenerator([
    'defaultPaperSize' => 'letter',
    'defaultPaperOrientation' => 'portrait'
]);

// Sample data
$studentName = 'John Doe';
$sessionType = 'HPV';
$rawFeedback = "1. COLLABORATION (7.5 pts): [Met] - Excellent partnership building...";
$chatHistory = [
    ['role' => 'user', 'content' => 'I am concerned about the HPV vaccine.'],
    ['role' => 'assistant', 'content' => 'I understand your concerns. Can you tell me more?']
];

// Generate PDF
try {
    $pdfContent = $pdfGenerator->generatePdfReport(
        $studentName,
        $rawFeedback,
        $chatHistory,
        $sessionType,
        'AI_System'
    );
    
    // Save to file
    $filename = $pdfGenerator->generateFilename($sessionType, $studentName);
    $filepath = $pdfGenerator->savePdfToFile($pdfContent, $filename, '/path/to/reports');
    
    echo "PDF saved to: $filepath\n";
    
    // Or send as download
    // $pdfGenerator->downloadPdf($pdfContent, $filename);
    
} catch (Exception $e) {
    echo "PDF generation failed: " . $e->getMessage() . "\n";
}
?>
```

### 5. Complete Integration Example

```php
<?php
// complete_assessment.php - Full assessment workflow
require_once 'src/utils/FeedbackUtils.php';
require_once 'src/utils/SessionStorage.php';
require_once 'src/utils/Logger.php';
require_once 'src/utils/PdfGenerator.php';

// Database configuration
$dbConfig = [/* your database config */];

// Initialize components
$storage = new SessionStorage($dbConfig);
$logger = new Logger($storage, true);
$pdfGenerator = new PdfGenerator();

// Session data
$sessionId = $_POST['session_id'] ?? 'session_' . uniqid();
$studentName = $_POST['student_name'] ?? '';
$sessionType = $_POST['session_type'] ?? 'General';

try {
    // Log session start
    $logger->logSessionStart($sessionId, $studentName, $sessionType);
    
    // Process chat messages
    $chatHistory = $_POST['chat_history'] ?? [];
    foreach ($chatHistory as $message) {
        $storage->addMessage($sessionId, $message['role'], $message['content']);
        $logger->logMessage($sessionId, $message['role'], strlen($message['content']));
    }
    
    // Generate feedback (this would typically come from AI/LLM)
    $rawFeedback = $_POST['feedback'] ?? '';
    
    // Parse and store feedback
    $scoreBreakdown = FeedbackUtils::getScoreBreakdown($rawFeedback);
    $feedbackId = $storage->storeFeedback(
        $sessionId,
        $studentName,
        $sessionType,
        $scoreBreakdown['components'],
        $scoreBreakdown['total_score'],
        $scoreBreakdown['percentage'],
        $rawFeedback
    );
    
    // Log feedback generation
    $logger->logFeedbackGenerated(
        $sessionId,
        $studentName,
        $sessionType,
        $scoreBreakdown['total_score'],
        $scoreBreakdown['percentage']
    );
    
    // Generate PDF report
    $pdfContent = $pdfGenerator->generatePdfReport(
        $studentName,
        $rawFeedback,
        $chatHistory,
        $sessionType
    );
    
    $filename = $pdfGenerator->generateFilename($sessionType, $studentName);
    $filepath = $pdfGenerator->savePdfToFile($pdfContent, $filename, '/var/www/reports');
    
    // Store PDF info
    $pdfId = $storage->storePdfReport(
        $sessionId,
        $studentName,
        $sessionType,
        $filename,
        $filepath,
        strlen($pdfContent),
        $scoreBreakdown['total_score'],
        $scoreBreakdown['percentage']
    );
    
    // Log PDF generation
    $logger->logPdfGenerated($sessionId, $studentName, $filename, strlen($pdfContent));
    
    // Complete session
    $storage->completeSession($sessionId);
    $logger->logSessionEnd($sessionId, count($chatHistory));
    
    // Return response
    echo json_encode([
        'success' => true,
        'session_id' => $sessionId,
        'feedback_id' => $feedbackId,
        'pdf_id' => $pdfId,
        'score' => $scoreBreakdown['total_score'],
        'percentage' => $scoreBreakdown['percentage'],
        'performance_level' => $scoreBreakdown['performance_level'],
        'pdf_filename' => $filename
    ]);
    
} catch (Exception $e) {
    $logger->logException($sessionId, $e);
    
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}
?>
```

## 🔧 Configuration

### Database Configuration
```php
$dbConfig = [
    'host' => 'localhost',
    'dbname' => 'mi_sessions',
    'username' => 'mi_app',
    'password' => 'your_secure_password',
    'charset' => 'utf8mb4',
    'options' => [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]
];
```

### Logger Configuration
```php
$logger = new Logger(
    $storage,           // SessionStorage instance or null
    true,              // Enable file logging
    '/var/log/mi.log', // Custom log file path
    Logger::INFO       // Minimum log level
);
```

### PDF Generator Configuration
```php
$pdfOptions = [
    'isHtml5ParserEnabled' => true,
    'isPhpEnabled' => false,
    'isRemoteEnabled' => false,
    'defaultFont' => 'Arial',
    'defaultPaperSize' => 'letter',
    'defaultPaperOrientation' => 'portrait',
    'tempDir' => '/tmp',
    'chroot' => '/var/www'  // Security restriction
];
```

## 🔒 Security Considerations

1. **Input Validation**: All user inputs are sanitized and validated
2. **SQL Injection Protection**: Uses prepared statements exclusively
3. **File Access Restriction**: PDF generator restricts file access via chroot
4. **Remote Content Disabled**: PDF generator blocks remote URLs
5. **XSS Prevention**: All output is properly escaped
6. **Database Credentials**: Store securely, never in code
7. **Log File Permissions**: Ensure proper file permissions (640 or 600)

## 🧪 Testing

Each utility includes basic self-tests. Run them individually:

```bash
php src/utils/FeedbackUtils.php
php src/utils/Logger.php
php src/utils/SessionStorage.php
php src/utils/PdfGenerator.php
```

## 🔍 Troubleshooting

### Common Issues

1. **"Class 'PDO' not found"**
   - Install PHP PDO extension: `sudo apt-get install php-mysql`

2. **"Database connection failed"**
   - Check database credentials and server status
   - Ensure MySQL/MariaDB is running
   - Verify user permissions

3. **"Dompdf library not found"**
   - Install via Composer: `composer require dompdf/dompdf`
   - Ensure autoloader is included

4. **"Permission denied" for log files**
   - Check file/directory permissions
   - Ensure web server can write to log directory

5. **PDF generation timeout**
   - Increase PHP max_execution_time
   - Optimize HTML content size
   - Consider paginating long conversations

### Debug Mode

Enable debug logging for troubleshooting:

```php
$logger = new Logger($storage, true, '/var/log/mi_debug.log', Logger::DEBUG);
```

## 📊 Performance Tips

1. **Database Indexing**: The schema includes proper indexes for common queries
2. **Connection Pooling**: Consider using persistent database connections
3. **Log Rotation**: Implement log rotation to prevent disk space issues
4. **PDF Caching**: Cache generated PDFs when possible
5. **Memory Management**: Monitor memory usage for large conversations

## 🔄 Migration from Python

If migrating from the existing Python implementation:

1. **Data Structure Compatibility**: The PHP utilities use the same scoring system and data structures
2. **Database Schema**: Designed to work alongside or replace Python storage
3. **API Compatibility**: Methods are named similarly to Python counterparts
4. **Configuration**: Maintain similar configuration patterns

## 📚 API Reference

### FeedbackUtils Class
- `formatEvaluationPrompt($sessionType, $transcript, $ragContext)`: Generate evaluation prompt
- `parseFeedbackScores($feedbackText)`: Parse component scores from feedback
- `calculateComponentScore($component, $status)`: Calculate individual component score
- `getScoreBreakdown($feedbackText)`: Get complete score analysis
- `validateStudentName($name)`: Validate and sanitize student names
- `extractSuggestionsFromFeedback($feedback)`: Extract improvement suggestions

### SessionStorage Class
- `createSession($sessionId, $studentName, $sessionType, $persona)`: Create new session
- `addMessage($sessionId, $role, $content)`: Add conversation message
- `getMessages($sessionId)`: Retrieve session messages
- `storeFeedback(...)`: Store assessment feedback
- `getFeedback($sessionId)`: Retrieve session feedback
- `storePdfReport(...)`: Store PDF report info
- `logActivity(...)`: Log system activity

### Logger Class
- `info($eventType, $message, $context, $sessionId)`: Log info message
- `error($eventType, $message, $context, $sessionId)`: Log error message
- `logSessionStart($sessionId, $studentName, $sessionType)`: Log session start
- `logFeedbackGenerated(...)`: Log feedback generation
- `logPdfGenerated(...)`: Log PDF creation
- `logException($sessionId, $exception)`: Log exception details

### PdfGenerator Class
- `generatePdfReport($studentName, $feedback, $chatHistory, $sessionType)`: Generate PDF
- `generateFilename($sessionType, $studentName, $evaluator)`: Generate filename
- `savePdfToFile($pdfContent, $filename, $directory)`: Save PDF to file
- `downloadPdf($pdfContent, $filename)`: Send PDF as download

## 📞 Support

For issues or questions:

1. Check this documentation first
2. Review the test outputs from each utility
3. Check log files for error details
4. Ensure all requirements are met
5. Verify database schema is properly installed

## 📄 License

This code is part of the MI Chatbots project and follows the same licensing terms as the main repository.