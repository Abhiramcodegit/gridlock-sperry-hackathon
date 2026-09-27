// Test-only setup (Agent 3). Not imported by application code.
// Registers jest-dom matchers (toBeInTheDocument, toHaveTextContent, etc.)
// and cleans up the DOM between tests.
import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
})
