use lumenvec_client::LumenVecClient;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = LumenVecClient::new("http://localhost:19294");
    let health = client.health().await?;
    let _ = client.upsert("sdk-rust-live", &[1.0, 0.0], None).await?;
    let search = client.search(&[1.0, 0.0], 1, Some("cosine"), None).await?;
    println!("rust health={health} search={search}");
    Ok(())
}
