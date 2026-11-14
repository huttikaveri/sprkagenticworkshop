import os
import pandas as pd
import numpy as np
import json, html

# Settings
WORK_DIR = '/content/sprk/run-7027'
FILE_PATH = f'{WORK_DIR}/input.xlsx'

# Load data
orders = pd.read_excel(FILE_PATH, sheet_name='Orders')
returns = pd.read_excel(FILE_PATH, sheet_name='Returns')
people = pd.read_excel(FILE_PATH, sheet_name='People')

# Merge returns info into orders
df = orders.merge(returns[['Order ID', 'Returned']], on='Order ID', how='left')
df['Returned'] = df['Returned'].fillna('No')

# KPIs
kpi_total_sales = df['Sales'].sum()
kpi_total_profit = df['Profit'].sum()
kpi_total_orders = df['Order ID'].nunique()
kpi_returned_orders = (df['Returned'] == 'Yes').sum()
kpi_avg_discount = df['Discount'].mean()

# Insights
insights = []
insights.append(f"Total sales: ${kpi_total_sales:,.0f}")
insights.append(f"Total profit: ${kpi_total_profit:,.0f}")
insights.append(f"Total unique orders: {kpi_total_orders}")
insights.append(f"Returned orders: {kpi_returned_orders} ({kpi_returned_orders/kpi_total_orders:.1%})")
insights.append(f"Average discount: {kpi_avg_discount:.2%}")

# Bar chart: Top 15 Sub-Category by Sales, filter by Region
bar_category = 'Sub-Category'
bar_value = 'Sales'
bar_filter = 'Region'
bar_data = {}
for region in ['All'] + sorted(df[bar_filter].unique()):
    d = df if region == 'All' else df[df[bar_filter] == region]
    top = d.groupby(bar_category)[bar_value].sum().sort_values(ascending=False).head(15)
    bar_data[region] = {'labels': top.index.tolist(), 'values': top.values.tolist()}

# Pie chart: Segment by Profit, filter by Market
pie_category = 'Segment'
pie_value = 'Profit'
pie_filter = 'Market'
pie_data = {}
for market in ['All'] + sorted(df[pie_filter].unique()):
    d = df if market == 'All' else df[df[pie_filter] == market]
    seg = d.groupby(pie_category)[pie_value].sum().sort_values(ascending=False)
    # Top 7 + Other
    if len(seg) > 7:
        top = seg.head(7)
        other = seg.iloc[7:].sum()
        top['Other'] = other
        seg = top
    pie_data[market] = {'labels': seg.index.tolist(), 'values': seg.values.tolist()}

# Preview table
preview_cols = ['Order ID', 'Order Date', 'Customer Name', 'Segment', 'Country', 'Region', 'Market', 'Category', 'Sub-Category', 'Sales', 'Profit', 'Returned']
preview = df[preview_cols].head(10)

# Save all chart data as JSON
chart_data = {
    'bar': {'category': bar_category, 'value': bar_value, 'filter': bar_filter, 'data': bar_data},
    'pie': {'category': pie_category, 'value': pie_value, 'filter': pie_filter, 'data': pie_data},
}
chart_data_json = json.dumps(chart_data)

# HTML template
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Global Superstore 2016 Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f8f8f8; }
.container { max-width: 1200px; margin: 30px auto; background: #fff; padding: 24px 32px 32px 32px; border-radius: 10px; box-shadow: 0 2px 8px #0001; }
h1 { font-size: 2.2em; margin-bottom: 0.2em; }
h2 { font-size: 1.2em; color: #555; margin-top: 0; }
.kpis { display: flex; gap: 24px; margin: 24px 0 32px 0; }
.kpi { background: #f0f4f8; border-radius: 8px; padding: 18px 28px; font-size: 1.25em; flex: 1; text-align: center; box-shadow: 0 1px 4px #0001; }
.charts { display: flex; gap: 32px; }
.chart-block { flex: 1; background: #fafbfc; border-radius: 8px; padding: 18px 18px 10px 18px; box-shadow: 0 1px 4px #0001; }
.chart-title { font-weight: bold; margin-bottom: 8px; }
.filter-row { margin-bottom: 10px; }
.insights { margin: 32px 0 18px 0; }
.insights li { margin-bottom: 6px; }
.preview-table { border-collapse: collapse; width: 100%; margin-top: 12px; background: #fff; }
.preview-table th, .preview-table td { border: 1px solid #ddd; padding: 6px 10px; font-size: 0.98em; }
.preview-table th { background: #f0f0f0; }
</style>
</head>
<body>
<div class="container">
<h1>__TITLE__</h1>
<h2>__SUBTITLE__</h2>
<div class="kpis">__KPIS__</div>
<div class="charts">
  <div class="chart-block">
    <div class="chart-title">Top 15 Sub-Categories by Sales</div>
    <div class="filter-row">
      <label for="bar-filter">Region:</label>
      <select id="bar-filter"></select>
    </div>
    <div id="bar-chart"></div>
  </div>
  <div class="chart-block">
    <div class="chart-title">Profit by Segment</div>
    <div class="filter-row">
      <label for="pie-filter">Market:</label>
      <select id="pie-filter"></select>
    </div>
    <div id="pie-chart"></div>
  </div>
</div>
<div class="insights">
  <h3>Key Insights</h3>
  <ul>__INSIGHTS__</ul>
</div>
<h3>Preview of First 10 Orders</h3>
<table class="preview-table">
<thead><tr>__PREVIEW_HEADER__</tr></thead>
<tbody>__PREVIEW_ROWS__</tbody>
</table>
</div>
<script>
const chartData = __DATA__;
function escapeHtml(text) {
  var map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}
function fillDropdown(id, options) {
  const sel = document.getElementById(id);
  sel.innerHTML = '';
  options.forEach(opt => {
    const o = document.createElement('option');
    o.value = opt; o.textContent = opt;
    sel.appendChild(o);
  });
}
function drawBar(region) {
  const d = chartData.bar.data[region];
  Plotly.react('bar-chart', [{
    x: d.labels,
    y: d.values,
    type: 'bar',
    marker: {color: '#2a7cff'}
  }], {margin: {t: 30, l: 60, r: 10, b: 80}, xaxis: {tickangle: -30}, yaxis: {title: 'Sales'}, title: ''}, {displayModeBar: false});
}
function drawPie(market) {
  const d = chartData.pie.data[market];
  Plotly.react('pie-chart', [{
    labels: d.labels,
    values: d.values,
    type: 'pie',
    textinfo: 'label+percent',
    marker: {colors: ['#2a7cff','#00b894','#fdcb6e','#e17055','#636e72','#6c5ce7','#00cec9','#b2bec3']}
  }], {margin: {t: 30, l: 10, r: 10, b: 10}, title: ''}, {displayModeBar: false});
}
document.addEventListener('DOMContentLoaded', function() {
  fillDropdown('bar-filter', Object.keys(chartData.bar.data));
  fillDropdown('pie-filter', Object.keys(chartData.pie.data));
  document.getElementById('bar-filter').addEventListener('change', e => drawBar(e.target.value));
  document.getElementById('pie-filter').addEventListener('change', e => drawPie(e.target.value));
  drawBar('All');
  drawPie('All');
});
</script>
</body>
</html>
