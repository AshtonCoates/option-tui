use anyhow::Result;
use regex::Regex;
use reqwest::header::{HeaderMap, HeaderValue, USER_AGENT};
use reqwest::{Client, ClientBuilder};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct YfResponse {
    finance: Finance,
}

#[derive(Debug, Deserialize)]
struct Finance {
    result: Option<Vec<ChainResult>>,
    error: Option<YfError>,
}

#[derive(Debug, Deserialize)]
struct ChainResult {
    expirationDates: Vec<u64>,
    strikes: Vec<f64>,
    options: Vec<OptionData>,
}

#[derive(Debug, Deserialize)]
pub struct OptionData {
    calls: Vec<OptionQuote>,
    puts: Vec<OptionQuote>,
}

#[derive(Debug, Deserialize)]
struct OptionQuote {
    contractSymbol:   String,
    strike:           f64,
    lastPrice:        f64,
    bid:              f64,
    ask:              f64,
    volume:           u64,
    openInterest:     u64,
    #[serde(rename = "impliedVolatility")]
    implied_volatility: f64,
}

#[derive(Debug, Deserialize)]
struct YfError {
    code: String,
    description: String,
}

async fn fetch_option_chain(symbol: &str) -> Result<YfResponse> {
    // 1) Build a client with cookie-store enabled
    let mut headers = HeaderMap::new();
    headers.insert(
        USER_AGENT,
        HeaderValue::from_static("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/100.0.4896.127 Safari/537.36"),
    );

    let client: Client = ClientBuilder::new()
        .default_headers(headers)
        .cookie_store(true)
        .build()?;

    // 2) GET the HTML page to populate cookies + find crumb
    let url_page = format!(
        "https://finance.yahoo.com/quote/{SYMBOL}/options?p={SYMBOL}",
        SYMBOL = symbol
    );
    let html = client.get(&url_page).send().await?.text().await?;

    // 3) Extract the crumb with a regex
    let re = Regex::new(r#"CrumbStore":\{"crumb":"(?P<crumb>[^"]+)""#)?;
    let crumb = re
        .captures(&html)
        .and_then(|cap| cap.name("crumb").map(|m| m.as_str().replace(r#"\""#, r#"""#)))
        .ok_or_else(|| anyhow::anyhow!("Failed to extract crumb"))?;

    // 4) Call the JSON endpoint re-using the same client (and its cookies)
    let url_json = format!(
        "https://query1.finance.yahoo.com/v7/finance/options/{SYMBOL}",
        SYMBOL = symbol
    );
    let resp = client
        .get(&url_json)
        .query(&[("crumb", &crumb)])
        .send()
        .await?
        .error_for_status()?
        .json::<YfResponse>()
        .await?;

    Ok(resp)
}

#[cfg(test)]
mod tests {
    
    use super::*;

    #[test]
    fn get_option_chain() {
        let symbol = "TSLA";
        let data = fetch_option_chain(symbol);
    }
}
