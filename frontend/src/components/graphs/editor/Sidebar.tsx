import { DynamicIcon } from "@/components/DynamicIcon";
import { Button } from "@/components/ui/button";
import {
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
} from "@/components/ui/sidebar";
import { Skeleton } from "@/components/ui/skeleton";
import { useDnD } from "@/contexts/DnDProvider";

import { useGraphStore } from "@/stores";

import { ChevronLeft } from "lucide-react";

import type { DragEvent } from 'react';

const EditorSidebar = ({backButtonClick}: {backButtonClick: () => void}) => {

  const {nodeDef, isLoading} = useGraphStore()
  const { setType } = useDnD();

  const onDragStart = (event: DragEvent<HTMLButtonElement>, nodeType: string) => {
    setType(nodeType);
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', nodeType || '');
  };

  return (
    <SidebarGroup>
      <SidebarHeader className="mb-2">
        <SidebarMenuButton asChild >
          <Button variant="ghost" size="sm" className="gap-2 justify-start" onClick={() => backButtonClick()}>
            <ChevronLeft />
            Back
          </Button>
        </SidebarMenuButton>
      </SidebarHeader>
      <SidebarContent>
        <SidebarMenu>
          
          {isLoading && (
            <SidebarGroup className="flex flex-col gap-2">
              <Skeleton className="h-12 w-full rounded-md" />
              <Skeleton className="h-12 w-full rounded-md" />
              <Skeleton className="h-12 w-full rounded-md" />
              <Skeleton className="h-12 w-full rounded-md" />
              <Skeleton className="h-12 w-full rounded-md" />
              <Skeleton className="h-12 w-full rounded-md" />
              <Skeleton className="h-12 w-full rounded-md" />
              <Skeleton className="h-12 w-full rounded-md" />
            </SidebarGroup>
          )}
          {!isLoading && nodeDef && (
            <>
              {nodeDef.categories.map((category, i) => (
                <SidebarGroup key={`node-category-${i}`}>
                  <SidebarGroupLabel>{category.name}</SidebarGroupLabel>
                  <SidebarGroupContent>
                    <SidebarMenu>
                      {category.nodes.map((node, j) => (
                        <SidebarMenuButton key={`node-category-${i}-node-${j}`} className="w-full gap-2 flex items-center cursor-grab transition-all duration-200 ease-in-out active:cursor-grabbing " 
                          onDragStart={(event) => onDragStart(event, node)}
                          draggable>
                          <DynamicIcon name={nodeDef.node_types[node].icon} className="size-4 text-muted-foreground"  />
                          {nodeDef.node_types[node].name}
                        </SidebarMenuButton>
                      ))}
                    </SidebarMenu>
                  </SidebarGroupContent>
                </SidebarGroup>
                
              ))}
            </>
          )}
        </SidebarMenu>
      </SidebarContent>
    </SidebarGroup>
  )
}

export default EditorSidebar;
