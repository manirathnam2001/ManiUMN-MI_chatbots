<?php
/**
 * example_integration.php - Complete integration example
 * 
 * Demonstrates how to use all MI LAMP-stack utilities together
 * This is a simplified example for testing and demonstration purposes
 * 
 * @package MIUtils
 * @version 1.0
 */

// Include all utilities
require_once __DIR__ . '/FeedbackUtils.php';
require_once __DIR__ . '/SessionStorage.php';
require_once __DIR__ . '/Logger.php';
require_once __DIR__ . '/PdfGenerator.php';

/**
 * Simple integration example
 */
function runMIAssessmentExample() {
    echo "=== MI Assessment Integration Example ===\n\n";
    
    try {
        // 1. Initialize components (using mock data since we don't have a real database)
        echo "1. Initializing system components...\n";
        
        // For this example, we'll use file-only logging
        $logger = new Logger(null, true, '/tmp/mi_integration_test.log', Logger::DEBUG);
        $pdfGenerator = new PdfGenerator();
        
        // Sample session data
        $sessionId = 'example_session_' . uniqid();
        $studentName = 'Jane Smith';
        $sessionType = 'HPV';
        $evaluator = 'AI_Assessment_System';
        
        echo "✓ Components initialized\n";
        echo "  Session ID: $sessionId\n";
        echo "  Student: $studentName\n";
        echo "  Type: $sessionType\n\n";
        
        // 2. Log session start
        echo "2. Starting assessment session...\n";
        $logger->logSessionStart($sessionId, $studentName, $sessionType);
        echo "✓ Session started and logged\n\n";
        
        // 3. Sample conversation
        echo "3. Processing conversation messages...\n";
        $chatHistory = [
            ['role' => 'user', 'content' => 'I heard the HPV vaccine can be dangerous. Is that true?'],
            ['role' => 'assistant', 'content' => 'I understand your concern about vaccine safety. That\'s a very important question. Can you tell me more about what specific things you\'ve heard that worry you?'],
            ['role' => 'user', 'content' => 'Well, I read online that it can cause serious side effects.'],
            ['role' => 'assistant', 'content' => 'I can see why reading about side effects would be concerning. It sounds like you want to make sure you\'re making a safe choice for your health. What would help you feel more confident about the information you\'re getting?'],
            ['role' => 'user', 'content' => 'I guess I\'d like to know what the actual risks are compared to the benefits.'],
            ['role' => 'assistant', 'content' => 'That\'s a really thoughtful approach - wanting to understand both sides. You\'re clearly someone who likes to make informed decisions. Would it be helpful if we looked at some reliable information together about both the benefits and the potential risks?']
        ];
        
        foreach ($chatHistory as $message) {
            $logger->logMessage($sessionId, $message['role'], strlen($message['content']));
        }
        
        echo "✓ Logged " . count($chatHistory) . " conversation messages\n\n";
        
        // 4. Generate feedback
        echo "4. Generating MI assessment feedback...\n";
        
        // Sample feedback (in real application, this would come from AI/LLM)
        $rawFeedback = "
## Motivational Interviewing Assessment Results

**1. COLLABORATION (7.5 pts): [Met] - Student demonstrated excellent partnership building by asking open-ended questions and showing genuine interest in the patient's concerns rather than immediately contradicting them.**

**2. EVOCATION (7.5 pts): [Partially Met] - Student made good efforts to draw out the patient's own motivations by asking about their decision-making process, though could have explored more about the patient's values and personal reasons for considering vaccination.**

**3. ACCEPTANCE (7.5 pts): [Met] - Student showed strong acceptance by acknowledging the patient's concerns as valid and respecting their autonomy to make informed decisions without being judgmental about their initial skepticism.**

**4. COMPASSION (7.5 pts): [Partially Met] - Student demonstrated warmth and understanding, particularly in acknowledging the patient's concerns, though could have shown more empathy for the emotional aspects of the patient's worry.**

### Improvement Suggestions:
- Continue using open-ended questions to explore patient motivations
- Consider asking more about the patient's personal values and what matters most to them
- Practice reflecting emotions as well as content
- Explore what 'making an informed decision' means to this specific patient

### Overall Strengths:
- Excellent use of reflective listening
- Strong respect for patient autonomy
- Good use of affirmations about the patient's thoughtful approach
        ";
        
        // Parse feedback and get scores
        $scoreBreakdown = FeedbackUtils::getScoreBreakdown($rawFeedback);
        
        echo "✓ Feedback generated and parsed\n";
        echo "  Total Score: {$scoreBreakdown['total_score']}/30 ({$scoreBreakdown['percentage']}%)\n";
        echo "  Performance Level: {$scoreBreakdown['performance_level']}\n";
        echo "  Components Analyzed: " . count($scoreBreakdown['components']) . "\n\n";
        
        // Log feedback generation
        $logger->logFeedbackGenerated(
            $sessionId,
            $studentName,
            $sessionType,
            $scoreBreakdown['total_score'],
            $scoreBreakdown['percentage']
        );
        
        // 5. Generate PDF report
        echo "5. Generating PDF report...\n";
        
        try {
            $pdfContent = $pdfGenerator->generatePdfReport(
                $studentName,
                $rawFeedback,
                $chatHistory,
                $sessionType,
                $evaluator
            );
            
            $filename = $pdfGenerator->generateFilename($sessionType, $studentName, $evaluator);
            $filepath = $pdfGenerator->savePdfToFile($pdfContent, $filename, '/tmp');
            
            echo "✓ PDF generated successfully\n";
            echo "  Filename: $filename\n";
            echo "  Size: " . formatBytes(strlen($pdfContent)) . "\n";
            echo "  Path: $filepath\n\n";
            
            // Log PDF generation
            $logger->logPdfGenerated($sessionId, $studentName, $filename, strlen($pdfContent));
            
        } catch (Exception $e) {
            echo "⚠ PDF generation skipped (Dompdf not installed): " . $e->getMessage() . "\n\n";
        }
        
        // 6. Complete session
        echo "6. Completing assessment session...\n";
        $logger->logSessionEnd($sessionId, count($chatHistory));
        echo "✓ Session completed and logged\n\n";
        
        // 7. Display summary
        echo "7. Assessment Summary:\n";
        echo "   Student Name: $studentName\n";
        echo "   Session Type: $sessionType\n";
        echo "   Total Messages: " . count($chatHistory) . "\n";
        echo "   Final Score: {$scoreBreakdown['total_score']}/30 ({$scoreBreakdown['percentage']}%)\n";
        echo "   Performance Level: {$scoreBreakdown['performance_level']}\n";
        
        // Show component breakdown
        echo "\n   Component Breakdown:\n";
        foreach ($scoreBreakdown['components'] as $component) {
            echo "   - {$component['component']}: {$component['status']} ({$component['score']} pts)\n";
        }
        
        // Show some suggestions
        $suggestions = FeedbackUtils::extractSuggestionsFromFeedback($rawFeedback);
        if (!empty($suggestions)) {
            echo "\n   Key Suggestions:\n";
            foreach (array_slice($suggestions, 0, 3) as $suggestion) {
                echo "   • " . substr($suggestion, 0, 80) . "...\n";
            }
        }
        
        echo "\n=== Integration Example Completed Successfully! ===\n";
        
        // Show log file location
        echo "\nLog file created at: /tmp/mi_integration_test.log\n";
        if (file_exists('/tmp/mi_integration_test.log')) {
            echo "Log entries: " . count(file('/tmp/mi_integration_test.log')) . "\n";
        }
        
        return true;
        
    } catch (Exception $e) {
        echo "✗ Integration example failed: " . $e->getMessage() . "\n";
        echo "Stack trace: " . $e->getTraceAsString() . "\n";
        return false;
    }
}

/**
 * Format bytes for display
 */
function formatBytes($bytes, $precision = 2) {
    $units = ['B', 'KB', 'MB', 'GB'];
    for ($i = 0; $bytes > 1024; $i++) {
        $bytes /= 1024;
    }
    return round($bytes, $precision) . ' ' . $units[$i];
}

// Run the example if this file is executed directly
if (basename(__FILE__) == basename($_SERVER["SCRIPT_FILENAME"])) {
    runMIAssessmentExample();
}
?>