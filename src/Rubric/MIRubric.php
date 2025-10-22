<?php
/**
 * MIRubric.php
 * 
 * New 40-point Binary MI Rubric System for PHP
 * 
 * This class mirrors the Python rubric/mi_rubric.py implementation,
 * providing the same 6-category, 40-point binary rubric system for
 * PHP-based workflows.
 * 
 * Categories:
 * - Collaboration: 9 points
 * - Acceptance: 6 points
 * - Compassion: 6 points
 * - Evocation: 6 points
 * - Summary: 3 points
 * - Response Factor: 10 points
 * 
 * @package MIChatbots
 * @version 2.0.0
 */

class CategoryAssessment
{
    const MEETS_CRITERIA = 'Meets Criteria';
    const NEEDS_IMPROVEMENT = 'Needs Improvement';
}

class RubricContext
{
    const HPV = 'HPV';
    const OHI = 'OHI';
}

class MIRubric
{
    /**
     * Total possible score
     */
    const TOTAL_POSSIBLE = 40;
    
    /**
     * Category definitions with point values and criteria
     */
    const CATEGORIES = [
        'Collaboration' => [
            'points' => 9,
            'criteria' => [
                CategoryAssessment::MEETS_CRITERIA => [
                    'Introduces self, role, is engaging, welcoming',
                    'Collaborated with the patient by eliciting their ideas for change in {context} or by providing support as a partnership',
                    'Did not lecture; Did not try to "fix" the patient'
                ],
                CategoryAssessment::NEEDS_IMPROVEMENT => [
                    'Did not introduce self/role/engaging/welcoming',
                    'Did not collaborate by eliciting patient ideas or provide partnership support',
                    'Lectured or tried to "fix" the patient'
                ]
            ]
        ],
        'Acceptance' => [
            'points' => 6,
            'criteria' => [
                CategoryAssessment::MEETS_CRITERIA => [
                    'Asks permission before eliciting accurate information about the {context}',
                    'Uses reflections to demonstrate listening'
                ],
                CategoryAssessment::NEEDS_IMPROVEMENT => [
                    'Did not ask permission and/or provided inaccurate information',
                    'Did not use reflections to demonstrate listening'
                ]
            ]
        ],
        'Compassion' => [
            'points' => 6,
            'criteria' => [
                CategoryAssessment::MEETS_CRITERIA => [
                    'Tries to understand the patient\'s perceptions and/or concerns with the {context}',
                    'Does not judge, shame or belittle the patient'
                ],
                CategoryAssessment::NEEDS_IMPROVEMENT => [
                    'Did not try to understand perceptions/concerns',
                    'Judged, shamed or belittled the patient'
                ]
            ]
        ],
        'Evocation' => [
            'points' => 6,
            'criteria' => [
                CategoryAssessment::MEETS_CRITERIA => [
                    'Uses open-ended questions for patient understanding OR stage of change OR eliciting change talk',
                    'Supports self-efficacy; emphasizes patient autonomy regarding the {context} (rolls with resistance)'
                ],
                CategoryAssessment::NEEDS_IMPROVEMENT => [
                    'Did not ask open-ended questions',
                    'Did not support self-efficacy/autonomy (did not roll with resistance)'
                ]
            ]
        ],
        'Summary' => [
            'points' => 3,
            'criteria' => [
                CategoryAssessment::MEETS_CRITERIA => [
                    'Reflects big picture; checks accuracy of information and/or next steps'
                ],
                CategoryAssessment::NEEDS_IMPROVEMENT => [
                    'Does not summarize appropriately'
                ]
            ]
        ],
        'Response Factor' => [
            'points' => 10,
            'criteria' => [
                CategoryAssessment::MEETS_CRITERIA => [
                    'Fast and intuitive responses to questions probed; acceptable average time throughout conversation'
                ],
                CategoryAssessment::NEEDS_IMPROVEMENT => [
                    'Delay in understanding and responding'
                ]
            ]
        ]
    ];
    
    /**
     * Performance band thresholds (percentage => message)
     */
    const PERFORMANCE_BANDS = [
        90 => 'Excellent MI skills demonstrated',
        75 => 'Strong MI performance with minor areas for growth',
        60 => 'Satisfactory MI foundation, continue practicing',
        40 => 'Basic MI awareness, significant practice needed',
        0 => 'Significant improvement needed in MI techniques'
    ];
    
    /**
     * Get total possible score
     * 
     * @return int Total possible score (40)
     */
    public static function getTotalPossible()
    {
        return self::TOTAL_POSSIBLE;
    }
    
    /**
     * Get point value for a specific category
     * 
     * @param string $category Category name
     * @return int Point value
     * @throws Exception if category is unknown
     */
    public static function getCategoryPoints($category)
    {
        if (!isset(self::CATEGORIES[$category])) {
            throw new Exception("Unknown category: $category");
        }
        return self::CATEGORIES[$category]['points'];
    }
    
