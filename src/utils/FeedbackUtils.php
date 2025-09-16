<?php
/**
 * FeedbackUtils.php - Unified feedback processing and scoring for MI assessments
 * 
 * LAMP-stack compatible utility for Motivational Interviewing chatbots
 * Provides standardized feedback formatting, parsing, and scoring calculations
 * 
 * Compatible with existing Python MI assessment framework:
 * - 4 MI Components: COLLABORATION, EVOCATION, ACCEPTANCE, COMPASSION  
 * - 30-point scoring system (7.5 points per component)
 * - Status levels: Met (100%), Partially Met (50%), Not Met (0%)
 * 
 * @package MIUtils
 * @version 1.0
 * @author MI Assessment System
 */

class FeedbackUtils {
    
    // MI Components and their maximum scores (compatible with Python scoring_utils.py)
    const MI_COMPONENTS = [
        'COLLABORATION' => 7.5,
        'EVOCATION' => 7.5,
        'ACCEPTANCE' => 7.5,
        'COMPASSION' => 7.5
    ];
    
    // Status multipliers for scoring calculation
    const STATUS_MULTIPLIERS = [
        'Met' => 1.0,
        'Partially Met' => 0.5,
        'Not Met' => 0.0,
        // Case variations
        'met' => 1.0,
        'partially met' => 0.5,
        'not met' => 0.0,
        // Common alternatives
        'Fully Met' => 1.0,
        'fully met' => 1.0,
        'Achieved' => 1.0,
        'achieved' => 1.0
    ];
    
    const TOTAL_POSSIBLE_SCORE = 30.0;
    
    /**
     * Generate standardized evaluation prompt for MI assessments
     * 
     * @param string $sessionType Type of session (HPV, OHI, etc.)
     * @param string $transcript Conversation transcript
     * @param string $ragContext RAG-based knowledge context
     * @return string Formatted evaluation prompt
     */
    public static function formatEvaluationPrompt($sessionType, $transcript, $ragContext) {
        return "
## Motivational Interviewing Assessment - {$sessionType} Session

You are evaluating a student's Motivational Interviewing (MI) skills based on their conversation with a simulated patient. Your role is to provide constructive, educational feedback that helps the student improve their MI competencies.

### Session Transcript:
{$transcript}

**Important Instructions:**
- Only evaluate the **student's responses** (lines marked 'STUDENT' or similar indicators)
- Do not attribute change talk or motivational statements made by the patient to the student
- Focus on the student's use of MI techniques, not the patient's responses

### MI Knowledge Base:
{$ragContext}

### Assessment Framework:
Evaluate the student's MI skills using the 30-point scoring system (7.5 points per component).

**Scoring Guidelines:**
- **Met** (7.5 pts): Student demonstrates proficient use of the MI component
- **Partially Met** (3.75 pts): Student shows some understanding but needs improvement
- **Not Met** (0 pts): Student does not demonstrate the component or uses techniques contrary to MI

### Required Evaluation Format:
Please structure your feedback exactly as follows for each component:

**1. COLLABORATION (7.5 pts): [Met/Partially Met/Not Met] - [Specific feedback about partnership building and rapport development]**

**2. EVOCATION (7.5 pts): [Met/Partially Met/Not Met] - [Specific feedback about drawing out patient motivations and exploring their perspective]**

**3. ACCEPTANCE (7.5 pts): [Met/Partially Met/Not Met] - [Specific feedback about respecting patient autonomy and using reflective listening]**

**4. COMPASSION (7.5 pts): [Met/Partially Met/Not Met] - [Specific feedback about demonstrating warmth and non-judgmental approach]**

### Additional Requirements:
- For each component, provide specific examples from the conversation
- Highlight what the student did well (strengths)
- Offer concrete suggestions for improvement with specific MI techniques
- Include overall recommendations for continued learning and skill development
- Maintain a supportive and educational tone throughout your feedback

Remember: Your feedback should help the student understand both what they did well and how they can improve their MI skills in future conversations.
        ";
    }
    
    /**
     * Parse feedback text and extract component scores
     * 
     * @param string $feedbackText Raw feedback text to parse
     * @return array Array of component scores with details
     */
    public static function parseFeedbackScores($feedbackText) {
        $componentScores = [];
        $lines = explode("\n", $feedbackText);
        
        foreach ($lines as $line) {
            $componentScore = self::parseComponentLine(trim($line));
            if ($componentScore !== null) {
                $componentScores[] = $componentScore;
            }
        }
        
        return $componentScores;
    }
    
