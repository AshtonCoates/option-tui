/*
 * CODE TO BUILD TUI DASHBOARD FOR IMPLIED VOLATILITY CALCULATION
 */

use ratatui::{
    backend::CrosstermBackend,
    widgets::{Block, Borders, Chart, Dataset, Axis},
    layout::{Constraint, Direction, Layout},
    Terminal,
};
use yahoo_finance_api as yahoo;
use crossterm::{event, execute, terminal};
use std::{io, time::Duration};
use tokio::sync::mpsc;

#[derive(Debug)]
struct Point(f64, f64);

// toy smile: U-shape for demo
fn implied_vol(k: i32) -> f64 {
    let m = 1300.0;
    0.02 + ((k as f64 - m).powi(2) / 700_000.0)
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // ── 1. Terminal init ────────────────────────────────────────────────
    terminal::enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, terminal::EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut term  = Terminal::new(backend)?;

    // ── 2. Channels & background fetch task ─────────────────────────────
    let (tx, mut rx) = mpsc::channel::<Vec<Point>>(8);
    tokio::spawn(async move {
        loop {
            // TODO: replace with real API call
            let fake_smile = (800..=1800).step_by(50)
                .map(|k| Point(k as f64, implied_vol(k)))   // your calc
                .collect();
            tx.send(fake_smile).await.ok();
            tokio::time::sleep(Duration::from_secs(2)).await;
        }
    });

    // ── 3. App state ----------------------------------------------------
    let mut smile: Vec<Point> = Vec::new();

    // ── 4. UI loop ──────────────────────────────────────────────────────
    loop {
        // non-blocking receive
        while let Ok(new) = rx.try_recv() { smile = new }

        term.draw(|f| {
            let chunks = Layout::default()
                .direction(Direction::Horizontal)
                .constraints([Constraint::Percentage(55), Constraint::Percentage(45)])
                .split(f.size());

            // Left-hand side split into two rows
            let left = Layout::default()
                .direction(Direction::Vertical)
                .constraints([Constraint::Percentage(60), Constraint::Percentage(40)])
                .split(chunks[0]);

            // ---- Vol smile scatter ------------------------------------
            let data: Vec<(f64, f64)> =
                smile.iter().map(|p| (p.0, p.1 * 100.0)).collect();
            let ds = Dataset::default()
                .name("IV%")
                .marker(ratatui::symbols::Marker::Dot)
                .data(&data);

            let chart = Chart::new(vec![ds])
                .block(Block::default().title("IV Smile").borders(Borders::ALL))
                .x_axis(Axis::default().title("Strike").bounds([800.0, 1800.0]))
                .y_axis(Axis::default().title("IV (%)").bounds([0.0, 7.0]));

            f.render_widget(chart, left[0]);

            // ---- Price-time line (placeholder) ------------------------
            // Do the same with another Chart widget on left[1]

            // ---- Calls / Puts tables (placeholder) --------------------
            // Use ratatui::widgets::Table on chunks[1]
        })?;

        // handle keypress
        if event::poll(Duration::from_millis(16))? {
            if let event::Event::Key(k) = event::read()? {
                if matches!(k.code, event::KeyCode::Char('q')) { break }
            }
        }
    }

    // ── 5. Cleanup ──────────────────────────────────────────────────────
    terminal::disable_raw_mode()?;
    execute!(term.backend_mut(), terminal::LeaveAlternateScreen)?;
    Ok(())
}

