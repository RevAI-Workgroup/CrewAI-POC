import * as React from "react"
import { GalleryVerticalEnd, Home, Network } from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar"
import { NavUser } from "./nav-user"
import { Link, useLocation } from "react-router-dom"
import { ROUTES } from "@/router/routes"

export interface NavItem {
  title: string
  url: string
  icon?: React.ComponentType<{ className?: string }>
  isActive?: boolean
  items?: Omit<NavItem, "items">[]
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation()

  // Navigation items for the app
  const data = {
    navMain: [
      {
        title: "Dashboard",
        url: ROUTES.DASHBOARD,
        icon: Home,
        isActive: location.pathname === ROUTES.DASHBOARD,
        items: [],
      },
      {
        title: "Graphs",
        url: ROUTES.GRAPHS,
        icon: Network,
        isActive: location.pathname.startsWith('/graphs'),
        items: [
          // TODO When Graph store is implemented, display the latest 5 graph. If no graph the show 'No graph created yet'
        ],
      },
    ] as NavItem[],
  }

  return (
    <Sidebar variant="floating" {...props} collapsible="offcanvas">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link to={ROUTES.DASHBOARD}>
                <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                  <GalleryVerticalEnd className="size-4" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-medium">RevAI</span>
                  <span className="font-light text-sm">CrewAI Builder</span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarMenu className="gap-2">
            {data.navMain.map((item) => (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton asChild isActive={item.isActive}>
                  <Link to={item.url} className="font-medium">
                    {item.icon && <item.icon className="size-4" />}
                    {item.title}
                  </Link>
                </SidebarMenuButton>
                {item.items && item.items.length > 0 ? (
                  <SidebarMenuSub className="ml-0 border-l-0 px-1.5">
                    {item.items.map((subItem) => (
                      <SidebarMenuSubItem key={subItem.title}>
                        <SidebarMenuSubButton asChild isActive={subItem.isActive}>
                          <Link to={subItem.url}>
                            {subItem.icon && <subItem.icon className="size-3" />}
                            {subItem.title}
                          </Link>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                    ))}
                  </SidebarMenuSub>
                ) : null}
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
    </Sidebar>
  )
}