    /**
     * Parse a single component line from feedback
     * 
     * @param string $line Single line of feedback text
     * @return array|null Component score details or null if not parseable
     */
    private static function parseComponentLine($line) {
        // Pattern to match component feedback lines
        // Example: "1. COLLABORATION (7.5 pts): [Met] - Student demonstrated excellent partnership building"
        $pattern = '/(\d+\.\s*)?(COLLABORATION|EVOCATION|ACCEPTANCE|COMPASSION)\s*\([^)]*\)?\s*:\s*\[([^\]]+)\]\s*-\s*(.+)/i';
        
        if (preg_match($pattern, $line, $matches)) {
            $component = strtoupper(trim($matches[2]));
            $status = trim($matches[3]);
            $feedback = trim($matches[4]);
            
            // Calculate score based on status
            try {
                $score = self::calculateComponentScore($component, $status);
                return [
                    'component' => $component,
                    'status' => $status,
                    'score' => $score,
                    'feedback' => $feedback
                ];
            } catch (Exception $e) {
                // If status is invalid, default to 0 score
                return [
                    'component' => $component,
                    'status' => $status,
                    'score' => 0.0,
                    'feedback' => $feedback
                ];
            }
        }
        
        return null;
    }
    
    /**
     * Calculate score for a specific component based on status
     * 
     * @param string $component MI component name
     * @param string $status Assessment status (Met, Partially Met, Not Met)
     * @return float Calculated score
     * @throws Exception If component or status is invalid
     */
    public static function calculateComponentScore($component, $status) {
        $component = strtoupper($component);
        
        if (!array_key_exists($component, self::MI_COMPONENTS)) {
            throw new Exception("Invalid MI component: {$component}");
        }
        
        if (!array_key_exists($status, self::STATUS_MULTIPLIERS)) {
            throw new Exception("Invalid status: {$status}");
        }
        
        $maxScore = self::MI_COMPONENTS[$component];
        $multiplier = self::STATUS_MULTIPLIERS[$status];
        
        return $maxScore * $multiplier;
    }
    
    /**
     * Calculate total score from component scores
     * 
     * @param array $componentScores Array of component score details
     * @return float Total score
     */
    public static function calculateTotalScore($componentScores) {
        $total = 0.0;
        foreach ($componentScores as $score) {
            $total += $score['score'];
        }
        
        return $total;
    }
    
    /**
     * Get comprehensive score breakdown from feedback text
     * 
     * @param string $feedbackText Raw feedback text
     * @return array Complete score breakdown with totals and percentage
     */
    public static function getScoreBreakdown($feedbackText) {
        $componentScores = self::parseFeedbackScores($feedbackText);
        $totalScore = self::calculateTotalScore($componentScores);
        $percentage = ($totalScore / self::TOTAL_POSSIBLE_SCORE) * 100;
        
        return [
            'components' => $componentScores,
            'total_score' => $totalScore,
            'total_possible' => self::TOTAL_POSSIBLE_SCORE,
            'percentage' => round($percentage, 1),
            'performance_level' => self::getPerformanceLevel($percentage)
        ];
    }
    
    /**
     * Get performance level description based on percentage score
     * 
     * @param float $percentage Score percentage
     * @return string Performance level description
     */
    public static function getPerformanceLevel($percentage) {
        if ($percentage >= 90) return "Excellent";
        if ($percentage >= 80) return "Proficient";
        if ($percentage >= 70) return "Developing";
        if ($percentage >= 60) return "Beginning";
        return "Needs Improvement";
    }
    
    /**
     * Format feedback for display in web interface
     * 
     * @param string $feedback Raw feedback content
     * @param string $timestamp Feedback timestamp
     * @param string $evaluator Name of evaluator (default: AI_System)
     * @return array Formatted feedback components for display
     */
    public static function formatFeedbackForDisplay($feedback, $timestamp, $evaluator = 'AI_System') {
        return [
            'header' => "## 📊 Motivational Interviewing Assessment Results",
            'timestamp' => "**Evaluation Timestamp:** " . $timestamp,
            'evaluator' => "**Evaluated by:** " . $evaluator,
            'separator' => "---",
            'content' => $feedback
        ];
    }
    
    /**
     * Extract improvement suggestions from feedback text
     * 
     * @param string $feedback Raw feedback text
     * @return array List of extracted suggestions
     */
    public static function extractSuggestionsFromFeedback($feedback) {
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
            foreach ($suggestionIndicators as $indicator) {
                if (stripos($line, $indicator) !== false) {
                    $inSuggestions = true;
                    $suggestions[] = $line;
                    continue 2;
                }
            }
            
            if ($inSuggestions) {
                // Stop when we hit a new section or component
                if (preg_match('/^\d+\.\s*(COLLABORATION|EVOCATION|ACCEPTANCE|COMPASSION)/i', $line)) {
                    $inSuggestions = false;
                    continue;
                }
                
                // Add suggestion lines
                if (preg_match('/^[-•*]\s*/', $line) || (!empty($line) && !ctype_upper($line))) {
                    $suggestions[] = $line;
                }
            }
        }
        
