module.exports = {
  opspilot: {
    input: {
      target: 'http://localhost:8000/openapi.json',
    },
    output: {
      mode: 'split',
      target: 'src/api-client.ts',
      schemas: 'src/api-schemas.ts',
      client: 'axios',
      mock: true,
    },
    hooks: {
      afterAllFilesWrite: 'prettier --write',
    },
  },
};
