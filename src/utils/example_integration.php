<?php
/**
 * example_integration.php
 * 
 * Complete working example demonstrating the integration of all MI chatbot
 * LAMP-stack utilities. This example shows a complete workflow from session
 * creation to PDF generation and comprehensive logging.
 * 
 * This file can be run directly to see the utilities in action, or used
 * as a reference for integrating the utilities into your own applications.
 * 
 * @package MIChatbots
 * @author LAMP-Stack MI Assessment System
 * @version 1.0.0
 */

// Include all utility classes
require_once 'FeedbackUtils.php';
require_once 'Logger.php';
require_once 'SessionStorage.php';
require_once 'PdfGenerator.php';

/**
 * Complete MI Assessment Workflow Example
 */
class MIAssessmentWorkflow
{
    private $storage;
    private $logger;
    private $pdfGenerator;
    private $dbConfig;
    
    /**
     * Initialize the workflow with database configuration
     * 
     * @param array $dbConfig Database configuration
     */
    public function __construct($dbConfig)
    {
        $this->dbConfig = $dbConfig;
        $this->initializeComponents();
    }
    
    /**
     * Initialize all utility components
     */
    private function initializeComponents()
    {
        try {
            // Initialize database storage
            $this->storage = new SessionStorage($this->dbConfig);
            
            // Initialize logger with both database and file logging
            $this->logger = new Logger(
                $this->storage,     // Database storage for logging
                true,              // Enable database logging
                true,              // Enable file logging
                '/tmp/mi_logs',    // Log directory
                Logger::INFO       // Minimum log level
            );
            
            // Initialize PDF generator
            $this->pdfGenerator = new PdfGenerator();
            
            $this->logger->info('system', 'MI Assessment Workflow initialized successfully');
            
        } catch (Exception $e) {
            throw new Exception("Failed to initialize workflow: " . $e->getMessage());
        }
    }
    
    /**
     * Run a complete MI assessment workflow demonstration
     * 
     * @return array Results of the workflow
     */
    public function runCompleteWorkflow()
    {
        $results = [];
        $sessionId = 'demo_session_' . uniqid();
        
        try {
            echo "🚀 Starting Complete MI Assessment Workflow\n";
            echo str_repeat('=', 50) . "\n";
            
            // Step 1: Create Session
            echo "📋 Step 1: Creating Session...\n";
            $sessionData = $this->createSession($sessionId);
            $results['session_creation'] = $sessionData;
            echo "   ✅ Session created: {$sessionData['session_id']}\n";
            
            // Step 2: Simulate Conversation
            echo "\n💬 Step 2: Simulating Conversation...\n";
            $chatHistory = $this->simulateConversation($sessionId);
            $results['conversation'] = $chatHistory;
            echo "   ✅ {$chatHistory['message_count']} messages exchanged\n";
            
            // Step 3: Generate AI Feedback
            echo "\n🧠 Step 3: Generating AI Feedback...\n";
            $feedbackData = $this->generateFeedback($sessionId, $sessionData);
            $results['feedback'] = $feedbackData;
            echo "   ✅ Feedback generated - Score: {$feedbackData['total_score']}/30.0 ({$feedbackData['percentage']}%)\n";
            echo "   📊 Performance Level: {$feedbackData['performance_level']}\n";
            
            // Step 4: Generate PDF Report
            echo "\n📄 Step 4: Generating PDF Report...\n";
            $pdfData = $this->generatePdfReport($sessionId, $sessionData, $feedbackData, $chatHistory['messages']);
            $results['pdf'] = $pdfData;
            echo "   ✅ PDF generated: {$pdfData['filename']} ({$pdfData['size']} bytes)\n";
            
            // Step 5: Complete Session
            echo "\n🏁 Step 5: Completing Session...\n";
            $completionData = $this->completeSession($sessionId, $chatHistory['message_count']);
            $results['completion'] = $completionData;
            echo "   ✅ Session completed successfully\n";
            
            // Step 6: Generate Analytics
            echo "\n📈 Step 6: Generating Analytics...\n";
            $analytics = $this->generateAnalytics($sessionId, $sessionData['student_name']);
            $results['analytics'] = $analytics;
            echo "   ✅ Analytics generated\n";
            
            echo "\n🎉 Workflow completed successfully!\n";
            echo str_repeat('=', 50) . "\n";
            
            $results['overall_status'] = 'SUCCESS';
            
        } catch (Exception $e) {
            $this->logger->logException($sessionId, $e, 'Workflow failed');
            $results['overall_status'] = 'FAILED';
            $results['error'] = $e->getMessage();
            echo "\n❌ Workflow failed: " . $e->getMessage() . "\n";
        }
        
        return $results;
    }
    
