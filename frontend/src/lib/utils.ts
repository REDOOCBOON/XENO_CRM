import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
  }).format(amount)
}

export function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

export function getRiskClass(risk: string) {
  if (risk.includes('High')) return 'risk-high'
  if (risk.includes('Medium')) return 'risk-medium'
  if (risk.includes('VIP')) return 'risk-active-vip'
  return 'risk-active'
}

export function getStatusClass(status: string) {
  return `status-${status.toLowerCase()}`
}


export function truncate(str: string, n: number) {
  return str.length > n ? str.substring(0, n) + '...' : str
}
