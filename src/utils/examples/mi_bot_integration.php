<?php
/**
 * mi_bot_integration.php
 * 
 * Example integration showing how to connect existing Python MI chatbots
 * with the new LAMP-stack utilities for database storage, logging, and PDF generation.
 * 
 * This file demonstrates the bridge between Python Streamlit apps and PHP utilities.
 * 
 * @package MIChatbots
 * @author MI Chatbots System
 * @version 1.0.0
 */

require_once '../vendor/autoload.php';
require_once '../FeedbackUtils.php';
require_once '../Logger.php';
require_once '../SessionStorage.php';
require_once '../PdfGenerator.php';

use MIChatbots\Utils\{SessionStorage, Logger, FeedbackUtils, PdfGenerator, PdfGeneratorFactory};

/**
 * MI Bot Integration Class
 * Provides bridge between Python applications and PHP utilities
 */
class MIBotIntegration {
    
    private $storage;
    private $logger;
    private $pdfGenerator;
    
    public function __construct($databaseConfig) {
        // Initialize database connection
        $pdo = new PDO(
            "mysql:host={$databaseConfig['host']};dbname={$databaseConfig['dbname']};charset=utf8mb4",
            $databaseConfig['username'],
            $databaseConfig['password'],
            [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            ]
        );
        
        // Initialize components
        $this->logger = new Logger($pdo, '/var/log/mi_chatbots.log', true, true, Logger::INFO);
        $this->storage = new SessionStorage($pdo, $this->logger);
        $this->pdfGenerator = PdfGeneratorFactory::createStandard($this->logger);
    }
    
    /**
     * Handle session creation from Python app
     * Expected to be called via HTTP POST from Python
     */
    public function handleCreateSession() {
        try {
            $input = json_decode(file_get_contents('php://input'), true);
            
            $studentName = FeedbackUtils::validateStudentName($input['student_name']);
            $sessionType = $input['session_type'] ?? 'HPV';
            $persona = $input['persona'] ?? null;
            
            $sessionId = $this->storage->generateSessionId();
            $success = $this->storage->createSession($sessionId, $studentName, $sessionType, $persona);
            
            if ($success) {
                header('Content-Type: application/json');
                echo json_encode([
                    'success' => true,
                    'session_id' => $sessionId,
                    'message' => 'Session created successfully'
                ]);
            } else {
                throw new Exception('Failed to create session in database');
            }
            
        } catch (Exception $e) {
            $this->logger->logError('Session creation failed via API', $e);
            http_response_code(500);
            header('Content-Type: application/json');
            echo json_encode([
                'success' => false,
                'error' => $e->getMessage()
            ]);
        }
    }
    
    /**
     * Handle conversation storage from Python app
     * Expected to receive complete conversation history
     */
    public function handleStoreConversation() {
        try {
            $input = json_decode(file_get_contents('php://input'), true);
            
            $sessionId = $input['session_id'];
            $messages = $input['messages'];
            
            // Validate session exists
            $session = $this->storage->getSession($sessionId);
            if (!$session) {
                throw new Exception('Session not found');
            }
            
            // Store conversation messages
            $success = $this->storage->storeConversationMessages($sessionId, $messages);
            
            if ($success) {
                header('Content-Type: application/json');
                echo json_encode([
                    'success' => true,
                    'message' => 'Conversation stored successfully',
                    'message_count' => count($messages)
                ]);
            } else {
                throw new Exception('Failed to store conversation');
            }
            
        } catch (Exception $e) {
            $this->logger->logError('Conversation storage failed via API', $e);
            http_response_code(500);
            header('Content-Type: application/json');
            echo json_encode([
                'success' => false,
                'error' => $e->getMessage()
            ]);
        }
    }
    
