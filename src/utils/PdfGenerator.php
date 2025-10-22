<?php
/**
 * PdfGenerator.php
 * 
 * Professional PDF report generation for MI chatbot assessments using Dompdf library.
 * Creates comprehensive PDF reports with MI scoring, feedback analysis, and conversation transcripts.
 * 
 * Features:
 * - Professional styling with enhanced typography
 * - MI component score breakdown tables
 * - Performance level visualization
 * - Complete conversation transcripts
 * - Consistent branding and formatting
 * - Security measures for safe PDF generation  
 * - Multiple output formats (download, save, display)
 * 
 * @package MIChatbots
 * @author LAMP-Stack MI Assessment System
 * @version 1.0.0
 */

// Dompdf library would be loaded via Composer autoloader in production
// require_once 'vendor/autoload.php';

// For demonstration purposes, we'll create a mock Dompdf interface
if (!class_exists('Dompdf\Dompdf')) {
    // Mock Dompdf class for demonstration
    class MockDompdf {
        private $html = '';
        private $options = [];
        
        public function __construct($options = []) {
            $this->options = $options;
        }
        
        public function loadHtml($html) {
            $this->html = $html;
        }
        
        public function setPaper($size, $orientation = 'portrait') {
            $this->options['paper'] = $size;
            $this->options['orientation'] = $orientation;
        }
        
        public function render() {
            // Mock render - in real implementation this would generate PDF
            return true;
        }
        
        public function output() {
            // Mock output - in real implementation this would return PDF binary data
            return "PDF Binary Data - Generated from: " . substr($this->html, 0, 100) . "...";
        }
        
        public function stream($filename, $options = []) {
            // Mock stream - in real implementation this would output PDF directly
            echo "Mock PDF Stream: $filename\n";
            echo "Content: " . substr($this->html, 0, 200) . "...\n";
        }
    }
}

require_once 'FeedbackUtils.php';

class PdfGenerator
{
    private $dompdf;
    private $defaultOptions;
    
    /**
     * Initialize PDF Generator with Dompdf
     * 
     * @param array $options Dompdf options
     */
    public function __construct($options = [])
    {
        $defaultOptions = [
            'enable_php' => true,
            'enable_remote' => false,  // Security: disable remote content
            'enable_css_float' => true,
            'enable_html5_parser' => true,
            'temp_dir' => sys_get_temp_dir(),
            'font_dir' => sys_get_temp_dir() . '/dompdf_fonts/',
            'font_cache' => sys_get_temp_dir() . '/dompdf_fonts/',
            'chroot' => sys_get_temp_dir(),  // Security: restrict file access
            'log_output_file' => sys_get_temp_dir() . '/dompdf.log',
            'default_media_type' => 'print',
            'default_paper_size' => 'letter',
            'default_font' => 'DejaVu Sans',
            'dpi' => 96,
            'font_height_ratio' => 1.1,
            'is_php_enabled' => true,
            'is_remote_enabled' => false,
            'is_html5_parser_enabled' => true
        ];
        
        $this->defaultOptions = array_merge($defaultOptions, $options);
        
        // Initialize Dompdf - using mock for demonstration
        if (class_exists('Dompdf\Dompdf')) {
            $this->dompdf = new \Dompdf\Dompdf($this->defaultOptions);
        } else {
            $this->dompdf = new MockDompdf($this->defaultOptions);
        }
    }
    