    /**
     * Create a new MI assessment session
     * 
     * @param string $sessionId Session identifier
     * @return array Session data
     */
    private function createSession($sessionId)
    {
        $studentName = 'Jane Smith';
        $sessionType = 'HPV';
        $persona = 'College Student - Alex';
        
        // Create session in database
        $this->storage->createSession($sessionId, $studentName, $sessionType, $persona);
        
        // Log session start
        $this->logger->logSessionStart($sessionId, $studentName, $sessionType, $persona);
        
        return [
            'session_id' => $sessionId,
            'student_name' => $studentName,
            'session_type' => $sessionType,
            'persona' => $persona,
            'started_at' => date('c')
        ];
    }
    
    /**
     * Simulate a realistic MI conversation
     * 
     * @param string $sessionId Session ID
     * @return array Conversation data
     */
    private function simulateConversation($sessionId)
    {
        $messages = [
            [
                'role' => 'assistant',
                'content' => 'Hi there! I\'m Alex, a college student. I\'ve been hearing about the HPV vaccine and I\'m not sure what to think about it.'
            ],
            [
                'role' => 'user',
                'content' => 'Hi Alex! I\'m glad you\'re asking about the HPV vaccine. It shows you\'re thinking about your health. What have you been hearing that\'s got you wondering?'
            ],
            [
                'role' => 'assistant',
                'content' => 'Well, some of my friends say it\'s important for preventing cancer, but others think it\'s not necessary since I\'m not really sexually active right now. I\'m just confused about whether I actually need it.'
            ],
            [
                'role' => 'user',
                'content' => 'That sounds like a lot to process with different opinions from your friends. It makes sense that you\'d feel confused. Can you tell me more about what\'s most important to you when it comes to making health decisions?'
            ],
            [
                'role' => 'assistant',
                'content' => 'I guess I want to make informed decisions, you know? I don\'t want to do something just because everyone else is doing it, but I also don\'t want to miss out on protecting myself if it\'s really important.'
            ],
            [
                'role' => 'user',
                'content' => 'I really appreciate that thoughtful approach - wanting to be informed and make decisions that are right for you. That tells me a lot about how you approach important choices. What kind of information would help you feel more confident about this decision?'
            ],
            [
                'role' => 'assistant',
                'content' => 'I think I\'d want to know more about what HPV actually is, how common it is, and what the risks really are. And also what the vaccine actually does - like, how effective is it?'
            ],
            [
                'role' => 'user',
                'content' => 'Those are excellent questions, and it sounds like having that factual information is really important for you to feel comfortable with whatever decision you make. I can definitely share some information about those topics. What else might influence your decision-making process?'
            ]
        ];
        
        $messageCount = 0;
        foreach ($messages as $index => $message) {
            $messageId = $this->storage->storeMessage(
                $sessionId,
                $message['role'],
                $message['content'],
                $index + 1
            );
            
            $this->logger->logMessageSent(
                $sessionId,
                $message['role'],
                strlen($message['content']),
                $index + 1
            );
            
            $messageCount++;
        }
        
        return [
            'messages' => $messages,
            'message_count' => $messageCount
        ];
    }
    