        return $suggestions;
    }
    
    /**
     * Validate student name for safe file naming
     * 
     * @param string $name Student name to validate
     * @return string Sanitized name safe for file naming
     * @throws Exception If name is invalid
     */
    public static function validateStudentName($name) {
        if (empty(trim($name))) {
            throw new Exception("Student name cannot be empty");
        }
        
        $name = trim($name);
        
        // Check for minimum length
        if (strlen($name) < 2) {
            throw new Exception("Student name must be at least 2 characters long");
        }
        
        // Check for maximum length
        if (strlen($name) > 100) {
            throw new Exception("Student name must be less than 100 characters");
        }
        
        // Remove potentially problematic characters for file naming
        $safeName = preg_replace('/[^a-zA-Z0-9\s\-_.]/', '', $name);
        $safeName = preg_replace('/\s+/', '_', $safeName);
        $safeName = trim($safeName, '_-.');
        
        if (empty($safeName)) {
            throw new Exception("Student name contains no valid characters");
        }
        
        return $safeName;
    }
    
    /**
     * Sanitize special characters for PDF/database compatibility
     * 
     * @param string $text Text to sanitize
     * @return string Sanitized text
     */
    public static function sanitizeSpecialCharacters($text) {
        // Remove or replace problematic characters
        $text = preg_replace('/[^\x20-\x7E\n\r\t]/', '', $text);
        
        // Convert common special characters
        $replacements = [
            "\xE2\x80\x9C" => '"',  // Left double quotation mark
            "\xE2\x80\x9D" => '"',  // Right double quotation mark
            "\xE2\x80\x98" => "'",  // Left single quotation mark
            "\xE2\x80\x99" => "'",  // Right single quotation mark
            "\xE2\x80\x93" => '-',  // En dash
            "\xE2\x80\x94" => '-',  // Em dash
            "\xE2\x80\xA6" => '...' // Horizontal ellipsis
        ];
        
        $text = str_replace(array_keys($replacements), array_values($replacements), $text);
        
        return $text;
    }
    
    /**
     * Validate feedback completeness
     * 
     * @param string $feedback Feedback text to validate
     * @return array Validation results
     */
    public static function validateFeedbackCompleteness($feedback) {
        $validation = [
            'is_valid' => true,
            'missing_components' => [],
            'warnings' => []
        ];
        
        // Check for all required components
        foreach (array_keys(self::MI_COMPONENTS) as $component) {
            if (stripos($feedback, $component) === false) {
                $validation['missing_components'][] = $component;
                $validation['is_valid'] = false;
            }
        }
        
        // Check for parseable scores
        try {
            $componentScores = self::parseFeedbackScores($feedback);
            if (count($componentScores) < 4) {
                $validation['warnings'][] = "Some components may not have parseable scores";
            }
        } catch (Exception $e) {
            $validation['warnings'][] = "Score parsing issue: " . $e->getMessage();
        }
        
        return $validation;
    }
}

// Example usage and testing functions (can be removed in production)
if (basename(__FILE__) == basename($_SERVER["SCRIPT_FILENAME"])) {
    // Simple test when file is run directly
    echo "=== FeedbackUtils PHP Test ===\n";
    
    try {
        // Test student name validation
        $name = FeedbackUtils::validateStudentName("John Doe Test");
        echo "✓ Name validation: $name\n";
        
        // Test component score calculation
        $score = FeedbackUtils::calculateComponentScore('COLLABORATION', 'Met');
        echo "✓ Component scoring: $score\n";
        
        // Test feedback parsing
        $sampleFeedback = "
1. COLLABORATION (7.5 pts): [Met] - Student demonstrated excellent partnership building
2. EVOCATION (7.5 pts): [Partially Met] - Some effort to elicit patient motivations  
3. ACCEPTANCE (7.5 pts): [Met] - Respected patient autonomy throughout
4. COMPASSION (7.5 pts): [Partially Met] - Generally warm and non-judgmental
        ";
        
        $breakdown = FeedbackUtils::getScoreBreakdown($sampleFeedback);
        echo "✓ Score breakdown: {$breakdown['total_score']}/{$breakdown['total_possible']} ({$breakdown['percentage']}%)\n";
        echo "✓ Performance level: {$breakdown['performance_level']}\n";
        echo "✓ Components found: " . count($breakdown['components']) . "\n";
        
        echo "\nAll tests passed! ✓\n";
        
    } catch (Exception $e) {
        echo "✗ Test error: " . $e->getMessage() . "\n";
    }
}
?>