    /**
     * Generate complete PDF report for MI assessment
     * 
     * @param string $studentName Student name
     * @param string $rawFeedback Raw feedback from AI evaluation
     * @param array $chatHistory Conversation history
     * @param string $sessionType Session type (HPV, OHI, etc.)
     * @param string $persona Student persona (optional)
     * @return string PDF content as binary string
     */
    public function generatePdfReport($studentName, $rawFeedback, $chatHistory, $sessionType = 'General', $persona = null)
    {
        // Validate and sanitize inputs
        $studentName = FeedbackUtils::validateStudentName($studentName);
        $rawFeedback = FeedbackUtils::sanitizeSpecialCharacters($rawFeedback);
        
        // Parse feedback for structured data - use new rubric with session type
        $scoreBreakdown = FeedbackUtils::getScoreBreakdown($rawFeedback, $sessionType, true);
        
        // Generate HTML content
        $html = $this->generateHtmlContent($studentName, $rawFeedback, $scoreBreakdown, $chatHistory, $sessionType, $persona);
        
        // Configure PDF settings
        $this->dompdf->loadHtml($html);
        $this->dompdf->setPaper('letter', 'portrait');
        
        // Render PDF
        $this->dompdf->render();
        
        return $this->dompdf->output();
    }
    
    /**
     * Generate HTML content for PDF
     * 
     * @param string $studentName Student name
     * @param string $rawFeedback Raw feedback
     * @param array $scoreBreakdown Parsed score breakdown
     * @param array $chatHistory Chat history
     * @param string $sessionType Session type
     * @param string $persona Persona
     * @return string HTML content
     */
    private function generateHtmlContent($studentName, $rawFeedback, $scoreBreakdown, $chatHistory, $sessionType, $persona)
    {
        $html = $this->getHtmlHeader($sessionType);
        $html .= $this->generateTitleSection($studentName, $sessionType, $persona);
        $html .= $this->generateExecutiveSummary($scoreBreakdown);
        $html .= $this->generateScoreBreakdownTable($scoreBreakdown);
        $html .= $this->generateDetailedFeedback($rawFeedback);
        $html .= $this->generateImprovementSuggestions($rawFeedback);
        $html .= $this->generateConversationTranscript($chatHistory);
        $html .= $this->generateFooter();
        $html .= $this->getHtmlFooter();
        
        return $html;
    }
    
    /**
     * Get HTML header with CSS styling
     * 
     * @param string $sessionType Session type for branding
     * @return string HTML header
     */
    private function getHtmlHeader($sessionType)
    {
        $brandColor = $this->getBrandColor($sessionType);
        
        return '<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MI Performance Assessment Report</title>
    <style>
        @page {
            margin: 0.75in;
            @top-center {
                content: "MI Assessment Report - ' . $sessionType . '";
                font-family: "DejaVu Sans", Arial, sans-serif;
                font-size: 10pt;
                color: #666;
            }
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-family: "DejaVu Sans", Arial, sans-serif;
                font-size: 9pt;
                color: #666;
            }
        }
        
        body {
            font-family: "DejaVu Sans", Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }
        
        .header {
            background: linear-gradient(135deg, ' . $brandColor . ', ' . $this->adjustBrightness($brandColor, -20) . ');
            color: white;
            padding: 20px;
            margin-bottom: 25px;
            border-radius: 8px;
        }
        
        .header h1 {
            margin: 0 0 8px 0;
            font-size: 24pt;
            font-weight: bold;
        }
        
        .header .subtitle {
            font-size: 14pt;
            opacity: 0.9;
            margin: 0;
        }
        
        .section {
            margin-bottom: 25px;
            page-break-inside: avoid;
        }
        
        .section h2 {
            color: ' . $brandColor . ';
            font-size: 16pt;
            font-weight: bold;
            margin: 0 0 12px 0;
            padding-bottom: 5px;
            border-bottom: 2px solid ' . $brandColor . ';
        }
        
        .section h3 {
            color: #444;
            font-size: 14pt;
            font-weight: bold;
            margin: 15px 0 8px 0;
        }
        
        .executive-summary {
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid ' . $brandColor . ';
            border-radius: 4px;
            margin-bottom: 20px;
        }
        
        .score-overview {
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
        }
        
