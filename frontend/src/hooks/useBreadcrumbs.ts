import { useMemo } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { ROUTES } from '@/router/routes'
import { useGraphStore } from '@/stores'

export interface BreadcrumbItem {
  title: string
  href?: string
  isCurrentPage?: boolean
}

export function useBreadcrumbs(): BreadcrumbItem[] {
  const location = useLocation()
  const params = useParams()
  const { getGraphById } = useGraphStore()

  const breadcrumbs = useMemo(() => {
    const path = location.pathname
    const items: BreadcrumbItem[] = []

    // Handle different route patterns
    if (path === ROUTES.DASHBOARD) {
      items.push({
        title: 'Dashboard',
        isCurrentPage: true,
      })
    } else if (path === ROUTES.GRAPHS) {
      items.push({
        title: 'Graphs',
        isCurrentPage: true,
      })
    } else if (path.startsWith('/graphs/') && params.id) {
      // Add Graphs parent
      items.push({
        title: 'Graphs',
        href: ROUTES.GRAPHS,
      })
      
      // Get the actual graph name from the store
      const graph = getGraphById(params.id)
      const graphName = graph?.name || 'Untitled Graph'
      
      items.push({
        title: graphName,
        isCurrentPage: true,
      })
    }

    return items
  }, [location.pathname, params, getGraphById])

  return breadcrumbs
}

// Hook to set custom breadcrumb for a specific page
export function useSetBreadcrumb(title: string, parentPath?: string) {
  const location = useLocation()
  
  return useMemo(() => {
    const items: BreadcrumbItem[] = []

    if (parentPath && location.pathname !== ROUTES.DASHBOARD) {
      items.push({
        title: 'Dashboard',
        href: ROUTES.DASHBOARD,
      })
    }

    if (parentPath) {
      // Parse parent path to add intermediate breadcrumbs
      if (parentPath === ROUTES.GRAPHS) {
        items.push({
          title: 'Graphs',
          href: ROUTES.GRAPHS,
        })
      }
    }

    items.push({
      title,
      isCurrentPage: true,
    })

    return items
  }, [title, parentPath, location.pathname])
} 