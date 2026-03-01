/**
 * Global Utility Formatters
 * Standardizes numerical output for financial and climate data.
 *
 */

// Formats numbers as USD currency (e.g., $1,240,000)
export const formatCurrency = (val) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(val);
};

// Formats decimals as percentages (e.g., 0.072 -> 7.2%)
export const formatPercent = (val, decimals = 1) => {
  if (val === undefined || val === null) return '0%';
  return `${val.toFixed(decimals)}%`;
};

// Formats large numbers with abbreviations (e.g., 1500000 -> 1.5M)
export const formatCompact = (val) => {
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    compactDisplay: 'short',
  }).format(val);
};

// Formats dates for the time-series charts (e.g., 02/28)
export const formatDate = (dateString) => {
  const date = new Date(dateString);
  return `${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`;
};

const formatters = {
  currency: formatCurrency,
  percent: formatPercent,
  compact: formatCompact,
  date: formatDate
};

export default formatters;