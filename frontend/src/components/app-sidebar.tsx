import * as React from "react"
import { ChevronRight, GalleryVerticalEnd, Home, Network, Settings2 } from "lucide-react"

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
import { Button } from "./ui/button"
import EditorSidebar from "./graphs/editor/Sidebar"

import { v4 as uuidv4 } from 'uuid';


export interface NavItem {
  title: string
  url: string
  icon?: React.ComponentType<{ className?: string }>
  isActive?: boolean
  items?: Omit<NavItem, "items">[]
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation()

  const [isGraphNodesOpen, setIsGraphNodesOpen] = React.useState(false)

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

  React.useEffect(() => {
    if(!location.pathname.startsWith('/graphs/')) {
      setIsGraphNodesOpen(false)
    }

    if(location.pathname.startsWith('/graphs/')) {
      setIsGraphNodesOpen(true)
    }
  }, [location.pathname])

  return (
    <Sidebar variant="floating" {...props} collapsible="offcanvas">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild draggable={false}>
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
        {
          !isGraphNodesOpen ? (
            <SidebarGroup>
              <SidebarMenu className="gap-2">
                {data.navMain.map((item, i) => (
                  <React.Fragment key={`nav-main-${i}`}>
                    <SidebarMenuItem>
                      <SidebarMenuButton asChild isActive={item.isActive}>
                        <Link to={item.url} className="font-medium">
                          {item.icon && <item.icon className="size-4" />}
                          {item.title}
                        </Link>
                      </SidebarMenuButton>
                      {item.items && item.items.length > 0 ? (
                        <SidebarMenuSub className="ml-0 border-l-0 px-1.5">
                          {item.items.map((subItem, j) => (
                            <SidebarMenuSubItem key={`nav-main-${i}-sub-${j}`}>
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
                    
                    {location.pathname.startsWith('/graphs/') && item.url == ROUTES.GRAPHS && (
                      <SidebarMenuItem key={uuidv4()}>
                        <SidebarMenuButton asChild >
                          <Button variant="ghost" size="sm" className="justify-between font-medium" onClick={() => setIsGraphNodesOpen(true)}>
                            <span className="flex items-center gap-2">
                              <Settings2 className="size-4" />
                              Graph Nodes
                            </span>
                            <ChevronRight />
                          </Button>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    )}
                    
                  </React.Fragment>
                ))}
              </SidebarMenu>
            </SidebarGroup>
          ) : (
            <EditorSidebar backButtonClick={() => setIsGraphNodesOpen(false)} />
          )
        }
        
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
    </Sidebar>
  )
}