    /**
     * Get criteria text for a category with context substitution
     * 
     * @param string $category Category name
     * @param string $assessment CategoryAssessment constant
     * @param string $context RubricContext constant (HPV or OHI)
     * @return array Array of criteria strings
     */
    public static function getCategoryCriteria($category, $assessment, $context = RubricContext::HPV)
    {
        if (!isset(self::CATEGORIES[$category])) {
            throw new Exception("Unknown category: $category");
        }
        
        $criteria = self::CATEGORIES[$category]['criteria'][$assessment];
        
        // Apply context substitution
        $contextText = ($context === RubricContext::HPV) ? 'HPV vaccination' : 'oral health';
        
        $result = [];
        foreach ($criteria as $c) {
            $result[] = str_replace('{context}', $contextText, $c);
        }
        
        return $result;
    }
    
    /**
     * Get performance band message based on total score
     * 
     * @param int $totalScore Total score (0-40)
     * @return string Performance band message
     */
    public static function getPerformanceBand($totalScore)
    {
        $percentage = ($totalScore / self::TOTAL_POSSIBLE) * 100;
        
        foreach (self::PERFORMANCE_BANDS as $threshold => $message) {
            if ($percentage >= $threshold) {
                return $message;
            }
        }
        
        return self::PERFORMANCE_BANDS[0];
    }
}

class MIEvaluator
{
    /**
     * Default Response Factor threshold in seconds
     */
    const DEFAULT_RESPONSE_FACTOR_THRESHOLD = 2.5;
    
    /**
     * Evaluate MI performance based on category assessments
     * 
     * @param array $assessments Array mapping category names to assessment values
     * @param string $context RubricContext constant (HPV or OHI)
     * @param array $notes Optional array of evaluator notes per category
     * @param float|null $responseFactorLatency Average bot response latency in seconds
     * @param float $responseFactorThreshold Threshold in seconds (default 2.5)
     * @return array Evaluation result array
     */
    public static function evaluate(
        $assessments,
        $context = RubricContext::HPV,
        $notes = [],
        $responseFactorLatency = null,
        $responseFactorThreshold = self::DEFAULT_RESPONSE_FACTOR_THRESHOLD
    ) {
        $categoryResults = [];
        $totalScore = 0;
        
        // Process each category
        foreach (MIRubric::CATEGORIES as $categoryName => $categoryInfo) {
            // Handle Response Factor specially if latency data provided
            if ($categoryName === 'Response Factor') {
                if ($responseFactorLatency !== null) {
                    // Auto-determine assessment based on latency
                    $assessment = ($responseFactorLatency <= $responseFactorThreshold)
                        ? CategoryAssessment::MEETS_CRITERIA
                        : CategoryAssessment::NEEDS_IMPROVEMENT;
                } else {
                    // Use provided assessment or default to Needs Improvement
                    $assessment = isset($assessments[$categoryName])
                        ? $assessments[$categoryName]
                        : CategoryAssessment::NEEDS_IMPROVEMENT;
                }
            } else {
                // Get assessment from provided assessments
                $assessment = isset($assessments[$categoryName])
                    ? $assessments[$categoryName]
                    : CategoryAssessment::NEEDS_IMPROVEMENT;
            }
            
            // Calculate score (binary: full points or 0)
            $points = ($assessment === CategoryAssessment::MEETS_CRITERIA)
                ? $categoryInfo['points']
                : 0;
            $totalScore += $points;
            
            // Get criteria text with context substitution
            $criteriaText = MIRubric::getCategoryCriteria($categoryName, $assessment, $context);
            
            $categoryResults[$categoryName] = [
                'points' => $points,
                'max_points' => $categoryInfo['points'],
                'assessment' => $assessment,
                'criteria_text' => $criteriaText,
                'notes' => isset($notes[$categoryName]) ? $notes[$categoryName] : ''
            ];
        }
        
        // Calculate percentage
        $percentage = ($totalScore / MIRubric::TOTAL_POSSIBLE) * 100;
        
        // Get performance band
        $performanceBand = MIRubric::getPerformanceBand($totalScore);
        
        return [
            'total_score' => $totalScore,
            'max_possible_score' => MIRubric::TOTAL_POSSIBLE,
            'percentage' => $percentage,
            'performance_band' => $performanceBand,
            'categories' => $categoryResults,
            'context' => $context
        ];
    }
    
    /**
     * Calculate Response Factor assessment from latency
     * 
     * @param float $averageLatency Average response latency in seconds
     * @param float $threshold Threshold in seconds (default 2.5)
     * @return string CategoryAssessment constant
     */
    public static function calculateResponseFactorAssessment(
        $averageLatency,
        $threshold = self::DEFAULT_RESPONSE_FACTOR_THRESHOLD
    ) {
        return ($averageLatency <= $threshold)
            ? CategoryAssessment::MEETS_CRITERIA
            : CategoryAssessment::NEEDS_IMPROVEMENT;
    }
}
