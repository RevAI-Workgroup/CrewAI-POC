


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

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"div">) {


    const [isLoading, setIsLoading] = useState(false);

    const formSchema = z.object({
        passphrase: z.string().min(1, {
          message: "Passphrase must be at least 1 characters.",
        }).refine((value) => isValidPassphraseFormat(value), {
            message: "Passphrase must be 6 words separated by hyphens (e.g., word-word-word-word-word-word)",
        }),
    })

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
          passphrase: "",
        },
    })


    const login = useAuthStore((state) => state.login);
    const navigate = useNavigate();

    // Validate passphrase format (6 words separated by hyphens)
    const isValidPassphraseFormat = (phrase: string): boolean => {
        const words = phrase.split('-');
        return words.length === 6 && words.every(word => word.length > 0);
    };

    const handleSubmit = async (values: z.infer<typeof formSchema>) => {

        setIsLoading(true);

        const passphrase = values.passphrase;

        try {
            await login( passphrase.trim());
            navigate('/');
        } catch (err: any) {
            if (err.message.includes('Invalid passphrase') || err.status === 401) {
                form.setError('passphrase', { message: 'Invalid passphrase. Please check and try again.' });
            } else {
                form.setError('passphrase', { message: err.message || 'Login failed' });
            }
        } finally {
            setIsLoading(false);
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
                            Don&apos;t have an account?{" "}
                            <Link to="/auth/register" className="underline underline-offset-4">
                                Sign up
                            </Link>
                        </div>
                    </div>
                    <div className="flex flex-col gap-6">
                        <div className="grid gap-3">
                            <FormField
                                control={form.control}
                                name="passphrase"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Passphrase</FormLabel>
                                        <FormControl>
                                            <Input placeholder="xxxxx-xxxxx-xxxxx-xxxxx-xxxxx-xxxxx" {...field} />
                                        </FormControl>
                                        <FormDescription>
                                            This is your private and unrecoverable passphrase.
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>
                        <Button type="submit" className="w-full">
                            Sign in
                        </Button>
                    </div>
                    
                </form>
            </Form>
            
            <div className="text-muted-foreground *:[a]:hover:text-primary text-center text-xs text-balance *:[a]:underline *:[a]:underline-offset-4">
                By clicking continue, you agree to our <a href="#">Terms of Service</a>{" "}
                and <a href="#">Privacy Policy</a>.
            </div>
        </div>
    )
}
