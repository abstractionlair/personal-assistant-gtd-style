// Minimal Vitest config that avoids importing from 'vitest/config'.
// This works even if the package export for 'vitest/config' isn't resolvable
// in environments with partially populated node_modules.
export default {
  test: {
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    coverage: {
      reporter: ['text', 'html'],
    },
  },
};
