The project is presenting the following errors:

See this log for the ancestor stack trace.       
[browser] Uncaught Error: Hydration failed because the server rendered HTML didn't match the client. As a result this tree will be regenerated on the client. This can happen if a SSR-ed Client Component used:

- A server/client branch `if (typeof window !== 'undefined')`.
- Variable input such as `Date.now()` or `Math.random()` which changes each time it's called.     
- Date formatting in a user's locale which doesn't match the server.
- External changing data without sending a snapshot of it along with the HTML.
- Invalid HTML tag nesting.

It can also happen if the client has a browser extension installed which messes with the HTML befo

It can also happen if the client has a browser extension installed which messes with the HTML befoIt can also happen if the client has a browser extension installed which messes with the HTML befotension installed which messes with the HTML before React loaded.

https://react.dev/link/hydration-mismatch        
    at <unknown> (https://react.dev/link/hydration-mismatch)
    at button (<anonymous>)

https://react.dev/link/hydration-mismatch        
    at <unknown> (https://react.dev/link/hydration-mismatch)
    at button (<anonymous>)
https://react.dev/link/hydration-mismatch        
    at <unknown> (https://react.dev/link/hydration-mismatch)
    at button (<anonymous>)
n-mismatch)
    at button (<anonymous>)
    at button (<anonymous>)
    at Button (components/ui/button.tsx:50:5)    
    at Header (components/shell.tsx:70:15)       
    at Shell (components/shell.tsx:92:7)
    at RootLayout (app\layout.tsx:33:9)
  48 | }: ButtonPrimitive.Props & VariantProps...
  49 |   return (
> 50 |     <ButtonPrimitive
     |     ^
  51 |       data-slot="button"
  52 |       className={cn(buttonVariants({ va...
  53 |       {...props}
