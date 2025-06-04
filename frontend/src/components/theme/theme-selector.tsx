import { useTheme } from "@/contexts/ThemeProvider"
import {Button} from "@/components/ui/button"
import { Monitor, MoonIcon, SunIcon } from "lucide-react"
import { cn } from "@/lib/utils"


const ThemeSelector = ({includeSystem}: {includeSystem:boolean}) => {

    const {theme, setTheme} = useTheme()

    return (
        <div className="flex border rounded-md p-1 w-fit">
            {includeSystem && (
                <Button variant="ghost" onClick={() => setTheme("system")}
                className={cn("rounded-sm size-6", {
                    "bg-primary hover:bg-primary text-primary-foreground": theme == "system",
                    "hover:bg-accent": theme != "system"
                })}>
                    <Monitor className="w-2 h-2" />
                </Button>
            )}
            <Button variant="ghost" onClick={() => setTheme("light")}
                className={cn("rounded-sm size-6", {
                    "bg-primary hover:bg-primary text-primary-foreground": theme == "light",
                    "hover:bg-accent": theme != "light"
                })}>
                <SunIcon className="w-2 h-2" />
            </Button>
            <Button variant="ghost" onClick={() => setTheme("dark")}
                className={cn("rounded-sm size-6", {
                    "bg-primary hover:bg-primary text-primary-foreground": theme == "dark",
                    "hover:bg-accent": theme != "dark"
                })}>
                <MoonIcon className="w-2 h-2" />
            </Button>
        </div>
    )
}

export default ThemeSelector