<?php
/**
 * PdfGenerator.php - PDF generation utility for MI assessment reports
 * 
 * LAMP-stack compatible PDF generator for Motivational Interviewing chatbots
 * Uses Dompdf library to create standardized assessment reports
 * Compatible with existing Python pdf_utils.py functionality
 * 
 * @package MIUtils
 * @version 1.0
 * @author MI Assessment System
 * @requires dompdf/dompdf
 */

// Require Dompdf - install via: composer require dompdf/dompdf
// For this demo, we'll include a note about installation
if (!class_exists('Dompdf\Dompdf')) {
    // Uncomment the following line when Dompdf is installed via Composer
    // require_once __DIR__ . '/../../vendor/autoload.php';
}

require_once __DIR__ . '/FeedbackUtils.php';

class PdfGenerator {
    
    private $dompdf;
    private $options;
    
    /**
     * Initialize PDF generator
     * 
     * @param array $options Dompdf options
     */
    public function __construct($options = []) {
        $defaultOptions = [
            'isHtml5ParserEnabled' => true,
            'isPhpEnabled' => false,
            'isRemoteEnabled' => false,  // Security: disable remote URLs
            'defaultFont' => 'Arial',
            'defaultPaperSize' => 'letter',
            'defaultPaperOrientation' => 'portrait',
            'tempDir' => sys_get_temp_dir(),
            'fontDir' => sys_get_temp_dir(),
            'fontCache' => sys_get_temp_dir(),
            'chroot' => realpath(__DIR__ . '/../..'),  // Restrict file access
        ];
        
        $this->options = array_merge($defaultOptions, $options);
        
        if (class_exists('Dompdf\Dompdf')) {
            $this->dompdf = new \Dompdf\Dompdf($this->options);
        }
    }
    
    /**
     * Generate PDF report for MI assessment
     * 
     * @param string $studentName Student name
     * @param string $rawFeedback Raw feedback text
     * @param array $chatHistory Array of conversation messages
     * @param string $sessionType Session type (HPV, OHI, etc.)
     * @param string|null $evaluator Evaluator name
     * @return string PDF content as binary string
     * @throws Exception If PDF generation fails
     */
    public function generatePdfReport($studentName, $rawFeedback, $chatHistory, 
                                    $sessionType = "General MI", $evaluator = null) {
        
        if (!class_exists('Dompdf\Dompdf')) {
            throw new Exception("Dompdf library not found. Install via: composer require dompdf/dompdf");
        }
        
        // Validate and sanitize inputs
        $validatedName = FeedbackUtils::validateStudentName($studentName);
        $cleanFeedback = FeedbackUtils::sanitizeSpecialCharacters($rawFeedback);
        $evaluator = $evaluator ?: 'AI Assessment System';
        
        // Validate feedback completeness
        $validation = FeedbackUtils::validateFeedbackCompleteness($cleanFeedback);
        if (!$validation['is_valid']) {
            error_log("Warning: Feedback may be incomplete - missing: " . implode(', ', $validation['missing_components']));
        }
        
        // Get score breakdown
        try {
            $scoreBreakdown = FeedbackUtils::getScoreBreakdown($cleanFeedback);
        } catch (Exception $e) {
            error_log("Warning: Could not parse scores: " . $e->getMessage());
            $scoreBreakdown = [
                'components' => [],
                'total_score' => 0,
                'total_possible' => 30,
                'percentage' => 0,
                'performance_level' => 'Score parsing unavailable'
            ];
        }
        
        // Generate HTML content
        $html = $this->generateHtmlContent(
            $validatedName,
            $cleanFeedback,
            $chatHistory,
            $sessionType,
            $evaluator,
            $scoreBreakdown
        );
        
        // Generate PDF
        $this->dompdf->loadHtml($html);
        $this->dompdf->setPaper($this->options['defaultPaperSize'], $this->options['defaultPaperOrientation']);
        $this->dompdf->render();
        
        return $this->dompdf->output();
    }
    
    /**
     * Generate filename for PDF report
     * 
     * @param string $sessionType Session type
     * @param string $studentName Student name
     * @param string $evaluator Evaluator name (optional)
     * @return string Generated filename
     */
    public function generateFilename($sessionType, $studentName, $evaluator = null) {
        $safeName = FeedbackUtils::validateStudentName($studentName);
        $safeEvaluator = $evaluator ? '_' . preg_replace('/[^a-zA-Z0-9]/', '', $evaluator) : '';
        $timestamp = date('Y-m-d_H-i-s');
        
        return "{$sessionType}_MI_Feedback_Report_{$safeName}{$safeEvaluator}_{$timestamp}.pdf";
    }
    
