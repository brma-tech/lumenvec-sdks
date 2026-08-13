use reqwest::Client;
use serde::Serialize;
use std::collections::HashMap;

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("request failed: {0}")]
    Http(#[from] reqwest::Error),
    #[error("server returned {status}: {body}")]
    Server { status: u16, body: String },
}

#[derive(Clone)]
pub struct LumenVecClient {
    base_url: String,
    api_key: Option<String>,
    http: Client,
}

#[derive(Default)]
pub struct SearchOptions<'a> {
    pub filter_ids: Option<&'a [String]>,
    pub text_query: Option<&'a str>,
    pub metadata: Option<&'a HashMap<String, String>>,
    pub metric: Option<&'a str>,
    pub namespace: Option<&'a str>,
}

#[derive(Serialize)]
pub struct BatchVector<'a> {
    pub id: &'a str,
    pub values: &'a [f64],
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<&'a HashMap<String, String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub namespace: Option<&'a str>,
}

#[derive(Debug, Serialize)]
struct VectorPayload<'a> {
    id: &'a str,
    values: &'a [f64],
    #[serde(skip_serializing_if = "Option::is_none")]
    metadata: Option<&'a HashMap<String, String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    namespace: Option<&'a str>,
}

#[derive(Debug, Serialize)]
struct SearchPayload<'a> {
    values: &'a [f64],
    k: usize,
    #[serde(skip_serializing_if = "Option::is_none")]
    filter_ids: Option<&'a [String]>,
    #[serde(skip_serializing_if = "Option::is_none")]
    text_query: Option<&'a str>,
    #[serde(skip_serializing_if = "Option::is_none")]
    metadata: Option<&'a HashMap<String, String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    metric: Option<&'a str>,
    #[serde(skip_serializing_if = "Option::is_none")]
    namespace: Option<&'a str>,
}