    /**
     * Generate AI feedback for the conversation
     * 
     * @param string $sessionId Session ID
     * @param array $sessionData Session information
     * @return array Feedback data
     */
    private function generateFeedback($sessionId, $sessionData)
    {
        // Simulate AI-generated feedback (in real implementation, this would come from your AI system)
        $aiGeneratedFeedback = "
**MI Performance Assessment for HPV Vaccine Discussion**

**1. COLLABORATION (7.5 pts): Met** - Excellent rapport building demonstrated through warm greeting and acknowledgment of the student's proactive health inquiry. The provider effectively positioned themselves as a partner in the decision-making process by asking about the student's values and decision-making preferences. The collaborative tone was maintained throughout the conversation.

**2. EVOCATION (7.5 pts): Met** - Strong evocation skills shown through open-ended questions that explored the student's motivations, values, and information needs. The provider skillfully drew out the student's own reasons for wanting to make informed decisions rather than imposing external motivations. Questions like 'What's most important to you when making health decisions?' effectively evoked the student's intrinsic motivations.

**3. ACCEPTANCE (7.5 pts): Met** - Demonstrated excellent acceptance through affirming the student's thoughtful approach to decision-making and reflecting their desire to be well-informed. The provider showed respect for the student's autonomy by not pressuring them toward any particular decision and instead supporting their information-gathering process.

**4. COMPASSION (7.5 pts): Partially Met** - Good empathetic responses were shown, particularly in acknowledging the confusion from conflicting information from friends. However, there were opportunities for deeper empathetic reflection of the student's emotional experience that could have been explored further.

**Overall Assessment:**
This was a strong MI performance demonstrating solid foundational skills. The provider effectively built rapport, explored motivations, and respected autonomy while maintaining a supportive, non-judgmental stance. The conversation successfully moved the student toward their own information-seeking goals rather than provider-imposed outcomes.

**Improvement Suggestions:**
- Consider using more reflective listening statements to deepen emotional understanding
- Explore the student's feelings about peer influence more thoroughly
- Use scaling questions to better understand confidence levels in decision-making
";
        
        // Parse the feedback using FeedbackUtils
        $scoreBreakdown = FeedbackUtils::getScoreBreakdown($aiGeneratedFeedback);
        
        // Store feedback in database
        $feedbackId = $this->storage->storeFeedback(
            $sessionId,
            $sessionData['student_name'],
            $sessionData['session_type'],
            $scoreBreakdown['components'],
            $scoreBreakdown['total_score'],
            $scoreBreakdown['percentage'],
            $aiGeneratedFeedback,
            'AI Evaluator v1.0'
        );
        
        // Log feedback generation
        $this->logger->logFeedbackGenerated(
            $sessionId,
            $sessionData['student_name'],
            $scoreBreakdown['total_score'],
            $scoreBreakdown['percentage'],
            $scoreBreakdown['performance_level'],
            $scoreBreakdown['component_count']
        );
        
        return array_merge($scoreBreakdown, [
            'feedback_id' => $feedbackId,
            'raw_feedback' => $aiGeneratedFeedback
        ]);
    }
    
    /**
     * Generate PDF report
     * 
     * @param string $sessionId Session ID
     * @param array $sessionData Session data
     * @param array $feedbackData Feedback data
     * @param array $chatHistory Chat messages
     * @return array PDF data
     */
    private function generatePdfReport($sessionId, $sessionData, $feedbackData, $chatHistory)
    {
        $startTime = microtime(true);
        
        // Generate PDF using PdfGenerator
        $pdfInfo = $this->pdfGenerator->generatePdfInfo(
            $sessionData['student_name'],
            $feedbackData['raw_feedback'],
            $chatHistory,
            $sessionData['session_type'],
            $sessionData['persona']
        );
        
        $generationTime = microtime(true) - $startTime;
        
        // Store PDF metadata in database
        $reportId = $this->storage->storePdfReport(
            $sessionId,
            $feedbackData['feedback_id'],
            $pdfInfo['filename'],
            null, // Could save to file system here
            $pdfInfo['size'],
            $pdfInfo['hash']
        );
        
        // Log PDF generation
        $this->logger->logPdfGenerated(
            $sessionId,
            $pdfInfo['filename'],
            $pdfInfo['size'],
            $generationTime
        );
        
        // Save PDF to temporary location for demonstration
        $tempPath = '/tmp/' . $pdfInfo['filename'];
        $this->pdfGenerator->savePdfToFile($pdfInfo['content'], $tempPath);
        
        return array_merge($pdfInfo, [
            'report_id' => $reportId,
            'generation_time' => $generationTime,
            'temp_path' => $tempPath
        ]);
    }
    
    /**
     * Complete the session
     * 
     * @param string $sessionId Session ID
     * @param int $messageCount Total messages in session
     * @return array Completion data
     */
    private function completeSession($sessionId, $messageCount)
    {
        // Update session status to completed
        $this->storage->updateSessionStatus($sessionId, 'completed');
        
        // Calculate session duration (simulated)
        $duration = rand(300, 900); // 5-15 minutes
        
        // Log session completion
        $this->logger->logSessionEnd($sessionId, $messageCount, $duration);
        
        // Log some performance metrics
        $this->logger->logPerformanceMetric($sessionId, 'session_duration', $duration, [
            'message_count' => $messageCount,
            'avg_message_length' => 85.3
        ]);
        
        $this->logger->logPerformanceMetric($sessionId, 'messages_per_minute', $messageCount / ($duration / 60), [
            'total_messages' => $messageCount,
            'duration_seconds' => $duration
        ]);
        
        return [
            'completed_at' => date('c'),
            'duration_seconds' => $duration,
            'message_count' => $messageCount,
            'status' => 'completed'
        ];
    }
    
