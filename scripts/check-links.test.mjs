import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { extractUrls } from './check-links.mjs';

describe('link checker URL extraction', () => {
  it('ignores fenced and inline code examples', () => {
    const urls = extractUrls(`
See https://docs.example.org/guide.
\`https://api.example.com/v1\`
\`\`\`bash
curl https://169.254.169.254/latest/meta-data/
\`\`\`
`);

    assert.deepEqual([...urls], ['https://docs.example.org/guide']);
  });

  it('strips longer fenced blocks by line, including URLs before later prose', () => {
    const urls = extractUrls([
      'Intro https://docs.example.org/intro',
      '````markdown',
      '```bash',
      'curl https://api.smith.langchain.com/v1',
      '```',
      '````',
      'Afterward https://docs.example.org/after',
    ].join('\n'));

    assert.deepEqual([...urls], ['https://docs.example.org/intro', 'https://docs.example.org/after']);
  });

  it('preserves bracketed IPv6 hosts and removes Chinese punctuation', () => {
    const urls = extractUrls('[loopback](https://[::1]/health)， [guide](https://docs.example.org/agent)。');

    assert.deepEqual([...urls], ['https://[::1]/health', 'https://docs.example.org/agent']);
  });

  it('removes a Markdown closing parenthesis without truncating URL paths', () => {
    const urls = extractUrls('[guide](https://docs.example.org/topic_(agents))');

    assert.deepEqual([...urls], ['https://docs.example.org/topic_(agents)']);
  });

  it('extracts adjacent Markdown links independently', () => {
    const urls = extractUrls('[first](https://docs.example.org/one)与[second](https://docs.example.org/two)。');

    assert.deepEqual([...urls], ['https://docs.example.org/one', 'https://docs.example.org/two']);
  });

  it('does not request reserved example domains', () => {
    const urls = extractUrls('https://attacker.example/x and https://api.example.com/v1');

    assert.deepEqual([...urls], []);
  });

  it('drops a bare URL scheme without a host', () => {
    assert.deepEqual([...extractUrls('默认端点是 https://。')], []);
  });
});
