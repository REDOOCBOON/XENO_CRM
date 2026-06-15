'use client'

import { useEffect, useState } from 'react'
import { getOrders } from '@/lib/api'
import { formatDate, formatCurrency } from '@/lib/utils'
import { ShoppingBag } from 'lucide-react'

type Order = {
  id: string
  customer_id: string
  amount: number
  item_count: number
  status: string
  properties: {
    category?: string
    items?: Array<{ name: string; price: number }>
    attributed_campaign_id?: string
  }
  created_at: string
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getOrders()
      .then(setOrders)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-5 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Orders</h1>
        <p className="text-muted-foreground text-sm mt-1">
          {orders.length} total orders - attributed ones show campaign linkage
        </p>
      </div>

      {loading ? (
        <div className="text-muted-foreground text-sm py-10 text-center">Loading...</div>
      ) : orders.length === 0 ? (
        <div className="gradient-border rounded-xl p-10 text-center">
          <ShoppingBag className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
          <p className="text-muted-foreground text-sm">No orders yet. Seed mock data from the dashboard.</p>
        </div>
      ) : (
        <div className="gradient-border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-4 text-xs text-muted-foreground font-medium">Order ID</th>
                <th className="text-left p-4 text-xs text-muted-foreground font-medium">Amount</th>
                <th className="text-left p-4 text-xs text-muted-foreground font-medium">Items</th>
                <th className="text-left p-4 text-xs text-muted-foreground font-medium">Category</th>
                <th className="text-left p-4 text-xs text-muted-foreground font-medium">Status</th>
                <th className="text-left p-4 text-xs text-muted-foreground font-medium">Attribution</th>
                <th className="text-left p-4 text-xs text-muted-foreground font-medium">Date</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.id} className="border-b border-border/50 hover:bg-accent/30 transition-colors">
                  <td className="p-4 font-mono text-xs text-muted-foreground">
                    {order.id.substring(0, 8)}...
                  </td>
                  <td className="p-4 font-semibold text-green-400">
                    {formatCurrency(order.amount)}
                  </td>
                  <td className="p-4 text-muted-foreground">{order.item_count}</td>
                  <td className="p-4">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-accent border border-border capitalize">
                      {order.properties.category || 'general'}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${
                      order.status === 'completed' ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'
                    }`}>
                      {order.status}
                    </span>
                  </td>
                  <td className="p-4">
                    {order.properties.attributed_campaign_id ? (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                        Campaign
                      </span>
                    ) : (
                      <span className="text-xs text-muted-foreground/50">-</span>
                    )}
                  </td>
                  <td className="p-4 text-muted-foreground text-xs">{formatDate(order.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
