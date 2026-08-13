export class LumenVecError extends Error {}

export class LumenVecClient {
  constructor(baseUrl, { apiKey, timeoutMs = 10000 } = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiKey = apiKey;
    this.timeoutMs = timeoutMs;
  }

  async request(method, path, body) {
    const headers = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (this.apiKey) headers.Authorization = `Bearer ${this.apiKey}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method, headers, body: body === undefined ? undefined : (typeof body === "string" ? body : JSON.stringify(body)),
        signal: controller.signal,
      });
      const text = await response.text();
      let value = null;
      if (text) {
        try { value = JSON.parse(text); } catch { value = text; }
      }
      if (!response.ok) throw new LumenVecError(`HTTP ${response.status}: ${text}`);
      return value;
    } catch (error) {
      if (error instanceof LumenVecError) throw error;
      throw new LumenVecError(error.message);
    } finally { clearTimeout(timer); }
  }

  health() { return this.request("GET", "/v1/health"); }
  upsert(id, values, metadata, { namespace } = {}) {
    return this.request("POST", "/v1/vectors", { id, values, ...(metadata ? { metadata } : {}), ...(namespace ? { namespace } : {}) });
  }
  upsertBatch(vectors, { namespace } = {}) {
    const payload = namespace ? vectors.map((vector) => ({ ...vector, namespace })) : vectors;
    return this.request("POST", "/v1/vectors/batch", { vectors: payload });
  }
  async upsertStream(records, { namespace } = {}) {
    const body = records.map((vector) => JSON.stringify(namespace ? { ...vector, namespace } : vector)).join("\n") + "\n";
    return this.request("POST", "/v1/vectors/stream", body);
  }
  get(id) { return this.request("GET", `/v1/vectors/${encodeURIComponent(id)}`); }
  search(values, { k = 10, filterIds, textQuery, metadata, metric, namespace } = {}) {
    return this.request("POST", "/v1/vectors/search", {
      values, k, ...(filterIds ? { filter_ids: filterIds } : {}),
      ...(textQuery ? { text_query: textQuery } : {}), ...(metadata ? { metadata } : {}),
      ...(metric ? { metric } : {}), ...(namespace ? { namespace } : {}),
    });
  }
}
