<?php
/**
 * EvaluationService.php
 * 
 * Evaluation Service for MI Assessment (PHP)
 * 
 * Provides a clean API for evaluating MI conversations using the new 40-point rubric.
 * Handles parsing of LLM feedback, context determination, and score calculation.
 * 
 * @package MIChatbots
 * @version 2.0.0
 */

require_once __DIR__ . '/../Rubric/MIRubric.php';

class EvaluationService
{
    /**
     * Default Response Factor threshold (configurable via env var)
     */
    const DEFAULT_RESPONSE_FACTOR_THRESHOLD = 2.5;
    
    /**
     * Get Response Factor threshold from environment or default
     * 
     * @return float Threshold in seconds
     */
    public static function getResponseFactorThreshold()
    {
        $threshold = getenv('RESPONSE_FACTOR_THRESHOLD');
        if ($threshold !== false && is_numeric($threshold)) {
            return (float)$threshold;
        }
        return self::DEFAULT_RESPONSE_FACTOR_THRESHOLD;
    }
    
    /**
     * Parse LLM-generated feedback to extract category assessments
     * 
     * Expected format patterns:
     * - "Collaboration: Meets Criteria - ..."
     * - "Collaboration (9 pts): Meets Criteria - ..."
     * - "1. Collaboration: Meets Criteria - ..."
     * - "**Collaboration**: Meets Criteria - ..."
     * 
     * @param string $feedbackText Raw feedback text from LLM
     * @return array Array mapping category names to assessment values
     */
    public static function parseLLMFeedback($feedbackText)
    {
        $assessments = [];
        $lines = explode("\n", $feedbackText);
        
        // Regex patterns to match category lines
        $patterns = [
            // Pattern: "Collaboration: Meets Criteria - ..." or with bold markdown
            '/^\*{0,2}(?:\d+\.\s*)?(?:\*{0,2})?(Collaboration|Acceptance|Compassion|Evocation|Summary|Response Factor)(?:\s*\([\d.]+\s*pts?\))?\s*:?\s*(?:\*{0,2})?\s*(Meets Criteria|Needs Improvement)(?:\*{0,2})?\s*[-–—]/i',
            // Pattern with brackets: "Collaboration: [Meets Criteria] - ..."
            '/^\*{0,2}(?:\d+\.\s*)?(?:\*{0,2})?(Collaboration|Acceptance|Compassion|Evocation|Summary|Response Factor)(?:\s*\([\d.]+\s*pts?\))?\s*:?\s*\[\s*(Meets Criteria|Needs Improvement)\s*\]\s*[-–—]/i'
        ];
        
        foreach ($lines as $line) {
            $line = trim($line);
            if (empty($line)) continue;
            
            foreach ($patterns as $pattern) {
                if (preg_match($pattern, $line, $matches)) {
                    $category = trim($matches[1]);
                    $assessmentText = trim($matches[2]);
                    
                    // Normalize category name
                    $categoryNormalized = ucwords(strtolower($category));
                    if ($categoryNormalized === 'Response factor') {
                        $categoryNormalized = 'Response Factor';
                    }
                    
                    // Map to assessment value
                    if (stripos($assessmentText, 'meets') !== false && stripos($assessmentText, 'needs') === false) {
                        $assessment = CategoryAssessment::MEETS_CRITERIA;
                    } else {
                        $assessment = CategoryAssessment::NEEDS_IMPROVEMENT;
                    }
                    
                    $assessments[$categoryNormalized] = $assessment;
                    break;
                }
            }
        }
        
        return $assessments;
    }
    
    /**
     * Determine rubric context from session type
     * 
     * @param string $sessionType Session type string (e.g., "HPV", "OHI", "HPV Vaccine")
     * @return string RubricContext constant (HPV or OHI)
     */
    public static function determineContext($sessionType)
    {
        $sessionTypeUpper = strtoupper($sessionType);
        
        if (strpos($sessionTypeUpper, 'HPV') !== false) {
            return RubricContext::HPV;
        } elseif (strpos($sessionTypeUpper, 'OHI') !== false || strpos($sessionTypeUpper, 'ORAL') !== false) {
            return RubricContext::OHI;
        }
        
        // Default to HPV if unclear
        return RubricContext::HPV;
    }
    
