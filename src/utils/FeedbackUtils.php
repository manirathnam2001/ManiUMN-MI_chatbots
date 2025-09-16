<?php
/**
 * FeedbackUtils.php
 * 
 * LAMP-compatible utility class for handling motivational interviewing (MI) 
 * feedback processing, scoring logic, and formatting operations.
 * 
 * This class provides standardized feedback handling equivalent to the Python
 * feedback_template.py and scoring_utils.py modules.
 * 
 * PHP Version: 7.4+
 * Dependencies: None (pure PHP)
 * 
 * @package MIChatbots
 * @author MI Chatbots System
 * @version 1.0.0
 * @since 2024
 */

namespace MIChatbots\Utils;

/**
 * Class MIComponentScore
 * Represents a score for an individual MI component
 */
class MIComponentScore {
    public $component;
    public $status;
    public $score;
    public $feedback;
    
    /**
     * Constructor for MI Component Score
     * 
     * @param string $component Component name (COLLABORATION, EVOCATION, etc.)
     * @param string $status Status (Met, Partially Met, Not Met)
     * @param float $score Numeric score (0-7.5)
     * @param string $feedback Detailed feedback text
     */
    public function __construct($component, $status, $score, $feedback) {
        $this->component = $component;
        $this->status = $status;
        $this->score = $score;
        $this->feedback = $feedback;
    }
    
    /**
     * String representation of the component score
     * 
     * @return string Formatted score information
     */
    public function __toString() {
        return "{$this->component}: {$this->status} ({$this->score} pts) - {$this->feedback}";
    }
}

/**
 * Class FeedbackUtils
 * Main utility class for MI feedback processing and scoring
 */
class FeedbackUtils {
    
    // Standard MI components and their maximum scores
    const COMPONENTS = [
        'COLLABORATION' => 7.5,
        'EVOCATION' => 7.5,
        'ACCEPTANCE' => 7.5,
        'COMPASSION' => 7.5
    ];
    
    // Valid status values and their scoring multipliers
    const STATUS_MULTIPLIERS = [
        'Met' => 1.0,
        'Partially Met' => 0.5,
        'Not Met' => 0.0,
        // Case variations
        'met' => 1.0,
        'partially met' => 0.5,
        'not met' => 0.0,
        // Common alternatives
        'Not Yet Met' => 0.0,
        'not yet met' => 0.0,
        'Partially Achieved' => 0.5,
        'partially achieved' => 0.5,
        'Achieved' => 1.0,
        'achieved' => 1.0,
        'Fully Met' => 1.0,
        'fully met' => 1.0
    ];
    
    /**
     * Generate standardized evaluation prompt for MI assessments
     * 
     * @param string $sessionType Type of session (HPV, OHI, etc.)
     * @param string $transcript Complete conversation transcript
     * @param string $ragContext RAG context for evaluation
     * @return string Formatted evaluation prompt
     */
    public static function formatEvaluationPrompt($sessionType, $transcript, $ragContext) {
        return "## Motivational Interviewing Assessment - {$sessionType} Session

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

Remember: Your feedback should help the student understand both what they did well and how they can improve their MI skills in future conversations.";
    }
    
    /**
     * Format feedback for display in web interfaces
     * 
     * @param string $feedback Raw feedback text
     * @param string $timestamp Evaluation timestamp
     * @param string $evaluator Name of evaluator
     * @return array Formatted feedback components
     */
    public static function formatFeedbackForDisplay($feedback, $timestamp, $evaluator) {
        return [
            'header' => '### Session Feedback',
            'timestamp' => "**Evaluation Timestamp (UTC):** {$timestamp}",
            'evaluator' => "**Evaluator:** {$evaluator}",
            'separator' => '---',
            'content' => $feedback
        ];
    }
    
    /**
     * Format feedback for PDF generation
     * 
     * @param string $feedback Raw feedback text
     * @param string $timestamp Evaluation timestamp
     * @param string $evaluator Name of evaluator (optional)
     * @return string Formatted feedback for PDF
     */
    public static function formatFeedbackForPdf($feedback, $timestamp, $evaluator = null) {
        $headerParts = [
            'Session Feedback',
            "Evaluation Timestamp (UTC): {$timestamp}"
        ];
        
        if ($evaluator) {
            $headerParts[] = "Evaluator: {$evaluator}";
        }
        
        $headerParts[] = '---';
        $headerParts[] = $feedback;
        
        return implode("\n", $headerParts);
    }
    