impl LumenVecClient {
    pub fn new(base_url: impl Into<String>) -> Self {
        Self {
            base_url: base_url.into().trim_end_matches('/').to_string(),
            api_key: None,
            http: Client::new(),
        }
    }
    pub fn with_api_key(mut self, key: impl Into<String>) -> Self {
        self.api_key = Some(key.into());
        self
    }
    async fn send<T: Serialize + ?Sized>(
        &self,
        method: reqwest::Method,
        path: &str,
        body: Option<&T>,
    ) -> Result<serde_json::Value, Error> {
        let mut request = self
            .http
            .request(method, format!("{}{}", self.base_url, path));
        if let Some(key) = &self.api_key {
            request = request.bearer_auth(key);
        }
        let response = if let Some(payload) = body {
            request.json(payload).send().await?
        } else {
            request.send().await?
        };
        let status = response.status();
        let text = response.text().await?;
        if !status.is_success() {
            return Err(Error::Server {
                status: status.as_u16(),
                body: text,
            });
        }
        Ok(if text.is_empty() {
            serde_json::Value::Null
        } else {
            serde_json::from_str(&text).unwrap_or(serde_json::Value::String(text))
        })
    }
    pub async fn health(&self) -> Result<serde_json::Value, Error> {
        self.send(reqwest::Method::GET, "/v1/health", None::<&()>)
            .await
    }
    pub async fn upsert(
        &self,
        id: &str,
        values: &[f64],
        metadata: Option<&HashMap<String, String>>,
    ) -> Result<serde_json::Value, Error> {
        self.send(
            reqwest::Method::POST,
            "/v1/vectors",
            Some(&VectorPayload {
                id,
                values,
                metadata,
                namespace: None,
            }),
        )
        .await
    }
    pub async fn upsert_with_namespace(
        &self, id: &str, values: &[f64], metadata: Option<&HashMap<String, String>>, namespace: &str,
    ) -> Result<serde_json::Value, Error> {
        self.send(reqwest::Method::POST, "/v1/vectors", Some(&VectorPayload {
            id, values, metadata, namespace: Some(namespace),
        })).await
    }
    pub async fn upsert_batch(&self, vectors: &[BatchVector<'_>]) -> Result<serde_json::Value, Error> {
        #[derive(Serialize)]
        struct Request<'a> { vectors: &'a [BatchVector<'a>] }
        self.send(reqwest::Method::POST, "/v1/vectors/batch", Some(&Request { vectors })).await
    }
    pub async fn upsert_stream(&self, ndjson: &str) -> Result<serde_json::Value, Error> {
        let mut request = self.http.post(format!("{}/v1/vectors/stream", self.base_url))
            .header(reqwest::header::CONTENT_TYPE, "application/x-ndjson").body(ndjson.to_owned());
        if let Some(key) = &self.api_key { request = request.bearer_auth(key); }
        let response = request.send().await?;
        let status = response.status();
        let text = response.text().await?;
        if !status.is_success() { return Err(Error::Server { status: status.as_u16(), body: text }); }
        Ok(if text.is_empty() { serde_json::Value::Null } else { serde_json::from_str(&text).unwrap_or(serde_json::Value::String(text)) })
    }
    pub async fn search(
        &self,
        values: &[f64],
        k: usize,
        metric: Option<&str>,
        metadata: Option<&HashMap<String, String>>,
    ) -> Result<serde_json::Value, Error> {
        self.search_with_options(
            values,
            k,
            SearchOptions {
                metadata,
                metric,
                ..Default::default()
            },
        )
        .await
    }
    pub async fn search_with_options(
        &self,
        values: &[f64],
        k: usize,
        options: SearchOptions<'_>,
    ) -> Result<serde_json::Value, Error> {
        self.send(
            reqwest::Method::POST,
            "/v1/vectors/search",
            Some(&SearchPayload {
                values,
                k,
                filter_ids: options.filter_ids,
                text_query: options.text_query,
                metadata: options.metadata,
                metric: options.metric,
                namespace: options.namespace,
            }),
        )
        .await
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn client_normalizes_base_url_and_api_key_is_chainable() {
        let client = LumenVecClient::new("http://localhost:8080///").with_api_key("secret");
        assert_eq!(client.base_url, "http://localhost:8080");
        assert_eq!(client.api_key.as_deref(), Some("secret"));
    }

    #[test]
    fn vector_payload_omits_absent_metadata() {
        let payload = VectorPayload {
            id: "v1",
            values: &[1.0, 2.0],
            metadata: None,
            namespace: None,
        };
        let json = serde_json::to_value(payload).expect("serialize vector payload");
        assert_eq!(json["id"], "v1");
        assert_eq!(json["values"], serde_json::json!([1.0, 2.0]));
        assert!(json.get("metadata").is_none());
    }

    #[test]
    fn search_payload_preserves_filters_metadata_and_metric() {
        let ids = vec!["doc-1".to_string(), "doc-2".to_string()];
        let mut metadata = HashMap::new();
        metadata.insert("tenant".to_string(), "acme".to_string());
        let payload = SearchPayload {
            values: &[0.1, 0.2],
            k: 10,
            filter_ids: Some(&ids),
            text_query: Some("distributed"),
            metadata: Some(&metadata),
            metric: Some("cosine"),
            namespace: Some("acme"),
        };
        let json = serde_json::to_value(payload).expect("serialize search payload");
        assert_eq!(json["k"], 10);
        assert_eq!(json["filter_ids"], serde_json::json!(["doc-1", "doc-2"]));
        assert_eq!(json["text_query"], "distributed");
        assert_eq!(json["metadata"]["tenant"], "acme");
        assert_eq!(json["metric"], "cosine");
        assert_eq!(json["namespace"], "acme");
    }

    #[tokio::test]
    async fn health_contract_uses_versioned_http_endpoint_and_auth_header() {
        use tokio::io::{AsyncReadExt, AsyncWriteExt};
        use tokio::net::TcpListener;

        let listener = TcpListener::bind("127.0.0.1:0")
            .await
            .expect("bind test server");
        let address = listener.local_addr().expect("server address");
        let server = tokio::spawn(async move {
            let (mut socket, _) = listener.accept().await.expect("accept client");
            let mut request = vec![0_u8; 2048];
            let size = socket.read(&mut request).await.expect("read request");
            let request = String::from_utf8_lossy(&request[..size]);
        assert!(request.starts_with("GET /v1/health HTTP/1.1"));
            assert!(
                request.contains("authorization: Bearer test-key")
                    || request.contains("Authorization: Bearer test-key")
            );
            socket.write_all(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 15\r\n\r\n{\"status\":\"ok\"}").await.expect("write response");
        });
        let client = LumenVecClient::new(format!("http://{}///", address)).with_api_key("test-key");
        let response = client.health().await.expect("health request");
        assert_eq!(response["status"], "ok");
        server.await.expect("test server");
    }
}
