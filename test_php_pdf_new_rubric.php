#!/usr/bin/env php
<?php
/**
 * Test PHP PDF generation with new 40-point rubric
 */

require_once __DIR__ . '/src/utils/FeedbackUtils.php';
require_once __DIR__ . '/src/Service/EvaluationService.php';
require_once __DIR__ . '/src/Rubric/MIRubric.php';

echo "Testing PHP PDF Generation with New 40-Point Rubric\n";
echo str_repeat("=", 70) . "\n\n";

// Test 1: New rubric feedback parsing
echo "Test 1: New Rubric Feedback Parsing (HPV)\n";
echo str_repeat("-", 70) . "\n";

$hpvFeedback = <<<EOT
**Collaboration (9 pts): Meets Criteria** - Student introduced themselves warmly and collaborated with the patient about HPV vaccination.

**Acceptance (6 pts): Meets Criteria** - Asked permission before discussing HPV vaccination details.

**Compassion (6 pts): Needs Improvement** - Did not fully explore patient concerns about HPV vaccination.

**Evocation (6 pts): Meets Criteria** - Used open-ended questions about HPV vaccination.

**Summary (3 pts): Needs Improvement** - No summary provided.

**Response Factor (10 pts): Meets Criteria** - Fast, intuitive responses.
EOT;

try {
    $breakdown = FeedbackUtils::getScoreBreakdown($hpvFeedback, 'HPV', true);
    
    echo "Total Score: {$breakdown['total_score']}/{$breakdown['total_possible']}\n";
    echo "Percentage: {$breakdown['percentage']}%\n";
    echo "Performance: {$breakdown['performance_level']}\n";
    echo "Rubric Version: {$breakdown['rubric_version']}\n";
    echo "Categories Found: {$breakdown['component_count']}\n\n";
    
    echo "Category Breakdown:\n";
    foreach ($breakdown['components'] as $component) {
        echo sprintf(
            "  %-20s: %2d/%2d - %s\n",
            $component['component'],
            $component['score'],
            $component['max_score'],
            $component['status']
        );
    }
    
    // Verify expected score: 9 + 6 + 0 + 6 + 0 + 10 = 31
    $expectedScore = 31;
    if ($breakdown['total_score'] == $expectedScore && $breakdown['total_possible'] == 40) {
        echo "\n✅ Test 1 PASSED: Correct score calculation\n";
    } else {
        echo "\n❌ Test 1 FAILED: Expected {$expectedScore}/40, got {$breakdown['total_score']}/{$breakdown['total_possible']}\n";
    }
} catch (Exception $e) {
    echo "\n❌ Test 1 FAILED: " . $e->getMessage() . "\n";
}

echo "\n";

// Test 2: OHI context evaluation
echo "Test 2: New Rubric Feedback Parsing (OHI)\n";
echo str_repeat("-", 70) . "\n";

$ohiFeedback = <<<EOT
**Collaboration (9 pts): Meets Criteria** - Excellent partnership building around oral health.

**Acceptance (6 pts): Meets Criteria** - Asked permission before discussing oral health information.

**Compassion (6 pts): Meets Criteria** - Showed empathy regarding oral health concerns.

**Evocation (6 pts): Meets Criteria** - Strong open-ended questioning about oral health.

**Summary (3 pts): Meets Criteria** - Provided clear summary of oral health discussion.

**Response Factor (10 pts): Meets Criteria** - Fast responses throughout.
EOT;

try {
    $breakdown = FeedbackUtils::getScoreBreakdown($ohiFeedback, 'OHI', true);
    
    echo "Total Score: {$breakdown['total_score']}/{$breakdown['total_possible']}\n";
    echo "Percentage: {$breakdown['percentage']}%\n";
    echo "Performance: {$breakdown['performance_level']}\n";
    
    // Verify perfect score
    if ($breakdown['total_score'] == 40 && $breakdown['total_possible'] == 40) {
        echo "✅ Test 2 PASSED: Perfect score for OHI\n";
    } else {
        echo "❌ Test 2 FAILED: Expected 40/40, got {$breakdown['total_score']}/{$breakdown['total_possible']}\n";
    }
} catch (Exception $e) {
    echo "❌ Test 2 FAILED: " . $e->getMessage() . "\n";
}

echo "\n";

// Test 3: Verify context-specific text in evaluation
echo "Test 3: Context-Specific Criteria Text\n";
echo str_repeat("-", 70) . "\n";

try {
    // HPV context
    $hpvResult = EvaluationService::evaluateSession($hpvFeedback, 'HPV');
    $hpvCriteria = $hpvResult['categories']['Collaboration']['criteria_text'];
    $hasHpvText = false;
    foreach ($hpvCriteria as $text) {
        if (strpos($text, 'HPV vaccination') !== false) {
            $hasHpvText = true;
            break;
        }
    }
    
    // OHI context
    $ohiResult = EvaluationService::evaluateSession($ohiFeedback, 'OHI');
    $ohiCriteria = $ohiResult['categories']['Collaboration']['criteria_text'];
    $hasOralText = false;
    foreach ($ohiCriteria as $text) {
        if (strpos($text, 'oral health') !== false) {
            $hasOralText = true;
            break;
        }
    }
    
    if ($hasHpvText && $hasOralText) {
        echo "✅ Test 3 PASSED: Context-specific text is correctly applied\n";
        echo "  HPV criteria includes 'HPV vaccination'\n";
        echo "  OHI criteria includes 'oral health'\n";
    } else {
        echo "❌ Test 3 FAILED: Context text not found\n";
        echo "  HPV has 'HPV vaccination': " . ($hasHpvText ? 'YES' : 'NO') . "\n";
        echo "  OHI has 'oral health': " . ($hasOralText ? 'YES' : 'NO') . "\n";
    }
} catch (Exception $e) {
    echo "❌ Test 3 FAILED: " . $e->getMessage() . "\n";
}

echo "\n";

// Test 4: Old rubric fallback (backward compatibility)
echo "Test 4: Old Rubric Fallback (30-point)\n";
echo str_repeat("-", 70) . "\n";

$oldFeedback = <<<EOT
1. COLLABORATION (7.5 pts): Met - Good rapport building
2. EVOCATION (7.5 pts): Partially Met - Some exploration
3. ACCEPTANCE (7.5 pts): Met - Respected autonomy
4. COMPASSION (7.5 pts): Met - Warm approach
EOT;

try {
    $breakdown = FeedbackUtils::getScoreBreakdown($oldFeedback, 'HPV', false);
    
    echo "Total Score: {$breakdown['total_score']}/{$breakdown['total_possible']}\n";
    echo "Rubric Version: {$breakdown['rubric_version']}\n";
    
    // Expected: 7.5 + 3.75 + 7.5 + 7.5 = 26.25 out of 30
    $expectedScore = 26.25;
    if (abs($breakdown['total_score'] - $expectedScore) < 0.01 && $breakdown['total_possible'] == 30) {
        echo "✅ Test 4 PASSED: Old rubric fallback works\n";
    } else {
        echo "❌ Test 4 FAILED: Expected {$expectedScore}/30, got {$breakdown['total_score']}/{$breakdown['total_possible']}\n";
    }
} catch (Exception $e) {
    echo "❌ Test 4 FAILED: " . $e->getMessage() . "\n";
}

echo "\n";

// Summary
echo str_repeat("=", 70) . "\n";
echo "PHP New Rubric Tests Complete\n";
echo str_repeat("=", 70) . "\n";
?>