    /**
     * Parse feedback text to extract component scores
     * 
     * @param string $feedback Raw feedback text
     * @return array Array of MIComponentScore objects
     * @throws Exception If parsing fails
     */
    public static function parseFeedbackScores($feedback) {
        $componentScores = [];
        
        // Regex pattern to match component scoring format
        $pattern = '/\*\*(\d+)\.\s+(COLLABORATION|EVOCATION|ACCEPTANCE|COMPASSION)\s+\(7\.5\s+pts\):\s+\[(Met|Partially Met|Not Met)\]\s+-\s+(.+?)\*\*/s';
        
        if (preg_match_all($pattern, $feedback, $matches, PREG_SET_ORDER)) {
            foreach ($matches as $match) {
                $component = $match[2];
                $status = $match[3];
                $feedbackText = trim($match[4]);
                
                // Calculate score based on status
                $maxScore = self::COMPONENTS[$component];
                $multiplier = self::STATUS_MULTIPLIERS[$status] ?? 0.0;
                $score = $maxScore * $multiplier;
                
                $componentScores[] = new MIComponentScore($component, $status, $score, $feedbackText);
            }
        }
        
        if (empty($componentScores)) {
            throw new \Exception('Could not parse component scores from feedback text');
        }
        
        return $componentScores;
    }
    
    /**
     * Get detailed score breakdown from feedback
     * 
     * @param string $feedback Raw feedback text
     * @return array Score breakdown with totals and percentages
     */
    public static function getScoreBreakdown($feedback) {
        try {
            $componentScores = self::parseFeedbackScores($feedback);
            
            $totalScore = 0;
            $totalPossible = 0;
            $breakdown = [];
            
            foreach ($componentScores as $score) {
                $totalScore += $score->score;
                $totalPossible += self::COMPONENTS[$score->component];
                
                $breakdown[$score->component] = [
                    'score' => $score->score,
                    'max_score' => self::COMPONENTS[$score->component],
                    'status' => $score->status,
                    'percentage' => ($score->score / self::COMPONENTS[$score->component]) * 100,
                    'feedback' => $score->feedback
                ];
            }
            
            return [
                'components' => $breakdown,
                'total_score' => $totalScore,
                'total_possible' => $totalPossible,
                'percentage' => ($totalScore / $totalPossible) * 100,
                'grade_level' => self::getGradeLevel(($totalScore / $totalPossible) * 100)
            ];
            
        } catch (\Exception $e) {
            return [
                'error' => 'Could not parse scores from feedback',
                'total_score' => 0,
                'total_possible' => 30,
                'percentage' => 0,
                'components' => []
            ];
        }
    }
    
    /**
     * Determine grade level based on percentage score
     * 
     * @param float $percentage Percentage score (0-100)
     * @return string Grade level description
     */
    public static function getGradeLevel($percentage) {
        if ($percentage >= 90) return 'Excellent (A)';
        if ($percentage >= 80) return 'Good (B)';
        if ($percentage >= 70) return 'Satisfactory (C)';
        if ($percentage >= 60) return 'Needs Improvement (D)';
        return 'Requires Significant Work (F)';
    }
    
    /**
     * Extract improvement suggestions from feedback text
     * 
     * @param string $feedback Raw feedback text
     * @return array List of improvement suggestions
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
            
            // Check for suggestion section indicators
            $lineToCheck = strtolower($line);
            foreach ($suggestionIndicators as $indicator) {
                if (strpos($lineToCheck, $indicator) !== false) {
                    $inSuggestions = true;
                    $suggestions[] = $line;
                    continue 2;
                }
            }
            
            if ($inSuggestions) {
                // Stop when we hit a new component section
                if (preg_match('/^[1-4]\.\s+(COLLABORATION|EVOCATION|ACCEPTANCE|COMPASSION)/', $line)) {
                    $inSuggestions = false;
                    continue;
                }
                
                // Add suggestion lines
                if (preg_match('/^[-•*]/', $line) || (!empty($line) && !ctype_upper($line))) {
                    $suggestions[] = $line;
                }
            }
        }
        
        return $suggestions;
    }
    
    /**
     * Generate component breakdown table data for PDF
     * 
     * @param string $feedback Raw feedback text
     * @return array Table data for PDF generation
     */
    public static function generateComponentBreakdownTable($feedback) {
        try {
            $componentScores = self::parseFeedbackScores($feedback);
            $tableData = [];
            
            foreach ($componentScores as $score) {
                $maxScore = self::COMPONENTS[$score->component];
                $percentage = ($score->score / $maxScore) * 100;
                $scoreDisplay = sprintf("%.1f pts (%.0f%%)", $score->score, $percentage);
                
                $tableData[] = [
                    'component' => $score->component,
                    'status' => $score->status,
                    'score' => $scoreDisplay,
                    'max_score' => sprintf("%.1f pts", $maxScore),
                    'feedback' => $score->feedback
                ];
            }
            
            return $tableData;
        } catch (\Exception $e) {
            return []; // Return empty array if parsing fails
        }
    }
    
