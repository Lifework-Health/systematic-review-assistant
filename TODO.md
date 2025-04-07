# TODO

This is work in progress.

## Protocol Page

- [ ] Add separate button under research question to generate PICO. Currently
      triggered from way below suggestion agent button. Bad UX.

## Search Page

- [ ] Add Embase, etc. support and query handling. UI probably tabbed.

## Screen Abstracts Page

- [ ] Test resolver in UI
- [ ] Make screening decision writable cell in table

## Testing

- [ ] Fix failing integration tests. E.g., suggestion agent.
- [ ] Test resolver in UI. DB integration tests pass.
- [ ] Add integration tests for repositories.
- [ ] Finish tests/integration/test_resolver_agent.py (non-db resolver tests)
- [ ] Aim for at least 80% test coverage. With each feat having at least one
      integration test.

## Models for other search databases and handling

- [ ] One generic search model or many specific models? what to do to PubMedResult?
- [ ] Implement model changes required. (big task)
