<?php
/**
 * PdfGenerator.php
 * 
 * LAMP-compatible PDF generation utility for MI chatbot performance reports
 * using DomPDF library. Provides comprehensive PDF generation with consistent
 * styling, scoring tables, and conversation transcripts.
 * 
 * This class mirrors the functionality of the Python pdf_utils.py module
 * while being compatible with LAMP stack environments.
 * 
 * PHP Version: 7.4+
 * Dependencies: DomPDF (via Composer), FeedbackUtils, Logger (optional)
 * 
 * @package MIChatbots
 * @author MI Chatbots System
 * @version 1.0.0
 * @since 2024
 */

namespace MIChatbots\Utils;

// Composer autoload for DomPDF (uncomment when DomPDF is installed)
// require_once __DIR__ . '/../../vendor/autoload.php';

require_once 'FeedbackUtils.php';
require_once 'Logger.php';

use Dompdf\Dompdf;
use Dompdf\Options;

/**
 * Class PdfGenerator
 * Professional PDF generation for MI performance reports
 */
class PdfGenerator {
    
    private $logger;
    private $dompdfOptions;
    
    /**
     * Constructor
     * 
     * @param Logger|null $logger Optional logger instance
     * @param array $options DomPDF configuration options
     */
    public function __construct(Logger $logger = null, $options = []) {
        $this->logger = $logger;
        
        // Configure DomPDF options
        $this->dompdfOptions = new Options();
        $this->dompdfOptions->set('defaultFont', 'Helvetica');
        $this->dompdfOptions->set('isRemoteEnabled', true);
        $this->dompdfOptions->set('isHtml5ParserEnabled', true);
        $this->dompdfOptions->set('isFontSubsettingEnabled', true);
        
        // Apply custom options
        foreach ($options as $key => $value) {
            $this->dompdfOptions->set($key, $value);
        }
    }
    
