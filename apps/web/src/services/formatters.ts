import { MetricType } from '../types/api';

/**
 * Friendly label for metrics with business clarification.
 */
export function getMetricLabel(metric: MetricType | string): string {
  switch (metric) {
    case 'total_gmv':
      return 'Total GMV (Revenue)';
    case 'orders_count':
      return 'Order Volume';
    case 'average_order_value':
      return 'Average Order Value';
    case 'late_delivery_rate_pct':
      return 'Late Delivery Rate';
    case 'avg_review_score':
      return 'Customer Review Score';
    default:
      return metric.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }
}

/**
 * Format metric value dynamically based on its semantic metric type.
 */
export function formatMetricValue(value: number | null | undefined, metric: MetricType | string): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }

  switch (metric) {
    case 'total_gmv':
    case 'average_order_value':
      return `R$ ${Math.round(value).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
    case 'orders_count':
      return `${Math.round(value).toLocaleString()} orders`;
    case 'late_delivery_rate_pct':
      return `${value.toFixed(1)}%`;
    case 'avg_review_score':
      return `${value.toFixed(2)} ★`;
    default:
      return value.toLocaleString();
  }
}

/**
 * Format currency in Brazilian Real (BRL) with clean integer or 2-decimal presentation.
 */
export function formatBRL(value: number | null | undefined, decimals = 0): string {
  if (value === null || value === undefined) return 'R$ 0';
  return `R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
}

/**
 * Format percentage with explicit +/- sign.
 */
export function formatPercentChange(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined) return 'N/A';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}

/**
 * Format ISO date string (YYYY-MM-DD) to business-friendly format (DD MMM YYYY).
 * e.g. "2017-11-01" -> "01 Nov 2017"
 */
export function formatDisplayDate(isoDate: string | null | undefined): string {
  if (!isoDate) return 'Select Date';
  try {
    const parts = isoDate.split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const monthIndex = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const dayStr = day < 10 ? `0${day}` : `${day}`;
      return `${dayStr} ${months[monthIndex]} ${year}`;
    }
    const d = new Date(isoDate + 'T00:00:00');
    if (!isNaN(d.getTime())) {
      return d.toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' });
    }
    return isoDate;
  } catch {
    return isoDate;
  }
}

/**
 * Friendly dimension label dictionary mapping database slugs to readable English names.
 */
const CATEGORY_NAMES: Record<string, string> = {
  cama_mesa_banho: 'Bed, Bath & Table',
  beleza_saude: 'Health & Beauty',
  esporte_lazer: 'Sports & Leisure',
  moveis_decoracao: 'Furniture & Decor',
  informatica_acessorios: 'Computers & Accessories',
  utilidades_domesticas: 'Housewares',
  relogios_presentes: 'Watches & Gifts',
  telefonia: 'Telephony & Mobile',
  automotivo: 'Automotive',
  brinquedos: 'Toys & Games',
  ferramentas_jardim: 'Garden Tools',
  perfumaria: 'Perfumery',
  bebes: 'Baby Products',
  eletronicos: 'Electronics',
  papelaria: 'Stationery & Office',
  fashion_bolsas_e_acessorios: 'Fashion & Bags',
  pet_shop: 'Pet Supplies',
  consoles_games: 'Games & Consoles',
  cool_stuff: 'Gadgets & Gifts',
};

const STATE_NAMES: Record<string, string> = {
  SP: 'São Paulo (SP)',
  RJ: 'Rio de Janeiro (RJ)',
  MG: 'Minas Gerais (MG)',
  RS: 'Rio Grande do Sul (RS)',
  PR: 'Paraná (PR)',
  SC: 'Santa Catarina (SC)',
  BA: 'Bahia (BA)',
  DF: 'Distrito Federal (DF)',
  GO: 'Goiás (GO)',
  ES: 'Espírito Santo (ES)',
  PE: 'Pernambuco (PE)',
  CE: 'Ceará (CE)',
};

/**
 * Friendly names for dimension attributes.
 */
export function prettifyDimensionName(dimension: string): string {
  switch (dimension) {
    case 'product_category':
      return 'Product Category';
    case 'customer_state':
      return 'Customer Region';
    case 'seller':
      return 'Seller';
    default:
      return dimension.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }
}

/**
 * Prettify database dimension values for executive presentation.
 */
export function prettifyDimensionValue(dimValue: string, dimension: string): string {
  if (!dimValue) return 'Unknown';

  if (dimension === 'product_category' && CATEGORY_NAMES[dimValue]) {
    return CATEGORY_NAMES[dimValue];
  }

  if (dimension === 'customer_state' && STATE_NAMES[dimValue.toUpperCase()]) {
    return STATE_NAMES[dimValue.toUpperCase()];
  }

  if (dimension === 'seller' && dimValue.length > 12) {
    return `Seller (${dimValue.slice(0, 8)}…)`;
  }

  // General slug to title case
  return dimValue
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