    /**
     * Create standardized filename for downloads
     * 
     * @param string $studentName Name of the student
     * @param string $sessionType Type of session (HPV, OHI)
     * @param string $persona Selected persona (optional)
     * @return string Standardized filename
     */
    public static function createDownloadFilename($studentName, $sessionType, $persona = null) {
        // Sanitize student name
        $cleanName = preg_replace('/[^a-zA-Z0-9\s]/', '', $studentName);
        $cleanName = preg_replace('/\s+/', '_', trim($cleanName));
        
        // Sanitize persona if provided
        $cleanPersona = '';
        if ($persona) {
            $cleanPersona = preg_replace('/[^a-zA-Z0-9\s]/', '', $persona);
            $cleanPersona = '_' . preg_replace('/\s+/', '_', trim($cleanPersona));
        }
        
        $timestamp = date('Ymd_His');
        
        return "{$sessionType}_MI_Feedback_Report_{$cleanName}{$cleanPersona}_{$timestamp}.pdf";
    }
    
    /**
     * Validate student name input
     * 
     * @param string $name Student name to validate
     * @return string Validated and cleaned name
     * @throws Exception If name is invalid
     */
    public static function validateStudentName($name) {
        if (empty($name) || trim($name) === '') {
            throw new \Exception('Student name cannot be empty');
        }
        
        $cleanName = trim($name);
        
        if (strlen($cleanName) < 2) {
            throw new \Exception('Student name must be at least 2 characters long');
        }
        
        if (strlen($cleanName) > 255) {
            throw new \Exception('Student name must be less than 255 characters');
        }
        
        // Check for obviously invalid names
        if (preg_match('/^[^a-zA-Z]*$|test|example|null|undefined/i', $cleanName)) {
            throw new \Exception('Please enter a valid student name');
        }
        
        return $cleanName;
    }
    
    /**
     * Sanitize text for special characters (useful for PDF generation)
     * 
     * @param string $text Text to sanitize
     * @return string Sanitized text
     */
    public static function sanitizeSpecialCharacters($text) {
        // Replace problematic characters that might cause issues in PDF generation
        $replacements = [
            '"' => '"',
            '"' => '"',
            ''' => "'",
            ''' => "'",
            '–' => '-',
            '—' => '-',
            '…' => '...',
            '©' => '(c)',
            '®' => '(R)',
            '™' => '(TM)'
        ];
        
        $cleanText = str_replace(array_keys($replacements), array_values($replacements), $text);
        
        // Remove or replace any remaining non-printable characters
        $cleanText = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', '', $cleanText);
        
        return $cleanText;
    }
    
    /**
     * Validate feedback completeness
     * 
     * @param string $feedback Feedback text to validate
     * @return array Validation results
     */
    public static function validateFeedbackCompleteness($feedback) {
        $requiredComponents = array_keys(self::COMPONENTS);
        $foundComponents = [];
        $missingComponents = [];
        
        foreach ($requiredComponents as $component) {
            if (stripos($feedback, $component) !== false) {
                $foundComponents[] = $component;
            } else {
                $missingComponents[] = $component;
            }
        }
        
        return [
            'is_valid' => empty($missingComponents),
            'found_components' => $foundComponents,
            'missing_components' => $missingComponents,
            'completeness_percentage' => (count($foundComponents) / count($requiredComponents)) * 100
        ];
    }
    
    /**
     * Format timestamp for consistent display
     * 
     * @param string $timestamp Input timestamp (various formats accepted)
     * @param string $format Output format (default: Y-m-d H:i:s)
     * @return string Formatted timestamp
     */
    public static function formatTimestamp($timestamp = null, $format = 'Y-m-d H:i:s') {
        if ($timestamp === null) {
            $timestamp = time();
        }
        
        // Handle various input formats
        if (is_string($timestamp)) {
            $timestamp = strtotime($timestamp);
        }
        
        return date($format, $timestamp);
    }
    