    /**
     * Handle feedback submission from Python app
     * Processes AI-generated feedback and stores with component scoring
     */
    public function handleSubmitFeedback() {
        try {
            $input = json_decode(file_get_contents('php://input'), true);
            
            $sessionId = $input['session_id'];
            $feedbackContent = $input['feedback_content'];
            $evaluator = $input['evaluator'] ?? 'AI Assistant';
            $timestamp = $input['timestamp'] ?? date('Y-m-d H:i:s');
            
            // Validate session exists
            $session = $this->storage->getSession($sessionId);
            if (!$session) {
                throw new Exception('Session not found');
            }
            
            // Process feedback to extract scores
            $componentScores = [];
            try {
                $componentScores = FeedbackUtils::parseFeedbackScores($feedbackContent);
            } catch (Exception $e) {
                $this->logger->log(Logger::WARNING, Logger::CATEGORY_FEEDBACK,
                    'Could not parse component scores from feedback', [
                        'session_id' => $sessionId,
                        'error' => $e->getMessage()
                    ]);
            }
            
            // Store feedback
            $success = $this->storage->storeFeedback($sessionId, $feedbackContent, $componentScores, $evaluator);
            
            // Update session status to completed
            $this->storage->updateSessionStatus($sessionId, 'COMPLETED');
            
            // Get score breakdown for response
            $breakdown = FeedbackUtils::getScoreBreakdown($feedbackContent);
            
            if ($success) {
                header('Content-Type: application/json');
                echo json_encode([
                    'success' => true,
                    'message' => 'Feedback stored successfully',
                    'score_breakdown' => $breakdown
                ]);
            } else {
                throw new Exception('Failed to store feedback');
            }
            
        } catch (Exception $e) {
            $this->logger->logError('Feedback submission failed via API', $e);
            http_response_code(500);
            header('Content-Type: application/json');
            echo json_encode([
                'success' => false,
                'error' => $e->getMessage()
            ]);
        }
    }
    
