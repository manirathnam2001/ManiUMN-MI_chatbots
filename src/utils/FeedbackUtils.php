<?php
/**
 * FeedbackUtils.php
 * 
 * Unified feedback processing and MI scoring system for motivational interviewing chatbots.
 * Provides consistent scoring logic, feedback parsing, and formatting that mirrors the 
 * Python implementation while adding PHP-specific functionality.
 * 
 * Features:
 * - 30-point MI scoring system (7.5 points per component)
 * - Component parsing from feedback text
 * - Score validation and calculation
 * - Performance level determination
 * - Input sanitization and validation
 * 
 * @package MIChatbots
 * @author LAMP-Stack MI Assessment System
 * @version 1.0.0
 */

class FeedbackUtils
{
    // MI Components and their maximum scores (mirroring Python scoring_utils.py)
    const COMPONENTS = [
        'COLLABORATION' => 7.5,
        'EVOCATION' => 7.5,
        'ACCEPTANCE' => 7.5,
        'COMPASSION' => 7.5
    ];
    
    // Status to score multiplier mapping
    const STATUS_MULTIPLIERS = [
        'Met' => 1.0,
        'met' => 1.0,
        'Partially Met' => 0.5,
        'partially met' => 0.5,
        'Not Met' => 0.0,
        'not met' => 0.0,
        'Not Yet Met' => 0.0,
        'not yet met' => 0.0,
        'Partially Achieved' => 0.5,
        'partially achieved' => 0.5,
        'Achieved' => 1.0,
        'achieved' => 1.0,
        'Fully Met' => 1.0,
        'fully met' => 1.0
    ];
    
    const TOTAL_POSSIBLE_SCORE = 30.0;
    
    // Performance level thresholds (based on percentage)
    const PERFORMANCE_LEVELS = [
        90.0 => 'Excellent',
        80.0 => 'Proficient', 
        70.0 => 'Developing',
        60.0 => 'Beginning',
        0.0 => 'Needs Improvement'
    ];
    
    /**
     * Parse feedback text and extract MI component scores
     * 
     * @param string $feedbackText Raw feedback text from AI evaluation
     * @return array Parsed component scores and details
     */
    public static function parseComponentScores($feedbackText)
    {
        $components = [];
        $lines = explode("\n", $feedbackText);
        
        foreach ($lines as $line) {
            $line = trim($line);
            if (empty($line)) continue;
            
            $componentData = self::parseComponentLine($line);
            if ($componentData) {
                $components[] = $componentData;
            }
        }
        
        return $components;
    }
    
    /**
     * Parse a single component line from feedback text
     * 
     * @param string $line Single line of feedback text
     * @return array|null Component data or null if no match
     */
    private static function parseComponentLine($line)
    {
        // Component parsing patterns (mirroring Python regex patterns)
        $patterns = [
            // Pattern 1: "1. COLLABORATION: Met - feedback text"
            '/^(?:\d+\.\s*)?(?:\*\*)?(\w+)(?:\s*\([0-9.]+\s*(?:pts?)?\))?\s*[:]\s*(?:\*\*)?(\w+(?:\s+\w+)*?)(?:\*\*)?\s*[-–—]\s*(.+)$/i',
            // Pattern 2: "COLLABORATION (7.5 pts): Met - feedback text"
            '/^(?:\d+\.\s*|[●•]\s*)?(\w+)(?:\s*\([0-9.]+\s*(?:pts?)?\))?\s*:\s*(\w+(?:\s+\w+)*?)\s*[-–—]\s*(.+)$/i'
        ];
        
        foreach ($patterns as $pattern) {
            if (preg_match($pattern, $line, $matches)) {
                $component = strtoupper(trim($matches[1]));
                $status = trim($matches[2]);
                $feedback = trim($matches[3]);
                
                // Validate component
                if (!array_key_exists($component, self::COMPONENTS)) {
                    continue;
                }
                
                // Calculate score
                $score = self::calculateComponentScore($component, $status);
                
                return [
                    'component' => $component,
                    'status' => $status,
                    'score' => $score,
                    'feedback' => $feedback,
                    'max_score' => self::COMPONENTS[$component]
                ];
            }
        }
        
        return null;
    }
    
