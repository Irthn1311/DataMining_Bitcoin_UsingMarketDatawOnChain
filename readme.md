# Bitcoin Market & On-Chain Data Mining

A data-mining project that studies Bitcoin using **market data, on-chain metrics, and event windows**. The repository covers data collection, preprocessing, exploratory analysis, clustering, association analysis, event studies, and next-day direction classification.

## Project questions

The work is organized around a few practical questions:

- What recurring market regimes appear in Bitcoin return, volatility, and volume data?
- Which on-chain metrics tend to move together?
- Do large-volume days coincide with unusually large price movements?
- Are abnormal changes visible around major public events?
- Which feature groups are most useful for next-day up/down classification?

The event analysis is treated as **association / event-window analysis**, not as proof that an event caused a price movement.

## Data

### Market data

Daily Bitcoin OHLCV data is collected through Yahoo Finance / `yfinance`.

Derived features include:

- daily and 7-day return
- rolling volatility
- volume change
- high-low range
- moving averages and moving-average ratios

### On-chain data

On-chain metrics are collected from public Coin Metrics and Blockchain.com endpoints, including features such as:

- active addresses
- transaction count
- hash rate
- supply
- fees
- mining difficulty
- miner revenue
- estimated transaction volume

### Event data

A manually curated event table is joined by date and transformed into event-window features such as 3-day, 7-day, and 14-day windows.

Because this table is manually curated, event dates and source references should be verified before using the data in formal research.

## Methods

| Task | Methods |
| --- | --- |
| Market / network regimes | K-Means, DBSCAN, hierarchical clustering |
| Relationship mining | Correlation analysis, Apriori / FP-Growth |
| Event analysis | Event windows, before/after comparison, statistical tests |
| Direction classification | Logistic Regression, Random Forest, XGBoost |
| Feature analysis | Feature importance and feature-group comparison |

Evaluation includes classification metrics, clustering quality metrics, association-rule statistics, and statistical tests where appropriate.

## Time-series evaluation

Bitcoin observations are ordered in time. Classification experiments should therefore use chronological train/validation/test splits or another time-aware protocol rather than random shuffling.

This repository explicitly avoids treating the final test period as a checkpoint-selection set.

## Repository structure

```text
DataMining_Bitcoin_UsingMarketDatawOnChain/
├── data/           market, on-chain, event, and merged datasets
├── scripts/        data collection
├── preprocessing/  preprocessing workflows
├── eda/            exploratory data analysis
├── mining/         data-mining experiments
├── DuDoan/         prediction experiments
├── Notebook/       notebooks
├── docs/           project documentation
├── requirements.txt
└── readme.md
```

## Reproduce the data pipeline

Install dependencies:

```bash
pip install -r requirements.txt
```

Fetch / rebuild the source datasets:

```bash
python scripts/fetchData.py
```

The script collects available market and on-chain data, engineers derived features, creates event-window variables, and produces the merged daily dataset used by downstream notebooks.

## Data sources

- Yahoo Finance via `yfinance`
- Coin Metrics Community API
- Blockchain.com Charts API
- Manually curated event dates for the event-study component

## Status

Academic data-mining project. The repository is kept public as an example of a complete workflow from data acquisition through exploratory analysis and multiple data-mining tasks.