    /**
     * Handle PDF generation request from Python app
     * Generates and returns PDF or provides download URL
     */
    public function handleGeneratePdf() {
        try {
            $sessionId = $_GET['session_id'] ?? null;
            $downloadMode = $_GET['download'] ?? 'inline'; // inline or attachment
            
            if (!$sessionId) {
                throw new Exception('Session ID required');
            }
            
            // Get complete session data
            $sessionData = $this->storage->getCompleteSessionData($sessionId);
            
            if (!$sessionData['session']) {
                throw new Exception('Session not found');
            }
            
            // Generate PDF
            $pdfContent = $this->pdfGenerator->generatePerformanceReport(
                $sessionData['session']['student_name'],
                $sessionData['feedback']['feedback_content'] ?? 'No feedback available',
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
            $this->storage->recordPdfExport($sessionId, $filename, null, strlen($pdfContent));
            $this->storage->recordPdfDownload($sessionId, $filename);
            
            // Set headers and output PDF
            $this->pdfGenerator->generateDownloadHeaders($filename, strlen($pdfContent), $downloadMode === 'inline');
            echo $pdfContent;
            
        } catch (Exception $e) {
            $this->logger->logError('PDF generation failed via API', $e);
            http_response_code(500);
            header('Content-Type: application/json');
            echo json_encode([
                'success' => false,
                'error' => $e->getMessage()
            ]);
        }
    }
    
    /**
     * Handle session data retrieval for Python app
     * Returns complete session information including stats
     */
    public function handleGetSession() {
        try {
            $sessionId = $_GET['session_id'] ?? null;
            
            if (!$sessionId) {
                throw new Exception('Session ID required');
            }
            
            // Get complete session data
            $sessionData = $this->storage->getCompleteSessionData($sessionId);
            
            if (!$sessionData['session']) {
                throw new Exception('Session not found');
            }
            
            // Add score breakdown if feedback exists
            if ($sessionData['feedback']) {
                $scoreBreakdown = FeedbackUtils::getScoreBreakdown($sessionData['feedback']['feedback_content']);
                $sessionData['score_breakdown'] = $scoreBreakdown;
            }
            
            // Add performance metrics
            $sessionData['metrics'] = [
                'message_count' => count($sessionData['conversation']),
                'pdf_count' => count($sessionData['pdf_exports']),
                'session_duration' => $sessionData['session']['session_duration'],
                'completion_status' => $sessionData['session']['status']
            ];
            
            header('Content-Type: application/json');
            echo json_encode([
                'success' => true,
                'data' => $sessionData
            ]);
            
        } catch (Exception $e) {
            $this->logger->logError('Session retrieval failed via API', $e);
            http_response_code(500);
            header('Content-Type: application/json');
            echo json_encode([
                'success' => false,
                'error' => $e->getMessage()
            ]);
        }
    }
    
    /**
     * Handle student session history retrieval
     * Returns list of sessions for a student
     */
    public function handleGetStudentSessions() {
        try {
            $studentName = $_GET['student_name'] ?? null;
            $limit = min((int)($_GET['limit'] ?? 50), 100); // Max 100 sessions
            $offset = max((int)($_GET['offset'] ?? 0), 0);
            
            if (!$studentName) {
                throw new Exception('Student name required');
            }
            
            $sessions = $this->storage->getSessionsByStudent($studentName, $limit, $offset);
            
            // Add score information for each session
            foreach ($sessions as &$session) {
                $feedback = $this->storage->getFeedback($session['session_id']);
                if ($feedback) {
                    $session['total_score'] = $feedback['total_score'];
                    $session['percentage_score'] = $feedback['percentage_score'];
                    $session['feedback_date'] = $feedback['created_at'];
                }
            }
            
            header('Content-Type: application/json');
            echo json_encode([
                'success' => true,
                'sessions' => $sessions,
                'pagination' => [
                    'limit' => $limit,
                    'offset' => $offset,
                    'has_more' => count($sessions) === $limit
                ]
            ]);
            
        } catch (Exception $e) {
            $this->logger->logError('Student sessions retrieval failed via API', $e);
            http_response_code(500);
            header('Content-Type: application/json');
            echo json_encode([
                'success' => false,
                'error' => $e->getMessage()
            ]);
        }
    }
    
    /**
     * Handle system health check
     * Returns system status for monitoring
     */
    public function handleHealthCheck() {
        try {
            $health = [
                'status' => 'healthy',
                'timestamp' => date('c'),
                'version' => '1.0.0',
                'checks' => []
            ];
            
            // Database check
            $connectionTest = $this->storage->testConnection();
            $health['checks']['database'] = [
                'status' => $connectionTest['connection'] ? 'healthy' : 'unhealthy',
                'version' => $connectionTest['version'],
                'tables_accessible' => count(array_filter($connectionTest['tables']))
            ];
            
            // Memory check
            $memoryUsage = memory_get_usage(true) / 1024 / 1024;
            $memoryLimit = (int)ini_get('memory_limit');
            
            $health['checks']['memory'] = [
                'status' => $memoryUsage < ($memoryLimit * 0.8) ? 'healthy' : 'warning',
                'usage_mb' => round($memoryUsage, 2),
                'limit_mb' => $memoryLimit
            ];
            
            // Recent activity check
            $recentSessions = $this->storage->searchSessions([
                'date_from' => date('Y-m-d H:i:s', strtotime('-24 hours'))
            ], 1);
            
            $health['checks']['activity'] = [
                'status' => 'healthy',
                'recent_sessions_24h' => count($recentSessions) > 0 ? 'active' : 'quiet'
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
            
            header('Content-Type: application/json');
            echo json_encode($health, JSON_PRETTY_PRINT);
            
        } catch (Exception $e) {
            $this->logger->logError('Health check failed', $e);
            http_response_code(500);
            header('Content-Type: application/json');
            echo json_encode([
                'status' => 'unhealthy',
                'error' => $e->getMessage(),
                'timestamp' => date('c')
            ]);
        }
    }
}

// ============================================================================
// Request Router
// ============================================================================

// Load configuration
$config = [
    'database' => [
        'host' => $_ENV['DB_HOST'] ?? 'localhost',
        'dbname' => $_ENV['DB_NAME'] ?? 'mi_chatbots',
        'username' => $_ENV['DB_USER'] ?? 'mi_app',
        'password' => $_ENV['DB_PASS'] ?? ''
    ]
];

// Initialize integration
$integration = new MIBotIntegration($config['database']);

// Route requests based on action parameter
$action = $_REQUEST['action'] ?? '';

switch ($action) {
    case 'create_session':
        $integration->handleCreateSession();
        break;
        
    case 'store_conversation':
        $integration->handleStoreConversation();
        break;
        
    case 'submit_feedback':
        $integration->handleSubmitFeedback();
        break;
        
    case 'generate_pdf':
        $integration->handleGeneratePdf();
        break;
        
    case 'get_session':
        $integration->handleGetSession();
        break;
        
    case 'get_student_sessions':
        $integration->handleGetStudentSessions();
        break;
        
    case 'health_check':
        $integration->handleHealthCheck();
        break;
        
    default:
        http_response_code(400);
        header('Content-Type: application/json');
        echo json_encode([
            'success' => false,
            'error' => 'Invalid or missing action parameter',
            'available_actions' => [
                'create_session',
                'store_conversation', 
                'submit_feedback',
                'generate_pdf',
                'get_session',
                'get_student_sessions',
                'health_check'
            ]
        ]);
}

?>