    /**
     * Extract evaluator notes/feedback for each category from LLM feedback
     * 
     * @param string $feedbackText Raw feedback text from LLM
     * @return array Array mapping category names to note strings
     */
    public static function extractEvaluatorNotes($feedbackText)
    {
        $notes = [];
        $lines = explode("\n", $feedbackText);
        
        // Pattern to extract category and notes
        $pattern = '/^\*{0,2}(?:\d+\.\s*)?(?:\*{0,2})?(Collaboration|Acceptance|Compassion|Evocation|Summary|Response Factor)(?:\s*\([\d.]+\s*pts?\))?\s*:?\s*(?:\[)?\s*(?:Meets Criteria|Needs Improvement)\s*(?:\])?\s*(?:\*{0,2})?\s*[-–—]\s*(.+)$/i';
        
        foreach ($lines as $line) {
            $line = trim($line);
            if (empty($line)) continue;
            
            if (preg_match($pattern, $line, $matches)) {
                $category = trim($matches[1]);
                $note = trim($matches[2]);
                
                // Normalize category name
                $categoryNormalized = ucwords(strtolower($category));
                if ($categoryNormalized === 'Response factor') {
                    $categoryNormalized = 'Response Factor';
                }
                
                $notes[$categoryNormalized] = $note;
            }
        }
        
        return $notes;
    }
    
    /**
     * Complete evaluation of an MI session from LLM feedback
     * 
     * @param string $feedbackText Raw feedback text from LLM evaluation
     * @param string $sessionType Type of session ("HPV", "OHI", etc.)
     * @param float|null $responseLatency Optional average bot response latency in seconds
     * @param float|null $responseThreshold Optional Response Factor threshold
     * @return array Complete evaluation result array
     */
    public static function evaluateSession(
        $feedbackText,
        $sessionType = 'HPV',
        $responseLatency = null,
        $responseThreshold = null
    ) {
        // Parse assessments from feedback
        $assessments = self::parseLLMFeedback($feedbackText);
        
        // Determine context
        $context = self::determineContext($sessionType);
        
        // Extract notes
        $notes = self::extractEvaluatorNotes($feedbackText);
        
        // Get threshold
        $threshold = ($responseThreshold !== null) ? $responseThreshold : self::getResponseFactorThreshold();
        
        // Evaluate using MIEvaluator
        $result = MIEvaluator::evaluate(
            $assessments,
            $context,
            $notes,
            $responseLatency,
            $threshold
        );
        
        return $result;
    }
    
    /**
     * Format evaluation result as a human-readable summary
     * 
     * @param array $evaluationResult Result array from evaluateSession()
     * @return string Formatted summary string
     */
    public static function formatEvaluationSummary($evaluationResult)
    {
        $lines = [];
        $lines[] = sprintf(
            "Total Score: %d/%d",
            $evaluationResult['total_score'],
            $evaluationResult['max_possible_score']
        );
        $lines[] = sprintf("Percentage: %.1f%%", $evaluationResult['percentage']);
        $lines[] = sprintf("Performance: %s", $evaluationResult['performance_band']);
        $lines[] = "";
        $lines[] = "Category Breakdown:";
        
        foreach ($evaluationResult['categories'] as $categoryName => $categoryData) {
            $lines[] = sprintf(
                "  %s: %d/%d - %s",
                $categoryName,
                $categoryData['points'],
                $categoryData['max_points'],
                $categoryData['assessment']
            );
            if (!empty($categoryData['notes'])) {
                $lines[] = sprintf("    %s", $categoryData['notes']);
            }
        }
        
        return implode("\n", $lines);
    }
}