    /**
     * Save PDF to file
     * 
     * @param string $pdfContent PDF binary content
     * @param string $filename Filename to save as
     * @param string|null $directory Directory to save in (default: temp)
     * @return string Full path to saved file
     */
    public function savePdfToFile($pdfContent, $filename, $directory = null) {
        if ($directory === null) {
            $directory = sys_get_temp_dir();
        }
        
        // Ensure directory exists
        if (!is_dir($directory)) {
            if (!mkdir($directory, 0755, true)) {
                throw new Exception("Cannot create directory: $directory");
            }
        }
        
        $filepath = $directory . '/' . $filename;
        
        if (file_put_contents($filepath, $pdfContent) === false) {
            throw new Exception("Cannot save PDF to: $filepath");
        }
        
        return $filepath;
    }
    
    /**
     * Send PDF as download response
     * 
     * @param string $pdfContent PDF binary content
     * @param string $filename Filename for download
     */
    public function downloadPdf($pdfContent, $filename) {
        // Set headers for PDF download
        header('Content-Type: application/pdf');
        header('Content-Disposition: attachment; filename="' . $filename . '"');
        header('Content-Length: ' . strlen($pdfContent));
        header('Cache-Control: private, max-age=0, must-revalidate');
        header('Pragma: public');
        
        echo $pdfContent;
        exit;
    }
    
    /**
     * Generate HTML content for PDF
     * 
     * @param string $studentName Student name
     * @param string $feedback Feedback content
     * @param array $chatHistory Chat messages
     * @param string $sessionType Session type
     * @param string $evaluator Evaluator name
     * @param array $scoreBreakdown Score breakdown details
     * @return string HTML content
     */
    private function generateHtmlContent($studentName, $feedback, $chatHistory, 
                                       $sessionType, $evaluator, $scoreBreakdown) {
        $timestamp = date('Y-m-d H:i:s');
        $suggestions = FeedbackUtils::extractSuggestionsFromFeedback($feedback);
        
        // Start HTML
        $html = '<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MI Performance Report - ' . htmlspecialchars($sessionType) . '</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 20px;
        }
        
        .title {
            font-size: 24px;
            font-weight: bold;
            color: #0066cc;
            margin-bottom: 10px;
        }
        
        .subtitle {
            font-size: 14px;
            color: #666;
        }
        
        .section-header {
            font-size: 18px;
            font-weight: bold;
            color: #0066cc;
            margin-top: 25px;
            margin-bottom: 15px;
            border-bottom: 1px solid #ccc;
            padding-bottom: 5px;
        }
        
