// Skeleton Vitest configuration mirroring file-storage-backend defaults.
export default {
  test: {
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    coverage: {
      reporter: ['text', 'html']
    }
  }
};