    /**
     * Generate analytics and summary data
     * 
     * @param string $sessionId Session ID
     * @param string $studentName Student name
     * @return array Analytics data
     */
    private function generateAnalytics($sessionId, $studentName)
    {
        // Get session summary
        $sessionSummary = $this->storage->getSessionSummary($sessionId);
        
        // Get student performance history
        $studentPerformance = $this->storage->getStudentPerformance($studentName, null, 10);
        
        // Get log statistics
        $logStats = $this->storage->getLogStatistics($sessionId);
        
        // Get database health
        $dbHealth = $this->storage->getDatabaseHealth();
        
        return [
            'session_summary' => $sessionSummary,
            'student_performance' => $studentPerformance,
            'log_statistics' => $logStats,
            'database_health' => $dbHealth
        ];
    }
    
    /**
     * Demonstrate error handling
     * 
     * @return array Error handling results
     */
    public function demonstrateErrorHandling()
    {
        echo "\n🚨 Demonstrating Error Handling\n";
        echo str_repeat('=', 40) . "\n";
        
        $results = [];
        $testSessionId = 'error_test_' . uniqid();
        
        try {
            // Test 1: Invalid student name
            echo "Test 1: Invalid student name...\n";
            try {
                FeedbackUtils::validateStudentName('');
                $results['invalid_name'] = 'FAILED - Should have thrown exception';
            } catch (Exception $e) {
                $results['invalid_name'] = 'PASSED - ' . $e->getMessage();
                echo "   ✅ Caught invalid name error: " . $e->getMessage() . "\n";
            }
            
            // Test 2: Database connection error (simulated)
            echo "Test 2: Database error handling...\n";
            try {
                $badConfig = ['host' => 'nonexistent', 'dbname' => 'fake', 'username' => 'none', 'password' => 'wrong'];
                $badStorage = new SessionStorage($badConfig);
                $results['db_connection'] = 'FAILED - Should have thrown exception';
            } catch (Exception $e) {
                $results['db_connection'] = 'PASSED - ' . $e->getMessage();
                echo "   ✅ Caught database error: " . substr($e->getMessage(), 0, 50) . "...\n";
            }
            
            // Test 3: Component parsing edge cases
            echo "Test 3: Malformed feedback parsing...\n";
            $malformedFeedback = "This is not properly formatted feedback without components";
            $breakdown = FeedbackUtils::getScoreBreakdown($malformedFeedback);
            if (empty($breakdown['components'])) {
                $results['malformed_feedback'] = 'PASSED - Handled gracefully';
                echo "   ✅ Handled malformed feedback gracefully\n";
            } else {
                $results['malformed_feedback'] = 'FAILED - Should have found no components';
            }
            
            // Test 4: Logger error handling
            echo "Test 4: Logger error conditions...\n";
            try {
                $badLogger = new Logger(null, false, true, '/nonexistent/path');
                $results['logger_error'] = 'FAILED - Should have thrown exception';
            } catch (Exception $e) {
                $results['logger_error'] = 'PASSED - ' . $e->getMessage();
                echo "   ✅ Logger handled bad path: " . $e->getMessage() . "\n";
            }
            
        } catch (Exception $e) {
            $results['overall_error'] = $e->getMessage();
            echo "   ❌ Unexpected error: " . $e->getMessage() . "\n";
        }
        
        return $results;
    }
    
    /**
     * Run all self-tests for the utilities
     * 
     * @return array Self-test results
     */
    public function runAllSelfTests()
    {
        echo "\n🧪 Running Self-Tests for All Utilities\n";
        echo str_repeat('=', 50) . "\n";
        
        $allResults = [];
        
        // Test FeedbackUtils
        echo "Testing FeedbackUtils...\n";
        $feedbackResults = FeedbackUtils::runSelfTest();
        $allResults['FeedbackUtils'] = $feedbackResults;
        foreach ($feedbackResults as $test => $result) {
            $status = ($result === 'PASS') ? '✅' : '❌';
            echo "   $status $test: $result\n";
        }
        
        // Test Logger
        echo "\nTesting Logger...\n";
        $loggerResults = Logger::runSelfTest();
        $allResults['Logger'] = $loggerResults;
        foreach ($loggerResults as $test => $result) {
            $status = ($result === 'PASS') ? '✅' : '❌';
            echo "   $status $test: $result\n";
        }
        
        // Test SessionStorage (if database is available)
        echo "\nTesting SessionStorage...\n";
        try {
            $storageResults = $this->storage->runSelfTest();
            $allResults['SessionStorage'] = $storageResults;
            foreach ($storageResults as $test => $result) {
                $status = ($result === 'PASS') ? '✅' : '❌';
                echo "   $status $test: $result\n";
            }
        } catch (Exception $e) {
            echo "   ⚠️  SessionStorage test skipped: " . $e->getMessage() . "\n";
            $allResults['SessionStorage'] = ['skipped' => $e->getMessage()];
        }
        
        // Test PdfGenerator
        echo "\nTesting PdfGenerator...\n";
        $pdfResults = PdfGenerator::runSelfTest();
        $allResults['PdfGenerator'] = $pdfResults;
        foreach ($pdfResults as $test => $result) {
            $status = ($result === 'PASS') ? '✅' : '❌';
            echo "   $status $test: $result\n";
        }
        
        return $allResults;
    }
}

