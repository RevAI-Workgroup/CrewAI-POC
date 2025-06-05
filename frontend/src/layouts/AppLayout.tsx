import React from "react"
import { AppSidebar } from "@/components/app-sidebar"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { Link, Outlet } from "react-router-dom"
import { useBreadcrumbs } from "@/hooks/useBreadcrumbs"
import { ReactFlowProvider } from "@xyflow/react"
import { DnDProvider } from "@/contexts/DnDProvider"

export function AppLayout() {
  const breadcrumbs = useBreadcrumbs()

  return (
    <div className='h-screen bg-background'>
      <SidebarProvider
        style={
          {
            "--sidebar-width": "19rem",
          } as React.CSSProperties
        }
      >
        <ReactFlowProvider>
        <DnDProvider>
          <AppSidebar />
          <SidebarInset>
            <header className="flex h-16 shrink-0 items-center gap-2 px-2">
              <SidebarTrigger className="-ml-1" />
              <Separator
                orientation="vertical"
                className="mr-2 data-[orientation=vertical]:h-4"
              />
              <Breadcrumb>
                <BreadcrumbList>
                  {breadcrumbs.map((item, index) => (
                    <React.Fragment key={index}>
                      {index > 0 && <BreadcrumbSeparator />}
                      <BreadcrumbItem>
                        {item.isCurrentPage ? (
                          <BreadcrumbPage>{item.title}</BreadcrumbPage>
                        ) : (
                          <BreadcrumbLink asChild>
                            <Link to={item.href || ""}>
                              {item.title}
                            </Link>
                            
                          </BreadcrumbLink>
                        )}
                      </BreadcrumbItem>
                    </React.Fragment>
                  ))}
                </BreadcrumbList>
              </Breadcrumb>
            </header>
            <div className="flex flex-1 flex-col gap-4 p-2 pt-0 rounded-lg overflow-hidden">
              <div className='space-y-6 w-full grow rounded-lg overflow-hidden'>
                <Outlet />
              </div>
            </div>
          </SidebarInset>`
        </DnDProvider>
        </ReactFlowProvider>
        
      </SidebarProvider>
    </div>
  )
}
  