/**
 * Integration test script to verify frontend-backend communication
 * This simulates what the React app does when submitting questions
 */

const API_URL = 'http://localhost:8000/ask';

async function testQuestion(question, testName) {
  console.log(`\n${'='.repeat(80)}`);
  console.log(`TEST: ${testName}`);
  console.log(`${'='.repeat(80)}`);
  console.log(`Question: "${question}"\n`);
  
  const startTime = Date.now();
  
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });
    
    const elapsed = Date.now() - startTime;
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    console.log(`✅ SUCCESS (${elapsed}ms)\n`);
    console.log('Response:');
    console.log('-'.repeat(80));
    console.log(data.answer);
    console.log('-'.repeat(80));
    
    return { success: true, elapsed, data };
    
  } catch (error) {
    const elapsed = Date.now() - startTime;
    console.log(`❌ FAILED (${elapsed}ms)\n`);
    console.log('Error:', error.message);
    return { success: false, elapsed, error: error.message };
  }
}

async function runTests() {
  console.log('\n');
  console.log('╔════════════════════════════════════════════════════════════════════════════╗');
  console.log('║     LENDING INFO PIPELINE - FRONTEND/BACKEND INTEGRATION TEST              ║');
  console.log('╚════════════════════════════════════════════════════════════════════════════╝');
  
  // Test 1: Real loan number query
  const test1 = await testQuestion(
    "What was the net operating income for loan number MTN-10234?",
    "Real Loan Number Query (MTN-10234)"
  );
  
  // Test 2: Missing loan number
  const test2 = await testQuestion(
    "What is the typical cap rate for commercial properties?",
    "Missing Loan Number Error Handling"
  );
  
  // Summary
  console.log(`\n${'='.repeat(80)}`);
  console.log('TEST SUMMARY');
  console.log(`${'='.repeat(80)}`);
  console.log(`Test 1 (Real Loan): ${test1.success ? '✅ PASS' : '❌ FAIL'} (${test1.elapsed}ms)`);
  console.log(`Test 2 (No Loan):   ${test2.success ? '✅ PASS' : '❌ FAIL'} (${test2.elapsed}ms)`);
  console.log(`\nTotal Time: ${test1.elapsed + test2.elapsed}ms`);
  console.log(`${'='.repeat(80)}\n`);
  
  // Verify expected content
  let allPassed = true;
  
  if (test1.success) {
    if (!test1.data.answer.includes('MTN-10234')) {
      console.log('⚠️  WARNING: Test 1 answer does not mention loan number MTN-10234');
      allPassed = false;
    }
    if (!test1.data.answer.includes('1,743,260') && !test1.data.answer.includes('1743260')) {
      console.log('⚠️  WARNING: Test 1 answer does not contain expected NOI value');
      allPassed = false;
    }
  } else {
    allPassed = false;
  }
  
  if (test2.success) {
    if (!test2.data.answer.includes("couldn't find a loan number")) {
      console.log('⚠️  WARNING: Test 2 should return "couldn\'t find a loan number" message');
      allPassed = false;
    }
  } else {
    allPassed = false;
  }
  
  if (allPassed) {
    console.log('\n🎉 ALL TESTS PASSED - Frontend/Backend integration is working correctly!\n');
  } else {
    console.log('\n⚠️  SOME TESTS HAD ISSUES - Review the output above\n');
  }
}

// Run the tests
runTests().catch(console.error);