/**
 * Main execution when run directly
 */
if (basename(__FILE__) === basename($_SERVER['PHP_SELF'])) {
    echo "🎯 MI Chatbots LAMP-Stack Utilities - Complete Integration Example\n";
    echo str_repeat('=', 60) . "\n";
    echo "This example demonstrates a complete MI assessment workflow using all utilities.\n\n";
    
    // Configuration
    $dbConfig = [
        'host' => 'localhost',
        'dbname' => 'mi_chatbots',
        'username' => 'demo_user',
        'password' => 'demo_password',
        'charset' => 'utf8mb4'
    ];
    
    echo "⚙️ Configuration:\n";
    echo "   Database: {$dbConfig['host']}/{$dbConfig['dbname']}\n";
    echo "   Username: {$dbConfig['username']}\n";
    echo "   Log Directory: /tmp/mi_logs\n";
    echo "   PDF Output: /tmp/\n\n";
    
    try {
        // Initialize workflow
        $workflow = new MIAssessmentWorkflow($dbConfig);
        
        // Run self-tests first
        echo "🧪 Running Self-Tests...\n";
        $selfTestResults = $workflow->runAllSelfTests();
        
        // Check if core tests passed
        $coreTestsPassed = true;
        foreach (['FeedbackUtils', 'Logger', 'PdfGenerator'] as $utility) {
            if (isset($selfTestResults[$utility]['overall']) && $selfTestResults[$utility]['overall'] !== 'PASS') {
                $coreTestsPassed = false;
                break;
            }
        }
        
        if (!$coreTestsPassed) {
            echo "\n⚠️  Some core utilities failed self-tests. Continuing with demonstration...\n";
        }
        
        // Run complete workflow
        $workflowResults = $workflow->runCompleteWorkflow();
        
        // Demonstrate error handling
        $errorResults = $workflow->demonstrateErrorHandling();
        
        // Summary
        echo "\n📊 Execution Summary\n";
        echo str_repeat('=', 30) . "\n";
        echo "Workflow Status: " . $workflowResults['overall_status'] . "\n";
        
        if ($workflowResults['overall_status'] === 'SUCCESS') {
            echo "✅ Session Created: " . $workflowResults['session_creation']['session_id'] . "\n";
            echo "✅ Messages Processed: " . $workflowResults['conversation']['message_count'] . "\n";
            echo "✅ MI Score: " . $workflowResults['feedback']['total_score'] . "/30.0\n";
            echo "✅ Performance Level: " . $workflowResults['feedback']['performance_level'] . "\n";
            echo "✅ PDF Generated: " . $workflowResults['pdf']['filename'] . "\n";
            echo "✅ Session Completed\n";
        } else {
            echo "❌ Workflow failed: " . ($workflowResults['error'] ?? 'Unknown error') . "\n";
        }
        
        echo "\n💡 Next Steps:\n";
        echo "1. Configure your database connection in the \$dbConfig array\n";
        echo "2. Import the database schema: mysql -u user -p database < ../database/mi_sessions.sql\n";
        echo "3. Install Dompdf: composer require dompdf/dompdf\n";
        echo "4. Integrate these utilities into your web application\n";
        echo "5. Customize the feedback parsing for your specific AI output format\n";
        
    } catch (Exception $e) {
        echo "\n❌ Example execution failed: " . $e->getMessage() . "\n";
        echo "\nThis is likely due to database configuration or missing dependencies.\n";
        echo "Please check the README.md for setup instructions.\n";
    }
    
    echo "\n🔗 For more information, see:\n";
    echo "   - README.md for detailed usage instructions\n";
    echo "   - ../database/mi_sessions.sql for database schema\n";
    echo "   - Individual utility files for specific documentation\n";
    
    echo "\n✨ Example completed. Thank you for using MI Chatbots Utilities!\n";
}
?>