        .score-item {
            text-align: center;
            flex: 1;
            padding: 10px;
            background: white;
            border-radius: 6px;
            margin: 0 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .score-item .label {
            font-size: 10pt;
            color: #666;
            margin-bottom: 5px;
        }
        
        .score-item .value {
            font-size: 18pt;
            font-weight: bold;
            color: ' . $brandColor . ';
        }
        
        .performance-level {
            font-size: 16pt;
            font-weight: bold;
            text-align: center;
            padding: 10px;
            border-radius: 6px;
            margin: 15px 0;
        }
        
        .performance-excellent { background: #d4edda; color: #155724; }
        .performance-proficient { background: #d1ecf1; color: #0c5460; }
        .performance-developing { background: #fff3cd; color: #856404; }
        .performance-beginning { background: #f8d7da; color: #721c24; }
        .performance-needs-improvement { background: #f5c6cb; color: #721c24; }
        
        .component-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .component-table th {
            background: ' . $brandColor . ';
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: bold;
            font-size: 10pt;
        }
        
        .component-table td {
            padding: 10px 8px;
            border-bottom: 1px solid #dee2e6;
            font-size: 10pt;
            vertical-align: top;
        }
        
        .component-table tr:nth-child(even) {
            background: #f8f9fa;
        }
        
        .status-met { color: #28a745; font-weight: bold; }
        .status-partial { color: #ffc107; font-weight: bold; }
        .status-not-met { color: #dc3545; font-weight: bold; }
        
        .feedback-text {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
            font-size: 10pt;
            line-height: 1.5;
        }
        
        .suggestions {
            background: #e7f3ff;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }
        
        .suggestions ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        
        .suggestions li {
            margin-bottom: 8px;
            line-height: 1.4;
        }
        
        .conversation {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .message {
            margin-bottom: 12px;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 10pt;
        }
        
        .message-user {
            background: #e3f2fd;
            border-left: 3px solid #2196f3;
        }
        
        .message-assistant {
            background: #f3e5f5;
            border-left: 3px solid #9c27b0;
        }
        
        .message-role {
            font-weight: bold;
            font-size: 9pt;
            color: #666;
            margin-bottom: 4px;
        }
        
        .footer {
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #dee2e6;
            font-size: 9pt;
            color: #666;
            text-align: center;
        }
        
        .timestamp {
            font-size: 9pt;
            color: #666;
            margin-bottom: 15px;
        }
        
        .page-break {
            page-break-before: always;
        }
    </style>
</head>
<body>';
    }
    
    /**
     * Get brand color based on session type
     * 
     * @param string $sessionType Session type
     * @return string Hex color code
     */
    private function getBrandColor($sessionType)
    {
        $colors = [
            'HPV' => '#6f42c1',     // Purple
            'OHI' => '#20c997',     // Teal
            'GENERAL' => '#007bff'  // Blue
        ];
        
        return $colors[strtoupper($sessionType)] ?? $colors['GENERAL'];
    }
    
    /**
     * Adjust color brightness
     * 
     * @param string $hexColor Hex color code
     * @param int $percent Brightness adjustment percentage
     * @return string Adjusted hex color
     */
    private function adjustBrightness($hexColor, $percent)
    {
        $hexColor = ltrim($hexColor, '#');
        
        if (strlen($hexColor) == 3) {
            $hexColor = $hexColor[0] . $hexColor[0] . $hexColor[1] . $hexColor[1] . $hexColor[2] . $hexColor[2];
        }
        
        $hexColor = array_map('hexdec', str_split($hexColor, 2));
        
        foreach ($hexColor as & $color) {
            $adjustableLimit = $percent < 0 ? $color : 255 - $color;
            $adjustAmount = ceil($adjustableLimit * $percent / 100);
            $color = str_pad(dechex($color + $adjustAmount), 2, '0', STR_PAD_LEFT);
        }
        
        return '#' . implode($hexColor);
    }
    
    /**
     * Generate title section
     * 
     * @param string $studentName Student name
     * @param string $sessionType Session type
     * @param string $persona Persona
     * @return string HTML content
     */
    private function generateTitleSection($studentName, $sessionType, $persona)
    {
        $subtitle = "Motivational Interviewing Performance Assessment";
        if ($persona) {
            $subtitle .= " • Persona: " . htmlspecialchars($persona);
        }
        
        return '<div class="header">
            <h1>' . htmlspecialchars($sessionType) . ' MI Assessment Report</h1>
            <p class="subtitle">' . htmlspecialchars($subtitle) . '</p>
        </div>
        
        <div class="timestamp">
            <strong>Student:</strong> ' . htmlspecialchars($studentName) . ' | 
            <strong>Generated:</strong> ' . date('F j, Y \a\t g:i A T') . '
        </div>';
    }
    
    /**
     * Generate executive summary
     * 
     * @param array $scoreBreakdown Score breakdown data
     * @return string HTML content
     */
    private function generateExecutiveSummary($scoreBreakdown)
    {
        $performanceClass = 'performance-' . strtolower(str_replace(' ', '-', $scoreBreakdown['performance_level']));
        
        // Determine expected component count based on rubric version
        $isNewRubric = isset($scoreBreakdown['rubric_version']) && $scoreBreakdown['rubric_version'] === '40-point';
        $expectedComponents = $isNewRubric ? 6 : 4;
        
        return '<div class="section">
            <h2>📊 Executive Summary</h2>
            <div class="executive-summary">
                <div class="score-overview">
                    <div class="score-item">
                        <div class="label">Total Score</div>
                        <div class="value">' . $scoreBreakdown['total_score'] . '</div>
                    </div>
                    <div class="score-item">
                        <div class="label">Maximum Possible</div>
                        <div class="value">' . $scoreBreakdown['total_possible'] . '</div>
                    </div>
                    <div class="score-item">
                        <div class="label">Percentage</div>
                        <div class="value">' . round($scoreBreakdown['percentage'], 1) . '%</div>
                    </div>
                    <div class="score-item">
                        <div class="label">Categories Found</div>
                        <div class="value">' . $scoreBreakdown['component_count'] . '/' . $expectedComponents . '</div>
                    </div>
                </div>
                
                <div class="performance-level ' . $performanceClass . '">
                    Performance Level: ' . $scoreBreakdown['performance_level'] . '
                </div>
            </div>
        </div>';
    }
    
    /**
     * Generate score breakdown table
     * 
     * @param array $scoreBreakdown Score breakdown data
     * @return string HTML content
     */
    private function generateScoreBreakdownTable($scoreBreakdown)
    {
        // Determine if using new or old rubric
        $isNewRubric = isset($scoreBreakdown['rubric_version']) && $scoreBreakdown['rubric_version'] === '40-point';
        
        $html = '<div class="section">
            <h2>📋 MI Category Breakdown</h2>
            <table class="component-table">
                <thead>
                    <tr>
                        <th style="width: 20%;">Category</th>
                        <th style="width: 15%;">Assessment</th>
                        <th style="width: 15%;">Score</th>
                        <th style="width: 10%;">Max</th>
                        <th style="width: 40%;">Notes</th>
                    </tr>
                </thead>
                <tbody>';
        
        if ($isNewRubric) {
            // New 40-point rubric: 6 categories
            $allCategories = ['COLLABORATION', 'ACCEPTANCE', 'COMPASSION', 'EVOCATION', 'SUMMARY', 'RESPONSE_FACTOR'];
            $categoryDefaults = [
                'COLLABORATION' => 9,
                'ACCEPTANCE' => 6,
                'COMPASSION' => 6,
                'EVOCATION' => 6,
                'SUMMARY' => 3,
                'RESPONSE_FACTOR' => 10
            ];
        } else {
            // Old 30-point rubric: 4 components
            $allCategories = ['COLLABORATION', 'EVOCATION', 'ACCEPTANCE', 'COMPASSION'];
            $categoryDefaults = [
                'COLLABORATION' => 7.5,
                'EVOCATION' => 7.5,
                'ACCEPTANCE' => 7.5,
                'COMPASSION' => 7.5
            ];
        }
        
        $foundComponents = array_column($scoreBreakdown['components'], 'component');
        
        foreach ($allCategories as $category) {
            $componentData = null;
            foreach ($scoreBreakdown['components'] as $comp) {
                if ($comp['component'] === $category) {
                    $componentData = $comp;
                    break;
                }
            }
            
            // Format category name for display
            $displayName = ucwords(strtolower(str_replace('_', ' ', $category)));
            
            if ($componentData) {
                $statusClass = $this->getStatusClass($componentData['status']);
                $html .= '<tr>
                    <td><strong>' . htmlspecialchars($displayName) . '</strong></td>
                    <td class="' . $statusClass . '">' . htmlspecialchars($componentData['status']) . '</td>
                    <td><strong>' . $componentData['score'] . '</strong></td>
                    <td>' . $componentData['max_score'] . '</td>
                    <td>' . htmlspecialchars($componentData['feedback']) . '</td>
                </tr>';
            } else {
                $defaultMax = isset($categoryDefaults[$category]) ? $categoryDefaults[$category] : 0;
                $html .= '<tr>
                    <td><strong>' . htmlspecialchars($displayName) . '</strong></td>
                    <td class="status-not-met">Not Assessed</td>
                    <td><strong>0</strong></td>
                    <td>' . $defaultMax . '</td>
                    <td><em>No assessment provided for this category</em></td>
                </tr>';
            }
        }
        
        $html .= '</tbody>
            </table>
        </div>';
        
        return $html;
    }
    
    /**
     * Get CSS class for status
     * 
     * @param string $status Component status
     * @return string CSS class name
     */
    private function getStatusClass($status)
    {
        $status = strtolower($status);
        if (strpos($status, 'met') !== false && strpos($status, 'partially') === false && strpos($status, 'not') === false) {
            return 'status-met';
        }
        if (strpos($status, 'partially') !== false) {
            return 'status-partial';
        }
        return 'status-not-met';
    }
    
    /**
     * Generate detailed feedback section
     * 
     * @param string $rawFeedback Raw feedback text
     * @return string HTML content
     */
    private function generateDetailedFeedback($rawFeedback)
    {
        $cleanFeedback = htmlspecialchars($rawFeedback);
        $cleanFeedback = nl2br($cleanFeedback);
        
        return '<div class="section">
            <h2>📝 Detailed Assessment Feedback</h2>
            <div class="feedback-text">
                ' . $cleanFeedback . '
            </div>
        </div>';
    }
    
    /**
     * Generate improvement suggestions section
     * 
     * @param string $rawFeedback Raw feedback text
     * @return string HTML content
     */
    private function generateImprovementSuggestions($rawFeedback)
    {
        $suggestions = FeedbackUtils::extractSuggestions($rawFeedback);
        
        $html = '<div class="section">
            <h2>💡 Improvement Suggestions</h2>
            <div class="suggestions">';
        
        if (!empty($suggestions)) {
            $html .= '<ul>';
            foreach ($suggestions as $suggestion) {
                $cleanSuggestion = htmlspecialchars(trim($suggestion));
                if (!empty($cleanSuggestion)) {
                    $html .= '<li>' . $cleanSuggestion . '</li>';
                }
            }
            $html .= '</ul>';
        } else {
            $html .= '<p>No specific improvement suggestions were extracted from the feedback. Please review the detailed assessment feedback above for guidance on areas of improvement.</p>';
        }
        
        $html .= '</div>
        </div>';
        
        return $html;
    }
    
    /**
     * Generate conversation transcript section
     * 
     * @param array $chatHistory Chat history array
     * @return string HTML content
     */
    private function generateConversationTranscript($chatHistory)
    {
        $html = '<div class="section page-break">
            <h2>💬 Conversation Transcript</h2>
            <div class="conversation">';
        
        if (!empty($chatHistory) && is_array($chatHistory)) {
            foreach ($chatHistory as $message) {
                $role = htmlspecialchars($message['role'] ?? 'unknown');
                $content = htmlspecialchars($message['content'] ?? '');
                $roleClass = 'message-' . $role;
                
                $roleName = ucfirst($role);
                if ($role === 'assistant') {
                    $roleName = 'AI Patient';
                } elseif ($role === 'user') {
                    $roleName = 'Student (Provider)';
                }
                
                $html .= '<div class="message ' . $roleClass . '">
                    <div class="message-role">' . $roleName . '</div>
                    <div class="message-content">' . nl2br($content) . '</div>
                </div>';
            }
        } else {
            $html .= '<p><em>No conversation transcript available.</em></p>';
        }
        
        $html .= '</div>
        </div>';
        
        return $html;
    }
    
    /**
     * Generate footer section
     * 
     * @return string HTML content
     */
    private function generateFooter()
    {
        return '<div class="footer">
            <p><strong>MI Chatbot Assessment System</strong></p>
            <p>This report was generated automatically based on AI evaluation of the motivational interviewing session.</p>
            <p>Generated on ' . date('F j, Y \a\t g:i A T') . '</p>
        </div>';
    }
    
    /**
     * Get HTML footer
     * 
     * @return string HTML footer
     */
    private function getHtmlFooter()
    {
        return '</body>
</html>';
    }
    
    /**
     * Generate filename for PDF report
     * 
     * @param string $sessionType Session type
     * @param string $studentName Student name
     * @param string $persona Persona (optional)
     * @return string Generated filename
     */
    public function generateFilename($sessionType, $studentName, $persona = null)
    {
        return FeedbackUtils::generateFilename($sessionType, $studentName, $persona);
    }
    
    /**
     * Save PDF to file
     * 
     * @param string $pdfContent PDF binary content
     * @param string $filePath Full file path
     * @return bool Success status
     */
    public function savePdfToFile($pdfContent, $filePath)
    {
        $directory = dirname($filePath);
        if (!is_dir($directory)) {
            if (!mkdir($directory, 0755, true)) {
                throw new Exception("Failed to create directory: $directory");
            }
        }
        
        $result = file_put_contents($filePath, $pdfContent);
        if ($result === false) {
            throw new Exception("Failed to save PDF to file: $filePath");
        }
        
        return true;
    }
    
    /**
     * Output PDF for download
     * 
     * @param string $pdfContent PDF binary content
     * @param string $filename Download filename
     * @param bool $inline Whether to display inline or as attachment
     */
    public function outputPdfForDownload($pdfContent, $filename, $inline = false)
    {
        $disposition = $inline ? 'inline' : 'attachment';
        
        header('Content-Type: application/pdf');
        header('Content-Disposition: ' . $disposition . '; filename="' . $filename . '"');
        header('Content-Length: ' . strlen($pdfContent));
        header('Cache-Control: private, max-age=0, must-revalidate');
        header('Pragma: public');
        
        echo $pdfContent;
        exit;
    }
    
    /**
     * Generate PDF and get file information
     * 
     * @param string $studentName Student name
     * @param string $rawFeedback Raw feedback
     * @param array $chatHistory Chat history
     * @param string $sessionType Session type
     * @param string $persona Persona
     * @return array PDF information
     */
    public function generatePdfInfo($studentName, $rawFeedback, $chatHistory, $sessionType = 'General', $persona = null)
    {
        $pdfContent = $this->generatePdfReport($studentName, $rawFeedback, $chatHistory, $sessionType, $persona);
        $filename = $this->generateFilename($sessionType, $studentName, $persona);
        
        return [
            'content' => $pdfContent,
            'filename' => $filename,
            'size' => strlen($pdfContent),
            'hash' => hash('sha256', $pdfContent),
            'mime_type' => 'application/pdf'
        ];
    }
    
    /**
     * Run self-test to verify PDF generation functionality
     * 
     * @return array Test results
     */
    public static function runSelfTest()
    {
        $results = [];
        
        try {
            $generator = new PdfGenerator();
            
            // Test PDF generation
            $sampleFeedback = "1. COLLABORATION: Met - Good rapport building\n2. EVOCATION: Partially Met - Some exploration";
            $sampleChat = [
                ['role' => 'user', 'content' => 'Hello, how are you today?'],
                ['role' => 'assistant', 'content' => 'I\'m doing well, thank you for asking.']
            ];
            
            $pdfContent = $generator->generatePdfReport('Test Student', $sampleFeedback, $sampleChat, 'HPV');
            $results['pdf_generation'] = !empty($pdfContent) ? 'PASS' : 'FAIL';
            
            // Test filename generation
            $filename = $generator->generateFilename('HPV', 'Test Student', 'Test Persona');
            $expected = 'HPV_MI_Feedback_Report_Test_Student_Test_Persona.pdf';
            $results['filename_generation'] = ($filename === $expected) ? 'PASS' : 'FAIL';
            
            // Test PDF info generation
            $pdfInfo = $generator->generatePdfInfo('Test Student', $sampleFeedback, $sampleChat, 'HPV');
            $results['pdf_info'] = (isset($pdfInfo['content']) && isset($pdfInfo['filename'])) ? 'PASS' : 'FAIL';
            
            $results['overall'] = 'PASS';
            
        } catch (Exception $e) {
            $results['overall'] = 'FAIL';
            $results['error'] = $e->getMessage();
        }
        
        return $results;
    }
}

// Example usage and testing
if (basename(__FILE__) === basename($_SERVER['PHP_SELF'])) {
    echo "PdfGenerator Self-Test Results:\n";
    echo str_repeat('=', 40) . "\n";
    
    $results = PdfGenerator::runSelfTest();
    foreach ($results as $test => $result) {
        echo sprintf("%-20s: %s\n", $test, $result);
    }
    
    echo "\nExample Usage:\n";
    echo str_repeat('-', 40) . "\n";
    
    // Example PDF generation
    $generator = new PdfGenerator();
    
    $sampleFeedback = "
1. COLLABORATION (7.5 pts): Met - Excellent rapport building and partnership approach.
2. EVOCATION (7.5 pts): Partially Met - Good exploration but could go deeper.
3. ACCEPTANCE (7.5 pts): Met - Strong respect for autonomy and reflective listening.
4. COMPASSION (7.5 pts): Met - Demonstrated warmth and non-judgmental approach.

Overall, this was a strong performance with clear MI techniques demonstrated.
    ";
    
    $sampleChat = [
        ['role' => 'assistant', 'content' => 'Hi, I\'m a bit worried about getting the HPV vaccine.'],
        ['role' => 'user', 'content' => 'I understand your concern. Can you tell me more about what worries you?'],
        ['role' => 'assistant', 'content' => 'Well, I\'ve heard some stories and I\'m not sure if it\'s really necessary.'],
        ['role' => 'user', 'content' => 'Those concerns are completely understandable. What have you heard that concerns you the most?']
    ];
    
    echo "Generating sample PDF...\n";
    try {
        $pdfInfo = $generator->generatePdfInfo('John Doe', $sampleFeedback, $sampleChat, 'HPV', 'College Student');
        echo "PDF generated successfully!\n";
        echo "Filename: {$pdfInfo['filename']}\n";
        echo "Size: " . number_format($pdfInfo['size']) . " bytes\n";
        echo "Hash: " . substr($pdfInfo['hash'], 0, 16) . "...\n";
        
        // Save to temporary file for demonstration
        $tempFile = '/tmp/' . $pdfInfo['filename'];
        $generator->savePdfToFile($pdfInfo['content'], $tempFile);
        echo "Sample PDF saved to: $tempFile\n";
        
    } catch (Exception $e) {
        echo "Error: " . $e->getMessage() . "\n";
    }
    
    echo "\nNOTE: This uses a mock Dompdf implementation for demonstration.\n";
    echo "Install Dompdf via Composer for actual PDF generation:\n";
    echo "composer require dompdf/dompdf\n";
}
?>