    /**
     * Calculate score for a specific component based on status
     * 
     * @param string $component MI component name
     * @param string $status Component status (Met, Partially Met, Not Met)
     * @return float Calculated score
     */
    public static function calculateComponentScore($component, $status)
    {
        if (!array_key_exists($component, self::COMPONENTS)) {
            throw new InvalidArgumentException("Invalid component: $component");
        }
        
        $maxScore = self::COMPONENTS[$component];
        $multiplier = self::STATUS_MULTIPLIERS[$status] ?? 0.0;
        
        return round($maxScore * $multiplier, 1);
    }
    
    /**
     * Calculate total score from component scores
     * 
     * @param array $componentScores Array of parsed component scores
     * @return float Total score
     */
    public static function calculateTotalScore($componentScores)
    {
        $total = 0.0;
        foreach ($componentScores as $component) {
            $total += $component['score'];
        }
        return round($total, 1);
    }
    
    /**
     * Calculate percentage from total score
     * 
     * @param float $totalScore Total achieved score
     * @return float Percentage (0-100)
     */
    public static function calculatePercentage($totalScore)
    {
        return round(($totalScore / self::TOTAL_POSSIBLE_SCORE) * 100, 2);
    }
    
    /**
     * Determine performance level based on percentage
     * 
     * @param float $percentage Score percentage
     * @return string Performance level
     */
    public static function getPerformanceLevel($percentage)
    {
        foreach (self::PERFORMANCE_LEVELS as $threshold => $level) {
            if ($percentage >= $threshold) {
                return $level;
            }
        }
        return 'Needs Improvement';
    }
    
    /**
     * Get complete score breakdown from feedback text
     * 
     * @param string $feedbackText Raw feedback text
     * @return array Complete score analysis
     */
    public static function getScoreBreakdown($feedbackText)
    {
        $components = self::parseComponentScores($feedbackText);
        $totalScore = self::calculateTotalScore($components);
        $percentage = self::calculatePercentage($totalScore);
        $performanceLevel = self::getPerformanceLevel($percentage);
        
        return [
            'components' => $components,
            'total_score' => $totalScore,
            'total_possible' => self::TOTAL_POSSIBLE_SCORE,
            'percentage' => $percentage,
            'performance_level' => $performanceLevel,
            'component_count' => count($components),
            'missing_components' => self::findMissingComponents($components)
        ];
    }
    
    /**
     * Find missing MI components from parsed feedback
     * 
     * @param array $components Parsed component scores
     * @return array Missing component names
     */
    private static function findMissingComponents($components)
    {
        $foundComponents = array_column($components, 'component');
        $allComponents = array_keys(self::COMPONENTS);
        return array_diff($allComponents, $foundComponents);
    }
    
    /**
     * Validate student name for database storage and filename generation
     * 
     * @param string $studentName Raw student name input
     * @return string Sanitized student name
     * @throws InvalidArgumentException If name is invalid
     */
    public static function validateStudentName($studentName)
    {
        if (empty($studentName) || !is_string($studentName)) {
            throw new InvalidArgumentException("Student name cannot be empty");
        }
        
        // Remove extra whitespace and convert to proper format
        $name = trim($studentName);
        
        // Basic validation - alphanumeric, spaces, hyphens, apostrophes
        if (!preg_match('/^[a-zA-Z0-9\s\-\'\.]+$/', $name)) {
            throw new InvalidArgumentException("Student name contains invalid characters");
        }
        
        // Length validation
        if (strlen($name) < 2 || strlen($name) > 100) {
            throw new InvalidArgumentException("Student name must be between 2 and 100 characters");
        }
        
        return $name;
    }
    
