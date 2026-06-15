'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Users,
  ShoppingBag,
  Filter,
  Megaphone,
  BarChart2,
  Lightbulb,
  Zap,
} from 'lucide-react'

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/customers', label: 'Customers', icon: Users },
  { href: '/orders', label: 'Orders', icon: ShoppingBag },
  { href: '/segments', label: 'Segment Builder', icon: Filter },
  { href: '/campaigns', label: 'Campaign Studio', icon: Megaphone },
  { href: '/analytics', label: 'Analytics', icon: BarChart2 },
  { href: '/agent', label: 'AI Agent', icon: Zap },
  { href: '/recommendations', label: 'Recommendations', icon: Lightbulb },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-60 h-screen border-r border-border bg-card flex flex-col shrink-0">
      
      <div className="p-5 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
            <Zap className="w-4 h-4 text-primary" />
          </div>
          <div>
            <p className="font-bold text-sm text-foreground">XenoPilot</p>
            <p className="text-xs text-muted-foreground">AI Marketing OS</p>
          </div>
        </div>
      </div>

      
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon
          const active = pathname === item.href

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150',
                active
                  ? 'bg-primary/15 text-primary font-medium'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
              )}
            >
              <Icon className={cn('w-4 h-4 shrink-0', active ? 'text-primary' : '')} />
              {item.label}
            </Link>
          )
        })}
      </nav>

      
      <div className="p-4 border-t border-border">
        <p className="text-xs text-muted-foreground">Xeno Engineering Assignment</p>
        <p className="text-xs text-muted-foreground/60 mt-0.5">v0.1.0 - built with FastAPI + Next.js</p>
      </div>
    </aside>
  )
}