    /**
     * Get performance metrics from feedback
     * 
     * @param string $feedback Raw feedback text
     * @return array Performance metrics
     */
    public static function getPerformanceMetrics($feedback) {
        $breakdown = self::getScoreBreakdown($feedback);
        
        if (isset($breakdown['error'])) {
            return $breakdown;
        }
        
        $strongAreas = [];
        $improvementAreas = [];
        
        foreach ($breakdown['components'] as $component => $data) {
            if ($data['percentage'] >= 80) {
                $strongAreas[] = $component;
            } elseif ($data['percentage'] < 60) {
                $improvementAreas[] = $component;
            }
        }
        
        return [
            'total_score' => $breakdown['total_score'],
            'percentage' => $breakdown['percentage'],
            'grade_level' => $breakdown['grade_level'],
            'strong_areas' => $strongAreas,
            'improvement_areas' => $improvementAreas,
            'components' => $breakdown['components'],
            'recommendations' => self::generateRecommendations($breakdown)
        ];
    }
    
    /**
     * Generate personalized recommendations based on performance
     * 
     * @param array $breakdown Score breakdown data
     * @return array List of recommendations
     */
    private static function generateRecommendations($breakdown) {
        $recommendations = [];
        
        foreach ($breakdown['components'] as $component => $data) {
            if ($data['percentage'] < 70) {
                switch ($component) {
                    case 'COLLABORATION':
                        $recommendations[] = 'Focus on building stronger partnership with patients through shared decision-making';
                        break;
                    case 'EVOCATION':
                        $recommendations[] = 'Practice using more open-ended questions to draw out patient motivations';
                        break;
                    case 'ACCEPTANCE':
                        $recommendations[] = 'Work on reflective listening and respecting patient autonomy';
                        break;
                    case 'COMPASSION':
                        $recommendations[] = 'Demonstrate more warmth and empathy in patient interactions';
                        break;
                }
            }
        }
        
        if (empty($recommendations)) {
            $recommendations[] = 'Excellent work! Continue practicing to maintain your MI skills';
        }
        
        return $recommendations;
    }
}

/**
 * Example usage and testing functions
 */
class FeedbackUtilsExample {
    
    /**
     * Demonstrate basic usage of FeedbackUtils
     */
    public static function demonstrateUsage() {
        echo "<h2>FeedbackUtils Example Usage</h2>\n";
        
        // Sample feedback text
        $sampleFeedback = "**1. COLLABORATION (7.5 pts): [Met] - Excellent partnership building with the patient**
        
**2. EVOCATION (7.5 pts): [Partially Met] - Good use of open questions, but could explore more**

**3. ACCEPTANCE (7.5 pts): [Met] - Demonstrated respect for patient autonomy**

**4. COMPASSION (7.5 pts): [Not Met] - Needs to show more warmth and empathy**";
        
        // Test score parsing
        try {
            $scores = FeedbackUtils::parseFeedbackScores($sampleFeedback);
            echo "<h3>Parsed Scores:</h3>\n";
            foreach ($scores as $score) {
                echo "<p>{$score}</p>\n";
            }
        } catch (\Exception $e) {
            echo "<p>Error parsing scores: {$e->getMessage()}</p>\n";
        }
        
        // Test score breakdown
        $breakdown = FeedbackUtils::getScoreBreakdown($sampleFeedback);
        echo "<h3>Score Breakdown:</h3>\n";
        echo "<p>Total Score: {$breakdown['total_score']}/{$breakdown['total_possible']} ({$breakdown['percentage']}%)</p>\n";
        echo "<p>Grade Level: {$breakdown['grade_level']}</p>\n";
        
        // Test filename generation
        $filename = FeedbackUtils::createDownloadFilename('John Doe', 'HPV', 'Alex');
        echo "<h3>Generated Filename:</h3>\n";
        echo "<p>{$filename}</p>\n";
        
        // Test validation
        try {
            $validName = FeedbackUtils::validateStudentName('John Doe');
            echo "<h3>Validated Name:</h3>\n";
            echo "<p>{$validName}</p>\n";
        } catch (\Exception $e) {
            echo "<p>Validation error: {$e->getMessage()}</p>\n";
        }
    }
}

// Uncomment the following line to run the example when this file is accessed directly
// if (basename(__FILE__) == basename($_SERVER['PHP_SELF'])) {
//     FeedbackUtilsExample::demonstrateUsage();
// }

?>