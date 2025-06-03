


import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { cn } from "@/lib/utils"
import { useState } from "react"
import { useAuthStore } from "@/stores"
import { Link, useNavigate } from "react-router-dom"

import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { GalleryVerticalEnd } from "lucide-react"

import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
  } from "@/components/ui/alert-dialog"
import { PassphraseDisplay } from "../ui/passphrase-display"

export function RegistrationForm({
  className,
  ...props
}: React.ComponentProps<"div">) {


    const [isLoading, setIsLoading] = useState(false);
    const [passphrase, setPassphrase] = useState<string | null>(null);

    const formSchema = z.object({
        username: z.string().min(5, {
          message: "Username must be at least 5 characters.",
        }),
    })

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
          username: "",
        },
    })


    const register = useAuthStore((state) => state.register);
    const navigate = useNavigate();


    const handleSubmit = async (values: z.infer<typeof formSchema>) => {

        //setIsLoading(true);

        const username = values.username;

        try {
            const pass = await register( username.trim());
            setPassphrase(pass);
        } catch (err: any) {
            
        } finally {
            //setIsLoading(false);
        }
    };


    return (
        <div className={cn("flex flex-col gap-6", className)} {...props}>
            <Form {...form}>
                <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-8">
                    <div className="flex flex-col items-center gap-2">
                        <Link to="/" className="flex flex-col items-center gap-2 font-medium" >
                            <div className="flex size-8 items-center justify-center rounded-md">
                                <GalleryVerticalEnd className="size-6" />
                            </div>
                            <span className="sr-only">RevAI</span>
                        </Link>
                        <h1 className="text-xl font-bold">Welcome to RevAI</h1>
                        <div className="text-center text-sm">
                           Already have an account?{" "}
                            <Link to="/auth/register" className="underline underline-offset-4">
                                Sign in
                            </Link>
                        </div>
                    </div>
                    <div className="flex flex-col gap-6">
                        <div className="grid gap-3">
                            <FormField
                                control={form.control}
                                name="username"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Username</FormLabel>
                                        <FormControl>
                                            <Input placeholder="John" {...field} />
                                        </FormControl>
                                        <FormDescription>
                                            This is your displayed username.
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>
                        <Button type="submit" className="w-full">
                            Sign up
                        </Button>
                    </div>
                </form>
            </Form>

            <AlertDialog open={passphrase !== null}>
                <AlertDialogContent className="z-[51]">
                    <AlertDialogHeader>
                        <AlertDialogTitle>Here is your passphrase</AlertDialogTitle>
                        <AlertDialogDescription>
                            This passphrase is your private and unrecoverable way to login.
                            Make sure to save it in a secure location.
                        </AlertDialogDescription>
                        <PassphraseDisplay passphrase={passphrase!} showCopyButton={true} />
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogAction onClick={() => navigate("/")}>Continue</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            <div className="text-muted-foreground *:[a]:hover:text-primary text-center text-xs text-balance *:[a]:underline *:[a]:underline-offset-4">
                By clicking continue, you agree to our <a href="#">Terms of Service</a>{" "}
                and <a href="#">Privacy Policy</a>.
            </div>
        </div>
    )
}