    /**
     * Sanitize student name for safe filename usage
     * 
     * @param string $studentName Validated student name
     * @return string Filename-safe student name
     */
    public static function sanitizeForFilename($studentName)
    {
        // Replace spaces with underscores, remove special characters
        $safe = preg_replace('/[^a-zA-Z0-9\-_]/', '_', $studentName);
        $safe = preg_replace('/_{2,}/', '_', $safe); // Remove multiple underscores
        $safe = trim($safe, '_'); // Remove leading/trailing underscores
        
        return $safe;
    }
    
    /**
     * Format feedback for display with consistent structure
     * 
     * @param string $feedback Raw feedback content
     * @param string $timestamp Evaluation timestamp
     * @param string $evaluator Evaluator name (optional)
     * @return array Formatted feedback components
     */
    public static function formatFeedbackForDisplay($feedback, $timestamp, $evaluator = null)
    {
        $formatted = [
            'header' => '## 📊 MI Performance Evaluation Results',
            'timestamp' => "**Evaluation Timestamp:** " . $timestamp,
            'evaluator' => $evaluator ? "**Evaluated by:** " . $evaluator : '',
            'separator' => '---',
            'content' => $feedback
        ];
        
        return $formatted;
    }
    
    /**
     * Format feedback for PDF generation
     * 
     * @param string $feedback Raw feedback content
     * @param string $timestamp Evaluation timestamp
     * @param string $evaluator Evaluator name (optional)
     * @return string PDF-formatted feedback
     */
    public static function formatFeedbackForPdf($feedback, $timestamp, $evaluator = null)
    {
        $header = "MI Performance Evaluation Results\n";
        $header .= "Evaluation Timestamp: " . $timestamp . "\n";
        if ($evaluator) {
            $header .= "Evaluated by: " . $evaluator . "\n";
        }
        $header .= str_repeat('-', 50) . "\n\n";
        
        return $header . $feedback;
    }
    
    /**
     * Generate standardized filename for PDF downloads
     * 
     * @param string $sessionType Session type (HPV, OHI, etc.)
     * @param string $studentName Student name
     * @param string $persona Persona name (optional)
     * @return string Generated filename
     */
    public static function generateFilename($sessionType, $studentName, $persona = null)
    {
        $validatedName = self::validateStudentName($studentName);
        $safeName = self::sanitizeForFilename($validatedName);
        
        $parts = ['MI_Feedback_Report', $safeName];
        
        if ($persona) {
            $safePersona = self::sanitizeForFilename($persona);
            $parts[] = $safePersona;
        }
        
        $filename = implode('_', $parts) . '.pdf';
        
        // Add session type prefix
        $sessionType = strtoupper($sessionType);
        if (in_array($sessionType, ['HPV', 'OHI'])) {
            return $sessionType . '_' . $filename;
        }
        
        return $filename;
    }
    
    /**
     * Sanitize special characters for PDF compatibility
     * 
     * @param string $text Input text with potential special characters
     * @return string Sanitized text
     */
    public static function sanitizeSpecialCharacters($text)
    {
        if (empty($text)) return '';
        
        // Character replacements for PDF compatibility
        $replacements = [
            "\u201c" => '"',  // Left double quote
            "\u201d" => '"',  // Right double quote
            "\u2018" => "'",  // Left single quote
            "\u2019" => "'",  // Right single quote
            "\u2013" => '-',  // En dash unicode
            "\u2014" => '--', // Em dash unicode
            "\u2026" => '...' // Ellipsis
        ];
        
        $text = str_replace(array_keys($replacements), array_values($replacements), $text);
        
        // Remove non-printable characters except common whitespace
        $text = preg_replace('/[^\x20-\x7E\n\r\t]/', '', $text);
        
        return $text;
    }
    
    /**
     * Validate score range
     * 
     * @param float $score Score to validate
     * @param float $maxScore Maximum possible score
     * @return bool True if score is valid
     */
    public static function validateScoreRange($score, $maxScore = null)
    {
        $maxScore = $maxScore ?? self::TOTAL_POSSIBLE_SCORE;
        return ($score >= 0.0 && $score <= $maxScore);
    }
    
