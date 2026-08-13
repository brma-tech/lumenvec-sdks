import assert from "node:assert/strict";
import { LumenVecClient } from "./index.mjs";

let seen;
globalThis.fetch = async (url, options) => {
  seen = { url, options, body: JSON.parse(options.body) };
  return { ok: true, status: 200, text: async () => JSON.stringify({ ok: true }) };
};

const client = new LumenVecClient("http://example.test", { apiKey: "secret" });
await client.search([1, 0], { k: 3, metadata: { tenant: "acme" }, metric: "cosine" });
assert.equal(seen.url, "http://example.test/v1/vectors/search");
assert.equal(seen.options.headers.Authorization, "Bearer secret");
assert.deepEqual(seen.body.metadata, { tenant: "acme" });
assert.equal(seen.body.metric, "cosine");
console.log("javascript SDK contract ok");

globalThis.fetch = async () => ({ ok: true, status: 200, text: async () => "ok" });
assert.equal(await client.health(), "ok");
console.log("javascript SDK health compatibility ok");