    /**
     * Generate comprehensive MI performance report PDF
     * 
     * @param string $studentName Student name
     * @param string $rawFeedback Complete feedback text
     * @param array $chatHistory Conversation messages
     * @param string $sessionType Session type (HPV, OHI, etc.)
     * @param array $options Additional generation options
     * @return string PDF content as binary string
     * @throws Exception If PDF generation fails
     */
    public function generatePerformanceReport($studentName, $rawFeedback, $chatHistory, $sessionType = 'HPV Vaccine', $options = []) {
        $startTime = microtime(true);
        $startMemory = memory_get_usage(true);
        
        try {
            // Validate inputs
            $validatedName = FeedbackUtils::validateStudentName($studentName);
            $cleanFeedback = FeedbackUtils::sanitizeSpecialCharacters($rawFeedback);
            
            // Validate feedback completeness
            $validation = FeedbackUtils::validateFeedbackCompleteness($cleanFeedback);
            if (!$validation['is_valid'] && $this->logger) {
                $this->logger->log(Logger::WARNING, Logger::CATEGORY_PDF_GENERATION,
                    "Feedback may be incomplete", [
                        'missing_components' => $validation['missing_components'],
                        'student_name' => $validatedName
                    ]);
            }
            
            // Generate HTML content
            $htmlContent = $this->generateHtmlContent($validatedName, $cleanFeedback, $chatHistory, $sessionType, $options);
            
            // Create DomPDF instance
            $dompdf = new Dompdf($this->dompdfOptions);
            $dompdf->loadHtml($htmlContent);
            $dompdf->setPaper('A4', 'portrait');
            
            // Render PDF
            $dompdf->render();
            
            // Get PDF content
            $pdfContent = $dompdf->output();
            
            // Log performance metrics
            if ($this->logger) {
                $executionTime = microtime(true) - $startTime;
                $memoryUsed = memory_get_usage(true) - $startMemory;
                
                $this->logger->logPerformance('pdf_generation', $executionTime, $memoryUsed, null, [
                    'student_name' => $validatedName,
                    'session_type' => $sessionType,
                    'pdf_size_bytes' => strlen($pdfContent),
                    'message_count' => count($chatHistory),
                    'feedback_length' => strlen($cleanFeedback)
                ]);
            }
            
            return $pdfContent;
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("PDF generation failed for student: {$studentName}", $e);
            }
            throw new \Exception("PDF generation failed: " . $e->getMessage());
        }
    }
    
    /**
     * Generate HTML content for PDF
     * 
     * @param string $studentName Validated student name
     * @param string $feedback Clean feedback text
     * @param array $chatHistory Conversation messages
     * @param string $sessionType Session type
     * @param array $options Generation options
     * @return string Complete HTML content
     */
    private function generateHtmlContent($studentName, $feedback, $chatHistory, $sessionType, $options) {
        $html = $this->getHtmlTemplate();
        
        // Replace placeholders
        $replacements = [
            '{{TITLE}}' => "MI Performance Report - {$sessionType}",
            '{{STUDENT_NAME}}' => htmlspecialchars($studentName),
            '{{SESSION_TYPE}}' => htmlspecialchars($sessionType),
            '{{GENERATED_DATE}}' => date('Y-m-d H:i:s T'),
            '{{EVALUATION_TIMESTAMP}}' => $this->extractEvaluationTimestamp($feedback),
            '{{SCORE_BREAKDOWN_TABLE}}' => $this->generateScoreBreakdownTable($feedback),
            '{{IMPROVEMENT_SUGGESTIONS}}' => $this->generateImprovementSuggestions($feedback),
            '{{CONVERSATION_TRANSCRIPT}}' => $this->generateConversationTranscript($chatHistory),
            '{{FOOTER_INFO}}' => $this->generateFooterInfo()
        ];
        
        foreach ($replacements as $placeholder => $value) {
            $html = str_replace($placeholder, $value, $html);
        }
        
        return $html;
    }
    
    /**
     * Get base HTML template for PDF
     * 
     * @return string HTML template with placeholders
     */
    private function getHtmlTemplate() {
        return '
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}}</title>
    <style>
        @page {
            margin: 1in;
            size: A4;
            @bottom-right {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10px;
                color: #666;
            }
        }
        
        body {
            font-family: "Helvetica", Arial, sans-serif;
            font-size: 11px;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #1f4e79;
            padding-bottom: 20px;
        }
        
        .title {
            font-size: 24px;
            font-weight: bold;
            color: #1f4e79;
            margin-bottom: 10px;
        }
        
        .subtitle {
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }
        
        .student-info {
            font-size: 14px;
            font-weight: bold;
            margin: 15px 0;
        }
        
        .section {
            margin: 25px 0;
            page-break-inside: avoid;
        }
        
        .section-title {
            font-size: 16px;
            font-weight: bold;
            color: #1f4e79;
            margin-bottom: 15px;
            border-bottom: 1px solid #ccc;
            padding-bottom: 5px;
        }
        
        .score-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10px;
        }
        
        .score-table th {
            background-color: #1f4e79;
            color: white;
            padding: 10px 8px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #ddd;
        }
        
        .score-table td {
            padding: 8px;
            border: 1px solid #ddd;
            vertical-align: top;
        }
        
        .score-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .score-table tr:nth-child(odd) {
            background-color: white;
        }
        
        .status-met {
            color: #2e7d32;
            font-weight: bold;
        }
        
        .status-partial {
            color: #f57c00;
            font-weight: bold;
        }
        
        .status-not-met {
            color: #c62828;
            font-weight: bold;
        }
        
        .suggestions-list {
            margin: 15px 0;
            padding-left: 0;
        }
        
        .suggestion-item {
            margin: 8px 0;
            padding: 8px 12px;
            background-color: #f5f5f5;
            border-left: 4px solid #1f4e79;
            list-style: none;
        }
        
        .conversation {
            margin: 15px 0;
        }
        
        .message {
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
            page-break-inside: avoid;
            word-wrap: break-word;
        }
        
        .message-user {
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
        }
        
        .message-assistant {
            background-color: #f3e5f5;
            border-left: 4px solid #9c27b0;
        }
        
        .message-system {
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
        }
        
        .message-role {
            font-weight: bold;
            margin-bottom: 5px;
            text-transform: capitalize;
        }
        
        .message-content {
            line-height: 1.5;
        }
        
        .summary-box {
            background-color: #f8f9fa;
            border: 2px solid #1f4e79;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        
        .summary-title {
            font-size: 14px;
            font-weight: bold;
            color: #1f4e79;
            margin-bottom: 10px;
        }
        
        .total-score {
            font-size: 18px;
            font-weight: bold;
            color: #1f4e79;
            text-align: center;
            margin: 15px 0;
        }
        
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ccc;
            font-size: 9px;
            color: #666;
            text-align: center;
        }
        
        .page-break {
            page-break-before: always;
        }
        
        .no-break {
            page-break-inside: avoid;
        }
        
        .performance-level {
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
            display: inline-block;
        }
        
        .level-excellent { background-color: #4caf50; color: white; }
        .level-good { background-color: #8bc34a; color: white; }
        .level-satisfactory { background-color: #ffc107; color: black; }
        .level-needs-improvement { background-color: #ff9800; color: white; }
        .level-requires-work { background-color: #f44336; color: white; }
        
    </style>
</head>
<body>
    <div class="header">
        <div class="title">{{TITLE}}</div>
        <div class="subtitle">Motivational Interviewing Skills Assessment</div>
        <div class="student-info">Student: {{STUDENT_NAME}}</div>
        <div class="subtitle">Generated: {{GENERATED_DATE}}</div>
        {{EVALUATION_TIMESTAMP}}
    </div>
    
    <div class="section">
        <div class="section-title">📊 Performance Summary</div>
        {{SCORE_BREAKDOWN_TABLE}}
    </div>
    
    <div class="section">
        <div class="section-title">💡 Improvement Suggestions</div>
        {{IMPROVEMENT_SUGGESTIONS}}
    </div>
    
    <div class="section page-break">
        <div class="section-title">💬 Conversation Transcript</div>
        {{CONVERSATION_TRANSCRIPT}}
    </div>
    
    <div class="footer">
        {{FOOTER_INFO}}
    </div>
</body>
</html>';
    }
    
    /**
     * Extract evaluation timestamp from feedback
     * 
     * @param string $feedback Feedback text
     * @return string HTML for timestamp display
     */
    private function extractEvaluationTimestamp($feedback) {
        $pattern = '/Evaluation Timestamp \(UTC\): ([^\n]+)/';
        if (preg_match($pattern, $feedback, $matches)) {
            return '<div class="subtitle">Evaluation Date: ' . htmlspecialchars($matches[1]) . '</div>';
        }
        return '';
    }
    
    /**
     * Generate score breakdown table HTML
     * 
     * @param string $feedback Feedback text
     * @return string HTML table of score breakdown
     */
    private function generateScoreBreakdownTable($feedback) {
        try {
            $breakdown = FeedbackUtils::getScoreBreakdown($feedback);
            
            if (isset($breakdown['error'])) {
                return '<div class="summary-box">
                    <div class="summary-title">Score Analysis Unavailable</div>
                    <p>Raw feedback content provided without structured scoring.</p>
                </div>';
            }
            
            $html = '<div class="summary-box no-break">
                <div class="total-score">
                    Total Score: ' . number_format($breakdown['total_score'], 1) . ' / ' . 
                    number_format($breakdown['total_possible'], 1) . ' (' . 
                    number_format($breakdown['percentage'], 1) . '%)
                </div>
                <div class="performance-level ' . $this->getPerformanceLevelClass($breakdown['percentage']) . '">
                    ' . htmlspecialchars($breakdown['grade_level']) . '
                </div>
            </div>';
            
            $html .= '<table class="score-table">
                <thead>
                    <tr>
                        <th style="width: 20%;">Component</th>
                        <th style="width: 15%;">Status</th>
                        <th style="width: 15%;">Score</th>
                        <th style="width: 15%;">Max Score</th>
                        <th style="width: 35%;">Feedback</th>
                    </tr>
                </thead>
                <tbody>';
            
            foreach ($breakdown['components'] as $component => $data) {
                $statusClass = $this->getStatusClass($data['status']);
                $html .= '<tr>
                    <td><strong>' . htmlspecialchars($component) . '</strong></td>
                    <td><span class="' . $statusClass . '">' . htmlspecialchars($data['status']) . '</span></td>
                    <td>' . number_format($data['score'], 1) . ' pts</td>
                    <td>' . number_format($data['max_score'], 1) . ' pts</td>
                    <td>' . htmlspecialchars($data['feedback']) . '</td>
                </tr>';
            }
            
            $html .= '</tbody></table>';
            
            return $html;
            
        } catch (\Exception $e) {
            return '<div class="summary-box">
                <div class="summary-title">Score Breakdown</div>
                <p>Unable to parse structured scoring. Please review the detailed feedback below.</p>
            </div>';
        }
    }
    
    /**
     * Generate improvement suggestions HTML
     * 
     * @param string $feedback Feedback text
     * @return string HTML for improvement suggestions
     */
    private function generateImprovementSuggestions($feedback) {
        $suggestions = FeedbackUtils::extractSuggestionsFromFeedback($feedback);
        
        if (empty($suggestions)) {
            return '<div class="suggestion-item">
                <strong>Great work!</strong> Continue practicing to maintain and improve your MI skills.
            </div>';
        }
        
        $html = '<ul class="suggestions-list">';
        foreach ($suggestions as $suggestion) {
            $cleanSuggestion = FeedbackUtils::sanitizeSpecialCharacters($suggestion);
            $html .= '<li class="suggestion-item">' . htmlspecialchars($cleanSuggestion) . '</li>';
        }
        $html .= '</ul>';
        
        return $html;
    }
    
    /**
     * Generate conversation transcript HTML
     * 
     * @param array $chatHistory Array of conversation messages
     * @return string HTML for conversation transcript
     */
    private function generateConversationTranscript($chatHistory) {
        if (empty($chatHistory)) {
            return '<div class="message">
                <div class="message-content">No conversation data available.</div>
            </div>';
        }
        
        $html = '<div class="conversation">';
        
        foreach ($chatHistory as $message) {
            $role = $message['role'] ?? 'unknown';
            $content = FeedbackUtils::sanitizeSpecialCharacters($message['content'] ?? '');
            
            // Break long messages into smaller chunks for better readability
            if (strlen($content) > 500) {
                $content = $this->breakLongText($content, 100);
            }
            
            $html .= '<div class="message message-' . htmlspecialchars($role) . '">
                <div class="message-role">' . htmlspecialchars(ucfirst($role)) . ':</div>
                <div class="message-content">' . nl2br(htmlspecialchars($content)) . '</div>
            </div>';
        }
        
        $html .= '</div>';
        
        return $html;
    }
    
    /**
     * Generate footer information
     * 
     * @return string HTML for footer
     */
    private function generateFooterInfo() {
        return 'Generated by MI Assessment System • ' . date('Y-m-d H:i:s T') . ' • 
                This report contains confidential student assessment information';
    }
    
    /**
     * Get CSS class for performance level
     * 
     * @param float $percentage Performance percentage
     * @return string CSS class name
     */
    private function getPerformanceLevelClass($percentage) {
        if ($percentage >= 90) return 'level-excellent';
        if ($percentage >= 80) return 'level-good';
        if ($percentage >= 70) return 'level-satisfactory';
        if ($percentage >= 60) return 'level-needs-improvement';
        return 'level-requires-work';
    }
    
    /**
     * Get CSS class for status
     * 
     * @param string $status Status value
     * @return string CSS class name
     */
    private function getStatusClass($status) {
        switch (strtolower($status)) {
            case 'met':
            case 'achieved':
            case 'fully met':
                return 'status-met';
            case 'partially met':
            case 'partially achieved':
                return 'status-partial';
            case 'not met':
            case 'not yet met':
                return 'status-not-met';
            default:
                return '';
        }
    }
    
    /**
     * Break long text into smaller chunks
     * 
     * @param string $text Text to break
     * @param int $wordsPerChunk Number of words per chunk
     * @return string Text with line breaks
     */
    private function breakLongText($text, $wordsPerChunk = 100) {
        $words = explode(' ', $text);
        $chunks = array_chunk($words, $wordsPerChunk);
        return implode("\n\n", array_map(function($chunk) {
            return implode(' ', $chunk);
        }, $chunks));
    }
    
    /**
     * Generate simple transcript PDF (conversation only)
     * 
     * @param string $studentName Student name
     * @param array $chatHistory Conversation messages
     * @param string $sessionType Session type
     * @return string PDF content as binary string
     */
    public function generateTranscriptOnly($studentName, $chatHistory, $sessionType = 'MI Session') {
        try {
            $validatedName = FeedbackUtils::validateStudentName($studentName);
            
            $html = '
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Conversation Transcript - ' . htmlspecialchars($sessionType) . '</title>
    <style>
        body { font-family: Helvetica, Arial, sans-serif; margin: 40px; }
        .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 15px; }
        .title { font-size: 20px; font-weight: bold; margin-bottom: 10px; }
        .message { margin: 15px 0; padding: 10px; border-left: 3px solid #ccc; }
        .role { font-weight: bold; margin-bottom: 5px; text-transform: capitalize; }
        .content { line-height: 1.5; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">Conversation Transcript</div>
        <div>Student: ' . htmlspecialchars($validatedName) . '</div>
        <div>Session: ' . htmlspecialchars($sessionType) . '</div>
        <div>Generated: ' . date('Y-m-d H:i:s') . '</div>
    </div>
    <div class="transcript">
                ' . $this->generateSimpleTranscript($chatHistory) . '
    </div>
</body>
</html>';
            
            $dompdf = new Dompdf($this->dompdfOptions);
            $dompdf->loadHtml($html);
            $dompdf->setPaper('A4', 'portrait');
            $dompdf->render();
            
            return $dompdf->output();
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Transcript PDF generation failed", $e);
            }
            throw new \Exception("Transcript PDF generation failed: " . $e->getMessage());
        }
    }
    
    /**
     * Generate simple transcript HTML
     * 
     * @param array $chatHistory Conversation messages
     * @return string HTML transcript
     */
    private function generateSimpleTranscript($chatHistory) {
        $html = '';
        
        foreach ($chatHistory as $message) {
            $role = htmlspecialchars(ucfirst($message['role'] ?? 'unknown'));
            $content = htmlspecialchars(FeedbackUtils::sanitizeSpecialCharacters($message['content'] ?? ''));
            
            $html .= '<div class="message">
                <div class="role">' . $role . ':</div>
                <div class="content">' . nl2br($content) . '</div>
            </div>';
        }
        
        return $html;
    }
    
    /**
     * Save PDF to file system
     * 
     * @param string $pdfContent PDF binary content
     * @param string $filePath Full file path to save
     * @return bool Success status
     */
    public function savePdfToFile($pdfContent, $filePath) {
        try {
            // Ensure directory exists
            $directory = dirname($filePath);
            if (!file_exists($directory)) {
                mkdir($directory, 0755, true);
            }
            
            $result = file_put_contents($filePath, $pdfContent);
            
            if ($this->logger && $result !== false) {
                $this->logger->log(Logger::INFO, Logger::CATEGORY_PDF_GENERATION,
                    "PDF saved to file system", [
                        'file_path' => $filePath,
                        'file_size' => $result
                    ]);
            }
            
            return $result !== false;
            
        } catch (\Exception $e) {
            if ($this->logger) {
                $this->logger->logError("Failed to save PDF to file", $e);
            }
            return false;
        }
    }
    
    /**
     * Generate PDF download response headers
     * 
     * @param string $filename Download filename
     * @param int $fileSize File size in bytes
     * @param bool $inline Whether to display inline or force download
     */
    public function generateDownloadHeaders($filename, $fileSize, $inline = false) {
        $disposition = $inline ? 'inline' : 'attachment';
        
        header('Content-Type: application/pdf');
        header("Content-Disposition: {$disposition}; filename=\"{$filename}\"");
        header('Content-Length: ' . $fileSize);
        header('Cache-Control: private, max-age=0, must-revalidate');
        header('Pragma: public');
        header('Expires: 0');
    }
}

/**
 * PDF Generator Factory
 * Utility class for creating configured PDF generator instances
 */
class PdfGeneratorFactory {
    
    /**
     * Create a standard PDF generator instance
     * 
     * @param Logger|null $logger Optional logger
     * @return PdfGenerator Configured generator instance
     */
    public static function createStandard(Logger $logger = null) {
        $options = [
            'defaultFont' => 'Helvetica',
            'isRemoteEnabled' => true,
            'isHtml5ParserEnabled' => true,
            'isFontSubsettingEnabled' => true,
            'debugKeepTemp' => false,
            'debugCss' => false,
            'debugLayout' => false,
            'debugLayoutLines' => false,
            'debugLayoutBlocks' => false,
            'debugLayoutInline' => false,
            'debugLayoutPaddingBox' => false
        ];
        
        return new PdfGenerator($logger, $options);
    }
    
    /**
     * Create a high-performance PDF generator (minimal features for speed)
     * 
     * @param Logger|null $logger Optional logger
     * @return PdfGenerator Configured generator instance
     */
    public static function createHighPerformance(Logger $logger = null) {
        $options = [
            'defaultFont' => 'Helvetica',
            'isRemoteEnabled' => false,
            'isHtml5ParserEnabled' => false,
            'isFontSubsettingEnabled' => false,
            'debugKeepTemp' => false
        ];
        
        return new PdfGenerator($logger, $options);
    }
    
    /**
     * Create a debug-enabled PDF generator for development
     * 
     * @param Logger|null $logger Optional logger
     * @return PdfGenerator Configured generator instance
     */
    public static function createDebug(Logger $logger = null) {
        $options = [
            'defaultFont' => 'Helvetica',
            'isRemoteEnabled' => true,
            'isHtml5ParserEnabled' => true,
            'debugKeepTemp' => true,
            'debugCss' => true,
            'debugLayout' => true
        ];
        
        return new PdfGenerator($logger, $options);
    }
}

/**
 * Example usage and testing functions
 */
class PdfGeneratorExample {
    
    /**
     * Demonstrate basic PDF generation
     */
    public static function demonstrateUsage() {
        echo "<h2>PdfGenerator Example Usage</h2>\n";
        
        try {
            // Create generator instance
            $logger = new Logger(null, null, false, false); // No actual logging for demo
            $generator = PdfGeneratorFactory::createStandard($logger);
            
            // Sample data
            $studentName = 'Demo Student';
            $sessionType = 'HPV Vaccine';
            
            $chatHistory = [
                ['role' => 'assistant', 'content' => 'Hello! I heard you wanted to discuss the HPV vaccine?'],
                ['role' => 'user', 'content' => 'Yes, I have some concerns about it.'],
                ['role' => 'assistant', 'content' => 'I understand. What specific concerns do you have? I am here to listen and help address them.']
            ];
            
            $feedback = "**1. COLLABORATION (7.5 pts): [Met] - Excellent partnership building with the patient**
            
**2. EVOCATION (7.5 pts): [Partially Met] - Good use of open questions, but could explore patient motivations more deeply**

**3. ACCEPTANCE (7.5 pts): [Met] - Demonstrated respect for patient autonomy and used effective reflective listening**

**4. COMPASSION (7.5 pts): [Partially Met] - Showed warmth but could demonstrate more empathy**

### Improvement Suggestions:
- Use more reflective listening techniques
- Ask follow-up questions to better understand patient concerns
- Demonstrate more empathy in responses";
            
            // Generate PDF
            $pdfContent = $generator->generatePerformanceReport($studentName, $feedback, $chatHistory, $sessionType);
            
            echo "<h3>PDF Generation Results:</h3>\n";
            echo "<p>PDF Size: " . number_format(strlen($pdfContent)) . " bytes</p>\n";
            echo "<p>Generation: Successful</p>\n";
            
            // Test transcript-only generation
            $transcriptPdf = $generator->generateTranscriptOnly($studentName, $chatHistory, $sessionType);
            echo "<p>Transcript PDF Size: " . number_format(strlen($transcriptPdf)) . " bytes</p>\n";
            
            // Test file saving (to temp directory)
            $tempFile = '/tmp/demo_mi_report.pdf';
            $saveResult = $generator->savePdfToFile($pdfContent, $tempFile);
            echo "<p>File Save: " . ($saveResult ? 'Successful' : 'Failed') . "</p>\n";
            
            if ($saveResult && file_exists($tempFile)) {
                echo "<p>Saved to: {$tempFile}</p>\n";
                echo "<p>File size on disk: " . number_format(filesize($tempFile)) . " bytes</p>\n";
                
                // Provide download link for testing
                echo "<p><a href=\"data:application/pdf;base64," . base64_encode($pdfContent) . "\" download=\"demo_report.pdf\">Download Demo PDF</a></p>\n";
            }
            
        } catch (\Exception $e) {
            echo "<p>Error: " . htmlspecialchars($e->getMessage()) . "</p>\n";
        }
    }
}

// Uncomment the following line to run the example when this file is accessed directly
// if (basename(__FILE__) == basename($_SERVER['PHP_SELF'])) {
//     PdfGeneratorExample::demonstrateUsage();
// }

?>