    /**
     * Extract improvement suggestions from feedback text
     * 
     * @param string $feedback Feedback text
     * @return array Array of suggestion strings
     */
    public static function extractSuggestions($feedback)
    {
        $suggestions = [];
        $lines = explode("\n", $feedback);
        $inSuggestions = false;
        
        $suggestionIndicators = [
            'suggestions for improvement',
            'next steps',
            'recommendations',
            'areas to focus',
            'improvement suggestions',
            'overall strengths',
            'continued learning'
        ];
        
        foreach ($lines as $line) {
            $line = trim($line);
            if (empty($line)) continue;
            
            // Look for suggestion indicators
            $lowerLine = strtolower($line);
            foreach ($suggestionIndicators as $indicator) {
                if (strpos($lowerLine, $indicator) !== false) {
                    $inSuggestions = true;
                    $suggestions[] = $line;
                    continue 2;
                }
            }
            
            if ($inSuggestions) {
                // Stop when we hit a new section or component
                $isComponentLine = false;
                foreach (array_keys(self::COMPONENTS) as $component) {
                    if (strpos(strtoupper($line), $component) !== false && 
                        preg_match('/^\d+\./', $line)) {
                        $isComponentLine = true;
                        break;
                    }
                }
                
                if ($isComponentLine) {
                    $inSuggestions = false;
                    continue;
                }
                
                // Add suggestion lines
                if (preg_match('/^[-•*]/', $line) || (!ctype_upper($line) && !empty($line))) {
                    $suggestions[] = $line;
                }
            }
        }
        
        return $suggestions;
    }
    
    /**
     * Run self-test to verify functionality
     * 
     * @return array Test results
     */
    public static function runSelfTest()
    {
        $results = [];
        
        try {
            // Test component score calculation
            $score = self::calculateComponentScore('COLLABORATION', 'Met');
            $results['component_scoring'] = ($score === 7.5) ? 'PASS' : 'FAIL';
            
            // Test student name validation
            $validName = self::validateStudentName('John Doe');
            $results['name_validation'] = ($validName === 'John Doe') ? 'PASS' : 'FAIL';
            
            // Test filename generation
            $filename = self::generateFilename('HPV', 'John Doe', 'Sarah');
            $expected = 'HPV_MI_Feedback_Report_John_Doe_Sarah.pdf';
            $results['filename_generation'] = ($filename === $expected) ? 'PASS' : 'FAIL';
            
            // Test score breakdown
            $sampleFeedback = "1. COLLABORATION: Met - Good rapport building\n2. EVOCATION: Partially Met - Some exploration";
            $breakdown = self::getScoreBreakdown($sampleFeedback);
            $results['score_breakdown'] = (count($breakdown['components']) === 2) ? 'PASS' : 'FAIL';
            
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
    echo "FeedbackUtils Self-Test Results:\n";
    echo str_repeat('=', 40) . "\n";
    
    $results = FeedbackUtils::runSelfTest();
    foreach ($results as $test => $result) {
        echo sprintf("%-20s: %s\n", $test, $result);
    }
    
    echo "\nExample Usage:\n";
    echo str_repeat('-', 40) . "\n";
    
    // Example feedback parsing
    $sampleFeedback = "
1. COLLABORATION (7.5 pts): Met - Excellent rapport building and partnership approach.
2. EVOCATION (7.5 pts): Partially Met - Good exploration of motivations but could go deeper.
3. ACCEPTANCE (7.5 pts): Met - Strong respect for autonomy and reflective listening.
4. COMPASSION (7.5 pts): Met - Demonstrated warmth and non-judgmental approach.
    ";
    
    $breakdown = FeedbackUtils::getScoreBreakdown($sampleFeedback);
    echo "Sample Feedback Analysis:\n";
    echo "Total Score: {$breakdown['total_score']}/{$breakdown['total_possible']} ({$breakdown['percentage']}%)\n";
    echo "Performance Level: {$breakdown['performance_level']}\n";
    echo "Components Found: " . count($breakdown['components']) . "\n";
    
    if (!empty($breakdown['missing_components'])) {
        echo "Missing Components: " . implode(', ', $breakdown['missing_components']) . "\n";
    }
}
?>