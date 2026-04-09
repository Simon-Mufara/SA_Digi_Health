/**
 * Test cases for error message extraction
 */

import { extractErrorMessage } from './errors';

// Test cases
const testCases = [
  {
    name: 'Simple string',
    input: 'Simple error message',
    expected: 'Simple error message',
  },
  {
    name: 'Pydantic validation error',
    input: {
      detail: [
        { type: 'value_error', loc: ['body', 'username'], msg: 'Username is required', input: null },
        { type: 'value_error', loc: ['body', 'password'], msg: 'Password too short', input: 'abc' },
      ],
    },
    expected: 'Username is required, Password too short',
  },
  {
    name: 'Single validation error object',
    input: { type: 'value_error', loc: ['body', 'email'], msg: 'Invalid email format', input: 'bad@' },
    expected: 'Invalid email format',
  },
  {
    name: 'Error with message property',
    input: { message: 'Something went wrong' },
    expected: 'Something went wrong',
  },
  {
    name: 'Error with detail property',
    input: { detail: 'Access denied' },
    expected: 'Access denied',
  },
  {
    name: 'Error with error property',
    input: { error: 'Not found' },
    expected: 'Not found',
  },
  {
    name: 'Unknown object',
    input: { unknown: 'structure', foo: 'bar' },
    expected: '{"unknown":"structure","foo":"bar"}',
  },
  {
    name: 'Null input',
    input: null,
    expected: 'null',
  },
];

console.log('Testing extractErrorMessage function...\n');

let passed = 0;
let failed = 0;

testCases.forEach((testCase) => {
  const result = extractErrorMessage(testCase.input);
  const success = result === testCase.expected;

  if (success) {
    console.log(`✓ ${testCase.name}`);
    passed++;
  } else {
    console.log(`✗ ${testCase.name}`);
    console.log(`  Expected: ${testCase.expected}`);
    console.log(`  Got:      ${result}`);
    failed++;
  }
});

console.log(`\n${passed}/${testCases.length} tests passed`);

if (failed > 0) {
  process.exit(1);
}
