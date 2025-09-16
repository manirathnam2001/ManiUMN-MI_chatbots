# MI Chatbots LAMP-Stack Utilities

A comprehensive set of PHP utilities for managing motivational interviewing (MI) chatbot operations in LAMP-stack environments. These utilities provide equivalent functionality to the existing Python modules while being optimized for traditional web hosting environments.

## Overview

This utility collection provides:

- **FeedbackUtils.php**: Feedback processing, scoring logic, and formatting
- **Logger.php**: Comprehensive logging for debugging and monitoring
- **SessionStorage.php**: MySQL database operations for session management
- **PdfGenerator.php**: Professional PDF report generation using DomPDF
- **Database Schema**: Complete MySQL schema for data storage

## Table of Contents

1. [Installation](#installation)
2. [Database Setup](#database-setup)
3. [Configuration](#configuration)
4. [Usage Examples](#usage-examples)
5. [API Reference](#api-reference)
6. [Integration Guide](#integration-guide)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- PHP 7.4 or higher
- MySQL 5.7 or higher (or MariaDB 10.2+)
- Composer (for DomPDF dependency)
- Web server (Apache/Nginx)

### Step 1: Install Dependencies

```bash
# Install Composer if not already installed
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer

# Create composer.json in your project root
cat > composer.json << 'EOF'
{
    "require": {
        "dompdf/dompdf": "^2.0"
    },
    "autoload": {
        "psr-4": {
            "MIChatbots\\Utils\\": "src/utils/"
        }
    }
}
EOF

# Install dependencies
composer install
```

### Step 2: Copy Utility Files

```bash
# Copy the utility files to your project
cp -r src/utils /path/to/your/project/src/
```

### Step 3: Include Autoloader

```php
<?php
// Include Composer autoloader in your PHP files
require_once __DIR__ . '/vendor/autoload.php';

// Or manually include the utilities
require_once 'src/utils/FeedbackUtils.php';
require_once 'src/utils/Logger.php';
require_once 'src/utils/SessionStorage.php';
require_once 'src/utils/PdfGenerator.php';
```

## Database Setup

### Step 1: Create Database

```sql
-- Create the database
CREATE DATABASE mi_chatbots CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 2: Import Schema

```bash
# Import the complete schema
mysql -u username -p mi_chatbots < database/mi_sessions.sql
```

### Step 3: Create Application User

```sql
-- Create dedicated database user
CREATE USER 'mi_app'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON mi_chatbots.* TO 'mi_app'@'localhost';
GRANT EXECUTE ON PROCEDURE mi_chatbots.* TO 'mi_app'@'localhost';
FLUSH PRIVILEGES;
```

### Step 4: Configure Connection

```php
<?php
// Database configuration
$dbConfig = [
    'host' => 'localhost',
    'dbname' => 'mi_chatbots',
    'username' => 'mi_app',
    'password' => 'your_secure_password',
    'charset' => 'utf8mb4'
];

try {
    $pdo = new PDO(
        "mysql:host={$dbConfig['host']};dbname={$dbConfig['dbname']};charset={$dbConfig['charset']}",
        $dbConfig['username'],
        $dbConfig['password'],
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false
        ]
    );
} catch (PDOException $e) {
    die("Database connection failed: " . $e->getMessage());
}
?>
```

## Configuration

### Environment Configuration

Create a configuration file for your environment:

```php
<?php
// config/mi_config.php

return [
    'database' => [
        'host' => $_ENV['DB_HOST'] ?? 'localhost',
        'dbname' => $_ENV['DB_NAME'] ?? 'mi_chatbots',
        'username' => $_ENV['DB_USER'] ?? 'mi_app',
        'password' => $_ENV['DB_PASS'] ?? '',
        'charset' => 'utf8mb4'
    ],
    
    'logging' => [
        'level' => $_ENV['LOG_LEVEL'] ?? 'INFO',
        'file_path' => $_ENV['LOG_PATH'] ?? '/var/log/mi_chatbots/app.log',
        'database_logging' => true,
        'file_logging' => true
    ],
    
    'pdf' => [
        'temp_dir' => $_ENV['PDF_TEMP_DIR'] ?? '/tmp/mi_pdfs',
        'font_dir' => $_ENV['PDF_FONT_DIR'] ?? null,
        'enable_remote' => false, // Security: disable remote resources
        'memory_limit' => '256M'
    ],
    
    'session' => [
        'cleanup_days' => 90, // Days to keep old sessions
        'max_message_length' => 5000,
        'max_messages_per_session' => 500
    ]
];
?>
```

## Usage Examples

### 1. Basic Session Management

```php
<?php
use MIChatbots\Utils\SessionStorage;
use MIChatbots\Utils\Logger;

// Initialize components
$config = require 'config/mi_config.php';
$pdo = new PDO(/* your database connection */);
$logger = new Logger($pdo, $config['logging']['file_path']);
$storage = new SessionStorage($pdo, $logger);

// Create a new session
$sessionId = $storage->generateSessionId();
$success = $storage->createSession(
    $sessionId,
    'John Doe',
    'HPV',
    'Alex - Hesitant Patient'
);

if ($success) {
    echo "Session created: {$sessionId}";
} else {
    echo "Failed to create session";
}

// Store conversation messages
$messages = [
    ['role' => 'assistant', 'content' => 'Hello! How can I help you today?'],
    ['role' => 'user', 'content' => 'I have questions about the HPV vaccine.'],
    ['role' => 'assistant', 'content' => 'I understand. What specific concerns do you have?']
];

$storage->storeConversationMessages($sessionId, $messages);

// Update session status when complete
$storage->updateSessionStatus($sessionId, 'COMPLETED', 300); // 5 minutes
?>
```

### 2. Feedback Processing

```php
<?php
use MIChatbots\Utils\FeedbackUtils;
use MIChatbots\Utils\SessionStorage;

// Sample feedback from AI evaluation
$rawFeedback = "**1. COLLABORATION (7.5 pts): [Met] - Excellent partnership building**

**2. EVOCATION (7.5 pts): [Partially Met] - Good questions, could explore more**

**3. ACCEPTANCE (7.5 pts): [Met] - Demonstrated respect for autonomy**

**4. COMPASSION (7.5 pts): [Not Met] - Needs more warmth and empathy**

### Improvement Suggestions:
- Practice reflective listening techniques
- Show more empathy in responses
- Ask follow-up questions to understand concerns better";

// Process and store feedback
try {
    // Parse component scores
    $componentScores = FeedbackUtils::parseFeedbackScores($rawFeedback);
    
    // Get detailed breakdown
    $breakdown = FeedbackUtils::getScoreBreakdown($rawFeedback);
    
    // Store in database
    $storage->storeFeedback($sessionId, $rawFeedback, $componentScores, 'AI Evaluator');
    
    // Display results
    echo "Total Score: {$breakdown['total_score']}/30 ({$breakdown['percentage']}%)\n";
    echo "Grade Level: {$breakdown['grade_level']}\n";
    
    foreach ($breakdown['components'] as $component => $data) {
        echo "{$component}: {$data['score']}/{$data['max_score']} ({$data['status']})\n";
    }
    
} catch (Exception $e) {
    echo "Error processing feedback: " . $e->getMessage();
}
?>
```

### 3. PDF Generation

```php
<?php
use MIChatbots\Utils\PdfGenerator;
use MIChatbots\Utils\PdfGeneratorFactory;
use MIChatbots\Utils\SessionStorage;

// Get session data
$sessionData = $storage->getCompleteSessionData($sessionId);

if (!$sessionData['session']) {
    die("Session not found");
}

// Create PDF generator
$generator = PdfGeneratorFactory::createStandard($logger);

try {
    // Generate comprehensive performance report
    $pdfContent = $generator->generatePerformanceReport(
        $sessionData['session']['student_name'],
        $sessionData['feedback']['feedback_content'],
        $sessionData['conversation'],
        $sessionData['session']['session_type']
    );
    
    // Generate filename
    $filename = FeedbackUtils::createDownloadFilename(
        $sessionData['session']['student_name'],
        $sessionData['session']['session_type'],
        $sessionData['session']['persona']
    );
    
    // Record PDF export
    $storage->recordPdfExport($sessionId, $filename, null, strlen($pdfContent));
    
    // Send PDF to browser
    $generator->generateDownloadHeaders($filename, strlen($pdfContent));
    echo $pdfContent;
    
    // Record download
    $storage->recordPdfDownload($sessionId, $filename);
    
} catch (Exception $e) {
    $logger->logError("PDF generation failed", $e, $sessionId);
    http_response_code(500);
    echo "PDF generation failed: " . $e->getMessage();
}
?>
```

### 4. Comprehensive Logging

```php
<?php
use MIChatbots\Utils\Logger;
use MIChatbots\Utils\PerformanceLogger;

// Create logger with both database and file logging
$logger = new Logger($pdo, '/var/log/mi_chatbots.log', true, true, Logger::DEBUG);

// Log various events
$logger->logSessionEvent($sessionId, 'START', 'John Doe', 'HPV');

$logger->logFeedbackProcessing($sessionId, 'John Doe', [
    'total_score' => 22.5,
    'percentage' => 75.0
], 'AI Evaluator');

$logger->logPdfGeneration($sessionId, 'report.pdf', '/tmp/report.pdf', 1024000, 2.5);

// Performance logging
$performanceLogger = new PerformanceLogger($logger);

$result = $performanceLogger->timeOperation('complex_operation', function() {
    // Your complex operation here
    sleep(1);
    return 'Operation completed';
}, $sessionId);

// Log custom events
$logger->log(Logger::INFO, Logger::CATEGORY_SYSTEM, 'Custom event occurred', [
    'user_id' => 'user123',
    'action' => 'custom_action',
    'metadata' => ['key' => 'value']
]);

// Get logs for analysis
$recentLogs = $logger->getSessionLogs($sessionId, 20);
$systemStats = $logger->getSystemStats(24); // Last 24 hours
?>
```

## API Reference

### FeedbackUtils Class

#### Key Methods

```php
// Format evaluation prompt for AI
FeedbackUtils::formatEvaluationPrompt($sessionType, $transcript, $ragContext)

// Parse feedback scores
FeedbackUtils::parseFeedbackScores($feedback) // Returns MIComponentScore[]

// Get detailed score breakdown
FeedbackUtils::getScoreBreakdown($feedback) // Returns array with totals and components

// Extract improvement suggestions
FeedbackUtils::extractSuggestionsFromFeedback($feedback) // Returns string[]

// Validate student name
FeedbackUtils::validateStudentName($name) // Returns cleaned name or throws exception

// Create download filename
FeedbackUtils::createDownloadFilename($studentName, $sessionType, $persona)

// Sanitize text for PDF
FeedbackUtils::sanitizeSpecialCharacters($text)
```

### SessionStorage Class

#### Session Management

```php
$storage->createSession($sessionId, $studentName, $sessionType, $persona, $metadata)
$storage->getSession($sessionId)
$storage->updateSessionStatus($sessionId, $status, $duration)
$storage->getSessionsByStudent($studentName, $limit, $offset)
```

#### Conversation Management

```php
$storage->addConversationMessage($sessionId, $messageOrder, $role, $content, $metadata)
$storage->getConversation($sessionId)
$storage->storeConversationMessages($sessionId, $messages) // Batch insert
```

#### Feedback Management

```php
$storage->storeFeedback($sessionId, $feedbackContent, $componentScores, $evaluator)
$storage->getFeedback($sessionId)
$storage->getFeedbackStatistics($sessionType, $days)
```

#### PDF Export Management

```php
$storage->recordPdfExport($sessionId, $filename, $filePath, $fileSize, $pdfType)
$storage->recordPdfDownload($sessionId, $filename)
$storage->getPdfExports($sessionId)
```

### Logger Class

#### Logging Methods

```php
$logger->logFeedbackProcessing($sessionId, $studentName, $scoreBreakdown, $evaluator)
$logger->logPdfGeneration($sessionId, $filename, $filePath, $fileSize, $generationTime)
$logger->logSessionEvent($sessionId, $event, $studentName, $sessionType)
$logger->logError($message, $exception, $sessionId, $additionalContext)
$logger->logValidation($validationType, $isValid, $input, $errorMessage)
$logger->logPerformance($operation, $executionTime, $memoryUsage, $sessionId)
```

### PdfGenerator Class

#### PDF Generation

```php
$generator->generatePerformanceReport($studentName, $rawFeedback, $chatHistory, $sessionType)
$generator->generateTranscriptOnly($studentName, $chatHistory, $sessionType)
$generator->savePdfToFile($pdfContent, $filePath)
$generator->generateDownloadHeaders($filename, $fileSize, $inline)
```

## Integration Guide

### Integrating with Existing Applications

#### 1. Web Application Integration

```php
<?php
// web/mi_session.php - Main session handler

session_start();
require_once '../vendor/autoload.php';
require_once '../config/mi_config.php';

use MIChatbots\Utils\{SessionStorage, Logger, FeedbackUtils, PdfGenerator};

// Initialize components
$config = require '../config/mi_config.php';
$pdo = new PDO(/* database connection */);
$logger = new Logger($pdo, $config['logging']['file_path']);
$storage = new SessionStorage($pdo, $logger);

// Handle different actions
$action = $_POST['action'] ?? $_GET['action'] ?? '';

switch ($action) {
    case 'start_session':
        $sessionId = $storage->generateSessionId();
        $success = $storage->createSession(
            $sessionId,
            $_POST['student_name'],
            $_POST['session_type'],
            $_POST['persona'] ?? null
        );
        
        if ($success) {
            $_SESSION['mi_session_id'] = $sessionId;
            header('Content-Type: application/json');
            echo json_encode(['success' => true, 'session_id' => $sessionId]);
        } else {
            http_response_code(500);
            echo json_encode(['success' => false, 'error' => 'Failed to create session']);
        }
        break;
        
    case 'add_message':
        $sessionId = $_SESSION['mi_session_id'] ?? null;
        if (!$sessionId) {
            http_response_code(400);
            echo json_encode(['error' => 'No active session']);
            break;
        }
        
        $success = $storage->addConversationMessage(
            $sessionId,
            $_POST['message_order'],
            $_POST['role'],
            $_POST['content']
        );
        
        header('Content-Type: application/json');
        echo json_encode(['success' => $success]);
        break;
        
    case 'submit_feedback':
        $sessionId = $_SESSION['mi_session_id'] ?? null;
        if (!$sessionId) {
            http_response_code(400);
            echo json_encode(['error' => 'No active session']);
            break;
        }
        
        try {
            $storage->storeFeedback(
                $sessionId,
                $_POST['feedback_content'],
                [], // Will be parsed automatically
                $_POST['evaluator'] ?? 'System'
            );
            
            $storage->updateSessionStatus($sessionId, 'COMPLETED');
            
            echo json_encode(['success' => true]);
        } catch (Exception $e) {
            $logger->logError('Failed to submit feedback', $e, $sessionId);
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        break;
        
    case 'download_pdf':
        $sessionId = $_SESSION['mi_session_id'] ?? null;
        if (!$sessionId) {
            http_response_code(400);
            echo "No active session";
            break;
        }
        
        try {
            $sessionData = $storage->getCompleteSessionData($sessionId);
            
            if (!$sessionData['session']) {
                http_response_code(404);
                echo "Session not found";
                break;
            }
            
            $generator = PdfGeneratorFactory::createStandard($logger);
            $pdfContent = $generator->generatePerformanceReport(
                $sessionData['session']['student_name'],
                $sessionData['feedback']['feedback_content'] ?? '',
                $sessionData['conversation'],
                $sessionData['session']['session_type']
            );
            
            $filename = FeedbackUtils::createDownloadFilename(
                $sessionData['session']['student_name'],
                $sessionData['session']['session_type'],
                $sessionData['session']['persona']
            );
            
            $storage->recordPdfExport($sessionId, $filename, null, strlen($pdfContent));
            $storage->recordPdfDownload($sessionId, $filename);
            
            $generator->generateDownloadHeaders($filename, strlen($pdfContent));
            echo $pdfContent;
            
        } catch (Exception $e) {
            $logger->logError('PDF download failed', $e, $sessionId);
            http_response_code(500);
            echo "PDF generation failed";
        }
        break;
        
    default:
        http_response_code(400);
        echo json_encode(['error' => 'Invalid action']);
}
?>
```

#### 2. API Endpoint Integration

```php
<?php
// api/mi_api.php - RESTful API

header('Content-Type: application/json');
require_once '../vendor/autoload.php';

use MIChatbots\Utils\{SessionStorage, Logger, FeedbackUtils};

// Initialize components
$pdo = new PDO(/* connection */);
$logger = new Logger($pdo);
$storage = new SessionStorage($pdo, $logger);

// Parse request
$method = $_SERVER['REQUEST_METHOD'];
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$segments = explode('/', trim($path, '/'));

try {
    switch ($method) {
        case 'GET':
            if ($segments[1] === 'sessions' && isset($segments[2])) {
                // GET /api/sessions/{sessionId}
                $sessionData = $storage->getCompleteSessionData($segments[2]);
                echo json_encode($sessionData);
            } elseif ($segments[1] === 'sessions') {
                // GET /api/sessions?student=name&type=HPV
                $filters = [
                    'student_name' => $_GET['student'] ?? null,
                    'session_type' => $_GET['type'] ?? null,
                    'status' => $_GET['status'] ?? null
                ];
                $sessions = $storage->searchSessions(array_filter($filters));
                echo json_encode($sessions);
            }
            break;
            
        case 'POST':
            $input = json_decode(file_get_contents('php://input'), true);
            
            if ($segments[1] === 'sessions') {
                // POST /api/sessions
                $sessionId = $storage->generateSessionId();
                $success = $storage->createSession(
                    $sessionId,
                    $input['student_name'],
                    $input['session_type'],
                    $input['persona'] ?? null
                );
                
                if ($success) {
                    echo json_encode(['session_id' => $sessionId]);
                } else {
                    http_response_code(500);
                    echo json_encode(['error' => 'Failed to create session']);
                }
            } elseif ($segments[1] === 'feedback') {
                // POST /api/feedback
                $storage->storeFeedback(
                    $input['session_id'],
                    $input['feedback_content'],
                    [],
                    $input['evaluator'] ?? 'API'
                );
                echo json_encode(['success' => true]);
            }
            break;
            
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
    }
    
} catch (Exception $e) {
    $logger->logError('API error', $e);
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
?>
```

### Frontend JavaScript Integration

```javascript
// js/mi_client.js - Frontend integration

class MIClient {
    constructor(apiBaseUrl = '/api') {
        this.apiBaseUrl = apiBaseUrl;
        this.sessionId = null;
    }
    
    async startSession(studentName, sessionType, persona = null) {
        const response = await fetch(`${this.apiBaseUrl}/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                student_name: studentName,
                session_type: sessionType,
                persona: persona
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to start session');
        }
        
        const data = await response.json();
        this.sessionId = data.session_id;
        return data.session_id;
    }
    
    async addMessage(role, content, messageOrder) {
        if (!this.sessionId) {
            throw new Error('No active session');
        }
        
        const response = await fetch(`${this.apiBaseUrl}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId,
                role: role,
                content: content,
                message_order: messageOrder
            })
        });
        
        return response.ok;
    }
    
    async submitFeedback(feedbackContent, evaluator = 'User') {
        if (!this.sessionId) {
            throw new Error('No active session');
        }
        
        const response = await fetch(`${this.apiBaseUrl}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId,
                feedback_content: feedbackContent,
                evaluator: evaluator
            })
        });
        
        return response.ok;
    }
    
    downloadPdf() {
        if (!this.sessionId) {
            throw new Error('No active session');
        }
        
        const link = document.createElement('a');
        link.href = `/web/mi_session.php?action=download_pdf`;
        link.download = 'mi_performance_report.pdf';
        link.click();
    }
    
    async getSessionData() {
        if (!this.sessionId) {
            throw new Error('No active session');
        }
        
        const response = await fetch(`${this.apiBaseUrl}/sessions/${this.sessionId}`);
        return response.json();
    }
}

// Usage example
const miClient = new MIClient();

// Start a session
miClient.startSession('John Doe', 'HPV', 'Alex - Hesitant Patient')
    .then(sessionId => {
        console.log('Session started:', sessionId);
        
        // Add messages as conversation progresses
        return miClient.addMessage('user', 'Hello, I have questions about vaccines', 1);
    })
    .then(() => {
        return miClient.addMessage('assistant', 'I would be happy to help. What specific questions do you have?', 2);
    })
    .then(() => {
        // Submit feedback when session is complete
        const feedback = "**1. COLLABORATION (7.5 pts): [Met] - Good rapport building...";
        return miClient.submitFeedback(feedback);
    })
    .then(() => {
        // Download PDF report
        miClient.downloadPdf();
    })
    .catch(error => {
        console.error('Error:', error);
    });
```

## Performance Considerations

### Database Optimization

1. **Index Strategy**
```sql
-- Add indexes for common queries
CREATE INDEX idx_sessions_student_type_date ON sessions(student_name, session_type, created_at);
CREATE INDEX idx_feedback_scores_date ON feedback(total_score, percentage_score, created_at);
CREATE INDEX idx_conversations_session_order ON conversations(session_id, message_order);
```

2. **Connection Pooling**
```php
// Use connection pooling for high-traffic applications
class DatabasePool {
    private static $connections = [];
    private static $maxConnections = 10;
    
    public static function getConnection($config) {
        $key = md5(serialize($config));
        
        if (!isset(self::$connections[$key])) {
            self::$connections[$key] = [];
        }
        
        if (count(self::$connections[$key]) < self::$maxConnections) {
            $pdo = new PDO(/* connection */);
            self::$connections[$key][] = $pdo;
            return $pdo;
        }
        
        return self::$connections[$key][array_rand(self::$connections[$key])];
    }
}
```

### Memory Management

1. **PDF Generation Optimization**
```php
// Increase memory limit for large PDFs
ini_set('memory_limit', '512M');

// Use streaming for large conversations
class StreamingPdfGenerator extends PdfGenerator {
    public function generateLargeReport($sessionId, $chunkSize = 50) {
        $conversation = $this->storage->getConversation($sessionId);
        $chunks = array_chunk($conversation, $chunkSize);
        
        $htmlParts = [];
        foreach ($chunks as $chunk) {
            $htmlParts[] = $this->generateConversationChunk($chunk);
            // Free memory after each chunk
            unset($chunk);
        }
        
        return $this->combineChunks($htmlParts);
    }
}
```

2. **Session Cleanup**
```php
// Regular cleanup script (run via cron)
// cleanup.php
require_once 'vendor/autoload.php';

$storage = new SessionStorage($pdo, $logger);

// Clean up sessions older than 90 days
$result = $storage->cleanupOldSessions(90);
echo "Cleaned up {$result['sessions_cleaned']} sessions\n";

// Clean up old logs
$logger->cleanupOldLogs(30);
```

### Caching Strategy

```php
// Simple Redis caching implementation
class CachedSessionStorage extends SessionStorage {
    private $redis;
    private $cacheTimeout = 300; // 5 minutes
    
    public function __construct($pdo, $logger, $redis) {
        parent::__construct($pdo, $logger);
        $this->redis = $redis;
    }
    
    public function getSession($sessionId) {
        $cacheKey = "session:{$sessionId}";
        $cached = $this->redis->get($cacheKey);
        
        if ($cached) {
            return json_decode($cached, true);
        }
        
        $session = parent::getSession($sessionId);
        if ($session) {
            $this->redis->setex($cacheKey, $this->cacheTimeout, json_encode($session));
        }
        
        return $session;
    }
}
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Problems

```php
// Test database connection
function testDatabaseConnection($config) {
    try {
        $pdo = new PDO(
            "mysql:host={$config['host']};dbname={$config['dbname']}",
            $config['username'],
            $config['password']
        );
        
        echo "✓ Database connection successful\n";
        
        // Test table access
        $stmt = $pdo->query("SELECT COUNT(*) FROM sessions");
        echo "✓ Table access successful\n";
        
    } catch (PDOException $e) {
        echo "✗ Database error: " . $e->getMessage() . "\n";
    }
}
```

#### 2. PDF Generation Issues

```php
// Debug PDF generation
function debugPdfGeneration() {
    // Enable DomPDF debugging
    $options = new Options();
    $options->set('debugCss', true);
    $options->set('debugLayout', true);
    $options->set('debugKeepTemp', true);
    
    $generator = new PdfGenerator(null, $options);
    
    // Test with simple content
    try {
        $pdfContent = $generator->generateTranscriptOnly(
            'Test Student',
            [['role' => 'user', 'content' => 'Test message']],
            'Test Session'
        );
        
        echo "✓ PDF generation successful\n";
        echo "PDF size: " . strlen($pdfContent) . " bytes\n";
        
    } catch (Exception $e) {
        echo "✗ PDF generation failed: " . $e->getMessage() . "\n";
    }
}
```

#### 3. Memory Issues

```php
// Monitor memory usage
function monitorMemoryUsage($operation, $callable) {
    $startMemory = memory_get_usage(true);
    $startPeak = memory_get_peak_usage(true);
    
    $result = $callable();
    
    $endMemory = memory_get_usage(true);
    $endPeak = memory_get_peak_usage(true);
    
    echo "Operation: {$operation}\n";
    echo "Memory used: " . number_format(($endMemory - $startMemory) / 1024 / 1024, 2) . " MB\n";
    echo "Peak memory: " . number_format($endPeak / 1024 / 1024, 2) . " MB\n";
    
    return $result;
}

// Usage
$result = monitorMemoryUsage('PDF Generation', function() use ($generator) {
    return $generator->generatePerformanceReport(/* params */);
});
```

### Log Analysis

```php
// Analyze system logs for issues
function analyzeSystemLogs($logger, $hours = 24) {
    $stats = $logger->getSystemStats($hours);
    
    echo "System Log Analysis (Last {$hours} hours):\n";
    echo str_repeat('-', 50) . "\n";
    
    foreach ($stats as $stat) {
        echo sprintf(
            "%-20s %-10s %8d events",
            $stat['log_category'],
            $stat['log_level'],
            $stat['count']
        );
        
        if ($stat['avg_exec_time']) {
            echo sprintf(" (avg: %.2fs)", $stat['avg_exec_time']);
        }
        
        echo "\n";
    }
}
```

### Health Check Endpoint

```php
// health_check.php - System health monitoring
require_once 'vendor/autoload.php';

header('Content-Type: application/json');

$health = [
    'status' => 'healthy',
    'timestamp' => date('c'),
    'checks' => []
];

try {
    // Database check
    $pdo = new PDO(/* connection */);
    $storage = new SessionStorage($pdo);
    $connectionTest = $storage->testConnection();
    
    $health['checks']['database'] = [
        'status' => $connectionTest['connection'] ? 'healthy' : 'unhealthy',
        'version' => $connectionTest['version'],
        'tables' => $connectionTest['tables']
    ];
    
    // PDF generation check
    $generator = PdfGeneratorFactory::createStandard();
    $testPdf = $generator->generateTranscriptOnly('Test', [], 'Test');
    
    $health['checks']['pdf'] = [
        'status' => strlen($testPdf) > 0 ? 'healthy' : 'unhealthy',
        'test_size' => strlen($testPdf)
    ];
    
    // Memory check
    $memoryUsage = memory_get_usage(true) / 1024 / 1024;
    $memoryLimit = (int)ini_get('memory_limit');
    
    $health['checks']['memory'] = [
        'status' => $memoryUsage < ($memoryLimit * 0.8) ? 'healthy' : 'warning',
        'usage_mb' => round($memoryUsage, 2),
        'limit_mb' => $memoryLimit
    ];
    
    // Overall status
    $allHealthy = true;
    foreach ($health['checks'] as $check) {
        if ($check['status'] !== 'healthy') {
            $allHealthy = false;
            break;
        }
    }
    
    $health['status'] = $allHealthy ? 'healthy' : 'degraded';
    
} catch (Exception $e) {
    $health['status'] = 'unhealthy';
    $health['error'] = $e->getMessage();
}

echo json_encode($health, JSON_PRETTY_PRINT);
?>
```

## Support and Maintenance

### Regular Maintenance Tasks

1. **Database Cleanup** (Weekly)
```bash
# cleanup_weekly.sh
#!/bin/bash
php /path/to/your/project/scripts/cleanup.php
```

2. **Log Rotation** (Daily)
```bash
# logrotate configuration
/var/log/mi_chatbots/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
}
```

3. **Performance Monitoring** (Hourly)
```bash
# monitor.sh
#!/bin/bash
curl http://your-domain.com/health_check.php > /tmp/health_check.json
# Process health check results and alert if needed
```

### Troubleshooting Checklist

- [ ] Database connection established
- [ ] Required tables exist and accessible
- [ ] PHP memory limit sufficient (256M+ recommended)
- [ ] DomPDF dependencies installed
- [ ] File permissions correct for temp directories
- [ ] Log files writable
- [ ] Composer dependencies up to date

For additional support, check the system logs and health check endpoint for detailed diagnostic information.