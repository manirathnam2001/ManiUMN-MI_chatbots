<?php
/**
 * test_utilities.php
 * 
 * Comprehensive test script for MI Chatbots LAMP utilities.
 * Tests all components: FeedbackUtils, Logger, SessionStorage, PdfGenerator
 * 
 * Run this script to validate your installation and configuration.
 * 
 * @package MIChatbots
 */

// Suppress warnings for testing environment
error_reporting(E_ERROR | E_PARSE | E_COMPILE_ERROR);
ini_set('display_errors', 1);

require_once '../FeedbackUtils.php';
require_once '../Logger.php';
require_once '../SessionStorage.php';
require_once '../PdfGenerator.php';

use MIChatbots\Utils\{FeedbackUtils, Logger, SessionStorage, PdfGenerator, PdfGeneratorFactory};

class MIUtilitiesTest {
    
    private $results = [];
    private $pdo = null;
    private $logger = null;
    private $storage = null;
    private $generator = null;
    
    public function __construct() {
        echo "<html><head><title>MI Utilities Test</title>";
        echo "<style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .test-section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .pass { color: green; font-weight: bold; }
                .fail { color: red; font-weight: bold; }
                .warning { color: orange; font-weight: bold; }
                .info { color: blue; }
                pre { background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }
                .summary { background: #e7f3ff; padding: 15px; border-radius: 5px; margin-top: 20px; }
              </style></head><body>";
        echo "<h1>🧪 MI Chatbots Utilities Test Suite</h1>";
        echo "<p>Testing all LAMP-stack utilities for compatibility and functionality.</p>";
    }
    
    public function runAllTests() {
        echo "<h2>Running Comprehensive Test Suite...</h2>";
        
        // Test each component
        $this->testFeedbackUtils();
        $this->testLogger();
        $this->testDatabaseConnection();
        $this->testSessionStorage();
        $this->testPdfGenerator();
        $this->testIntegration();
        
        // Display summary
        $this->displaySummary();
        
        echo "</body></html>";
    }
    
    private function testFeedbackUtils() {
        echo "<div class='test-section'>";
        echo "<h3>📊 Testing FeedbackUtils</h3>";
        
        try {
            // Test feedback parsing
            $sampleFeedback = "**1. COLLABORATION (7.5 pts): [Met] - Excellent partnership building with the patient**

**2. EVOCATION (7.5 pts): [Partially Met] - Good use of open questions, but could explore patient motivations more deeply**

**3. ACCEPTANCE (7.5 pts): [Met] - Demonstrated respect for patient autonomy and used effective reflective listening**

**4. COMPASSION (7.5 pts): [Not Met] - Showed warmth but could demonstrate more empathy**

### Improvement Suggestions:
- Use more reflective listening techniques
- Ask follow-up questions to better understand patient concerns
- Demonstrate more empathy in responses";
            
            // Test score parsing
            $scores = FeedbackUtils::parseFeedbackScores($sampleFeedback);
            $this->addResult('Feedback score parsing', count($scores) == 4, 
                           "Parsed " . count($scores) . " component scores");
            
            // Test score breakdown
            $breakdown = FeedbackUtils::getScoreBreakdown($sampleFeedback);
            $expectedTotal = 22.5; // 7.5 + 3.75 + 7.5 + 0
            $actualTotal = $breakdown['total_score'];
            $this->addResult('Score calculation', abs($actualTotal - $expectedTotal) < 0.1,
                           "Expected: {$expectedTotal}, Got: {$actualTotal}");
            
            // Test suggestion extraction
            $suggestions = FeedbackUtils::extractSuggestionsFromFeedback($sampleFeedback);
            $this->addResult('Suggestion extraction', count($suggestions) > 0,
                           "Extracted " . count($suggestions) . " suggestions");
            
            // Test name validation
            $validName = FeedbackUtils::validateStudentName('John Doe');
            $this->addResult('Name validation', $validName === 'John Doe',
                           "Validated name: {$validName}");
            
            // Test filename generation
            $filename = FeedbackUtils::createDownloadFilename('John Doe', 'HPV', 'Alex');
            $this->addResult('Filename generation', strpos($filename, '.pdf') !== false,
                           "Generated: {$filename}");
            
            // Test text sanitization
            $dirtyText = 'Text with "smart quotes" and — dashes';
            $cleanText = FeedbackUtils::sanitizeSpecialCharacters($dirtyText);
            $this->addResult('Text sanitization', $cleanText !== $dirtyText,
                           "Sanitized special characters");
            
            echo "<div class='pass'>✓ FeedbackUtils tests completed</div>";
            
        } catch (Exception $e) {
            $this->addResult('FeedbackUtils', false, "Error: " . $e->getMessage());
            echo "<div class='fail'>✗ FeedbackUtils tests failed: " . $e->getMessage() . "</div>";
        }
        
        echo "</div>";
    }
    
    private function testLogger() {
        echo "<div class='test-section'>";
        echo "<h3>📝 Testing Logger</h3>";
        
        try {
            // Test file logging only (no database required)
            $logFile = '/tmp/mi_test_' . time() . '.log';
            $this->logger = new Logger(null, $logFile, false, true, Logger::DEBUG);
            
            // Test basic logging
            $this->logger->log(Logger::INFO, Logger::CATEGORY_SYSTEM, 'Test log message', ['test' => true]);
            
            // Check if log file was created
            $logExists = file_exists($logFile);
            $this->addResult('Log file creation', $logExists, "Log file: {$logFile}");
            
            if ($logExists) {
                $logContent = file_get_contents($logFile);
                $hasTestMessage = strpos($logContent, 'Test log message') !== false;
                $this->addResult('Log message writing', $hasTestMessage, "Log content written successfully");
                
                // Clean up
                unlink($logFile);
            }
            
            // Test performance logger
            $performanceLogger = new \MIChatbots\Utils\PerformanceLogger($this->logger);
            $result = $performanceLogger->timeOperation('test_operation', function() {
                usleep(10000); // 0.01 second
                return 'test completed';
            });
            
            $this->addResult('Performance logging', $result === 'test completed',
                           "Performance operation completed");
            
            echo "<div class='pass'>✓ Logger tests completed</div>";
            
        } catch (Exception $e) {
            $this->addResult('Logger', false, "Error: " . $e->getMessage());
            echo "<div class='fail'>✗ Logger tests failed: " . $e->getMessage() . "</div>";
        }
        
        echo "</div>";
    }
    
    private function testDatabaseConnection() {
        echo "<div class='test-section'>";
        echo "<h3>🗄️ Testing Database Connection</h3>";
        
        try {
            // Try to load configuration
            $configFile = __DIR__ . '/config.php';
            if (!file_exists($configFile)) {
                echo "<div class='warning'>⚠️ No config.php found. Using default test configuration.</div>";
                $config = [
                    'database' => [
                        'host' => 'localhost',
                        'dbname' => 'mi_chatbots',
                        'username' => 'root',
                        'password' => ''
                    ]
                ];
            } else {
                $config = require $configFile;
            }
            
            // Attempt database connection
            try {
                $this->pdo = new PDO(
                    "mysql:host={$config['database']['host']};dbname={$config['database']['dbname']};charset=utf8mb4",
                    $config['database']['username'],
                    $config['database']['password'],
                    [
                        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                    ]
                );
                
                // Test basic query
                $stmt = $this->pdo->query("SELECT VERSION() as version");
                $version = $stmt->fetch()['version'];
                
                $this->addResult('Database connection', true, "MySQL version: {$version}");
                
                // Test required tables
                $requiredTables = ['sessions', 'conversations', 'feedback', 'pdf_exports', 'system_logs'];
                $existingTables = [];
                
                foreach ($requiredTables as $table) {
                    try {
                        $this->pdo->query("SELECT 1 FROM {$table} LIMIT 1");
                        $existingTables[] = $table;
                    } catch (Exception $e) {
                        // Table doesn't exist
                    }
                }
                
                $this->addResult('Database tables', count($existingTables) > 0,
                               "Found tables: " . implode(', ', $existingTables));
                
                if (count($existingTables) < count($requiredTables)) {
                    echo "<div class='warning'>⚠️ Some tables missing. Run database/mi_sessions.sql to create schema.</div>";
                }
                
            } catch (PDOException $e) {
                $this->addResult('Database connection', false, "Connection failed: " . $e->getMessage());
                echo "<div class='warning'>⚠️ Database connection failed. Tests will continue without database features.</div>";
                $this->pdo = null;
            }
            
        } catch (Exception $e) {
            $this->addResult('Database setup', false, "Error: " . $e->getMessage());
            echo "<div class='fail'>✗ Database setup failed: " . $e->getMessage() . "</div>";
        }
        
        echo "</div>";
    }
    
    private function testSessionStorage() {
        echo "<div class='test-section'>";
        echo "<h3>💾 Testing SessionStorage</h3>";
        
        if (!$this->pdo) {
            echo "<div class='warning'>⚠️ Skipping SessionStorage tests - no database connection</div>";
            echo "</div>";
            return;
        }
        
        try {
            $this->storage = new SessionStorage($this->pdo, $this->logger);
            
            // Test connection check
            $connectionTest = $this->storage->testConnection();
            $this->addResult('Storage connection test', $connectionTest['connection'],
                           "Database accessible: " . ($connectionTest['connection'] ? 'Yes' : 'No'));
            
            // Test session creation
            $sessionId = $this->storage->generateSessionId('test');
            $createResult = $this->storage->createSession($sessionId, 'Test Student', 'HPV', 'Test Persona');
            $this->addResult('Session creation', $createResult, "Session ID: {$sessionId}");
            
            if ($createResult) {
                // Test session retrieval
                $session = $this->storage->getSession($sessionId);
                $this->addResult('Session retrieval', $session !== null,
                               "Retrieved session: " . ($session ? 'Yes' : 'No'));
                
                // Test conversation storage
                $messages = [
                    ['role' => 'user', 'content' => 'Test message 1'],
                    ['role' => 'assistant', 'content' => 'Test response 1'],
                    ['role' => 'user', 'content' => 'Test message 2']
                ];
                
                $conversationResult = $this->storage->storeConversationMessages($sessionId, $messages);
                $this->addResult('Conversation storage', $conversationResult,
                               "Stored " . count($messages) . " messages");
                
                // Test feedback storage
                $testFeedback = "**1. COLLABORATION (7.5 pts): [Met] - Good work**";
                $feedbackResult = $this->storage->storeFeedback($sessionId, $testFeedback, [], 'Test Evaluator');
                $this->addResult('Feedback storage', $feedbackResult, "Feedback stored successfully");
                
                // Test PDF export recording
                $pdfResult = $this->storage->recordPdfExport($sessionId, 'test_report.pdf', null, 1024);
                $this->addResult('PDF export recording', $pdfResult, "PDF export recorded");
                
                // Test complete data retrieval
                $completeData = $this->storage->getCompleteSessionData($sessionId);
                $hasAllData = isset($completeData['session']) && 
                             isset($completeData['conversation']) && 
                             isset($completeData['feedback']);
                $this->addResult('Complete data retrieval', $hasAllData, "All data components present");
                
                // Clean up test data
                try {
                    $this->pdo->exec("DELETE FROM sessions WHERE session_id = '{$sessionId}'");
                } catch (Exception $e) {
                    // Cleanup failed, but test still passed
                }
            }
            
            echo "<div class='pass'>✓ SessionStorage tests completed</div>";
            
        } catch (Exception $e) {
            $this->addResult('SessionStorage', false, "Error: " . $e->getMessage());
            echo "<div class='fail'>✗ SessionStorage tests failed: " . $e->getMessage() . "</div>";
        }
        
        echo "</div>";
    }
    
    private function testPdfGenerator() {
        echo "<div class='test-section'>";
        echo "<h3>📄 Testing PdfGenerator</h3>";
        
        try {
            // Check if DomPDF is available (it won't be in this test environment)
            if (!class_exists('Dompdf\Dompdf')) {
                echo "<div class='warning'>⚠️ DomPDF not installed. Skipping PDF generation tests.</div>";
                echo "<div class='info'>💡 Install DomPDF with: composer require dompdf/dompdf</div>";
                $this->addResult('DomPDF availability', false, "DomPDF not installed");
                echo "</div>";
                return;
            }
            
            $this->generator = PdfGeneratorFactory::createStandard($this->logger);
            
            // Test data
            $studentName = 'Test Student';
            $feedback = "**1. COLLABORATION (7.5 pts): [Met] - Excellent work**";
            $chatHistory = [
                ['role' => 'user', 'content' => 'Hello'],
                ['role' => 'assistant', 'content' => 'Hi there!']
            ];
            
            // Test PDF generation
            $pdfContent = $this->generator->generatePerformanceReport($studentName, $feedback, $chatHistory);
            $this->addResult('PDF generation', strlen($pdfContent) > 0,
                           "PDF size: " . number_format(strlen($pdfContent)) . " bytes");
            
            // Test transcript-only PDF
            $transcriptPdf = $this->generator->generateTranscriptOnly($studentName, $chatHistory);
            $this->addResult('Transcript PDF', strlen($transcriptPdf) > 0,
                           "Transcript PDF size: " . number_format(strlen($transcriptPdf)) . " bytes");
            
            // Test file saving
            $tempFile = '/tmp/test_mi_report_' . time() . '.pdf';
            $saveResult = $this->generator->savePdfToFile($pdfContent, $tempFile);
            $this->addResult('PDF file saving', $saveResult && file_exists($tempFile),
                           "Saved to: {$tempFile}");
            
            if (file_exists($tempFile)) {
                unlink($tempFile); // Clean up
            }
            
            echo "<div class='pass'>✓ PdfGenerator tests completed</div>";
            
        } catch (Exception $e) {
            $this->addResult('PdfGenerator', false, "Error: " . $e->getMessage());
            echo "<div class='fail'>✗ PdfGenerator tests failed: " . $e->getMessage() . "</div>";
        }
        
        echo "</div>";
    }
    
    private function testIntegration() {
        echo "<div class='test-section'>";
        echo "<h3>🔗 Testing Component Integration</h3>";
        
        try {
            // Test that all components can work together
            if ($this->pdo && $this->storage && $this->logger) {
                // Create a complete workflow test
                $sessionId = $this->storage->generateSessionId('integration_test');
                
                // Create session with logging
                $createResult = $this->storage->createSession($sessionId, 'Integration Test Student', 'HPV', 'Test Persona');
                
                if ($createResult) {
                    // Store conversation
                    $messages = [
                        ['role' => 'assistant', 'content' => 'Welcome to the integration test!'],
                        ['role' => 'user', 'content' => 'This is a test conversation.'],
                        ['role' => 'assistant', 'content' => 'Great! The integration is working.']
                    ];
                    
                    $this->storage->storeConversationMessages($sessionId, $messages);
                    
                    // Process feedback
                    $feedback = "**1. COLLABORATION (7.5 pts): [Met] - Integration test successful**";
                    $breakdown = FeedbackUtils::getScoreBreakdown($feedback);
                    
                    // Store feedback
                    $this->storage->storeFeedback($sessionId, $feedback, [], 'Integration Test');
                    
                    // Complete session
                    $this->storage->updateSessionStatus($sessionId, 'COMPLETED');
                    
                    // Verify all data
                    $completeData = $this->storage->getCompleteSessionData($sessionId);
                    
                    $integrationWorking = 
                        isset($completeData['session']) &&
                        count($completeData['conversation']) === 3 &&
                        isset($completeData['feedback']) &&
                        $completeData['session']['status'] === 'COMPLETED';
                    
                    $this->addResult('Full integration workflow', $integrationWorking,
                                   "Complete workflow executed successfully");
                    
                    // Clean up
                    try {
                        $this->pdo->exec("DELETE FROM sessions WHERE session_id = '{$sessionId}'");
                    } catch (Exception $e) {
                        // Cleanup failed, but test still passed
                    }
                } else {
                    $this->addResult('Integration workflow', false, "Failed to create test session");
                }
            } else {
                echo "<div class='warning'>⚠️ Skipping integration tests - missing components</div>";
            }
            
            echo "<div class='pass'>✓ Integration tests completed</div>";
            
        } catch (Exception $e) {
            $this->addResult('Integration', false, "Error: " . $e->getMessage());
            echo "<div class='fail'>✗ Integration tests failed: " . $e->getMessage() . "</div>";
        }
        
        echo "</div>";
    }
    
    private function addResult($test, $passed, $details = '') {
        $this->results[] = [
            'test' => $test,
            'passed' => $passed,
            'details' => $details
        ];
        
        $status = $passed ? '<span class="pass">✓ PASS</span>' : '<span class="fail">✗ FAIL</span>';
        echo "<div>{$status} {$test}";
        if ($details) {
            echo " - {$details}";
        }
        echo "</div>";
    }
    
    private function displaySummary() {
        $total = count($this->results);
        $passed = count(array_filter($this->results, function($r) { return $r['passed']; }));
        $failed = $total - $passed;
        
        echo "<div class='summary'>";
        echo "<h2>📋 Test Summary</h2>";
        echo "<p><strong>Total Tests:</strong> {$total}</p>";
        echo "<p><strong class='pass'>Passed:</strong> {$passed}</p>";
        echo "<p><strong class='fail'>Failed:</strong> {$failed}</p>";
        
        if ($failed > 0) {
            echo "<h3>Failed Tests:</h3>";
            echo "<ul>";
            foreach ($this->results as $result) {
                if (!$result['passed']) {
                    echo "<li><strong>{$result['test']}</strong>: {$result['details']}</li>";
                }
            }
            echo "</ul>";
        }
        
        if ($passed === $total) {
            echo "<div class='pass'>🎉 All tests passed! The MI Utilities are working correctly.</div>";
        } else {
            echo "<div class='warning'>⚠️ Some tests failed. Check the configuration and requirements above.</div>";
        }
        
        echo "<h3>Next Steps:</h3>";
        echo "<ul>";
        echo "<li>If database tests failed: Import database/mi_sessions.sql schema</li>";
        echo "<li>If PDF tests failed: Run <code>composer require dompdf/dompdf</code></li>";
        echo "<li>Configure your environment by copying config_example.php to config.php</li>";
        echo "<li>Test the integration with your Python applications</li>";
        echo "</ul>";
        
        echo "</div>";
    }
}

// Run tests if accessed directly
if (basename(__FILE__) == basename($_SERVER['PHP_SELF'])) {
    $test = new MIUtilitiesTest();
    $test->runAllTests();
}

?>