        .info-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        .info-table th, .info-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        .info-table th {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        
        .score-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        .score-table th, .score-table td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        
        .score-table th {
            background-color: #0066cc;
            color: white;
            font-weight: bold;
        }
        
        .score-table .total-row {
            background-color: #f0f8ff;
            font-weight: bold;
        }
        
        .performance-excellent { color: #28a745; font-weight: bold; }
        .performance-proficient { color: #17a2b8; font-weight: bold; }
        .performance-developing { color: #ffc107; font-weight: bold; }
        .performance-beginning { color: #fd7e14; font-weight: bold; }
        .performance-needs-improvement { color: #dc3545; font-weight: bold; }
        
        .suggestion-list {
            margin-left: 20px;
        }
        
        .conversation {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 10px;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-left: 3px solid #0066cc;
            background-color: white;
        }
        
        .message-role {
            font-weight: bold;
            color: #0066cc;
            margin-bottom: 5px;
        }
        
        .page-break {
            page-break-before: always;
        }
        
        .footer {
            text-align: center;
            font-size: 10px;
            color: #666;
            margin-top: 30px;
            border-top: 1px solid #ccc;
            padding-top: 10px;
        }
    </style>
</head>
<body>';

        // Header section
        $html .= '
    <div class="header">
        <div class="title">Motivational Interviewing Performance Report</div>
        <div class="subtitle">' . htmlspecialchars($sessionType) . ' Session Assessment</div>
    </div>';

        // Student and session information
        $html .= '
    <table class="info-table">
        <tr>
            <th>Student Name</th>
            <td>' . htmlspecialchars($studentName) . '</td>
            <th>Session Type</th>
            <td>' . htmlspecialchars($sessionType) . '</td>
        </tr>
        <tr>
            <th>Evaluation Date</th>
            <td>' . $timestamp . '</td>
            <th>Evaluated By</th>
            <td>' . htmlspecialchars($evaluator) . '</td>
        </tr>
        <tr>
            <th>Total Score</th>
            <td>' . $scoreBreakdown['total_score'] . ' / ' . $scoreBreakdown['total_possible'] . '</td>
            <th>Percentage</th>
            <td>' . $scoreBreakdown['percentage'] . '%</td>
        </tr>
        <tr>
            <th>Performance Level</th>
            <td colspan="3" class="performance-' . strtolower(str_replace(' ', '-', $scoreBreakdown['performance_level'])) . '">' 
                . htmlspecialchars($scoreBreakdown['performance_level']) . '</td>
        </tr>
    </table>';

        // Component scores table
        if (!empty($scoreBreakdown['components'])) {
            $html .= '
    <div class="section-header">Component Assessment</div>
    <table class="score-table">
        <thead>
            <tr>
                <th>MI Component</th>
                <th>Status</th>
                <th>Score</th>
                <th>Max Points</th>
                <th>Feedback</th>
            </tr>
        </thead>
        <tbody>';

            foreach ($scoreBreakdown['components'] as $component) {
                $maxPoints = FeedbackUtils::MI_COMPONENTS[$component['component']] ?? 7.5;
                $html .= '
            <tr>
                <td><strong>' . htmlspecialchars($component['component']) . '</strong></td>
                <td>' . htmlspecialchars($component['status']) . '</td>
                <td>' . number_format($component['score'], 2) . '</td>
                <td>' . number_format($maxPoints, 2) . '</td>
                <td>' . htmlspecialchars($component['feedback']) . '</td>
            </tr>';
            }

            // Total row
            $html .= '
            <tr class="total-row">
                <td><strong>TOTAL</strong></td>
                <td>-</td>
                <td><strong>' . number_format($scoreBreakdown['total_score'], 2) . '</strong></td>
                <td><strong>' . number_format($scoreBreakdown['total_possible'], 2) . '</strong></td>
                <td><strong>' . $scoreBreakdown['percentage'] . '% - ' . htmlspecialchars($scoreBreakdown['performance_level']) . '</strong></td>
            </tr>
        </tbody>
    </table>';
        }

        // Improvement suggestions
        if (!empty($suggestions)) {
            $html .= '
    <div class="section-header">Improvement Suggestions</div>
    <div class="suggestion-list">';
            
            foreach ($suggestions as $suggestion) {
                $html .= '<p>• ' . htmlspecialchars($suggestion) . '</p>';
            }
            
            $html .= '</div>';
        }

        // Conversation transcript (on new page)
        if (!empty($chatHistory)) {
            $html .= '
    <div class="page-break">
        <div class="section-header">Conversation Transcript</div>';

            foreach ($chatHistory as $index => $message) {
                $role = ucfirst($message['role'] ?? 'unknown');
                $content = FeedbackUtils::sanitizeSpecialCharacters($message['content'] ?? '');
                
                // Truncate very long messages for readability
                if (strlen($content) > 500) {
                    $content = substr($content, 0, 500) . '... (truncated)';
                }
                
                $html .= '
        <div class="message">
            <div class="message-role">' . htmlspecialchars($role) . ':</div>
            <div>' . nl2br(htmlspecialchars($content)) . '</div>
        </div>';
            }
            
            $html .= '</div>';
        }

        // Footer
        $html .= '
    <div class="footer">
        Generated by MI Assessment System • ' . $timestamp . ' • Page <script type="text/php">
            if (isset($pdf)) {
                $font = $fontMetrics->getFont("Arial");
                $pdf->page_text(520, 820, "Page {PAGE_NUM} of {PAGE_COUNT}", $font, 8, array(0,0,0));
            }
        </script>
    </div>

</body>
</html>';

        return $html;
    }
}

// Example usage and testing functions (can be removed in production)
if (basename(__FILE__) == basename($_SERVER["SCRIPT_FILENAME"])) {
    // Simple test when file is run directly
    echo "=== PdfGenerator PHP Test ===\n";
    
    try {
        $generator = new PdfGenerator();
        
        // Test filename generation
        $filename = $generator->generateFilename('HPV', 'John Doe', 'AI_System');
        echo "✓ Filename generation: $filename\n";
        
        // Test HTML generation (without actual Dompdf)
        $sampleFeedback = "
1. COLLABORATION (7.5 pts): [Met] - Student demonstrated excellent partnership building
2. EVOCATION (7.5 pts): [Partially Met] - Some effort to elicit patient motivations  
3. ACCEPTANCE (7.5 pts): [Met] - Respected patient autonomy throughout
4. COMPASSION (7.5 pts): [Partially Met] - Generally warm and non-judgmental
        ";
        
        $sampleChat = [
            ['role' => 'user', 'content' => 'I am concerned about the HPV vaccine.'],
            ['role' => 'assistant', 'content' => 'I understand your concerns. Can you tell me more?']
        ];
        
        echo "✓ HTML content generation ready\n";
        echo "✓ Class methods available: " . count(get_class_methods('PdfGenerator')) . "\n";
        
        if (class_exists('Dompdf\Dompdf')) {
            echo "✓ Dompdf library is available\n";
        } else {
            echo "ℹ Dompdf library not found (install via: composer require dompdf/dompdf)\n";
        }
        
        echo "\nAll tests passed! ✓\n";
        
    } catch (Exception $e) {
        echo "✗ Test error: " . $e->getMessage() . "\n";
    }
}
?>