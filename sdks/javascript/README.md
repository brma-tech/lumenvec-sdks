# LumenVec JavaScript SDK

Dependency-free ESM client for the versioned HTTP API. Requires a runtime with
`fetch` and `AbortController` (Node 18+ or modern browsers).

```js
import { LumenVecClient } from "./index.mjs";
const client = new LumenVecClient("http://localhost:19190");
await client.upsert("doc-1", [1, 0], { tenant: "acme" });
const hits = await client.search([1, 0], { k: 10, metadata: { tenant: "acme" }, metric: "cosine" });
```
